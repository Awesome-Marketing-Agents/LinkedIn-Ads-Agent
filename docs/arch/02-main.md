# Module: Web Dashboard (Flask Entry Point)

## Overview

`main.py` is the web entry point for the LinkedIn Ads Action Center. It runs a Flask app on port 5000 with routes for authentication, data sync, and status. Users interact via the browser instead of the CLI.

---

## File Path

`main.py`

---

## Components & Explanation

- **`app`** — Flask application instance.
- **`auth_manager`** — Shared `AuthManager` for token handling.
- **`LAYOUT`** — HTML template string with shared styles and layout.
- **`_render(content_html)`** — Renders `content_html` inside `LAYOUT` and returns an HTML response.
- **`home()`** — Route `/`; shows three cards: Authenticate, Sync Data, Check Status.
- **`auth()`** — Route `/auth`; if authenticated, shows token status; otherwise redirects to LinkedIn.
- **`callback()`** — Route `/callback`; handles OAuth redirect, validates state, exchanges code for tokens.
- **`sync()`** — Route `/sync`; runs full data sync (accounts → campaigns → creatives → metrics → persist).
- **`status()`** — Route `/status`; shows token health, DB row counts, and active campaign audit.

---

## Relationships

- Uses `AuthManager`, `LinkedInClient`, fetchers, metrics, snapshot, and repository.
- Reads `OAUTH_STATE` from `core.config`.
- Depends on `bootstrap` for imports.

---

## Example Code Snippets

```bash
# Start the web server
uv run python main.py
```

```bash
# Example curl calls (with server running)
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/auth
curl http://127.0.0.1:5000/status
```

```python
# Minimal test of _render
from main import _render
resp = _render("<p>Hello</p>")
assert "Hello" in resp.get_data(as_text=True)
```

---

## Edge Cases & Tips

- **State validation**: `/callback` checks `state == OAUTH_STATE`; mismatches return 400 (CSRF protection).
- **Sync without auth**: `/sync` returns 401 if not authenticated.
- **Date range**: Sync uses last 90 days by default (`today - timedelta(days=90)`).
- **Creative fetch**: Web sync fetches creatives per account with `campaign_ids` filter; same pattern as CLI.

---

## Architecture / Flow

```
Browser
    │
    ├── GET /         → home()        → Cards with links
    ├── GET /auth     → auth()        → Redirect to LinkedIn or show status
    ├── GET /callback → callback()    → Exchange code → tokens.json
    ├── GET /sync     → sync()        → auth → fetch → assemble → persist → log
    └── GET /status   → status()      → token_status + table_counts + audit
```

---

## Node.js Equivalent

- Python's `main.py` (Flask on port 5000) is replaced by `node-app/src/server.ts` (Fastify on port 5002).
- Inline HTML templates are replaced by a React SPA in `node-app/frontend/`.
- Routes are split into separate modules: `node-app/src/routes/auth.ts`, `sync.ts`, `status.ts`, and `report.ts`.
- The Node.js backend is API-only; the frontend is served by the Vite dev server (port 3000) during development, or as built static files in production.
- New capability: SSE streaming for sync progress via `POST /api/sync` using an EventEmitter pattern, allowing the frontend to display real-time sync updates.

---

## Advanced Notes

- Uses `render_template_string` with a single `LAYOUT`; no separate template files.
- Sync logs are built in a list and rendered in a `<pre>` block.
- Flask runs with `debug=True`; disable in production.
