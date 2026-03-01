# Module: Snapshot Assembly & JSON Export

## Overview

`storage/snapshot.py` transforms raw LinkedIn API data into a structured snapshot dict suitable for persistence and future LLM analysis. It validates all incoming data through Pydantic models before processing, resolves demographic URNs to human-readable names, and writes snapshots to JSON files on disk.

---

## File Path

`src/linkedin_action_center/storage/snapshot.py`

---

## Components & Explanation

### Validation

- **`_validate_list(raw_items, model_cls, label)`** — Validate a list of raw dicts through a Pydantic model class. Returns valid dicts; invalid items are logged and skipped. This is the data quality gate — bad API records never reach the database.

### Helper Functions

- **`_extract_id_from_urn(urn)`** — Extract trailing numeric ID from a LinkedIn URN (e.g. `urn:li:sponsoredCampaign:123` -> `123`).
- **`_aggregate_metrics(rows)`** — Sum core metrics across rows and compute derived ratios: CTR, CPC, CPM, CPL.
- **`_daily_time_series(rows)`** — Collapse metric rows into date-sorted daily time series with per-day aggregation.
- **`_resolve_urn_locally(urn)`** — Best-effort local resolution of LinkedIn URNs using static enum maps (seniority, company size, job function). No API call needed.
- **`_top_demographics(demo_rows, urn_names=None, top_n=10)`** — Return top N demographic segments ranked by impressions with share-of-impressions. Uses API-resolved names first, then local enum lookup, then raw URN as fallback.

### Static Enum Maps

The module contains three lookup maps for resolving LinkedIn entity URNs locally:
- **`_SENIORITY_MAP`** — Maps seniority IDs (1-10) to names (Unpaid, Training, Entry, Senior, Manager, Director, VP, CXO, Partner, Owner).
- **`_COMPANY_SIZE_MAP`** — Maps size codes (A-I) to ranges (Self-employed through 10,001+).
- **`_JOB_FUNCTION_MAP`** — Maps function IDs (1-26) to names (Accounting through Customer Success).

### Main Assembly

- **`assemble_snapshot(accounts, campaigns_list, creatives_list, camp_metrics, creat_metrics, demo_data, date_start, date_end)`** — Main assembly function.
  - **Purpose**: Combine all raw API data into a single structured dict.
  - **Validation gate**: All inputs are validated through their respective Pydantic models (`LinkedInAccount`, `LinkedInCampaign`, `LinkedInCreative`, `LinkedInAnalyticsRow`, `LinkedInDemographicRow`) before processing. Invalid records are logged and skipped.
  - **Inputs**: Lists of accounts, campaigns, creatives; metric lists; demographic dict; date range.
  - **Outputs**: Nested dict with `date_range`, `accounts` (each with `campaigns`, `creatives`, `audience_demographics`).
  - **Index building**: Campaigns, creatives, and metrics are indexed by ID/URN for efficient attachment.

- **`save_snapshot_json(snap, path=None)`** — Write snapshot to JSON file; returns path. Default filename: `snapshot_YYYYMMDDTHHMMSSZ.json`.

---

## Relationships

- Called by `main.py` and `cli.py` after fetchers and metrics return.
- Output feeds `persist_snapshot()` and `save_snapshot_json()`.
- Imports Pydantic models from `models/api_models` for validation.
- Reads `SNAPSHOT_DIR` from `core.config`.
- Uses `utils/logger` for logging validation failures.
- No direct DB access; transformation and validation only.

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
# snapshot["date_range"] = {"start": "2026-01-01", "end": "2026-03-01", "days": 59}
# snapshot["accounts"][0]["campaigns"][0]["daily_metrics"] = [{"date": "2026-01-01", "impressions": 1000, ...}]
# snapshot["accounts"][0]["audience_demographics"]["seniority"] = [{"segment": "Director", ...}]
```

---

## Edge Cases & Tips

- **Pydantic validation**: Invalid API records are silently skipped (logged at WARNING level). Check logs if data looks incomplete.
- **Campaign-creative linkage**: Creatives are indexed by `campaign` URN; campaigns must match that URN format.
- **Creative metrics**: Indexed by creative URN; `pivotValues` in API response must contain `sponsoredCreative` for correct mapping.
- **Demographics**: Keys are normalized (e.g. `MEMBER_JOB_TITLE` -> `job_title`); `_top_demographics` limits to top 10 per pivot.
- **URN resolution**: Three-tier fallback: (1) API-resolved name from `resolve_demographic_urns()`, (2) local enum map lookup, (3) raw URN string.
- **Empty data**: Handles empty metric lists; aggregates default to 0.
- **Backward compatibility**: If campaigns don't have `_account_id` tags, all campaigns are attached to every account.

---

## Architecture / Flow

```
Raw API data
    |
    └── assemble_snapshot(...)
            ├── Validation gate:
            │       ├── _validate_list(accounts, LinkedInAccount)
            │       ├── _validate_list(campaigns, LinkedInCampaign)
            │       ├── _validate_list(creatives, LinkedInCreative)
            │       ├── _validate_list(camp_metrics, LinkedInAnalyticsRow)
            │       └── _validate_list(demo_data[pivot], LinkedInDemographicRow)
            |
            ├── Index camp_metrics by campaign ID
            ├── Index creat_metrics by creative URN
            ├── Index creatives by campaign URN
            ├── Index campaigns by account ID
            |
            ├── For each account:
            │       For each campaign:
            │           _aggregate_metrics -> metrics_summary
            │           _daily_time_series -> daily_metrics
            │           Attach creatives with their metrics
            │       _top_demographics -> audience_demographics (top 10 per pivot)
            │           _resolve_urn_locally for seniority/size/function
            |
            └── return snapshot dict
    |
    └── save_snapshot_json(snapshot) -> data/snapshots/snapshot_*.json
```

---

## Advanced Notes

- Designed for LLM consumption; structure is self-contained and human-readable.
- `default=str` in `json.dumps` handles non-JSON-serializable types (e.g. datetime).
- `metrics_summary` and `daily_metrics` use different structures; repository maps both to DB columns.
- The validation gate uses `model_validate()` but returns the **original raw dicts** (not the Pydantic model instances) to preserve all original keys for downstream processing.
- Metrics tracked: impressions, clicks, spend, landing_page_clicks, conversions, likes, comments, shares, follows, leads, opens, sends.
