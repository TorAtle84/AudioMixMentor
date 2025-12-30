from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

try:
    from scipy.signal import stft
except Exception:  # pragma: no cover
    stft = None


@dataclass
class MaskingConflict:
    band_hz: str
    likely_sources: str
    note: str


def analyze_masking(audio: np.ndarray, sr: int) -> List[MaskingConflict]:
    if stft is None:
        raise RuntimeError("scipy is required for masking analysis")
    mono = np.mean(audio, axis=1) if audio.ndim > 1 else audio
    freqs, _, spec = stft(mono, fs=sr, nperseg=4096, noverlap=2048)
    mag = np.mean(np.abs(spec), axis=1) + 1e-9
    total = float(np.mean(mag))

    bands = [
        ("60-120 Hz", 60, 120, "kick + bass"),
        ("120-250 Hz", 120, 250, "bass grunntoner"),
        ("250-500 Hz", 250, 500, "lav-mellomtone grums"),
        ("1-2 kHz", 1000, 2000, "vokal kropp + gitarer"),
        ("2-4 kHz", 2000, 4000, "vokal presence + synther"),
        ("4-6 kHz", 4000, 6000, "skarptromme smekk + vokal kant"),
    ]

    scored = []
    for label, low, high, source in bands:
        idx = (freqs >= low) & (freqs < high)
        energy = float(np.mean(mag[idx])) if np.any(idx) else 0.0
        ratio = energy / (total + 1e-9)
        scored.append((ratio, label, source))

    top = sorted(scored, reverse=True)[:3]
    conflicts: List[MaskingConflict] = []
    for ratio, label, source in top:
        note = "Sannsynlig maskering på grunn av tett energi i dette båndet."
        conflicts.append(MaskingConflict(band_hz=label, likely_sources=source, note=note))
    return conflicts
