# Module: Database Models (SQLModel ORM)

## Overview

`models/db_models.py` defines SQLModel table classes that mirror the SQLite schema. These models serve as the **authoritative schema definition** and are consumed by:

1. **Alembic** for migration generation.
2. **Repository** (`storage/repository.py`) for type-safe upserts via SQLAlchemy Core.
3. **Future code** that needs ORM-style queries via SQLModel sessions.

They deliberately mirror the raw SQL schema in `storage/database.py` so that `alembic upgrade head` on an existing database is a no-op.

---

## File Path

`src/linkedin_action_center/models/db_models.py`

---

## Components & Explanation

### Entity Tables

- **`AdAccount`** — Maps to `ad_accounts` table.
  - Primary key: `id` (int).
  - Fields: `name`, `status`, `currency`, `type`, `is_test`, `created_at`, `fetched_at`.

- **`Campaign`** — Maps to `campaigns` table.
  - Primary key: `id` (int).
  - Foreign key: `account_id` -> `ad_accounts.id`.
  - Fields: `name`, `status`, `type`, `daily_budget`, `daily_budget_currency`, `total_budget`, `cost_type`, `unit_cost`, `bid_strategy`, `creative_selection`, `offsite_delivery_enabled`, `audience_expansion_enabled`, `campaign_group`, `created_at`, `fetched_at`.

- **`Creative`** — Maps to `creatives` table.
  - Primary key: `id` (str — creative IDs are strings in LinkedIn's API).
  - Foreign keys: `campaign_id` -> `campaigns.id`, `account_id` -> `ad_accounts.id`.
  - Fields: `intended_status`, `is_serving`, `content_reference`, `created_at` (int, epoch timestamp), `last_modified_at` (int), `fetched_at`.

### Metrics Tables

- **`CampaignDailyMetric`** — Maps to `campaign_daily_metrics` table.
  - Composite primary key: `(campaign_id, date)`.
  - Foreign key: `campaign_id` -> `campaigns.id`.
  - Fields: `impressions`, `clicks`, `spend`, `landing_page_clicks`, `conversions`, `likes`, `comments`, `shares`, `ctr`, `cpc`, `fetched_at`.
  - All metric fields default to 0.

- **`CreativeDailyMetric`** — Maps to `creative_daily_metrics` table.
  - Composite primary key: `(creative_id, date)`.
  - Foreign key: `creative_id` -> `creatives.id`.
  - Same metric fields as `CampaignDailyMetric`.

- **`AudienceDemographic`** — Maps to `audience_demographics` table.
  - Composite primary key: `(account_id, pivot_type, segment, date_start)`.
  - Foreign key: `account_id` -> `ad_accounts.id`.
  - Fields: `impressions`, `clicks`, `ctr`, `share_pct`, `date_end`, `fetched_at`.

### Sync Tracking

- **`SyncLog`** — Maps to `sync_log` table.
  - Primary key: `id` (autoincrement).
  - Fields: `account_id` (str), `started_at`, `finished_at`, `status` (default: `"running"`), `trigger`, `campaigns_fetched`, `creatives_fetched`, `api_calls_made`, `errors`.
  - Used by the freshness gate (`should_sync()`) to track sync history.

---

## Relationships

- Imported by `storage/repository.py` for SQLAlchemy Core `insert()` statements.
- Referenced by Alembic's `env.py` for migration autogeneration.
- Schema mirrors the raw SQL `_SCHEMA` in `storage/database.py`.
- Uses `SQLModel` (which extends both Pydantic's `BaseModel` and SQLAlchemy's declarative base).

---

## Example Code Snippets

```python
from linkedin_action_center.models.db_models import (
    AdAccount,
    Campaign,
    CampaignDailyMetric,
    SyncLog,
)

# Create a model instance (useful for testing)
account = AdAccount(id=123, name="Test Account", status="ACTIVE", currency="USD")
print(account.id, account.name)

# Use in SQLAlchemy Core insert (as done in repository.py)
from sqlalchemy.dialects.sqlite import insert

stmt = insert(AdAccount).values(id=123, name="Test", status="ACTIVE")
stmt = stmt.on_conflict_do_update(
    index_elements=["id"],
    set_={"name": stmt.excluded.name, "status": stmt.excluded.status},
)
```

```python
# Use in SQLModel session queries
from linkedin_action_center.storage.database import get_session
from sqlmodel import select

with get_session() as session:
    campaigns = session.exec(select(Campaign).where(Campaign.status == "ACTIVE")).all()
    for c in campaigns:
        print(f"{c.name}: budget={c.daily_budget}")
```

---

## Edge Cases & Tips

- **Composite primary keys**: Metrics and demographics tables use multi-column primary keys. This is what makes upserts work correctly — `ON CONFLICT (campaign_id, date) DO UPDATE`.
- **String vs int IDs**: `Creative.id` is `str` (LinkedIn uses URN-style IDs for creatives), while `AdAccount.id` and `Campaign.id` are `int`.
- **Optional fields**: Most fields are `Optional` to handle partial data from the API gracefully.
- **`fetched_at`**: ISO timestamp string recording when the data was last fetched. Set by the repository during upserts.
- **`created_at` types**: `AdAccount.created_at` and `Campaign.created_at` are `Optional[str]` (ISO timestamp), but `Creative.created_at` is `Optional[int]` (epoch timestamp) — this matches LinkedIn's API format.
- **`table=True`**: The `table=True` parameter on `SQLModel` classes tells SQLModel to create actual database tables (not just Pydantic models).

---

## Architecture / Flow

```
models/db_models.py
    |
    ├── Alembic reads these models -> generates migrations
    |
    ├── repository.py imports models -> uses for insert() statements
    │       insert(AdAccount).values(...).on_conflict_do_update(...)
    |
    └── Future: direct SQLModel queries
            session.exec(select(Campaign).where(...))
```

---

## Advanced Notes

- The `__tablename__` attribute explicitly sets the table name for each model to match the existing schema.
- `SyncLog.id` uses `default=None` with `primary_key=True` to enable AUTOINCREMENT behavior in SQLite.
- Foreign keys are defined using `foreign_key="table.column"` syntax, which SQLModel translates to SQLAlchemy `ForeignKey` constraints.
- These models are the **single source of truth** for the schema. The raw SQL in `database.py` is kept for backward compatibility (creates tables on first connection), but Alembic migrations are generated from these models.
