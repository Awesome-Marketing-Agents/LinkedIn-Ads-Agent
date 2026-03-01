# Module: CRUD — Sync Log

## Overview

`sync_log.py` manages the sync audit trail: freshness gate (should we sync?), sync run lifecycle (start/finish), table row counts, and active campaign auditing for configuration issues.

---

## File Path

`backend/app/crud/sync_log.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `app.core.config.settings` | `FRESHNESS_TTL_MINUTES` for gate check |
| `app.models.sync.SyncLog` | Sync log table model |

---

## Components

### `should_sync(session, account_id, force) -> tuple[bool, str]`

```python
def should_sync(session: Session, account_id: str, force: bool = False) -> tuple[bool, str]:
```

**Purpose**: Freshness gate — check if an account needs syncing.

**Behavior**:
1. If `force=True`, returns `(True, "force=True")`
2. Queries last successful sync for the account
3. If no previous sync, returns `(True, "no previous successful sync")`
4. If elapsed time >= `FRESHNESS_TTL_MINUTES` (default 240), returns `(True, ...)`
5. Otherwise returns `(False, "fresh (...)")`

### `start_sync_run(session, account_id, trigger) -> int`

**Purpose**: Create a new sync_log entry and return its ID.

**Behavior**: Creates `SyncLog` with `started_at` timestamp and `trigger` ("manual"). Commits immediately.

### `finish_sync_run(session, run_id, status, stats) -> None`

**Purpose**: Update a sync_log entry with results.

**Parameters**:
- `status` — `"success"` or `"failed"`
- `stats` — Dict with `campaigns_fetched`, `creatives_fetched`, `api_calls_made`, `errors`

### `table_counts(session) -> dict[str, int]`

**Purpose**: Return row counts for 6 tables.

**Tables**: `ad_accounts`, `campaigns`, `creatives`, `campaign_daily_metrics`, `creative_daily_metrics`, `audience_demographics`.

**Implementation**: Raw SQL `SELECT COUNT(*) FROM {table}` for each table.

### `active_campaign_audit(session) -> list[dict]`

**Purpose**: Flag active campaigns with potential configuration issues.

**Flags**:
| Condition | Issue |
|-----------|-------|
| `offsite_delivery_enabled = true` | "LAN enabled" |
| `audience_expansion_enabled = true` | "Audience Expansion ON" |
| `cost_type = 'CPM'` | "Maximum Delivery (CPM)" |

**Returns**: `[{"name": "Campaign A", "issues": ["LAN enabled", "Audience Expansion ON"]}]`

---

## Code Snippet

```python
from app.crud.sync_log import should_sync, start_sync_run, finish_sync_run

should, reason = should_sync(session, "all")
if should:
    run_id = start_sync_run(session, "all", trigger="manual")
    # ... sync ...
    finish_sync_run(session, run_id, status="success", stats={"campaigns_fetched": 5})
```

---

## Relationships

- **Called by**: `services/sync.py` (start/finish), `routes/status.py` (table_counts, audit)
- **Uses**: `models/sync.py` for `SyncLog` table

---

## Known Gaps

- **Raw SQL in `table_counts()` and `active_campaign_audit()`** — Uses `text()` SQL strings
- **`should_sync()` not called by the current sync pipeline** — The pipeline always syncs; freshness gate is available but unused
