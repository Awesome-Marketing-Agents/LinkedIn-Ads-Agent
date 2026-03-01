# Module: Snapshot Assembly

## Overview

`snapshot.py` transforms raw LinkedIn API data into a structured, validated snapshot dict. It validates all data through Pydantic models, aggregates metrics (CTR, CPC, CPM, CPL), resolves demographic URNs to human-readable names, and builds daily time series. The snapshot is the canonical intermediate format between API data and database persistence.

---

## File Path

`backend/app/services/snapshot.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `pydantic.ValidationError` | Catch validation failures |
| `app.models.linkedin_api` | Pydantic models for validation gate |
| `app.utils.logging.get_logger` | Logging |

---

## Components

### `_extract_id_from_urn(urn: str) -> str`

Extract the numeric ID from a LinkedIn URN. `"urn:li:sponsoredCampaign:12345"` → `"12345"`.

### `_aggregate_metrics(rows: list[dict]) -> dict`

**Purpose**: Sum 12 raw metric fields across all rows and compute derived metrics.

**Computed fields**: `ctr` (%), `cpc`, `cpm`, `cpl` — all rounded.

### `_daily_time_series(rows: list[dict]) -> list[dict]`

**Purpose**: Group metric rows by date, aggregate per day, compute daily CTR and CPC.

**Returns**: Sorted list of daily metric dicts.

### Static Lookup Maps

| Map | Purpose |
|-----|---------|
| `_SENIORITY_MAP` | 10 seniority levels (1="Unpaid" through 10="Owner") |
| `_COMPANY_SIZE_MAP` | 9 company size ranges (A="Self-employed" through I="10,001+") |
| `_JOB_FUNCTION_MAP` | 26 job functions (1="Accounting" through 26="Customer Success") |

### `_resolve_urn_locally(urn: str) -> str`

**Purpose**: Resolve demographic URNs to human-readable names using the static lookup maps. Returns empty string if URN type is not recognized.

### `_top_demographics(demo_rows, urn_names, top_n) -> list[dict]`

**Purpose**: Sort demographic rows by impressions, take top N, compute share percentages.

**Returns**: List of `{segment, segment_urn, impressions, clicks, ctr, share_of_impressions}`.

### `_validate_list(raw_items, model_cls, label) -> list[dict]`

**Purpose**: Gate raw API data through Pydantic validation. Invalid records are logged at WARNING and skipped.

**Behavior**: Calls `model_cls.model_validate(raw)` for each item. Returns only valid items.

### `assemble_snapshot(...) -> dict`

```python
def assemble_snapshot(
    accounts, campaigns_list, creatives_list,
    camp_metrics, creat_metrics, demo_data,
    date_start, date_end,
    content_names=None,
) -> dict:
```

**Purpose**: Main orchestrator that builds the complete snapshot.

**Steps**:
1. Validate all input lists through Pydantic models
2. Build index maps: `camp_metric_map`, `creat_metric_map`, `creatives_by_campaign`, `campaigns_by_account`
3. For each account:
   - Build account dict with metadata
   - For each campaign: build campaign dict with settings, aggregate metrics, daily time series
   - For each creative: build creative dict with content reference, content name, metrics
   - Process demographics by pivot type with `_top_demographics()`
4. Return snapshot with `generated_at`, `date_range`, and `accounts` list

### `save_snapshot_json(snap, path) -> Path`

**Purpose**: Write snapshot to a timestamped JSON file.

**Default path**: `data/snapshots/snapshot_{YYYYMMDDTHHMMSSZ}.json`

---

## Code Snippet

```python
from app.services.snapshot import assemble_snapshot, save_snapshot_json

snapshot = assemble_snapshot(
    accounts, campaigns, creatives,
    camp_metrics, creat_metrics, demographics,
    date_start, date_end,
    content_names=content_names,
)
path = save_snapshot_json(snapshot)
```

---

## Relationships

- **Called by**: `services/sync.py` (step 7-8 of pipeline)
- **Calls**: Pydantic models from `models/linkedin_api.py` for validation
- **Consumed by**: `services/sync.py` iterates the snapshot to call CRUD upserts
