# Module: Web Dashboard (Flask Entry Point)

## Overview

`main.py` is the web entry point for the LinkedIn Ads Action Center. It runs a Flask app on port 5000 with routes for authentication, data sync, and status. The UI rendering logic lives in `ui.py`, which provides inline HTML templates with Chart.js visualisations. Users interact via the browser instead of the CLI.

---

## File Path

`main.py` (entry point), `ui.py` (UI rendering)

---

## Components & Explanation

- **`app`** — Flask application instance.
- **`auth_manager`** — Shared `AuthManager` for token handling.
- **`home()`** — Route `/`; shows three cards: Authenticate, Sync Data, Check Status.
- **`auth()`** — Route `/auth`; if authenticated, shows token status; otherwise redirects to LinkedIn.
- **`callback()`** — Route `/callback`; handles OAuth redirect, validates state, exchanges code for tokens.
- **`sync()`** — Route `/sync`; runs full data sync (accounts -> campaigns -> creatives -> metrics -> demographics -> persist).
- **`status()`** — Route `/status`; shows token health, DB row counts, and active campaign audit.
- **`report_visual()`** — Route `/report/visual`; renders a Chart.js dashboard with 9 chart types: KPI scorecards, performance trends, campaign comparisons, spend distribution, conversion funnel, budget utilisation, engagement radar, creative performance, demographic breakdowns.

### UI Layer (`ui.py`)

The UI logic was separated from `main.py` into `ui.py` to keep the entry point lean. `ui.py` contains:
- HTML layout template with shared styles (ink-blue sidebar, Inter typography, semantic tokens)
- Route handlers for all pages
- Chart.js integration for visual reports
- Data tables and stat blocks for structured data display

---

## Relationships

- Uses `AuthManager`, `LinkedInClient`, fetchers, metrics, snapshot, and repository.
- Reads `OAUTH_STATE` from `core.config`.
- Depends on `bootstrap` for imports.
- `ui.py` handles all template rendering and CSS/JS.

---

## Example Code Snippets

```bash
# Start the web server
uv run python main.py
```

```bash
# Available routes
# http://127.0.0.1:5000/           -> Home page
# http://127.0.0.1:5000/auth       -> Auth flow
# http://127.0.0.1:5000/sync       -> Data sync
# http://127.0.0.1:5000/status     -> Status dashboard
# http://127.0.0.1:5000/report/visual -> Chart.js visual report
```

---

## Edge Cases & Tips

- **State validation**: `/callback` checks `state == OAUTH_STATE`; mismatches return 400 (CSRF protection).
- **Sync without auth**: `/sync` returns 401 if not authenticated.
- **Date range**: Sync uses last 90 days by default (`today - timedelta(days=90)`).
- **Creative fetch**: Web sync fetches creatives per account with `campaign_ids` filter.
- **Visual report**: Requires at least one synced snapshot to display charts.

---

## Architecture / Flow

```
Browser
    |
    ├── GET /              -> home()           -> Cards with links
    ├── GET /auth          -> auth()           -> Redirect to LinkedIn or show status
    ├── GET /callback      -> callback()       -> Exchange code -> tokens.json
    ├── GET /sync          -> sync()           -> auth -> fetch -> assemble -> persist -> log
    ├── GET /status        -> status()         -> token_status + table_counts + audit
    └── GET /report/visual -> report_visual()  -> Chart.js dashboard
```

---

## Advanced Notes

- Uses `render_template_string` with inline templates; no separate template files.
- Sync logs are built in a list and rendered in a `<pre>` block.
- Flask runs with `debug=True`; disable in production.
- `ui.py` is ~1900 lines; contains all CSS, HTML templates, and Chart.js config inline.
