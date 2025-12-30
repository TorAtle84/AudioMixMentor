from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

try:
    import soundfile as sf
except Exception:  # pragma: no cover - handled by fallback loader
    sf = None

try:
    from scipy.signal import resample_poly
except Exception:  # pragma: no cover - optional dependency
    resample_poly = None

try:
    import librosa
except Exception:  # pragma: no cover - optional dependency
    librosa = None


@dataclass
class AudioData:
    audio: np.ndarray
    sr: int
    duration_sec: float
    num_channels: int
    warnings: List[str]
    source_format: Optional[str]


def _resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr:
        return audio
    if resample_poly is not None:
        return resample_poly(audio, target_sr, orig_sr, axis=0)
    if librosa is None:
        raise RuntimeError("Resampling requires scipy or librosa")
    return librosa.resample(audio.T, orig_sr=orig_sr, target_sr=target_sr).T


def load_audio(path: str, target_sr: int = 48000) -> AudioData:
    warnings: List[str] = []
    ext = os.path.splitext(path)[1].lower()
    if ext == ".mp3":
        warnings.append("MP3-opplasting oppdaget; analysen kan være mindre nøyaktig.")

    audio = None
    sr = None
    source_format = None

    if sf is not None:
        try:
            info = sf.info(path)
            source_format = info.format
            audio, sr = sf.read(path, always_2d=True)
        except Exception:
            audio = None

    if audio is None:
        if librosa is None:
            raise RuntimeError("Audio loader not available. Install soundfile or librosa.")
        audio, sr = librosa.load(path, sr=None, mono=False)
        if audio.ndim == 1:
            audio = audio[None, :]
        audio = audio.T

    if audio.ndim == 1:
        audio = audio[:, None]

    if sr is None:
        raise RuntimeError("Could not determine sample rate")

    audio = _resample(audio, sr, target_sr)
    audio = np.ascontiguousarray(audio, dtype=np.float32)
    duration_sec = audio.shape[0] / float(target_sr)
    return AudioData(
        audio=audio,
        sr=target_sr,
        duration_sec=duration_sec,
        num_channels=audio.shape[1],
        warnings=warnings,
        source_format=source_format,
    )
