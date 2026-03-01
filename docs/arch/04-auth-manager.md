# Module: Auth Manager (OAuth Token Management)

## Overview

`auth/manager.py` implements LinkedIn OAuth 2.0 token management: loading, saving, refreshing, and validating access and refresh tokens. Other modules use `AuthManager` to obtain a valid access token for API calls.

---

## File Path

`src/linkedin_action_center/auth/manager.py`

---

## Components & Explanation

- **`AuthManager`** — Main class for OAuth and token handling.
  - **Purpose**: Manage the full OAuth lifecycle and token storage.
  - **Inputs**: Reads config from `core.config` and `core.constants`.
  - **Outputs**: Tokens stored in `tokens.json`; methods return token data or status.
  - **Dependencies**: `requests`, `core.config`, `core.constants`, `utils.logger`, `utils.errors`.

- **`_load_tokens()`** — Load tokens from `tokens.json` if it exists; otherwise return `{}`.
- **`_save_tokens()`** — Write current token dict to `tokens.json` with `saved_at` timestamp.
- **`get_authorization_url()`** — Build LinkedIn OAuth authorization URL for the user to visit.
- **`exchange_code_for_token(auth_code)`** — Exchange authorization code for access and refresh tokens; saves to disk. Raises `AuthenticationError` on failure.
- **`refresh_access_token()`** — Use refresh token to get a new access token; saves to disk. Raises `AuthenticationError` if no refresh token or if refresh fails.
- **`get_access_token()`** — Return a valid access token; auto-refreshes if expired (5-minute buffer). This is the primary method other modules should call. Raises `TokenExpiredError` if refresh fails.
- **`is_authenticated()`** — Return `True` if a non-expired access token exists.
- **`check_token_health()`** — Call LinkedIn `/me` to verify the token works. Logs the authenticated user's name.
- **`introspect_token()`** — Call LinkedIn introspect endpoint for token metadata.
- **`token_status()`** — Return a dict with `authenticated`, `access_token_days_remaining`, `refresh_token_days_remaining`, `saved_at`.

---

## Relationships

- Used by `main.py`, `cli.py`, `ingestion/client.py`, and `auth/callback.py`.
- Reads from `core.config` (credentials, paths) and `core.constants` (URLs, scopes).
- Raises `AuthenticationError`, `TokenExpiredError` (from `utils.errors`) on failures.
- Uses `utils.logger` for auth event logging.

---

## Example Code Snippets

```python
from linkedin_action_center.auth.manager import AuthManager

auth = AuthManager()

# Check if already authenticated
if auth.is_authenticated():
    print("Token valid:", auth.token_status())
else:
    # Get URL for user to visit
    url = auth.get_authorization_url()
    print(f"Visit: {url}")
    code = input("Paste code from redirect: ")
    auth.exchange_code_for_token(code)

# Use token (e.g., for API client)
token = auth.get_access_token()
```

```python
# Token status dict
status = auth.token_status()
# {
#   "authenticated": True,
#   "access_token_expired": False,
#   "access_token_days_remaining": 45,
#   "refresh_token_days_remaining": 60,
#   "saved_at": "2026-02-22T12:00:00+00:00"
# }
```

---

## Edge Cases & Tips

- **Expiry buffer**: Tokens are treated as expired 5 minutes (`_EXPIRY_BUFFER = 300`) before actual expiry. This prevents using a token that expires mid-request.
- **Refresh token**: LinkedIn may not always return a new refresh token; the code handles both cases (preserves existing refresh token if not returned).
- **Missing tokens**: `get_access_token()` raises `AuthenticationError` if no tokens exist.
- **Refresh failure**: Raises `TokenExpiredError` when refresh fails; user must re-authenticate.

---

## Architecture / Flow

```
User -> get_authorization_url() -> LinkedIn login
    -> Redirect with ?code=... -> exchange_code_for_token(code)
    -> _save_tokens() -> tokens.json

API call -> get_access_token()
    -> if expired: refresh_access_token() -> _save_tokens()
    -> return access_token
```

---

## Advanced Notes

- Tokens include `access_token_expires_at` and optionally `refresh_token_expires_at` (computed from `expires_in`).
- Scopes come from `core.constants.SCOPES` (`r_ads`, `r_ads_reporting`, `r_basicprofile`).
- `check_token_health()` uses `GET /me`; useful for CLI verification.
- Token file path is configurable via `TOKENS_FILE` in config (default: `tokens.json` in project root).
