# Module: Snapshot Assembly & JSON Export

## Overview

`storage/snapshot.py` transforms raw LinkedIn API data into a structured snapshot dict suitable for persistence and future LLM analysis. It also writes snapshots to JSON files on disk.

---

## File Path

`src/linkedin_action_center/storage/snapshot.py`

---

## Components & Explanation

- **`_extract_id_from_urn(urn)`** — Extract trailing numeric ID from a LinkedIn URN (e.g. `urn:li:sponsoredCampaign:123` → `123`).
- **`_aggregate_metrics(rows)`** — Sum core metrics across rows and compute CTR, CPC, CPM, CPL.
- **`_daily_time_series(rows)`** — Collapse metric rows into date-sorted daily time series.
- **`_top_demographics(demo_rows, top_n=10)`** — Return top N demographic segments by impressions with share-of-impressions.

- **`assemble_snapshot(accounts, campaigns_list, creatives_list, camp_metrics, creat_metrics, demo_data, date_start, date_end)`** — Main assembly function.
  - **Purpose**: Combine all raw API data into a single structured dict.
  - **Inputs**: Lists of accounts, campaigns, creatives; metric lists; demographic dict; date range.
  - **Outputs**: Nested dict with `date_range`, `accounts` (each with `campaigns`, `creatives`, `audience_demographics`).
  - **Note**: Campaigns and creatives are flattened lists; assembly indexes them by ID/URN for correct attachment.

- **`save_snapshot_json(snap, path=None)`** — Write snapshot to JSON file; returns path. Default filename: `snapshot_YYYYMMDDTHHMMSSZ.json`.

---

## Relationships

- Called by `main.py` and `cli.py` after fetchers and metrics return.
- Output feeds `persist_snapshot()` and `save_snapshot_json()`.
- Reads `SNAPSHOT_DIR` from `core.config`.
- No direct DB access; transformation only.

---

## Example Code Snippets

```python
from linkedin_action_center.storage.snapshot import assemble_snapshot, save_snapshot_json
from datetime import date, timedelta

today = date.today()
date_start = today - timedelta(days=90)

snapshot = assemble_snapshot(
    accounts, all_campaigns, all_creatives,
    camp_metrics, creative_metrics, demographics,
    date_start, today,
)

# Save to JSON
path = save_snapshot_json(snapshot)
print(f"Saved to {path}")

# Snapshot structure
# snapshot["date_range"] = {"start": "2026-01-01", "end": "2026-02-22", "days": 52}
# snapshot["accounts"][0]["campaigns"][0]["daily_metrics"] = [{"date": "2026-01-01", "impressions": 1000, ...}]
```

---

## Edge Cases & Tips

- **Campaign–creative linkage**: Creatives are indexed by `campaign` URN; campaigns must match that URN format.
- **Creative metrics**: Indexed by creative URN; `pivotValues` in API response must contain `sponsoredCreative` for correct mapping.
- **Demographics**: Keys are normalized (e.g. `MEMBER_JOB_TITLE` → `job_title`); `_top_demographics` limits to top 10 per pivot.
- **Empty data**: Handles empty metric lists; aggregates default to 0.

---

## Architecture / Flow

```
Raw API data
    │
    └── assemble_snapshot(...)
            ├── Index camp_metrics by campaign ID
            ├── Index creat_metrics by creative URN
            ├── Index creatives by campaign URN
            ├── For each account:
            │       For each campaign:
            │           Aggregate metrics, build daily_metrics
            │           Attach creatives with their metrics
            │       Attach demographics (top 10 per pivot)
            └── return snapshot dict
    │
    └── save_snapshot_json(snapshot) → data/snapshots/snapshot_*.json
```

---

## Advanced Notes

- Designed for LLM consumption; structure is self-contained and human-readable.
- `default=str` in `json.dumps` handles non-JSON-serializable types (e.g. datetime).
- `metrics_summary` and `daily_metrics` use different structures; repository maps both to DB columns.
