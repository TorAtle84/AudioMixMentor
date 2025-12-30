from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    import librosa
except Exception:  # pragma: no cover
    librosa = None


@dataclass
class ReverbReport:
    depth_score: float
    forwardness_score: float
    note: str


def analyze_reverb(audio: np.ndarray, sr: int) -> ReverbReport:
    mono = np.mean(audio, axis=1) if audio.ndim > 1 else audio
    if librosa is None:
        rms = np.sqrt(np.mean(mono ** 2))
        depth_score = float(min(1.0, rms))
    else:
        rms_env = librosa.feature.rms(y=mono, frame_length=2048, hop_length=512)[0]
        high = np.percentile(rms_env, 85) + 1e-9
        low = np.percentile(rms_env, 15) + 1e-9
        depth_score = float(min(1.0, low / high))

    forwardness_score = float(max(0.0, 1.0 - depth_score))
    note = "Vocal feels forward." if forwardness_score > 0.6 else "Vocal depth may be pushing back."

    return ReverbReport(
        depth_score=depth_score,
        forwardness_score=forwardness_score,
        note=note,
    )
