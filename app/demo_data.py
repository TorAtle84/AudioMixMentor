from __future__ import annotations

import random
from typing import Any, Dict, Optional


def demo_result(job_id: str, mode: str, genre: str, vocal_style: Optional[str]) -> Dict[str, Any]:
    rng = random.Random(42)
    scores = {
        "loudness": rng.randint(70, 92),
        "spectral_balance": rng.randint(65, 90),
        "stereo": rng.randint(60, 88),
        "dynamics": rng.randint(55, 85),
        "noise": rng.randint(70, 95),
    }

    report: Dict[str, Any] = {
        "job_id": job_id,
        "mode": mode,
        "genre": genre,
        "vocal_style": vocal_style,
        "duration_sec": 184.0,
        "summary": "Demo report: balanced mix with targeted improvements.",
        "scores": scores,
        "recommendations": {
            "recording": ["Demo: tighten mic technique to reduce plosives."],
            "mixing": ["Demo: add 1-2 dB presence around 3 kHz."],
        },
        "metrics": {
            "loudness": {
                "integrated_lufs": -13.2,
                "short_term_lufs": -11.0,
                "true_peak_db": -0.8,
                "sample_peak_db": -1.2,
                "crest_factor_db": 9.8,
                "dynamic_range_db": 7.2,
                "noise_floor_db": -52.0,
            },
            "spectral": {
                "band_energies_db": {
                    "sub": -35.0,
                    "low": -28.0,
                    "low_mid": -26.0,
                    "mid": -24.0,
                    "high_mid": -22.0,
                    "high": -21.0,
                    "air": -27.0,
                },
                "spectral_tilt_db_per_oct": -0.9,
                "centroid_hz": 2150.0,
                "rolloff_hz": 8500.0,
            },
            "stereo": {
                "width": 0.32,
                "correlation": 0.4,
                "mono_compatibility": 0.9,
            },
        },
        "warnings": [],
        "appendix": {
            "notes": "Demo mode metrics; upload audio for real analysis.",
        },
    }

    if mode in {"instrumental", "mix"}:
        report["bpm_key"] = {
            "bpm": 142.0,
            "confidence": 0.74,
            "warning": None,
            "key": "A minor",
            "key_confidence": 0.61,
            "note": "Best guess only; tempo/key can be ambiguous.",
        }
    if mode == "mix":
        report["ab_compare"] = {
            "loudness_diff_lufs": -1.2,
            "short_term_diff_lufs": -0.6,
            "true_peak_diff_db": 0.3,
            "spectral_diff_summary": "Mix is slightly darker than the reference.",
            "stereo_diff_summary": "Stereo width is close to the reference.",
            "phase_corr_diff": -0.08,
            "dynamics_diff_summary": "Mix is slightly more compressed than the reference.",
            "match_suggestions": [
                "Raise high-end shelf by ~1 dB above 8 kHz.",
                "Ease bus compression for more punch.",
            ],
        }

    return report
