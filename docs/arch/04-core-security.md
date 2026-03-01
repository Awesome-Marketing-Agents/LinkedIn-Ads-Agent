# Module: AuthManager (OAuth Token Management)

## Overview

`AuthManager` handles the complete LinkedIn OAuth 2.0 lifecycle: building authorization URLs, exchanging codes for tokens, refreshing expired access tokens, and providing diagnostic methods for token health. Tokens are persisted to a JSON file on disk.

---

## File Path

`backend/app/core/security.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `httpx` | Async HTTP for token exchange, refresh, introspection, health check |
| `app.core.config.settings` | Client ID, secret, redirect URI, tokens file path |
| `app.errors.exceptions` | `AuthenticationError`, `TokenExpiredError` |
| `app.linkedin.constants` | `OAUTH2_BASE_URL`, `API_BASE_URL`, `INTROSPECT_URL`, `SCOPES`, `LINKEDIN_API_VERSION` |
| `app.utils.logging` | `get_logger`, `log_auth_event` |

---

## Constants

| Name | Value | Purpose |
|------|-------|---------|
| `_EXPIRY_BUFFER` | `300` (5 minutes) | Refresh access token this many seconds before actual expiry |

---

## Components

### `AuthManager.__init__(self) -> None`

**Purpose**: Loads config from settings and reads tokens from disk.

**Behavior**: Sets `client_id`, `client_secret`, `redirect_uri`, `tokens_file` from `settings`. Calls `_load_tokens()` to read existing tokens.

### `AuthManager._load_tokens(self) -> dict`

**Purpose**: Read tokens from JSON file. Returns empty dict if file doesn't exist.

### `AuthManager._save_tokens(self) -> None`

**Purpose**: Write tokens to JSON file with `saved_at` timestamp. Creates parent directories if needed.

### `AuthManager.get_authorization_url(self) -> str`

**Purpose**: Build the LinkedIn OAuth authorization URL.

**Returns**: URL string like `https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=...&scope=r_ads r_ads_reporting r_basicprofile`

### `AuthManager.exchange_code_for_token(self, auth_code: str) -> dict` (async)

**Purpose**: Exchange OAuth authorization code for access + refresh tokens.

**Parameters**: `auth_code` — the code from LinkedIn's callback.

**Behavior**:
1. POST to `{OAUTH2_BASE_URL}/accessToken` with code + credentials
2. Raises `AuthenticationError` if response status >= 400
3. Computes `access_token_expires_at` and `refresh_token_expires_at`
4. Saves tokens to disk

**Returns**: Token dict with `access_token`, `refresh_token`, expiry timestamps.

### `AuthManager.refresh_access_token(self) -> dict` (async)

**Purpose**: Refresh the access token using the refresh token.

**Raises**: `AuthenticationError` if no refresh token exists or if refresh fails.

**Behavior**: POST with `grant_type=refresh_token`. Updates access token and optionally the refresh token if LinkedIn rotates it. Saves to disk.

### `AuthManager.get_access_token(self) -> str` (async)

**Purpose**: Get a valid access token, auto-refreshing if within `_EXPIRY_BUFFER` of expiry.

**Raises**:
- `AuthenticationError` if no tokens exist
- `TokenExpiredError` if token expired and refresh fails

**Returns**: Access token string.

### `AuthManager.is_authenticated(self) -> bool`

**Purpose**: Check if a valid (non-expired) access token exists. Does NOT trigger refresh.

### `AuthManager.check_token_health(self) -> bool` (async)

**Purpose**: Validate the token by calling LinkedIn's `/me` endpoint.

**Behavior**: Refreshes if needed, then GETs `/me`. Logs the authenticated user's name on success. Returns `False` on HTTP errors.

### `AuthManager.introspect_token(self) -> dict` (async)

**Purpose**: Call LinkedIn's token introspection endpoint.

**Returns**: Introspection response dict (active, scopes, client_id, etc.).

### `AuthManager.token_status(self) -> dict`

**Purpose**: Return diagnostic info about stored tokens without making API calls.

**Returns**: Dict with `authenticated`, `access_token_expired`, `access_token_days_remaining`, `refresh_token_days_remaining`, `saved_at`.

---

## Code Snippet

```python
from app.core.security import AuthManager

auth = AuthManager()
if auth.is_authenticated():
    token = await auth.get_access_token()  # auto-refreshes if needed
```

---

## Relationships

- **Called by**: `routes/auth.py` (via `Depends(get_auth)`), `services/sync.py` (creates instance directly)
- **Calls**: LinkedIn OAuth endpoints via `httpx.AsyncClient`
- **Depends on**: `core/config.py` for credentials, `linkedin/constants.py` for URLs

---

## Known Gaps

- Token file is read on every `AuthManager()` instantiation (no caching across requests)
- No locking on token file writes — concurrent writes could corrupt
- `get_authorization_url()` is synchronous but called from async routes (acceptable since it's pure computation)
