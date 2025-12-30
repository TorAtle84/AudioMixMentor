from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

try:
    import librosa
except Exception:  # pragma: no cover
    librosa = None


MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


@dataclass
class TempoEstimate:
    bpm: float
    confidence: float
    half_double_warning: Optional[str]


@dataclass
class KeyEstimate:
    key: str
    confidence: float


def _mono(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return audio
    return np.mean(audio, axis=1)


def estimate_bpm(audio: np.ndarray, sr: int) -> TempoEstimate:
    if librosa is None:
        raise RuntimeError("librosa is required for BPM estimation")
    mono = _mono(audio)
    onset_env = librosa.onset.onset_strength(y=mono, sr=sr)
    tempi = librosa.beat.tempo(onset_envelope=onset_env, sr=sr, aggregate=None)
    tempo = float(np.median(tempi)) if len(tempi) else 0.0
    spread = float(np.std(tempi)) if len(tempi) > 1 else tempo * 0.1
    confidence = float(1.0 - min(1.0, spread / max(tempo, 1.0)))

    warning = None
    if 60 <= tempo <= 85:
        warning = "Possible double-time interpretation"
    elif 120 <= tempo <= 170:
        warning = "Possible half-time interpretation"

    return TempoEstimate(bpm=tempo, confidence=confidence, half_double_warning=warning)


def estimate_key(audio: np.ndarray, sr: int) -> KeyEstimate:
    if librosa is None:
        raise RuntimeError("librosa is required for key estimation")
    mono = _mono(audio)
    chroma = librosa.feature.chroma_cqt(y=mono, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)

    def score(profile: np.ndarray) -> Tuple[str, float]:
        scores = []
        for i in range(12):
            rotated = np.roll(profile, i)
            corr = np.corrcoef(chroma_mean, rotated)[0, 1]
            scores.append(corr)
        best = int(np.argmax(scores))
        return KEYS[best], float(max(scores))

    major_key, major_score = score(MAJOR_PROFILE)
    minor_key, minor_score = score(MINOR_PROFILE)

    if major_score >= minor_score:
        return KeyEstimate(key=f"{major_key} major", confidence=major_score)
    return KeyEstimate(key=f"{minor_key} minor", confidence=minor_score)
