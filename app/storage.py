from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from .config import settings


def ensure_dirs() -> None:
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.results_dir).mkdir(parents=True, exist_ok=True)


def safe_extension(filename: Optional[str]) -> str:
    if not filename:
        return ""
    _, ext = os.path.splitext(filename)
    return ext.lower()


async def save_upload(upload: UploadFile, dest_path: str) -> None:
    """Stream upload to disk to avoid holding large files in memory."""
    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
    chunk_size = 1024 * 1024
    with open(dest_path, "wb") as handle:
        while True:
            chunk = await upload.read(chunk_size)
            if not chunk:
                break
            handle.write(chunk)


def result_path(job_id: str) -> str:
    return os.path.join(settings.results_dir, f"{job_id}.json")
