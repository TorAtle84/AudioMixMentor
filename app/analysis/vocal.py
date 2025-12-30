from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np

try:
    from scipy.signal import stft, find_peaks
except Exception:  # pragma: no cover
    stft = None
    find_peaks = None


@dataclass
class VocalFindings:
    sibilance_severity: float
    plosive_severity: float
    resonance_bands_hz: List[int]
    roominess_score: float
    sibilance_bands: Dict[str, float]


def _mono(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return audio
    return np.mean(audio, axis=1)


def _band_energy(mag: np.ndarray, freqs: np.ndarray, low: float, high: float) -> float:
    idx = (freqs >= low) & (freqs < high)
    if not np.any(idx):
        return 0.0
    return float(np.mean(mag[idx]))


def analyze_vocal(audio: np.ndarray, sr: int) -> VocalFindings:
    mono = _mono(audio)
    if stft is None:
        raise RuntimeError("scipy is required for vocal analysis")
    freqs, _, spec = stft(mono, fs=sr, nperseg=4096, noverlap=2048)
    mag = np.abs(spec) + 1e-9
    avg = np.mean(mag, axis=1)

    sibilance = _band_energy(avg, freqs, 5000, 10000)
    presence = _band_energy(avg, freqs, 2000, 5000) + 1e-9
    sibilance_ratio = sibilance / presence
    sibilance_severity = float(min(1.0, sibilance_ratio / 0.7))

    low_band = _band_energy(avg, freqs, 20, 150)
    mid_band = _band_energy(avg, freqs, 150, 400)
    plosive_ratio = low_band / (mid_band + 1e-9)
    plosive_severity = float(min(1.0, plosive_ratio / 1.2))

    resonance_bands: List[int] = []
    if find_peaks is not None:
        peaks, _ = find_peaks(avg, height=np.percentile(avg, 85))
        resonance_candidates = [int(freqs[idx]) for idx in peaks if 200 <= freqs[idx] <= 6000]
        resonance_bands = resonance_candidates[:5]

    roominess_ratio = _band_energy(avg, freqs, 200, 600) / (_band_energy(avg, freqs, 2000, 6000) + 1e-9)
    roominess_score = float(min(1.0, roominess_ratio / 0.8))

    sibilance_bands = {
        "5-7k": float(_band_energy(avg, freqs, 5000, 7000)),
        "7-10k": float(_band_energy(avg, freqs, 7000, 10000)),
        "10-12k": float(_band_energy(avg, freqs, 10000, 12000)),
    }

    return VocalFindings(
        sibilance_severity=sibilance_severity,
        plosive_severity=plosive_severity,
        resonance_bands_hz=resonance_bands,
        roominess_score=roominess_score,
        sibilance_bands=sibilance_bands,
    )
