from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np

try:
    from scipy.signal import stft
except Exception:  # pragma: no cover
    stft = None


@dataclass
class ArtifactReport:
    gating: bool
    warble: bool
    crackle: bool
    codec: Optional[str]
    notes: List[str]


def detect_artifacts(audio: np.ndarray, sr: int, extension: str) -> ArtifactReport:
    mono = np.mean(audio, axis=1) if audio.ndim > 1 else audio
    frame = int(0.05 * sr)
    hop = int(0.025 * sr)
    rms_vals = []
    for start in range(0, max(len(mono) - frame, 1), hop):
        chunk = mono[start : start + frame]
        if len(chunk) == 0:
            continue
        rms_vals.append(np.sqrt(np.mean(chunk ** 2)))
    rms_vals = np.array(rms_vals) if rms_vals else np.array([np.sqrt(np.mean(mono ** 2))])

    gating = bool(np.percentile(rms_vals, 5) < np.percentile(rms_vals, 60) * 0.15)

    crackle = bool(np.mean(np.abs(np.diff(np.sign(mono)))) > 1.5)

    warble = False
    if stft is not None:
        _, _, spec = stft(mono, fs=sr, nperseg=2048, noverlap=1024)
        flux = np.mean(np.diff(np.abs(spec), axis=1) ** 2, axis=0)
        warble = bool(np.std(flux) > np.mean(flux) * 2.0)

    codec = extension if extension in {".mp3", ".aac", ".m4a"} else None
    notes: List[str] = []
    if gating:
        notes.append("Gating artifacts suspected in low-level passages.")
    if warble:
        notes.append("Noise reduction warble/chirp patterns detected.")
    if crackle:
        notes.append("Crackle-like discontinuities detected.")
    if codec:
        notes.append("Lossy codec artifacts possible due to compressed source.")

    return ArtifactReport(
        gating=gating,
        warble=warble,
        crackle=crackle,
        codec=codec,
        notes=notes,
    )
