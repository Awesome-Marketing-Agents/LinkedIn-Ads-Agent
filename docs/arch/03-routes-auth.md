# Module: Auth Routes

## Overview

Auth routes handle the LinkedIn OAuth 2.0 flow: checking token status, generating the authorization URL, validating token health against the `/me` endpoint, and processing the OAuth callback to exchange the authorization code for tokens.

---

## File Path

`backend/app/routes/auth.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `app.core.deps.get_auth` | Dependency injection for `AuthManager` |
| `app.core.config.settings` | OAuth state validation |
| `app.utils.logging.log_auth_event` | Auth event logging |

---

## Components

### `GET /auth/status`

```python
async def auth_status(auth: AuthManager = Depends(get_auth)):
    return auth.token_status()
```

**Returns**: Dict with `authenticated`, `access_token_expired`, `access_token_days_remaining`, `refresh_token_days_remaining`, `saved_at`.

### `GET /auth/url`

```python
async def auth_url(auth: AuthManager = Depends(get_auth)):
    return {"url": auth.get_authorization_url()}
```

**Returns**: `{"url": "https://www.linkedin.com/oauth/v2/authorization?..."}`.

### `GET /auth/health`

```python
async def auth_health(auth: AuthManager = Depends(get_auth)):
    healthy = await auth.check_token_health()
    return {"healthy": healthy}
```

**Behavior**: Calls LinkedIn `/me` endpoint to verify the token works. Returns `{"healthy": true/false}`.

### `GET /auth/callback`

```python
async def auth_callback(request: Request, auth: AuthManager = Depends(get_auth)):
```

**Behavior**:
1. Validates `state` query param against `settings.OAUTH_STATE`
2. Extracts `code` query param (raises 400 if missing)
3. Calls `auth.exchange_code_for_token(code)` to get tokens
4. Redirects to `http://localhost:5173/auth` (frontend)

**Response**: `HTMLResponse` (redirect)

---

## Code Snippet

```python
# Frontend: check auth status
const response = await fetch("/api/v1/auth/status");
const { authenticated, access_token_days_remaining } = await response.json();
```

---

## Relationships

- **Uses**: `AuthManager` via `Depends(get_auth)` — see [04-core-security.md](04-core-security.md)
- **Mounted by**: `routes/__init__.py` at `/auth` — see [02-routes-overview.md](02-routes-overview.md)
