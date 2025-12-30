from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from .genre_profiles import get_profile


def _score_range(value: float, target_min: float, target_max: float, scale: float = 100.0) -> float:
    if target_min <= value <= target_max:
        return scale
    if value < target_min:
        diff = target_min - value
    else:
        diff = value - target_max
    return max(0.0, scale - diff * 5.0)


def build_report(
    *,
    job_id: str,
    mode: str,
    genre: str,
    vocal_style: Optional[str],
    duration_sec: float,
    metrics: Dict[str, Any],
    warnings: List[str],
    bpm_key: Optional[Dict[str, Any]] = None,
    ab_compare: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    profile = get_profile(genre, mode, vocal_style)
    loudness_target = profile.get("lufs_target", [-16, -12])
    spectral_tilt_target = profile.get("spectral_tilt", [-1.5, -0.5])
    stereo_target = profile.get("stereo_width", [0.2, 0.5])
    crest_target = profile.get("crest_factor", [8, 14])

    loudness_metrics = metrics["loudness"]
    spectral_metrics = metrics["spectral"]
    stereo_metrics = metrics["stereo"]

    scores = {
        "loudness": _score_range(loudness_metrics["integrated_lufs"], loudness_target[0], loudness_target[1]),
        "spectral_balance": _score_range(
            spectral_metrics["spectral_tilt_db_per_oct"],
            spectral_tilt_target[0],
            spectral_tilt_target[1],
        ),
        "stereo": _score_range(stereo_metrics["width"], stereo_target[0], stereo_target[1]),
        "dynamics": _score_range(loudness_metrics["crest_factor_db"], crest_target[0], crest_target[1]),
        "noise": max(0.0, 100.0 - abs(loudness_metrics["noise_floor_db"]))
    }

    recording_fixes: List[str] = []
    mix_fixes: List[str] = []

    if loudness_metrics["true_peak_db"] > -1.0:
        mix_fixes.append("Reduser 'true-peak' ved å senke 'ceiling' på limiter eller justere gain.")

    if loudness_metrics["integrated_lufs"] < loudness_target[0]:
        mix_fixes.append("Øk total lydstyrke med forsiktig busskomprimering og limiting.")
    elif loudness_metrics["integrated_lufs"] > loudness_target[1]:
        mix_fixes.append("Reduser master gain for å treffe målet for sjangeren.")

    if spectral_metrics["spectral_tilt_db_per_oct"] < spectral_tilt_target[0]:
        mix_fixes.append("Legg til presence/luft for å balansere diskanten for sjangeren.")
    elif spectral_metrics["spectral_tilt_db_per_oct"] > spectral_tilt_target[1]:
        mix_fixes.append("Demp øvre mellomtone eller diskant for en mykere balanse.")

    if stereo_metrics["correlation"] < 0.0:
        mix_fixes.append("Sjekk monokompatibilitet; fasekorrelasjonen er negativ.")

    if "vocal" in metrics:
        vocal = metrics["vocal"]
        if vocal["sibilance_severity"] > 0.6:
            recording_fixes.append("Bruk en de-esser eller mykere mikrofonplassering for å kontrollere sibilans.")
        if vocal["plosive_severity"] > 0.6:
            recording_fixes.append("Bruk et pop-filter og øk mikrofonavstanden for å redusere plosiver.")
        if vocal["roominess_score"] > 0.6:
            recording_fixes.append("Reduser romrefleksjoner med demping eller tettere mikrofonteknikk.")

    if metrics.get("artifacts") and metrics["artifacts"]["notes"]:
        recording_fixes.extend(metrics["artifacts"]["notes"])

    if not recording_fixes:
        recording_fixes.append("Innspillingskvaliteten ser bra ut; fokuser på miksejusteringer.")
    if not mix_fixes:
        mix_fixes.append("Miksen er nær målet; gjør små justeringer i tone og lydstyrke.")

    executive_summary = "Totalbalansen er god, med noen få målrettede forbedringer nødvendig."
    if min(scores.values()) < 60:
        executive_summary = "Mikskvaliteten er ujevn; prioriter områdene med lavest score først."

    report: Dict[str, Any] = {
        "job_id": job_id,
        "mode": mode,
        "genre": genre,
        "vocal_style": vocal_style,
        "duration_sec": duration_sec,
        "summary": executive_summary,
        "scores": scores,
        "recommendations": {
            "recording": recording_fixes,
            "mixing": mix_fixes,
        },
        "metrics": metrics,
        "warnings": warnings,
    }

    if bpm_key:
        report["bpm_key"] = bpm_key
    if ab_compare:
        report["ab_compare"] = ab_compare

    report["appendix"] = {
        "notes": "Teknisk vedlegg inkluderer målte verdier for referanse.",
    }

    return report
