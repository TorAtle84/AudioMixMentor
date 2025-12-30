from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass
class QaReport:
    dc_offset_db: float
    channel_imbalance_db: float
    warnings: List[str]


def analyze_qa(audio: np.ndarray, sr: int) -> QaReport:
    mono = np.mean(audio, axis=1) if audio.ndim > 1 else audio
    dc_offset = float(np.mean(mono))
    dc_offset_db = 20.0 * np.log10(abs(dc_offset) + 1e-9)

    if audio.ndim > 1 and audio.shape[1] > 1:
        left = audio[:, 0]
        right = audio[:, 1]
        rms_left = np.sqrt(np.mean(left ** 2)) + 1e-9
        rms_right = np.sqrt(np.mean(right ** 2)) + 1e-9
        channel_imbalance_db = float(20.0 * np.log10(rms_left / rms_right))
    else:
        channel_imbalance_db = 0.0

    warnings: List[str] = []
    if abs(dc_offset_db) > -40.0:
        warnings.append("Detectable DC offset; consider high-pass filtering or re-export.")
    if abs(channel_imbalance_db) > 1.5:
        warnings.append("Channel imbalance detected; check stereo balance.")
    if sr not in {44100, 48000, 96000}:
        warnings.append("Non-standard sample rate detected; consider re-exporting at 48 kHz.")

    return QaReport(
        dc_offset_db=dc_offset_db,
        channel_imbalance_db=channel_imbalance_db,
        warnings=warnings,
    )
