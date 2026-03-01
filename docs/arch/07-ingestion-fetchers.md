# Module: Entity Fetchers (Accounts, Campaigns, Creatives)

## Overview

`ingestion/fetchers.py` provides functions to fetch LinkedIn Ads entity data: ad accounts, campaigns, and creatives. Each function takes a `LinkedInClient` and returns raw dicts from the API. No transformation or persistence happens here.

---

## File Path

`src/linkedin_action_center/ingestion/fetchers.py`

---

## Components & Explanation

- **`fetch_ad_accounts(client)`** — Fetch all ad accounts the authenticated user can access.
  - **Purpose**: Get list of ad account IDs for subsequent fetches.
  - **Inputs**: `LinkedInClient`.
  - **Outputs**: `list[dict]` of account objects.
  - **Endpoint**: `GET /adAccounts?q=search`.

- **`fetch_campaigns(client, account_id, statuses=None)`** — Fetch campaigns for an account.
  - **Purpose**: Get campaigns for sync and metrics.
  - **Inputs**: `client`, `account_id`, optional `statuses` (default: `ACTIVE`, `PAUSED`, `DRAFT`).
  - **Outputs**: `list[dict]` of campaign objects.
  - **Endpoint**: `GET /adAccounts/{id}/adCampaigns?q=search`.
  - **Note**: Excludes `ARCHIVED` and `CANCELED` by default to keep the dataset relevant.

- **`fetch_creatives(client, account_id, campaign_ids=None)`** — Fetch creatives for an account.
  - **Purpose**: Get creatives, optionally filtered by campaign.
  - **Inputs**: `client`, `account_id`, optional `campaign_ids` list.
  - **Outputs**: `list[dict]` of creative objects.
  - **Endpoint**: `GET /adAccounts/{id}/creatives?q=criteria`.
  - **Note**: If `campaign_ids` provided, uses `campaigns=List(urn:li:sponsoredCampaign:...)` filter.

---

## Relationships

- Depends only on `ingestion/client.py`.
- Used by `main.py`, `cli.py` during sync.
- Output is passed to `storage/snapshot.py` and `ingestion/metrics.py` (for IDs).

---

## Example Code Snippets

```python
from linkedin_action_center.ingestion.client import LinkedInClient
from linkedin_action_center.ingestion.fetchers import (
    fetch_ad_accounts,
    fetch_campaigns,
    fetch_creatives,
)

client = LinkedInClient(auth_manager)

# Fetch all accounts
accounts = fetch_ad_accounts(client)
print(f"Accounts: {[a['id'] for a in accounts]}")

# Fetch campaigns for first account
account_id = accounts[0]["id"]
campaigns = fetch_campaigns(client, account_id)
campaign_ids = [c["id"] for c in campaigns]

# Fetch creatives (all campaigns)
creatives = fetch_creatives(client, account_id, campaign_ids)

# Or fetch creatives for specific campaigns only
creatives = fetch_creatives(client, account_id, [campaign_ids[0]])
```

---

## Edge Cases & Tips

- **Empty accounts**: `fetch_ad_accounts` can return `[]`; sync logic should handle this.
- **Campaign statuses**: To include archived campaigns, pass `statuses=["ACTIVE","PAUSED","DRAFT","ARCHIVED"]`.
- **Creative filtering**: Passing `campaign_ids` reduces payload; omitting it fetches all creatives for the account.
- **Web vs CLI**: `main.py` fetches creatives per campaign in a loop; `cli.py` fetches all at once with `campaign_ids`. Both are valid; CLI is more efficient.

---

## Architecture / Flow

```
Sync flow
    |
    ├── fetch_ad_accounts(client) -> list[dict]
    |
    └── For each account:
            ├── fetch_campaigns(client, account_id) -> list[dict]
            └── fetch_creatives(client, account_id, campaign_ids) -> list[dict]
```

---

## Advanced Notes

- Campaign URN format: `urn:li:sponsoredCampaign:{id}`.
- Creatives are linked to campaigns via `campaign` field (URN) in the creative object.
- Pagination is handled inside `client.get_all_pages()`.
