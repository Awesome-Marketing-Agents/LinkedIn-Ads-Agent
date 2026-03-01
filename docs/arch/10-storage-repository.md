# Module: Repository (Data Access Layer)

## Overview

`storage/repository.py` is the data-access layer for the LinkedIn Ads SQLite database. It provides:

1. **Freshness gate** — `should_sync()`, `start_sync_run()`, `finish_sync_run()` to avoid redundant API calls.
2. **Snapshot persistence** — `persist_snapshot()` writes assembled snapshot data using SQLAlchemy Core `insert().on_conflict_do_update()` for true upserts.
3. **Read helpers** — `table_counts()` and `active_campaign_audit()` for status and diagnostics.

---

## File Path

`src/linkedin_action_center/storage/repository.py`

---

## Components & Explanation

### Freshness Gate

- **`should_sync(account_id, force=False, db_path=None)`** — Decide whether a sync is needed.
  - **Purpose**: Prevent redundant API calls by checking the last successful sync time.
  - **Inputs**: Account ID, optional force flag, optional db_path.
  - **Outputs**: `(bool, str)` — `(True, reason)` to sync, `(False, reason)` to skip.
  - **Logic**: Queries `sync_log` for the last `status='success'` row. Compares `finished_at` against `settings.freshness_ttl_minutes` (default: 240 minutes / 4 hours).

- **`start_sync_run(account_id, trigger="manual", db_path=None)`** — Insert a new `sync_log` row with `status='running'`. Returns the row ID for later update.

- **`finish_sync_run(run_id, status="success", stats=None, db_path=None)`** — Update the `sync_log` row with final status, timing, and stats (campaigns_fetched, creatives_fetched, api_calls_made, errors).

### Snapshot Persistence

- **`persist_snapshot(snap, db_path=None)`** — Write the full snapshot dict into SQLite using true upserts.
  - **Purpose**: Persist accounts, campaigns, creatives, metrics, and demographics.
  - **Inputs**: Snapshot dict from `assemble_snapshot()`, optional `db_path`.
  - **Outputs**: None; raises `StorageError` on failure.
  - **Flow**: Opens a SQLAlchemy `Session`, iterates accounts -> campaigns -> metrics -> creatives -> demographics, commits once at end.
  - **Upsert pattern**: Uses `insert(Model).values(**data).on_conflict_do_update(index_elements=[...], set_={...})` — this is a true upsert that updates existing rows and inserts new ones without data loss.

### Private Upsert Helpers

- **`_upsert_account(session, acct, now)`** — Upsert single ad account by `id`.
- **`_upsert_campaign(session, account_id, camp, now)`** — Upsert campaign with settings (budgets, targeting flags). Conflict key: `id`.
- **`_upsert_campaign_daily_metrics(session, camp, now)`** — Upsert daily metrics. Conflict key: `(campaign_id, date)`.
- **`_upsert_creatives(session, account_id, camp, now)`** — Upsert creatives. Conflict key: `id`. Preserves `created_at` on update.
- **`_upsert_demographics(session, acct, date_range, now)`** — Upsert demographic segments. Conflict key: `(account_id, pivot_type, segment, date_start)`.

### Read Helpers

- **`table_counts(db_path=None)`** — Return `dict[table_name, row_count]` for all six entity tables.
- **`active_campaign_audit(db_path=None)`** — Return list of active campaigns with potential issues (LAN enabled, Audience Expansion ON, CPM cost type).

---

## Relationships

- Uses `storage/database.get_connection()` (freshness gate) and `storage/database.get_engine()` (upserts).
- Imports SQLModel definitions from `models/db_models` for type-safe upserts.
- Called by `main.py` and `cli.py` after `assemble_snapshot()`.
- Expects snapshot structure from `storage/snapshot.assemble_snapshot()`.
- Raises `StorageError` (from `utils/errors`) on DB errors.
- Reads `settings.freshness_ttl_minutes` from `core/config`.

---

## Example Code Snippets

```python
from linkedin_action_center.storage.repository import (
    should_sync,
    start_sync_run,
    finish_sync_run,
    persist_snapshot,
    table_counts,
    active_campaign_audit,
)

# Check if sync is needed
needs_sync, reason = should_sync("12345")
if not needs_sync:
    print(f"Skipping: {reason}")
else:
    # Start tracking the sync run
    run_id = start_sync_run("12345", trigger="cli")

    # ... fetch data and assemble snapshot ...
    snapshot = assemble_snapshot(accounts, campaigns, creatives, ...)
    persist_snapshot(snapshot)

    # Finish with stats
    finish_sync_run(run_id, status="success", stats={
        "campaigns_fetched": 12,
        "creatives_fetched": 45,
        "api_calls_made": 8,
    })
```

```python
# Get row counts
counts = table_counts()
# {"ad_accounts": 1, "campaigns": 12, "creatives": 45, ...}

# Audit active campaigns
audit = active_campaign_audit()
for entry in audit:
    if entry["issues"]:
        print(f"{entry['name']}: {', '.join(entry['issues'])}")
```

---

## Edge Cases & Tips

- **Snapshot structure**: Must match `assemble_snapshot()` output; nested `campaigns` and `creatives` under each account.
- **True upserts**: `INSERT ON CONFLICT DO UPDATE` updates existing rows in-place. Unlike `INSERT OR REPLACE`, this preserves the row identity and does not delete/re-insert.
- **Composite primary keys**: Metrics tables use `(campaign_id, date)` or `(creative_id, date)` as conflict targets. Demographics use `(account_id, pivot_type, segment, date_start)`.
- **Freshness gate**: Default TTL is 4 hours (240 minutes). Use `force=True` to bypass.
- **Sync log**: Each sync run is tracked with timing, counts, and error details.
- **Audit issues**: Flags `offsite_delivery_enabled` (LAN), `audience_expansion_enabled`, and `cost_type == "CPM"` as potential concerns.

---

## Architecture / Flow

```
Sync Flow:
    |
    ├── should_sync(account_id)
    │       └── Query sync_log -> compare elapsed time vs TTL
    |
    ├── start_sync_run(account_id) -> run_id
    |
    ├── persist_snapshot(snap)
    │       └── SQLAlchemy Session:
    │               ├── For each account:
    │               │       ├── _upsert_account
    │               │       └── For each campaign:
    │               │               ├── _upsert_campaign
    │               │               ├── _upsert_campaign_daily_metrics
    │               │               └── _upsert_creatives
    │               │       └── _upsert_demographics
    │               └── session.commit()
    |
    └── finish_sync_run(run_id, status, stats)
```

---

## Advanced Notes

- Field mapping: API uses camelCase (e.g. `dailyBudget`); snapshot transforms to snake_case structures; repository maps from snapshot keys to DB columns.
- All upserts use SQLAlchemy Core `insert()` with `on_conflict_do_update()` — parameterized and SQL-injection safe.
- The `_upsert_creatives` helper preserves `created_at` on update (excluded from the update set) since creation time should never change.
- Error handling: All persistence is wrapped in try/except; failures raise `StorageError` with operation and table context.
- The freshness gate uses the legacy `get_connection()` interface (raw SQL) for simplicity, while upserts use the SQLAlchemy `get_engine()` interface.
