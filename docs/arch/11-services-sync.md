# Module: Sync Orchestration

## Overview

`sync.py` contains the complete data synchronization pipeline. It fetches all data from the LinkedIn API, assembles a snapshot, saves it to disk, persists it to PostgreSQL, and emits real-time progress events via an `asyncio.Queue` consumed by SSE.

---

## File Path

`backend/app/services/sync.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `asyncio` | Queue for SSE events, `gather` for parallel fetches |
| `app.core.security.AuthManager` | Token validation |
| `app.crud.*` | Database upsert functions |
| `app.linkedin.client.LinkedInClient` | API client |
| `app.linkedin.fetchers` | Entity fetchers |
| `app.linkedin.metrics` | Analytics and demographics fetchers |
| `app.services.snapshot` | Snapshot assembly and JSON export |
| `app.utils.logging` | `get_logger`, `log_sync_progress` |

---

## Components

### `SyncJob`

```python
class SyncJob:
    def __init__(self, job_id: str) -> None:
        self.id = job_id
        self.status: str = "running"
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.result: dict[str, Any] | None = None
        self.error: str | None = None

    def emit(self, step: str, detail: str) -> None:
        self.queue.put_nowait({"step": step, "detail": detail})
```

**Purpose**: Represents an in-flight sync operation. The `queue` is consumed by the SSE endpoint.

### `_jobs: dict[str, SyncJob]`

Module-level in-memory job store. Lost on process restart.

### `get_job(job_id: str) -> SyncJob | None`

Look up a job by ID.

### `create_job(job_id: str) -> SyncJob`

Create and store a new job.

### `run_sync(job: SyncJob, get_session_fn: Any) -> None` (async)

**Purpose**: Execute the full 10-step sync pipeline.

**Parameters**:
- `job` — SyncJob instance for status tracking and SSE events
- `get_session_fn` — Generator function (e.g., `get_db`) that yields database sessions

**Pipeline Steps**:

| Step | Emit | Action |
|------|------|--------|
| 1 | `"1/6"` | Check auth, create `LinkedInClient`, set 90-day date range |
| 2 | `"2/6"` | Fetch campaigns per account, tag with `_account_id` |
| 3 | `"3/6"` | Fetch creatives per account |
| 4-6 | `"4-6/6"` | Parallel: campaign metrics + creative metrics + demographics |
| — | — | Resolve content references for human-readable names |
| 7 | `"assemble"` | `assemble_snapshot()` with Pydantic validation |
| 8 | `"persist"` | `save_snapshot_json()` to `data/snapshots/` |
| 9 | `"persist"` | Database upserts: accounts → campaigns → metrics → creatives → demographics |
| 10 | `"done"` | Update sync_log, set job status to `"completed"` |

**Session Management**: The function receives `get_session_fn` (a generator factory), calls it to get a generator, then calls `next()` to get a session. This avoids FastAPI's dependency injection since `run_sync` runs as a background `asyncio.Task`.

**Error Handling**: On any exception, marks sync_log as `"failed"`, sets `job.status = "failed"`, emits error event, and logs with traceback.

**Database Persistence Order**:
```
for account in snapshot["accounts"]:
    upsert_account(session, account)
    for campaign in account["campaigns"]:
        upsert_campaign(session, account_id, campaign)
        upsert_campaign_daily_metrics(session, campaign)
        upsert_creatives(session, account_id, campaign)
        for creative in campaign["creatives"]:
            upsert_creative_daily_metrics(session, creative)
    upsert_demographics(session, account, date_range)
session.commit()
```

---

## Code Snippet

```python
# From routes/sync.py
job = create_job(job_id)
asyncio.create_task(run_sync(job, get_db))
```

---

## Relationships

- **Called by**: `routes/sync.py` via `asyncio.create_task`
- **Calls**: All `linkedin/` fetchers, `services/snapshot.py`, all `crud/` upsert functions
- **Depends on**: `core/security.py` for auth, `core/deps.py` for session factory

---

## Known Gaps

- **In-memory job store** — `_jobs` dict is lost on restart; no persistent job tracking
- **No concurrency guard** — Multiple syncs can run simultaneously
- **Single commit** — All upserts in one transaction; failure rolls back everything
- **No freshness check** — `should_sync()` exists in CRUD but isn't called here
