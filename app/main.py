from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .analysis import process_job
from .config import settings
from .demo_data import demo_result
from .jobs import JobStore, JobWorker
from .schemas import JobCreateResponse, JobStatusResponse
from .storage import ensure_dirs, result_path, safe_extension, save_upload
from .analysis.genre_profiles import load_profiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

store = JobStore()
worker = JobWorker(store, process_job)


@app.on_event("startup")
async def startup_event() -> None:
    ensure_dirs()
    asyncio.create_task(worker.run())


@app.get("/")
async def root() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/genres")
async def genres() -> dict:
    profiles = load_profiles()
    genre_list = [key for key in profiles.keys() if key != "default"]
    return {"genres": sorted(genre_list)}


@app.post("/api/jobs", response_model=JobCreateResponse)
async def create_job(
    mode: str = Form(...),
    genre: str = Form(...),
    vocal_style: Optional[str] = Form(None),
    demo: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    reference: Optional[UploadFile] = File(None),
) -> JobCreateResponse:
    job_id = str(uuid4())
    is_demo = str(demo).lower() in {"1", "true", "yes"}

    if is_demo:
        result = demo_result(job_id, mode, genre, vocal_style)
        await store.create(job_id, {"mode": mode, "genre": genre})
        await store.update(job_id, status="done", progress=1.0, stage="complete", result=result)
        with open(result_path(job_id), "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
        return JobCreateResponse(job_id=job_id, status="done")

    if audio is None:
        await store.create(job_id, {"mode": mode, "genre": genre})
        await store.update(job_id, status="failed", progress=1.0, stage="failed", error="Lydfil mangler")
        return JobCreateResponse(job_id=job_id, status="failed")

    ext = safe_extension(audio.filename)
    audio_path = os.path.join(settings.uploads_dir, f"{job_id}{ext or '.wav'}")
    await save_upload(audio, audio_path)

    reference_path = None
    if reference is not None:
        ref_ext = safe_extension(reference.filename)
        reference_path = os.path.join(settings.uploads_dir, f"{job_id}-ref{ref_ext or '.wav'}")
        await save_upload(reference, reference_path)

    payload = {
        "job_id": job_id,
        "mode": mode,
        "genre": genre,
        "vocal_style": vocal_style,
        "audio_path": audio_path,
        "reference_path": reference_path,
        "extension": ext,
    }

    await store.create(job_id, payload)
    await worker.enqueue(payload)
    return JobCreateResponse(job_id=job_id, status="queued")


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def job_status(job_id: str) -> JobStatusResponse:
    record = await store.get(job_id)
    if record is None:
        return JobStatusResponse(job_id=job_id, status="not_found", progress=0.0, stage="unknown")
    return JobStatusResponse(
        job_id=record.job_id,
        status=record.status,
        progress=record.progress,
        stage=record.stage,
        result=record.result,
        error=record.error,
    )


@app.get("/api/results/{job_id}")
async def job_result(job_id: str) -> JSONResponse:
    path = result_path(job_id)
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "Result not found"})
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return JSONResponse(content=data)
