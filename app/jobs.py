from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class JobRecord:
    job_id: str
    status: str
    created_at: float
    updated_at: float
    progress: float = 0.0
    stage: str = "queued"
    payload: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class JobStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobRecord] = {}
        self._lock = asyncio.Lock()

    async def create(self, job_id: str, payload: Dict[str, Any]) -> JobRecord:
        async with self._lock:
            record = JobRecord(
                job_id=job_id,
                status="queued",
                created_at=time.time(),
                updated_at=time.time(),
                payload=payload,
            )
            self._jobs[job_id] = record
            return record

    async def update(
        self,
        job_id: str,
        *,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        stage: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        async with self._lock:
            record = self._jobs.get(job_id)
            if not record:
                return
            if status is not None:
                record.status = status
            if progress is not None:
                record.progress = progress
            if stage is not None:
                record.stage = stage
            if result is not None:
                record.result = result
            if error is not None:
                record.error = error
            record.updated_at = time.time()

    async def get(self, job_id: str) -> Optional[JobRecord]:
        async with self._lock:
            return self._jobs.get(job_id)


class JobWorker:
    def __init__(self, store: JobStore, processor) -> None:
        self._queue: "asyncio.Queue[Dict[str, Any]]" = asyncio.Queue()
        self._store = store
        self._processor = processor
        self._running = False

    async def enqueue(self, payload: Dict[str, Any]) -> None:
        await self._queue.put(payload)

    async def run(self) -> None:
        if self._running:
            return
        self._running = True
        logger.info("Job worker started")
        while True:
            payload = await self._queue.get()
            job_id = payload.get("job_id")
            try:
                await self._store.update(job_id, status="processing", progress=0.05, stage="ingest")
                result = await self._processor(payload, self._store)
                await self._store.update(
                    job_id,
                    status="done",
                    progress=1.0,
                    stage="complete",
                    result=result,
                )
            except Exception as exc:
                logger.exception("Job failed: %s", job_id)
                await self._store.update(
                    job_id,
                    status="failed",
                    progress=1.0,
                    stage="failed",
                    error=str(exc),
                )
            finally:
                self._queue.task_done()
