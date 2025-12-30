from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    from scipy.signal import stft
except Exception:  # pragma: no cover
    stft = None


@dataclass
class LowEndReport:
    low_end_score: float
    wide_sub_flag: bool
    side_energy_ratio: float
    note: str


def analyze_low_end(audio: np.ndarray, sr: int) -> LowEndReport:
    if stft is None:
        raise RuntimeError("scipy is required for low-end analysis")
    if audio.ndim == 1:
        audio = audio[:, None]
    left = audio[:, 0]
    right = audio[:, 1] if audio.shape[1] > 1 else audio[:, 0]
    mid = 0.5 * (left + right)
    side = 0.5 * (left - right)

    freqs, _, spec_mid = stft(mid, fs=sr, nperseg=4096, noverlap=2048)
    _, _, spec_side = stft(side, fs=sr, nperseg=4096, noverlap=2048)
    mag_mid = np.mean(np.abs(spec_mid), axis=1)
    mag_side = np.mean(np.abs(spec_side), axis=1)

    idx = (freqs >= 20) & (freqs < 120)
    mid_energy = float(np.mean(mag_mid[idx])) if np.any(idx) else 0.0
    side_energy = float(np.mean(mag_side[idx])) if np.any(idx) else 0.0
    ratio = side_energy / (mid_energy + 1e-9)

    low_end_score = float(max(0.0, 100.0 - ratio * 120.0))
    wide_sub = ratio > 0.25
    note = "Sub energy is centered." if not wide_sub else "Wide sub detected; mono the sub-bass for safer translation."

    return LowEndReport(
        low_end_score=low_end_score,
        wide_sub_flag=wide_sub,
        side_energy_ratio=ratio,
        note=note,
    )
