# Module: LinkedIn Analytics & Demographics Fetchers

## Overview

Metric fetchers retrieve campaign-level and creative-level analytics plus audience demographics from the LinkedIn Analytics API. Requests are batched (20 campaigns per call) and parallelized via `asyncio.gather`.

---

## File Path

`backend/app/linkedin/metrics.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `asyncio` | Parallel batch fetching |
| `datetime` | Date range parameters |
| `app.linkedin.client.LinkedInClient` | HTTP client |
| `app.utils.logging.get_logger` | Logging |

---

## Constants

| Name | Value | Purpose |
|------|-------|---------|
| `CORE_METRICS` | 12 metric names | Fields requested from analytics API |
| `FIELDS_PARAM` | Joined metrics + `dateRange,pivotValues` | Full field list for campaign/creative queries |
| `DEMOGRAPHIC_PIVOTS` | 6 pivot types | Demographics breakdown categories |
| `DEMO_FIELDS` | `impressions,clicks,costInLocalCurrency,pivotValues` | Lightweight fields for demographic queries |
| `_BATCH_SIZE` | `20` | Max campaigns per API call |

**`CORE_METRICS`**: `impressions`, `clicks`, `costInLocalCurrency`, `landingPageClicks`, `externalWebsiteConversions`, `likes`, `comments`, `shares`, `follows`, `oneClickLeads`, `opens`, `sends`

**`DEMOGRAPHIC_PIVOTS`**: `MEMBER_JOB_TITLE`, `MEMBER_JOB_FUNCTION`, `MEMBER_INDUSTRY`, `MEMBER_SENIORITY`, `MEMBER_COMPANY_SIZE`, `MEMBER_COUNTRY_V2`

---

## Components

### `_date_range_param(start, end) -> str`

**Purpose**: Format a date range for the LinkedIn Analytics API.

**Returns**: `"(start:(year:2026,month:1,day:1),end:(year:2026,month:3,day:1))"`

### `_campaign_urns(campaign_ids) -> str`

**Purpose**: Format campaign IDs as URL-encoded URN list.

### `_fetch_metrics_batch(client, batch, start, end, pivot, granularity) -> list[dict]` (async)

**Purpose**: Fetch analytics for a single batch of campaigns.

**API call**: `GET /adAnalytics?q=analytics&pivot={pivot}&timeGranularity={granularity}&...`

### `fetch_campaign_metrics(client, campaign_ids, start, end, granularity) -> list[dict]` (async)

**Purpose**: Fetch daily campaign metrics with parallel batching.

**Behavior**:
1. Splits `campaign_ids` into batches of 20
2. Creates an async task per batch
3. `asyncio.gather` runs all batches in parallel
4. Flattens results into a single list

### `fetch_creative_metrics(client, campaign_ids, start, end, granularity) -> list[dict]` (async)

**Purpose**: Same as campaign metrics but with `pivot=CREATIVE`.

### `fetch_demographics(client, campaign_ids, start, end, pivots) -> dict[str, list[dict]]` (async)

**Purpose**: Fetch audience demographics across 6 pivot types.

**Behavior**:
1. For each pivot type, fetches all campaign batches sequentially
2. All 6 pivot types run in parallel via `asyncio.gather`
3. Failures for individual pivots are caught and logged — returns empty list for that pivot

**Returns**: Dict mapping pivot name to list of demographic rows: `{"MEMBER_SENIORITY": [...], ...}`

---

## Code Snippet

```python
from app.linkedin.metrics import fetch_campaign_metrics, fetch_demographics

camp_metrics = await fetch_campaign_metrics(client, campaign_ids, date_start, today)
demographics = await fetch_demographics(client, campaign_ids, date_start, today)
```

---

## Relationships

- **Called by**: `services/sync.py` (steps 4-6 of the pipeline)
- **Calls**: `LinkedInClient.get()` for analytics API requests

---

## Known Gaps

- **Batch size is fixed** — 20 campaigns per API call, not configurable
- **No retry on partial failure** — If one batch fails, results from other batches are still returned but the failed batch is lost
