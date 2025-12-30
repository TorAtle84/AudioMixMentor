from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np

try:
    import pyloudnorm as pyln
except Exception:  # pragma: no cover - optional dependency
    pyln = None

try:
    from scipy.signal import resample_poly, stft
except Exception:  # pragma: no cover - optional dependency
    resample_poly = None
    stft = None


@dataclass
class LoudnessMetrics:
    integrated_lufs: float
    short_term_lufs: float
    true_peak_db: float
    sample_peak_db: float
    crest_factor_db: float
    dynamic_range_db: float
    noise_floor_db: float


@dataclass
class SpectralMetrics:
    band_energies_db: Dict[str, float]
    spectral_tilt_db_per_oct: float
    centroid_hz: float
    rolloff_hz: float


@dataclass
class StereoMetrics:
    width: float
    correlation: float
    mono_compatibility: float


def _mono(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return audio
    return np.mean(audio, axis=1)


def _db(value: float, floor: float = 1e-9) -> float:
    return 20.0 * np.log10(max(value, floor))


def _rms(signal: np.ndarray) -> float:
    return float(np.sqrt(np.mean(signal ** 2)))


def _windowed_rms(signal: np.ndarray, window: int, hop: int) -> List[float]:
    rms_vals = []
    for start in range(0, max(len(signal) - window, 1), hop):
        chunk = signal[start : start + window]
        if len(chunk) == 0:
            continue
        rms_vals.append(_rms(chunk))
    return rms_vals or [_rms(signal)]


def _spectral_features(mono: np.ndarray, sr: int) -> SpectralMetrics:
    if stft is None:
        raise RuntimeError("scipy is required for spectral metrics")
    freqs, _, spec = stft(mono, fs=sr, nperseg=4096, noverlap=2048)
    mag = np.abs(spec) + 1e-9
    avg_mag = np.mean(mag, axis=1)

    bands = {
        "sub": (20, 60),
        "low": (60, 150),
        "low_mid": (150, 400),
        "mid": (400, 2000),
        "high_mid": (2000, 6000),
        "high": (6000, 16000),
        "air": (16000, 20000),
    }
    band_energies_db: Dict[str, float] = {}
    for name, (low, high) in bands.items():
        idx = (freqs >= low) & (freqs < high)
        energy = float(np.mean(avg_mag[idx])) if np.any(idx) else 0.0
        band_energies_db[name] = _db(energy)

    # Spectral tilt via linear regression of log-frequency vs log-magnitude
    valid = (freqs > 20) & (freqs < 20000)
    log_f = np.log2(freqs[valid] + 1e-9)
    log_m = np.log10(avg_mag[valid] + 1e-9)
    if len(log_f) > 1:
        slope = np.polyfit(log_f, log_m, 1)[0]
        spectral_tilt = float(slope * 20.0)  # approx dB per octave
    else:
        spectral_tilt = 0.0

    # Spectral centroid and rolloff
    freqs_valid = freqs[valid]
    mag_valid = avg_mag[valid]
    centroid = float(np.sum(freqs_valid * mag_valid) / np.sum(mag_valid))
    cumulative = np.cumsum(mag_valid)
    rolloff_threshold = 0.85 * cumulative[-1]
    rolloff = float(freqs_valid[np.searchsorted(cumulative, rolloff_threshold)])

    return SpectralMetrics(
        band_energies_db=band_energies_db,
        spectral_tilt_db_per_oct=spectral_tilt,
        centroid_hz=centroid,
        rolloff_hz=rolloff,
    )


def _true_peak_db(audio: np.ndarray, oversample: int = 4) -> float:
    if resample_poly is not None:
        up = resample_poly(audio, oversample, 1, axis=0)
        peak = float(np.max(np.abs(up)))
    else:
        peak = float(np.max(np.abs(audio)))
    return _db(peak)


def compute_loudness(audio: np.ndarray, sr: int) -> LoudnessMetrics:
    mono = _mono(audio)
    if pyln is None:
        raise RuntimeError("pyloudnorm is required for loudness metrics")
    meter = pyln.Meter(sr)
    integrated = float(meter.integrated_loudness(mono))

    window = int(3.0 * sr)
    hop = int(1.0 * sr)
    short_terms = []
    for start in range(0, max(len(mono) - window, 1), hop):
        chunk = mono[start : start + window]
        if len(chunk) < window:
            continue
        short_terms.append(float(meter.integrated_loudness(chunk)))
    short_term = float(np.percentile(short_terms, 90)) if short_terms else integrated

    sample_peak = float(np.max(np.abs(audio)))
    true_peak = _true_peak_db(audio)
    sample_peak_db = _db(sample_peak)

    rms = _rms(mono)
    crest = _db(sample_peak / (rms + 1e-9))

    rms_windows = _windowed_rms(mono, int(0.5 * sr), int(0.25 * sr))
    rms_db = [_db(val) for val in rms_windows]
    dynamic_range = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 10))
    noise_floor = float(np.percentile(rms_db, 10))

    return LoudnessMetrics(
        integrated_lufs=integrated,
        short_term_lufs=short_term,
        true_peak_db=true_peak,
        sample_peak_db=sample_peak_db,
        crest_factor_db=crest,
        dynamic_range_db=dynamic_range,
        noise_floor_db=noise_floor,
    )


def compute_spectral(audio: np.ndarray, sr: int) -> SpectralMetrics:
    mono = _mono(audio)
    return _spectral_features(mono, sr)


def compute_stereo(audio: np.ndarray) -> StereoMetrics:
    if audio.ndim == 1 or audio.shape[1] == 1:
        return StereoMetrics(width=0.0, correlation=1.0, mono_compatibility=1.0)
    left = audio[:, 0]
    right = audio[:, 1]
    mid = 0.5 * (left + right)
    side = 0.5 * (left - right)
    mid_energy = float(np.mean(mid ** 2) + 1e-9)
    side_energy = float(np.mean(side ** 2) + 1e-9)
    width = float(side_energy / mid_energy)
    corr = float(np.corrcoef(left, right)[0, 1]) if len(left) > 1 else 1.0
    mono_compat = float(1.0 - max(0.0, -corr))
    return StereoMetrics(width=width, correlation=corr, mono_compatibility=mono_compat)
