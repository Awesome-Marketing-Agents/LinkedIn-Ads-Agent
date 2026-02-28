# Module: Metrics Fetchers (Analytics & Demographics)

## Overview

`ingestion/metrics.py` fetches LinkedIn Ads analytics and demographic data via the `/adAnalytics` endpoint. It supports different pivots (CAMPAIGN, CREATIVE, demographic) and batches campaign URNs to avoid URL length limits.

---

## File Path

`src/linkedin_action_center/ingestion/metrics.py`

---

## Components & Explanation

- **`CORE_METRICS`** — List of metric names requested on every analytics call (impressions, clicks, costInLocalCurrency, etc.).
- **`DEMOGRAPHIC_PIVOTS`** — Demographic pivot types (MEMBER_JOB_TITLE, MEMBER_JOB_FUNCTION, etc.).
- **`_date_range_param(start, end)`** — Build LinkedIn `dateRange` query string.
- **`_campaign_urns(campaign_ids)`** — Build comma-separated URN list for campaigns.
- **`fetch_campaign_metrics(client, campaign_ids, start, end, granularity="DAILY")`** — Fetch metrics pivoted by CAMPAIGN.
- **`fetch_creative_metrics(client, campaign_ids, start, end, granularity="DAILY")`** — Fetch metrics pivoted by CREATIVE.
- **`fetch_demographics(client, campaign_ids, start, end, pivots=None)`** — Fetch demographic breakdowns; returns `dict[pivot_name, list[dict]]`.

---

## Relationships

- Depends on `ingestion/client.py`.
- Used by `main.py` and `cli.py` during sync.
- Output is passed to `storage/snapshot.py` for assembly.

---

## Example Code Snippets

```python
from datetime import date, timedelta
from linkedin_action_center.ingestion.metrics import (
    fetch_campaign_metrics,
    fetch_creative_metrics,
    fetch_demographics,
)

today = date.today()
date_start = today - timedelta(days=90)
campaign_ids = [123456, 789012]

# Campaign-level metrics (daily time series)
camp_metrics = fetch_campaign_metrics(client, campaign_ids, date_start, today)

# Creative-level metrics
creative_metrics = fetch_creative_metrics(client, campaign_ids, date_start, today)

# Demographics (aggregate, not daily)
demographics = fetch_demographics(client, campaign_ids, date_start, today)
# demographics["MEMBER_JOB_TITLE"] = [{"segment": "Engineer", "impressions": 5000, ...}, ...]
```

---

## Edge Cases & Tips

- **Batch size**: Campaign IDs are batched in groups of 20 (`_BATCH_SIZE`) to avoid URL length limits.
- **Empty campaign_ids**: All fetchers return `[]` or `{}` when `campaign_ids` is empty.
- **Demographic failures**: Individual pivot failures are caught; failed pivots get `[]` instead of raising.
- **Creative metrics**: Uses `campaign_ids` (not creative IDs); the API returns rows per creative within those campaigns.
- **Date format**: `start` and `end` must be `datetime.date` objects; `_date_range_param` formats them for the API.

---

## Architecture / Flow

```
Sync flow
    │
    ├── fetch_campaign_metrics(client, campaign_ids, start, end)
    │       └── GET /adAnalytics?pivot=CAMPAIGN&timeGranularity=DAILY&...
    │
    ├── fetch_creative_metrics(client, campaign_ids, start, end)
    │       └── GET /adAnalytics?pivot=CREATIVE&timeGranularity=DAILY&...
    │
    └── fetch_demographics(client, campaign_ids, start, end)
            └── For each pivot: GET /adAnalytics?pivot=MEMBER_JOB_TITLE&timeGranularity=ALL&...
```

---

## Advanced Notes

- `granularity="DAILY"` produces time-series rows; `"ALL"` produces one aggregate row per pivot value.
- Demographics use `timeGranularity=ALL` and a reduced field set (`DEMO_FIELDS`).
- `costInLocalCurrency` in API maps to `spend` in snapshot/repository.

---

## Node.js Equivalent

**File**: `node-app/src/ingestion/metrics.ts`

The Node.js port replaces `ingestion/metrics.py` with an equivalent TypeScript module that introduces a significant performance improvement through parallel batch processing.

### Key Mappings

| Python | Node.js |
|--------|---------|
| `ingestion/metrics.py` | `node-app/src/ingestion/metrics.ts` |
| `fetch_campaign_metrics()` | `fetchCampaignMetrics()` |
| `fetch_creative_metrics()` | `fetchCreativeMetrics()` |
| `fetch_demographics()` | `fetchDemographics()` |

### Preserved Patterns

- **Same batch size of 20** campaign URNs per API request (`_BATCH_SIZE`).
- **Same demographic pivots** (`MEMBER_JOB_TITLE`, `MEMBER_JOB_FUNCTION`, etc.) and metric fields (`CORE_METRICS`).
- **Same date range formatting** and URN encoding logic.
- **Same error handling** for individual pivot failures in demographics (failed pivots return `[]`).

### Key Performance Improvement

The Python version processes campaign URN batches **sequentially** -- each batch waits for the previous one to complete before starting. The Node.js version uses **`Promise.all` combined with `p-limit(3)`** to process up to 3 batches concurrently while still respecting API rate limits.

This parallel batch processing results in an estimated **3-4x faster metric fetching** for accounts with many campaigns (e.g., 100+ campaigns = 5+ batches). The concurrency limit of 3 prevents overwhelming the LinkedIn API while still providing a substantial speedup over serial execution.
