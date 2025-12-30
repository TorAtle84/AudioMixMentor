from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ABComparison:
    loudness_diff_lufs: float
    short_term_diff_lufs: float
    true_peak_diff_db: float
    spectral_diff_summary: str
    stereo_diff_summary: str
    phase_corr_diff: float
    dynamics_diff_summary: str
    match_suggestions: List[str]


def compare_ab(mix_metrics: Dict[str, float], ref_metrics: Dict[str, float]) -> ABComparison:
    loudness_diff = mix_metrics["integrated_lufs"] - ref_metrics["integrated_lufs"]
    short_term_diff = mix_metrics["short_term_lufs"] - ref_metrics["short_term_lufs"]
    true_peak_diff = mix_metrics["true_peak_db"] - ref_metrics["true_peak_db"]

    spectral_diff = mix_metrics["spectral_tilt_db_per_oct"] - ref_metrics["spectral_tilt_db_per_oct"]
    stereo_diff = mix_metrics["stereo_width"] - ref_metrics["stereo_width"]
    phase_corr_diff = mix_metrics.get("stereo_correlation", 0.0) - ref_metrics.get("stereo_correlation", 0.0)
    dynamics_diff = mix_metrics["crest_factor_db"] - ref_metrics["crest_factor_db"]

    spectral_summary = ""
    if spectral_diff > 0.6:
        spectral_summary = "Mix is brighter than the reference."
    elif spectral_diff < -0.6:
        spectral_summary = "Mix is darker than the reference."
    else:
        spectral_summary = "Spectral tilt is close to the reference."

    stereo_summary = ""
    if stereo_diff > 0.2:
        stereo_summary = "Mix is wider than the reference."
    elif stereo_diff < -0.2:
        stereo_summary = "Mix is narrower than the reference."
    else:
        stereo_summary = "Stereo width is close to the reference."

    if abs(phase_corr_diff) > 0.1:
        stereo_summary += " Phase correlation differs; check mono compatibility."

    dynamics_summary = ""
    if dynamics_diff > 2.0:
        dynamics_summary = "Mix has more dynamic range than the reference."
    elif dynamics_diff < -2.0:
        dynamics_summary = "Mix is more compressed than the reference."
    else:
        dynamics_summary = "Dynamics are close to the reference."

    suggestions: List[str] = []
    if loudness_diff < -1.0:
        suggestions.append("Increase overall loudness slightly while preserving transients.")
    elif loudness_diff > 1.0:
        suggestions.append("Reduce overall loudness to match the reference headroom.")

    if true_peak_diff > 1.0:
        suggestions.append("Lower limiter ceiling or reduce peaks to align true peak.")

    if spectral_diff > 0.6:
        suggestions.append("Tame high-end or add warmth in low-mids for a closer tonal balance.")
    elif spectral_diff < -0.6:
        suggestions.append("Add presence/air to approach the reference brightness.")

    if stereo_diff > 0.2:
        suggestions.append("Narrow wide elements or check mono compatibility for closer width.")
    elif stereo_diff < -0.2:
        suggestions.append("Enhance stereo width with subtle mid/side EQ or spatial effects.")

    if dynamics_diff < -2.0:
        suggestions.append("Ease bus compression to regain punch and crest factor.")

    if not suggestions:
        suggestions.append("Overall close to the reference; focus on minor tweaks only.")

    return ABComparison(
        loudness_diff_lufs=loudness_diff,
        short_term_diff_lufs=short_term_diff,
        true_peak_diff_db=true_peak_diff,
        spectral_diff_summary=spectral_summary,
        stereo_diff_summary=stereo_summary,
        phase_corr_diff=phase_corr_diff,
        dynamics_diff_summary=dynamics_summary,
        match_suggestions=suggestions,
    )
