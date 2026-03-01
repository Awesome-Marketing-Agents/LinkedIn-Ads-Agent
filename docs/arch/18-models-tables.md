# Module: SQLModel Table Definitions

## Overview

Seven SQLModel table classes define the PostgreSQL schema. All fields are `Optional` (except primary keys) for resilience against partial API responses. The `models/__init__.py` re-exports all tables for Alembic metadata discovery.

---

## File Paths

- `backend/app/models/ad_account.py`
- `backend/app/models/campaign.py`
- `backend/app/models/creative.py`
- `backend/app/models/metrics.py`
- `backend/app/models/demographics.py`
- `backend/app/models/sync.py`
- `backend/app/models/__init__.py`

---

## Tables

### `AdAccount` — `ad_accounts`

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| `id` | `int` | PK | LinkedIn ad account ID |
| `name` | `Optional[str]` | | Account name |
| `status` | `Optional[str]` | | ACTIVE, DRAFT, etc. |
| `currency` | `Optional[str]` | | Account currency code |
| `type` | `Optional[str]` | | Account type |
| `is_test` | `Optional[bool]` | | Test account flag |
| `created_at` | `Optional[str]` | | Creation timestamp |
| `fetched_at` | `Optional[str]` | | Last sync timestamp |

### `Campaign` — `campaigns`

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| `id` | `int` | PK | Campaign ID |
| `account_id` | `Optional[int]` | FK → `ad_accounts.id` | Parent account |
| `name` | `Optional[str]` | | Campaign name |
| `status` | `Optional[str]` | | ACTIVE, PAUSED, DRAFT |
| `type` | `Optional[str]` | | Campaign type |
| `daily_budget` | `Optional[float]` | | Daily budget amount |
| `daily_budget_currency` | `Optional[str]` | | Budget currency |
| `total_budget` | `Optional[float]` | | Total budget amount |
| `cost_type` | `Optional[str]` | | CPC, CPM, etc. |
| `unit_cost` | `Optional[float]` | | Bid amount |
| `bid_strategy` | `Optional[str]` | | Optimization target |
| `creative_selection` | `Optional[str]` | | Creative rotation |
| `offsite_delivery_enabled` | `Optional[bool]` | | LinkedIn Audience Network |
| `audience_expansion_enabled` | `Optional[bool]` | | Audience expansion |
| `campaign_group` | `Optional[str]` | | Parent campaign group URN |
| `created_at` | `Optional[str]` | | Creation timestamp |
| `fetched_at` | `Optional[str]` | | Last sync timestamp |

### `Creative` — `creatives`

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| `id` | `str` | PK | Creative URN (string, not int) |
| `campaign_id` | `Optional[int]` | FK → `campaigns.id` | Parent campaign |
| `account_id` | `Optional[int]` | FK → `ad_accounts.id` | Parent account |
| `intended_status` | `Optional[str]` | | ACTIVE, PAUSED |
| `is_serving` | `Optional[bool]` | | Currently serving |
| `content_reference` | `Optional[str]` | | Content URN |
| `content_name` | `Optional[str]` | | Human-readable name |
| `serving_hold_reasons` | `Optional[str]` | | Comma-separated reasons |
| `created_at` | `Optional[int]` | | Epoch ms (`BigInteger`) |
| `last_modified_at` | `Optional[int]` | | Epoch ms (`BigInteger`) |
| `fetched_at` | `Optional[str]` | | Last sync timestamp |

**Note**: `created_at` and `last_modified_at` use `sa_column=Column(BigInteger)` because LinkedIn returns epoch milliseconds as large integers.

### `CampaignDailyMetric` — `campaign_daily_metrics`

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| `campaign_id` | `int` | PK, FK → `campaigns.id` | Campaign |
| `date` | `str` | PK | Date string (YYYY-M-DD) |
| `impressions` | `int` | | Default 0 |
| `clicks` | `int` | | Default 0 |
| `spend` | `float` | | Default 0.0 |
| `landing_page_clicks` | `int` | | Default 0 |
| `conversions` | `int` | | Default 0 |
| `likes` | `int` | | Default 0 |
| `comments` | `int` | | Default 0 |
| `shares` | `int` | | Default 0 |
| `follows` | `int` | | Default 0 |
| `leads` | `int` | | Default 0 |
| `opens` | `int` | | Default 0 |
| `sends` | `int` | | Default 0 |
| `ctr` | `float` | | Computed CTR |
| `cpc` | `float` | | Computed CPC |
| `fetched_at` | `Optional[str]` | | Sync timestamp |

### `CreativeDailyMetric` — `creative_daily_metrics`

Same schema as `CampaignDailyMetric` but with `creative_id: str` (FK → `creatives.id`) instead of `campaign_id`.

### `AudienceDemographic` — `audience_demographics`

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| `account_id` | `int` | PK, FK → `ad_accounts.id` | Account |
| `pivot_type` | `str` | PK | e.g., "job_title", "seniority" |
| `segment` | `str` | PK | Segment name or URN |
| `date_start` | `str` | PK | Period start |
| `impressions` | `int` | | Default 0 |
| `clicks` | `int` | | Default 0 |
| `ctr` | `float` | | Computed CTR |
| `share_pct` | `float` | | Share of impressions |
| `date_end` | `Optional[str]` | | Period end |
| `fetched_at` | `Optional[str]` | | Sync timestamp |

### `SyncLog` — `sync_log`

| Column | Type | Key | Description |
|--------|------|-----|-------------|
| `id` | `Optional[int]` | PK (auto) | Sync run ID |
| `account_id` | `str` | | Account ID or "all" |
| `started_at` | `str` | | ISO timestamp |
| `finished_at` | `Optional[str]` | | ISO timestamp |
| `status` | `str` | | "running", "success", "failed" |
| `trigger` | `Optional[str]` | | "manual" |
| `campaigns_fetched` | `int` | | Default 0 |
| `creatives_fetched` | `int` | | Default 0 |
| `api_calls_made` | `int` | | Default 0 |
| `errors` | `Optional[str]` | | Error message |

---

## `models/__init__.py`

```python
from app.models.ad_account import AdAccount
from app.models.campaign import Campaign
from app.models.creative import Creative
from app.models.metrics import CampaignDailyMetric, CreativeDailyMetric
from app.models.demographics import AudienceDemographic
from app.models.sync import SyncLog
```

Re-exports all tables. Used by `alembic/env.py` (`from app.models import *`) to ensure all tables are registered in `SQLModel.metadata`.

---

## Code Snippet

```python
from app.models import AdAccount, Campaign
from sqlmodel import select

# Query
accounts = session.exec(select(AdAccount).order_by(AdAccount.name)).all()
```

---

## Relationships

- **Used by**: All `crud/` modules for upserts and queries
- **Used by**: `alembic/env.py` for migration metadata
- **Used by**: `tests/conftest.py` for test table creation
