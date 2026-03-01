# Module: LinkedIn Entity Fetchers

## Overview

Entity fetchers retrieve structural data from the LinkedIn Marketing API: ad accounts, campaigns, creatives, and content reference names. Each function takes a `LinkedInClient` and returns parsed entity lists.

---

## File Path

`backend/app/linkedin/fetchers.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `app.linkedin.client.LinkedInClient` | HTTP client for API calls |
| `app.utils.logging.get_logger` | Logging |

---

## Components

### `fetch_ad_accounts(client: LinkedInClient) -> list[dict]` (async)

**Purpose**: Fetch all ad accounts accessible to the authenticated user.

**API call**: `GET /adAccounts?q=search` (paginated)

**Returns**: List of raw account dicts from the API.

### `fetch_campaigns(client, account_id, statuses) -> list[dict]` (async)

```python
async def fetch_campaigns(
    client: LinkedInClient,
    account_id: int,
    statuses: list[str] | None = None,
) -> list[dict]:
```

**Purpose**: Fetch campaigns for a specific ad account.

**Parameters**:
- `account_id` — Numeric ad account ID
- `statuses` — Filter by status (default: `["ACTIVE", "PAUSED", "DRAFT"]`)

**API call**: `GET /adAccounts/{account_id}/adCampaigns?q=search&search=(status:(values:List(...)))`

### `fetch_creatives(client, account_id, campaign_ids) -> list[dict]` (async)

```python
async def fetch_creatives(
    client: LinkedInClient,
    account_id: int,
    campaign_ids: list[int] | None = None,
) -> list[dict]:
```

**Purpose**: Fetch creatives for an ad account, optionally filtered by campaigns.

**API call**: `GET /adAccounts/{account_id}/creatives?q=criteria&sortOrder=ASCENDING`

### `resolve_content_references(client, creatives) -> dict[str, str]` (async)

```python
async def resolve_content_references(
    client: LinkedInClient,
    creatives: list[dict],
) -> dict[str, str]:
```

**Purpose**: Build human-readable display names for creative content reference URNs. Derives names from URN type and ID — **no extra API calls needed**.

**Type labels**:
| URN Type | Label |
|----------|-------|
| `share` | Sponsored Post |
| `adInMailContent` | InMail |
| `video` | Video Ad |
| `ugcPost` | UGC Post |
| `adCreativeV2` | Creative |

**Example**: `urn:li:share:7123456789` -> `"Sponsored Post #456789"`

**Returns**: Mapping of `{content_reference_URN: display_name}`.

---

## Code Snippet

```python
from app.linkedin.client import LinkedInClient
from app.linkedin.fetchers import fetch_ad_accounts, fetch_campaigns, fetch_creatives

client = LinkedInClient(auth)
accounts = await fetch_ad_accounts(client)
for acct in accounts:
    campaigns = await fetch_campaigns(client, acct["id"])
    campaign_ids = [c["id"] for c in campaigns]
    creatives = await fetch_creatives(client, acct["id"], campaign_ids)
```

---

## Relationships

- **Called by**: `services/sync.py` during the sync pipeline
- **Calls**: `LinkedInClient.get_all_pages()` for paginated fetches
