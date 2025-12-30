from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any, Dict, Optional

from .ab_compare import compare_ab
from .artifacts import detect_artifacts
from .bpm_key import estimate_bpm, estimate_key
from .ingest import load_audio
from .lowend import analyze_low_end
from .masking import analyze_masking
from .metrics import compute_loudness, compute_spectral, compute_stereo
from .reverb import analyze_reverb
from .report import build_report
from .transient import analyze_transients
from .vocal import analyze_vocal
from .qa import analyze_qa
from ..storage import result_path


async def process_job(payload: Dict[str, Any], store) -> Dict[str, Any]:
    job_id = payload["job_id"]
    mode = payload["mode"]
    genre = payload["genre"]
    vocal_style = payload.get("vocal_style")
    audio_path = payload.get("audio_path")
    reference_path = payload.get("reference_path")
    extension = payload.get("extension", "")

    audio_data = load_audio(audio_path)
    warnings = list(audio_data.warnings)
    await store.update(job_id, progress=0.2, stage="metrics")

    loudness = compute_loudness(audio_data.audio, audio_data.sr)
    spectral = compute_spectral(audio_data.audio, audio_data.sr)
    stereo = compute_stereo(audio_data.audio)
    await store.update(job_id, progress=0.35, stage="detectors")

    metrics: Dict[str, Any] = {
        "loudness": asdict(loudness),
        "spectral": asdict(spectral),
        "stereo": asdict(stereo),
    }

    if mode in {"vocal", "mix"}:
        vocal = analyze_vocal(audio_data.audio, audio_data.sr)
        reverb = analyze_reverb(audio_data.audio, audio_data.sr)
        metrics["vocal"] = asdict(vocal)
        metrics["reverb"] = asdict(reverb)

    if mode in {"instrumental", "mix"}:
        masking = analyze_masking(audio_data.audio, audio_data.sr)
        low_end = analyze_low_end(audio_data.audio, audio_data.sr)
        transient = analyze_transients(audio_data.audio, audio_data.sr, loudness.crest_factor_db)
        metrics["masking"] = [asdict(item) for item in masking]
        metrics["low_end"] = asdict(low_end)
        metrics["transient"] = asdict(transient)

    artifacts = detect_artifacts(audio_data.audio, audio_data.sr, extension)
    qa = analyze_qa(audio_data.audio, audio_data.sr)
    metrics["artifacts"] = asdict(artifacts)
    metrics["qa"] = asdict(qa)
    warnings.extend(qa.warnings)
    warnings.extend(artifacts.notes)

    bpm_key: Optional[Dict[str, Any]] = None
    if mode in {"instrumental", "mix"}:
        tempo = estimate_bpm(audio_data.audio, audio_data.sr)
        key = estimate_key(audio_data.audio, audio_data.sr)
        bpm_key = {
            "bpm": tempo.bpm,
            "confidence": tempo.confidence,
            "warning": tempo.half_double_warning,
            "key": key.key,
            "key_confidence": key.confidence,
            "note": "Best guess only; tempo/key can be ambiguous.",
        }

    await store.update(job_id, progress=0.6, stage="report")

    ab_report: Optional[Dict[str, Any]] = None
    if mode == "mix" and reference_path:
        ref_audio = load_audio(reference_path)
        ref_loudness = compute_loudness(ref_audio.audio, ref_audio.sr)
        ref_spectral = compute_spectral(ref_audio.audio, ref_audio.sr)
        ref_stereo = compute_stereo(ref_audio.audio)
        ref_metrics = {
            "integrated_lufs": ref_loudness.integrated_lufs,
            "short_term_lufs": ref_loudness.short_term_lufs,
            "true_peak_db": ref_loudness.true_peak_db,
            "crest_factor_db": ref_loudness.crest_factor_db,
            "spectral_tilt_db_per_oct": ref_spectral.spectral_tilt_db_per_oct,
            "stereo_width": ref_stereo.width,
            "stereo_correlation": ref_stereo.correlation,
        }
        mix_metrics = {
            "integrated_lufs": loudness.integrated_lufs,
            "short_term_lufs": loudness.short_term_lufs,
            "true_peak_db": loudness.true_peak_db,
            "crest_factor_db": loudness.crest_factor_db,
            "spectral_tilt_db_per_oct": spectral.spectral_tilt_db_per_oct,
            "stereo_width": stereo.width,
            "stereo_correlation": stereo.correlation,
        }
        ab_report = asdict(compare_ab(mix_metrics, ref_metrics))

    await store.update(job_id, progress=0.8, stage="summarizing")

    report = build_report(
        job_id=job_id,
        mode=mode,
        genre=genre,
        vocal_style=vocal_style,
        duration_sec=audio_data.duration_sec,
        metrics=_serialize_metrics(metrics),
        warnings=warnings,
        bpm_key=bpm_key,
        ab_compare=ab_report,
    )

    with open(result_path(job_id), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    return report


def _serialize_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all metrics are JSON-serializable."""
    serialized: Dict[str, Any] = {}
    for key, value in metrics.items():
        if hasattr(value, "__dict__"):
            serialized[key] = value.__dict__
        else:
            serialized[key] = value
    return serialized
