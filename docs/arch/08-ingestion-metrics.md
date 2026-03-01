# Module: Metrics Fetchers (Analytics & Demographics)

## Overview

`ingestion/metrics.py` fetches LinkedIn Ads analytics and demographic data via the `/adAnalytics` endpoint. It supports different pivots (CAMPAIGN, CREATIVE, and MEMBER_* demographic pivots), batches campaign URNs in groups of 20 to avoid URL length limits, and can resolve demographic URNs to human-readable names via the LinkedIn API.

---

## File Path

`src/linkedin_action_center/ingestion/metrics.py`

---

## Components & Explanation

### Constants

- **`CORE_METRICS`** — List of 12 metric fields requested on every analytics call:
  `impressions`, `clicks`, `costInLocalCurrency`, `landingPageClicks`, `externalWebsiteConversions`, `likes`, `comments`, `shares`, `follows`, `oneClickLeads`, `opens`, `sends`.
- **`FIELDS_PARAM`** — Comma-separated string of `CORE_METRICS + dateRange + pivotValues`.
- **`DEMOGRAPHIC_PIVOTS`** — Six demographic pivot types:
  `MEMBER_JOB_TITLE`, `MEMBER_JOB_FUNCTION`, `MEMBER_INDUSTRY`, `MEMBER_SENIORITY`, `MEMBER_COMPANY_SIZE`, `MEMBER_COUNTRY_V2`.
- **`DEMO_FIELDS`** — Reduced field set for demographics: `impressions,clicks,costInLocalCurrency,pivotValues`.
- **`_BATCH_SIZE`** — 20 campaign URNs per API call to avoid URL-length limits.

### Helper Functions

- **`_date_range_param(start, end)`** — Build LinkedIn's `dateRange` query string value.
- **`_campaign_urns(campaign_ids)`** — Build URL-encoded comma-separated campaign URN list.
- **`_extract_urn_parts(urn)`** — Extract `(entity_type, entity_id)` from a URN like `urn:li:title:1335`.

### Fetcher Functions

- **`fetch_campaign_metrics(client, campaign_ids, start, end, granularity="DAILY")`** — Fetch metrics pivoted by CAMPAIGN.
  - Batches in groups of 20 campaign IDs.
  - Returns `list[dict]` of metric rows from the API.
  - `granularity="DAILY"` produces time-series; `"ALL"` produces one aggregate row per campaign.

- **`fetch_creative_metrics(client, campaign_ids, start, end, granularity="DAILY")`** — Fetch metrics pivoted by CREATIVE.
  - Same batching and return format as campaign metrics.

- **`fetch_demographics(client, campaign_ids, start, end, pivots=None)`** — Fetch audience demographic breakdowns.
  - Returns `dict[pivot_name, list[dict]]` mapping each pivot to its rows.
  - Uses `timeGranularity=ALL` (aggregate, not daily).
  - Individual pivot failures are caught — failed pivots get `[]` instead of raising.
  - Default pivots: all six `DEMOGRAPHIC_PIVOTS`.

- **`resolve_demographic_urns(client, demo_data)`** — Resolve demographic URNs to human-readable names.
  - Groups all URNs by entity type across all pivots.
  - Calls LinkedIn `/adTargetingEntities` API in batches of 50.
  - Returns `dict[urn, name]` mapping.
  - Falls back gracefully on API errors — returns whatever was resolved.
  - Used by `cli.py` and `main.py` before snapshot assembly.

---

## Relationships

- Depends on `ingestion/client.py` (`LinkedInClient`).
- Used by `main.py` and `cli.py` during sync.
- Output is passed to `storage/snapshot.py` for assembly.
- `resolve_demographic_urns()` output is passed alongside `demo_data` to `assemble_snapshot()`.

---

## Example Code Snippets

```python
from datetime import date, timedelta
from linkedin_action_center.ingestion.metrics import (
    fetch_campaign_metrics,
    fetch_creative_metrics,
    fetch_demographics,
    resolve_demographic_urns,
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
# demographics["MEMBER_JOB_TITLE"] = [{"pivotValues": ["urn:li:title:123"], "impressions": 5000, ...}]

# Resolve URNs to names
urn_names = resolve_demographic_urns(client, demographics)
# urn_names["urn:li:title:123"] = "Software Engineer"
```

---

## Edge Cases & Tips

- **Batch size**: Campaign IDs are batched in groups of 20 (`_BATCH_SIZE`) to avoid URL length limits.
- **Empty campaign_ids**: All fetchers return `[]` or `{}` when `campaign_ids` is empty.
- **Demographic failures**: Individual pivot failures are caught; failed pivots get `[]` instead of raising.
- **Creative metrics**: Uses `campaign_ids` (not creative IDs); the API returns rows per creative within those campaigns.
- **Date format**: `start` and `end` must be `datetime.date` objects; `_date_range_param` formats them for the API.
- **URN resolution**: `resolve_demographic_urns` tries two query styles (`q=urns` and `q=adTargetingFacet`). If neither works, falls back gracefully.
- **Local fallback**: `snapshot.py` has static enum maps for seniority, company size, and job function that work without API calls.

---

## Architecture / Flow

```
Sync flow
    |
    ├── fetch_campaign_metrics(client, campaign_ids, start, end)
    │       └── For each batch of 20:
    │           GET /adAnalytics?pivot=CAMPAIGN&timeGranularity=DAILY&...
    |
    ├── fetch_creative_metrics(client, campaign_ids, start, end)
    │       └── For each batch of 20:
    │           GET /adAnalytics?pivot=CREATIVE&timeGranularity=DAILY&...
    |
    ├── fetch_demographics(client, campaign_ids, start, end)
    │       └── For each pivot (6 pivots):
    │           GET /adAnalytics?pivot=MEMBER_JOB_TITLE&timeGranularity=ALL&...
    |
    └── resolve_demographic_urns(client, demo_data)
            └── Collect all URNs -> batch GET /adTargetingEntities
```

---

## Advanced Notes

- `granularity="DAILY"` produces time-series rows; `"ALL"` produces one aggregate row per pivot value.
- Demographics use `timeGranularity=ALL` and a reduced field set (`DEMO_FIELDS`).
- `costInLocalCurrency` in API maps to `spend` in snapshot/repository.
- URN format: `urn:li:sponsoredCampaign:{id}` for campaigns, `urn:li:seniority:{id}` for demographics.
- The `resolve_demographic_urns` function is the only place that calls the `/adTargetingEntities` endpoint.
