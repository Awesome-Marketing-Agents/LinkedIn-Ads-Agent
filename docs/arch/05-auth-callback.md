# Module: OAuth Callback Server (FastAPI)

## Overview

`auth/callback.py` runs a FastAPI server that handles the OAuth redirect from LinkedIn. It is used by the CLI auth flow: the server runs in a background thread, opens the auth URL in the browser, and waits for the callback with the authorization code before exchanging it for tokens.

---

## File Path

`src/linkedin_action_center/auth/callback.py`

---

## Components & Explanation

- **`app`** — FastAPI application instance.
- **`auth_manager`** — Shared `AuthManager` instance.
- **`auth_code_received`** — Global variable holding the authorization code from the callback.
- **`callback(request)`** — Route `GET /callback`; validates state, extracts code, stores it in `auth_code_received`, returns success HTML.
- **`run_callback_server()`** — Runs Uvicorn on `localhost:5000`.
- **`start_auth_flow()`** — Orchestrates the full flow: start server in thread, open browser, wait for code, exchange for tokens.

---

## Relationships

- Uses `AuthManager` and `OAUTH_STATE` from `core.config`.
- Runs on port 5000; **conflicts with Flask** if both run at once.
- Intended for CLI auth; web dashboard uses Flask’s `/callback` in `main.py`.

---

## Example Code Snippets

```bash
# Run the callback server standalone (for CLI auth)
uv run python -m linkedin_action_center.auth.callback
```

```python
# Programmatic usage
from linkedin_action_center.auth.callback import start_auth_flow
start_auth_flow()  # Opens browser, waits, exchanges code
```

```bash
# Callback URL must match .env
# LINKEDIN_REDIRECT_URI=http://localhost:5000/callback
```

---

## Edge Cases & Tips

- **Port conflict**: Both Flask (`main.py`) and this callback server use port 5000. Do not run them simultaneously.
- **State validation**: Invalid `state` returns 400; protects against CSRF.
- **Error handling**: If LinkedIn returns `error` in query params, an HTML error page is returned.
- **Threading**: Server runs as a daemon thread; process exits after `start_auth_flow()` completes.

---

## Architecture / Flow

```
start_auth_flow()
    │
    ├── If authenticated → check_token_health() → return
    │
    └── Else:
            ├── Thread: uvicorn.run(app, port=5000)
            ├── webbrowser.open(auth_url)
            ├── while not auth_code_received: sleep(1)
            └── auth_manager.exchange_code_for_token(auth_code_received)
```

---

## Node.js Equivalent

- `auth/callback.py` (FastAPI on port 5000) is replaced by `node-app/src/auth/callback.ts` (a Fastify route plugin).
- No separate server is needed; the callback is a Fastify route plugin registered on the main server.
- This eliminates the port conflict between Flask and FastAPI that exists in the Python version.
- The same state validation and CSRF protection logic is preserved.

---

## Advanced Notes

- The CLI (`cli.py`) does **not** use this module; it uses interactive `input()` for the code.
- This module is useful when you want a fully automated CLI auth flow with browser redirect.
- `.env.example` shows `OAUTH_PORT=8080`; this module hardcodes 5000.
