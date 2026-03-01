# Module: CRUD — Accounts & Campaigns

## Overview

CRUD operations for ad accounts and campaigns. Uses PostgreSQL `INSERT ON CONFLICT DO UPDATE` for idempotent upserts and SQLModel queries with JOINs for reads.

---

## File Paths

- `backend/app/crud/accounts.py`
- `backend/app/crud/campaigns.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `sqlalchemy.dialects.postgresql.insert` | PostgreSQL upsert |
| `sqlmodel.Session`, `select` | ORM queries |
| `app.models.ad_account.AdAccount` | Account table model |
| `app.models.campaign.Campaign` | Campaign table model |

---

## Components — accounts.py

### `upsert_account(session, acct, now) -> None`

```python
def upsert_account(session: Session, acct: dict, now: str | None = None) -> None:
```

**Purpose**: Insert or update an ad account.

**Conflict resolution**: `index_elements=["id"]` — updates all fields except `id` on conflict.

**Fields persisted**: `id`, `name`, `status`, `currency`, `type`, `is_test`, `created_at`, `fetched_at`.

### `get_accounts(session) -> list[AdAccount]`

**Purpose**: Return all accounts ordered by name.

---

## Components — campaigns.py

### `upsert_campaign(session, account_id, camp, now) -> None`

```python
def upsert_campaign(
    session: Session, account_id: int, camp: dict, now: str | None = None,
) -> None:
```

**Purpose**: Insert or update a campaign.

**Behavior**: Extracts budget/strategy fields from `camp["settings"]` sub-dict. Converts budget amounts to float (defaulting to 0).

**Fields persisted**: `id`, `account_id`, `name`, `status`, `type`, `daily_budget`, `daily_budget_currency`, `total_budget`, `cost_type`, `unit_cost`, `bid_strategy`, `creative_selection`, `offsite_delivery_enabled`, `audience_expansion_enabled`, `campaign_group`, `created_at`, `fetched_at`.

### `get_campaigns(session) -> list[dict]`

**Purpose**: Return all campaigns with account name via `OUTERJOIN`.

**Returns**: List of campaign dicts, each with an added `account_name` field. Ordered by `status`, `name`.

---

## Code Snippet

```python
from app.crud.accounts import upsert_account, get_accounts
from app.crud.campaigns import upsert_campaign, get_campaigns

# Upsert
upsert_account(session, {"id": 123, "name": "My Account", "status": "ACTIVE"})
upsert_campaign(session, 123, snapshot_campaign_dict)
session.commit()

# Query
accounts = get_accounts(session)
campaigns = get_campaigns(session)  # includes account_name
```

---

## Relationships

- **Called by**: `services/sync.py` (upserts during persist step), `routes/report.py` (queries)
- **Uses**: `models/ad_account.py`, `models/campaign.py` for table definitions
