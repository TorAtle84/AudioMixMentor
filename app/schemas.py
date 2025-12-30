from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


class JobCreateResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    stage: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
