from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    import librosa
except Exception:  # pragma: no cover
    librosa = None


@dataclass
class TransientReport:
    punch_score: float
    limiter_vulnerability: float
    note: str


def analyze_transients(audio: np.ndarray, sr: int, crest_factor_db: float) -> TransientReport:
    mono = np.mean(audio, axis=1) if audio.ndim > 1 else audio
    if librosa is not None:
        onset_env = librosa.onset.onset_strength(y=mono, sr=sr)
        onset_score = float(np.percentile(onset_env, 85)) if len(onset_env) else 0.0
        onset_score = min(onset_score / 10.0, 1.0)
    else:
        onset_score = float(np.std(mono) / (np.mean(np.abs(mono)) + 1e-9))
        onset_score = min(onset_score, 1.0)

    punch_score = float(min(100.0, onset_score * 100.0))
    limiter_vulnerability = float(max(0.0, 100.0 - crest_factor_db * 5.0))
    note = "Transient detail looks healthy." if punch_score > 60 else "Transient punch may be softened."

    return TransientReport(
        punch_score=punch_score,
        limiter_vulnerability=limiter_vulnerability,
        note=note,
    )
