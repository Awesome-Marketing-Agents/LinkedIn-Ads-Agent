"""Sync routes: start sync job + SSE stream for progress."""

from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.core.deps import get_db
from app.services.sync import create_job, get_job, run_sync
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("")
async def start_sync():
    job_id = f"sync-{int(time.time() * 1000)}"
    job = create_job(job_id)

    # Run sync in background task
    asyncio.create_task(run_sync(job, get_db))

    return {"job_id": job_id, "status": "running"}


@router.get("/{job_id}/stream")
async def sync_stream(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        while True:
            try:
                data = await asyncio.wait_for(job.queue.get(), timeout=30.0)
                yield {"data": data}
                if data.get("step") in ("done", "error"):
                    break
            except asyncio.TimeoutError:
                yield {"data": {"step": "heartbeat", "detail": "waiting..."}}
                if job.status != "running":
                    break

    return EventSourceResponse(event_generator())


@router.get("/{job_id}")
async def sync_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "status": job.status,
        "result": job.result,
        "error": job.error,
    }
