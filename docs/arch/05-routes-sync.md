# Module: Sync Routes

## Overview

Sync routes expose the data synchronization pipeline via HTTP. A POST triggers a background sync job, and clients can subscribe to real-time progress via Server-Sent Events (SSE) or poll for job status.

---

## File Path

`backend/app/routes/sync.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `asyncio` | Background task creation, SSE timeout |
| `sse_starlette.sse.EventSourceResponse` | SSE streaming response |
| `app.core.deps.get_db` | Session generator passed to sync pipeline |
| `app.services.sync` | `create_job`, `get_job`, `run_sync` |

---

## Components

### `POST /sync`

```python
async def start_sync():
    job_id = f"sync-{int(time.time() * 1000)}"
    job = create_job(job_id)
    asyncio.create_task(run_sync(job, get_db))
    return {"job_id": job_id, "status": "running"}
```

**Purpose**: Launch a sync job in the background.

**Behavior**:
1. Generates a timestamped job ID
2. Creates a `SyncJob` in the in-memory store
3. Spawns `run_sync()` as an `asyncio.Task` (non-blocking)
4. Returns immediately with the job ID

**Returns**: `{"job_id": "sync-1709312400000", "status": "running"}`

### `GET /sync/{job_id}/stream`

```python
async def sync_stream(job_id: str):
```

**Purpose**: Stream sync progress events via SSE.

**Behavior**:
1. Looks up job from in-memory store, returns 404 if not found
2. Returns an `EventSourceResponse` that yields events from the job's `asyncio.Queue`
3. Each event is `{"step": "1/6", "detail": "Fetching ad accounts..."}`
4. Stream ends when step is `"done"` or `"error"`
5. 30-second timeout sends heartbeat `{"step": "heartbeat", "detail": "waiting..."}`
6. Checks `job.status` after timeout — breaks if no longer `"running"`

### `GET /sync/{job_id}`

```python
async def sync_status(job_id: str):
```

**Purpose**: Poll sync job status without SSE.

**Returns**: `{"id": "...", "status": "running|completed|failed", "result": {...}, "error": "..."}`

---

## Code Snippet

```python
# Frontend SSE subscription
const evtSource = new EventSource(`/api/v1/sync/${jobId}/stream`);
evtSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data.step, data.detail);
    if (data.step === "done" || data.step === "error") evtSource.close();
};
```

---

## Relationships

- **Uses**: `services/sync.py` for job management and pipeline execution — see [11-services-sync.md](11-services-sync.md)
- **Passes**: `get_db` generator function to `run_sync()` for session creation
- **Mounted by**: `routes/__init__.py` at `/sync` — see [02-routes-overview.md](02-routes-overview.md)

---

## Known Gaps

- **No concurrency control** — Multiple POST requests create multiple simultaneous sync jobs
- **In-memory job store** — Jobs are lost on server restart
- **No authentication** — Any client can trigger a sync
