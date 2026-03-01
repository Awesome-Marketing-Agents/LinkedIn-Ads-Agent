# Module: LinkedIn API Client

## Overview

`LinkedInClient` is an async HTTP client for the LinkedIn Marketing REST API. It wraps `httpx.AsyncClient` with automatic authentication headers, API versioning, request timing, rate limit detection, and transparent pagination.

---

## File Path

`backend/app/linkedin/client.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `httpx` | Async HTTP requests |
| `app.core.security.AuthManager` | Token management for auth headers |
| `app.errors.exceptions` | `LinkedInAPIError`, `RateLimitError` |
| `app.linkedin.constants` | `API_BASE_URL`, `LINKEDIN_API_VERSION` |
| `app.utils.logging` | `get_logger`, `log_api_call` |

---

## Components

### `LinkedInClient.__init__(self, auth: AuthManager) -> None`

**Purpose**: Store a reference to the `AuthManager` for token retrieval.

### `LinkedInClient._headers(self) -> dict[str, str]` (async)

**Purpose**: Build request headers with a fresh access token.

**Returns**:
```python
{
    "Authorization": "Bearer <token>",
    "LinkedIn-Version": "202602",
    "X-Restli-Protocol-Version": "2.0.0",
}
```

### `LinkedInClient.get(self, path: str, params_str: str = "") -> dict` (async)

**Purpose**: Execute a single GET request to the LinkedIn API.

**Parameters**:
- `path` — API path (e.g., `"/adAccounts"`)
- `params_str` — Pre-encoded query string (e.g., `"q=search"`)

**Behavior**:
1. Builds full URL: `https://api.linkedin.com/rest{path}?{params_str}`
2. Gets fresh headers (triggers token refresh if needed)
3. Sends GET with 30-second timeout
4. Logs the API call with status and duration via `log_api_call()`
5. On 429: raises `RateLimitError` with `Retry-After` header
6. On other errors: raises `LinkedInAPIError` with status code and response data

**Returns**: Parsed JSON response dict.

**Raises**: `RateLimitError`, `LinkedInAPIError`

### `LinkedInClient.get_all_pages(self, path, params_str, key, page_size) -> list[dict]` (async)

```python
async def get_all_pages(
    self, path: str, params_str: str = "",
    key: str = "elements", page_size: int = 100,
) -> list[dict]:
```

**Purpose**: Auto-paginate through all results.

**Behavior**:
1. Tries token-based pagination first (uses `metadata.nextPageToken`)
2. Falls back to offset-based pagination (`start=N&count=100`)
3. Stops when a page returns fewer items than `page_size` and no next token

**Returns**: Concatenated list of all items across all pages.

---

## Code Snippet

```python
from app.core.security import AuthManager
from app.linkedin.client import LinkedInClient

auth = AuthManager()
client = LinkedInClient(auth)
accounts = await client.get_all_pages("/adAccounts", "q=search")
```

---

## Relationships

- **Called by**: `linkedin/fetchers.py`, `linkedin/metrics.py`
- **Calls**: `AuthManager.get_access_token()` on every request
- **Used by**: `services/sync.py` (creates client instance)

---

## Known Gaps

- **No retry on rate limit** — `RateLimitError` is raised but never caught/retried
- **New httpx client per request** — Each `get()` creates and closes an `AsyncClient` (no connection pooling)
- **No concurrent request limiting** — Could overwhelm the API if many pages are fetched simultaneously
