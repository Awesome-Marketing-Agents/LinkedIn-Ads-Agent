# Module: LinkedIn API Client

## Overview

`ingestion/client.py` provides a low-level HTTP client for the LinkedIn Marketing REST API. It handles authentication headers, pagination, and error handling so higher-level fetchers can work with simple Python dicts instead of raw HTTP.

---

## File Path

`src/linkedin_action_center/ingestion/client.py`

---

## Components & Explanation

- **`LinkedInClient`** — Thin wrapper around `requests` for the LinkedIn REST API.
  - **Purpose**: Centralize auth, headers, and error handling for all API calls.
  - **Inputs**: `AuthManager` instance in constructor.
  - **Outputs**: JSON response dicts or raises domain exceptions.
  - **Dependencies**: `requests`, `auth.manager`, `core.constants`, `utils.logger`, `utils.errors`.

- **`_headers()`** — Returns dict with `Authorization`, `LinkedIn-Version`, `X-Restli-Protocol-Version`.
- **`get(path, params_str="")`** — Single GET request; returns JSON. Raises `RateLimitError` on 429, `LinkedInAPIError` on other errors.
- **`get_all_pages(path, params_str="", key="elements", page_size=100)`** — Paginates through all results using `start`/`count` or `pageToken`; returns flattened list.

---

## Relationships

- Used by `fetchers.py` and `metrics.py`.
- Requires `AuthManager` for `get_access_token()` (auto-refresh on expiry).
- Raises `LinkedInAPIError`, `RateLimitError`, `DataFetchError`.

---

## Example Code Snippets

```python
from linkedin_action_center.auth.manager import AuthManager
from linkedin_action_center.ingestion.client import LinkedInClient

auth = AuthManager()
client = LinkedInClient(auth)

# Single request
data = client.get("/adAccounts", "q=search")

# Paginated request (all pages)
accounts = client.get_all_pages("/adAccounts", "q=search")
print(f"Found {len(accounts)} accounts")
```

```python
# Error handling
from linkedin_action_center.utils.errors import RateLimitError, LinkedInAPIError

try:
    data = client.get("/adAnalytics", params)
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after} seconds")
except LinkedInAPIError as e:
    print(f"API error: {e.status_code} - {e.endpoint}")
```

---

## Edge Cases & Tips

- **`params_str`**: Must be a pre-formatted query string (e.g. `q=search`, `List(urn%3Ali%3A...)`). LinkedIn uses URN encoding.
- **429 handling**: `RateLimitError` includes `retry_after` from `Retry-After` header when present.
- **Pagination**: Supports both offset-based (`start`, `count`) and token-based (`pageToken`); `get_all_pages` handles both.
- **Key**: Default `key="elements"`; some endpoints use a different response key.

---

## Architecture / Flow

```
Fetcher / Metrics
    │
    └── LinkedInClient.get(path, params_str)
            ├── _headers() → Bearer token from AuthManager
            ├── requests.get(API_BASE_URL + path, headers, params)
            └── resp.ok? → return resp.json() : raise LinkedInAPIError
```

---

## Advanced Notes

- API base URL: `https://api.linkedin.com/rest` (from `core.constants`).
- LinkedIn API version: `202602` (via `LinkedIn-Version` header).
- No retry logic; callers can implement retries for `RateLimitError`.
