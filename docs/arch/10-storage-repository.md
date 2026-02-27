# Module: Repository (Data Access Layer)

## Overview

`storage/repository.py` is the data-access layer for the LinkedIn Ads SQLite database. Its main API is `persist_snapshot()`, which upserts an assembled snapshot into the normalized tables. It also provides read helpers for status and auditing.

---

## File Path

`src/linkedin_action_center/storage/repository.py`

---

## Components & Explanation

- **`persist_snapshot(snap, db_path=None)`** — Write the full snapshot dict into SQLite using `INSERT OR REPLACE`.
  - **Purpose**: Persist accounts, campaigns, creatives, metrics, and demographics.
  - **Inputs**: Snapshot dict from `assemble_snapshot()`, optional `db_path`.
  - **Outputs**: None; raises `StorageError` on failure.
  - **Flow**: Iterates accounts → campaigns → metrics → creatives → demographics; commits once at end.

- **`_upsert_account(cur, acct, now)`** — Upsert single ad account.
- **`_upsert_campaign(cur, account_id, camp, now)`** — Upsert campaign and its settings.
- **`_upsert_campaign_daily_metrics(cur, camp, now)`** — Upsert daily metric rows for a campaign.
- **`_upsert_creatives(cur, account_id, camp, now)`** — Upsert creatives for a campaign.
- **`_upsert_demographics(cur, acct, date_range, now)`** — Upsert audience demographic segments.

- **`table_counts(db_path=None)`** — Return `dict[table_name, row_count]` for all six tables.
- **`active_campaign_audit(db_path=None)`** — Return list of active campaigns with potential issues (LAN enabled, Audience Expansion ON, CPM cost type).

---

## Relationships

- Uses `storage/database.get_connection()`.
- Called by `main.py` and `cli.py` after `assemble_snapshot()`.
- Expects snapshot structure from `storage/snapshot.assemble_snapshot()`.
- Raises `StorageError` on DB errors.

---

## Example Code Snippets

```python
from linkedin_action_center.storage.repository import (
    persist_snapshot,
    table_counts,
    active_campaign_audit,
)

# After assembling snapshot
snapshot = assemble_snapshot(accounts, campaigns, creatives, camp_metrics, creat_metrics, demographics, date_start, date_end)
persist_snapshot(snapshot)

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
- **Upsert**: `INSERT OR REPLACE` overwrites existing rows; no separate update logic.
- **Demographics**: Stored per account; `date_range` from snapshot is used for `date_start`/`date_end`.
- **Audit issues**: Flags `offsite_delivery_enabled`, `audience_expansion_enabled`, and `cost_type == "CPM"` as potential concerns.

---

## Architecture / Flow

```
persist_snapshot(snap)
    │
    └── For each account:
            ├── _upsert_account
            └── For each campaign:
                    ├── _upsert_campaign
                    ├── _upsert_campaign_daily_metrics
                    ├── _upsert_creatives
            └── _upsert_demographics
    └── conn.commit()
```

---

## Advanced Notes

- Field mapping: API uses camelCase (e.g. `dailyBudget`); repository expects snake_case from snapshot (e.g. `daily_budget`).
- `creative_id` in `creative_daily_metrics` can be URN or ID depending on snapshot.
- All upserts use parameterized queries to avoid SQL injection.
