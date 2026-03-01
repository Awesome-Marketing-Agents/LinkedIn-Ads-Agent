# Module: CRUD — Metrics & Demographics

## Overview

CRUD operations for campaign metrics, creative metrics, creatives, and demographics. Includes upserts with composite primary key conflict resolution, paginated queries with JOINs, and raw SQL aggregation for visual reports.

---

## File Paths

- `backend/app/crud/metrics.py`
- `backend/app/crud/demographics.py`

---

## Components — metrics.py

### Upserts

#### `upsert_campaign_daily_metrics(session, camp, now) -> None`

**Purpose**: Upsert daily metrics for a campaign. Iterates `camp["daily_metrics"]` list.

**Conflict**: `index_elements=["campaign_id", "date"]` — composite PK.

**Fields**: 14 metric fields + `fetched_at`. Updates all except PK fields on conflict.

#### `upsert_creative_daily_metrics(session, creative, now) -> None`

**Purpose**: Same pattern for creative metrics.

**Conflict**: `index_elements=["creative_id", "date"]`.

#### `upsert_creatives(session, account_id, camp, now) -> None`

**Purpose**: Upsert creative entities from `camp["creatives"]` list.

**Behavior**: Converts `serving_hold_reasons` from list to comma-separated string. Persists `content_name` for human-readable labels.

**Conflict**: `index_elements=["id"]`. Updates all except `id` and `created_at`.

### Paginated Queries

#### `get_campaign_metrics_paginated(session, page, page_size) -> dict`

**Purpose**: Paginated campaign metrics with campaign name via JOIN.

**Returns**:
```python
{
    "rows": [{"campaign_id": ..., "campaign_name": "...", ...}],
    "total": 150,
    "page": 1,
    "page_size": 50,
    "total_pages": 3,
}
```

#### `get_creative_metrics_paginated(session, page, page_size) -> dict`

**Purpose**: Paginated creative metrics with content name and campaign name via double JOIN (Creative → Campaign).

#### `get_creatives(session) -> list[dict]`

**Purpose**: All creatives with campaign name, ordered by `last_modified_at` descending.

### Visual Aggregation

#### `get_visual_data(session) -> dict`

**Purpose**: Aggregate data for Chart.js visualizations.

**Returns**:
```python
{
    "time_series": [{"date": "...", "impressions": ..., "clicks": ..., "spend": ..., "conversions": ...}],
    "campaign_comparison": [{"name": "...", "impressions": ..., ...}],
    "kpis": {"impressions": ..., "clicks": ..., "spend": ..., "conversions": ..., "ctr": ..., "cpc": ..., "cpm": ...},
}
```

**Implementation**: Uses raw SQL via `text()` for GROUP BY aggregations.

---

## Components — demographics.py

### `upsert_demographics(session, acct, date_range, now) -> None`

**Purpose**: Upsert demographic segments from the snapshot.

**Conflict**: 4-column composite PK `["account_id", "pivot_type", "segment", "date_start"]`.

### `get_demographics(session, pivot_type) -> list[dict]`

**Purpose**: Query demographics with optional pivot_type filter. Ordered by impressions descending.

---

## Code Snippet

```python
from app.crud.metrics import get_visual_data, get_campaign_metrics_paginated

# Paginated query
result = get_campaign_metrics_paginated(session, page=1, page_size=50)

# Visual data for charts
visual = get_visual_data(session)
```

---

## Relationships

- **Called by**: `services/sync.py` (upserts), `routes/report.py` (queries)
- **Uses**: `models/metrics.py`, `models/creative.py`, `models/campaign.py`, `models/demographics.py`

---

## Known Gaps

- **Raw SQL in `get_visual_data()`** — Uses `text()` SQL strings instead of ORM queries
- **No index optimization** — Composite PK queries may benefit from additional indexes at scale
