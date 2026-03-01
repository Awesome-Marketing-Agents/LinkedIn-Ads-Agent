# Architecture Overview: LinkedIn Ads Action Center

## Overview

The **LinkedIn Ads Action Center** is a modular Python application that lets you authenticate with the LinkedIn API, ingest ad campaign data, and view performance metrics through either a web dashboard or a command-line interface. Data flows from the LinkedIn REST API through Pydantic validation into a local SQLite database (via SQLAlchemy upserts) and JSON snapshots, enabling offline analysis and historical tracking.

This document provides a high-level view of the system. For detailed per-module documentation, see the other files in this folder.

---

## File Path

`docs/arch/00-overview.md`

---

## System Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Auth** | `auth/` | OAuth 2.0 flow, token storage, refresh |
| **Ingestion** | `ingestion/` | HTTP client, API fetchers, metrics & demographics |
| **Storage** | `storage/` | SQLite schema, SQLAlchemy engine, repository (upserts), snapshot assembly |
| **Models** | `models/` | Pydantic API models (validation), SQLModel DB models (ORM) |
| **Core** | `core/` | Pydantic BaseSettings config, API constants |
| **Utils** | `utils/` | Rich logging, custom exceptions |
| **Migrations** | `alembic/` | Database schema versioning with Alembic |
| **Web Dashboard** | `main.py` + `ui.py` | Flask app with routes for auth, sync, status, visual reports |
| **CLI** | `cli.py` | Scriptable commands (`auth`, `sync`, `status`) |
| **OAuth Callback** | `auth/callback.py` | FastAPI server for CLI auth flow |

---

## Data Flow: LinkedIn API -> Local Storage

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. User initiates action (Web or CLI)                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      |
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. Freshness Gate (repository.should_sync)                                 │
│    - Checks sync_log for last successful sync                              │
│    - Skips if data is fresh (default: 4-hour TTL)                          │
│    - Logs new sync_log entry via start_sync_run()                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      |
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. AuthManager.get_access_token()                                          │
│    - Loads tokens from tokens.json                                         │
│    - Auto-refreshes if expired (5 min buffer)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      |
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. ingestion/fetchers + metrics                                            │
│    a) fetch_ad_accounts(client)                                            │
│    b) For each account: fetch_campaigns(client, account_id)                │
│    c) For each account: fetch_creatives(client, account_id, campaign_ids)  │
│    d) fetch_campaign_metrics(client, campaign_ids, date_start, date_end)   │
│    e) fetch_creative_metrics(client, campaign_ids, dates)                  │
│    f) fetch_demographics(client, campaign_ids, dates)                      │
│    g) resolve_demographic_urns(client, demo_data)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      |
┌─────────────────────────────────────────────────────────────────────────────┐
│ 5. storage/snapshot.assemble_snapshot()                                     │
│    - Validates ALL raw data through Pydantic models (api_models.py)        │
│    - Invalid records are logged and skipped                                │
│    - Combines raw API data into a structured dict                          │
│    - Aggregates metrics, computes CTR, CPC, CPM, CPL                      │
│    - Resolves demographic URNs to human-readable names                     │
│    - Indexes demographics by pivot type (top 10 per pivot)                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      |
┌─────────────────────────────────────────────────────────────────────────────┐
│ 6. Persistence                                                             │
│    a) save_snapshot_json(snapshot) -> data/snapshots/snapshot_YYYYMMDD.json │
│    b) persist_snapshot(snapshot) -> data/linkedin_ads.db                    │
│       Uses SQLAlchemy Core insert().on_conflict_do_update()                │
│       True upserts — no data loss, no duplicates                           │
│    c) finish_sync_run(run_id) -> updates sync_log with stats               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      |
┌─────────────────────────────────────────────────────────────────────────────┐
│ 7. User sees results (status page, visual report, sync log, CLI output)    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Environment & Config

Configuration is managed through a Pydantic `BaseSettings` class in `core/config.py`. Environment variables are loaded from `.env` via `python-dotenv` and validated at startup.

| Variable | Purpose | Required |
|----------|---------|----------|
| `LINKEDIN_CLIENT_ID` | LinkedIn app client ID | Yes |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn app secret | Yes |
| `LINKEDIN_REDIRECT_URI` | OAuth callback URL (e.g. `http://localhost:5000/callback`) | No (has default) |
| `OAUTH_STATE` | CSRF protection string | No (default: `supersecretstate`) |
| `FRESHNESS_TTL_MINUTES` | Minutes before a sync is re-run | No (default: `240`) |

Paths are derived from `BASE_DIR` (project root):

- `tokens.json` — OAuth tokens
- `data/linkedin_ads.db` — SQLite database
- `data/snapshots/` — JSON snapshots
- `logs/` — Log files

---

## Dependencies & Tech Stack

| Layer | Technology |
|-------|-------------|
| Package manager | uv |
| Web dashboard | Flask |
| OAuth callback (CLI) | FastAPI + Uvicorn |
| HTTP client | requests |
| Database | SQLite (WAL mode) |
| ORM | SQLAlchemy + SQLModel |
| Migrations | Alembic |
| Config validation | Pydantic BaseSettings |
| API data validation | Pydantic models |
| Logging | Rich |
| Testing | pytest |
| Python | 3.13+ |

---

## User Interaction Flow

### Web Dashboard

1. Start: `uv run python main.py`
2. Open: http://127.0.0.1:5000
3. Authenticate -> `/auth` -> redirect to LinkedIn -> callback at `/callback`
4. Sync -> `/sync` -> freshness check -> fetches all data -> persists -> shows log
5. Status -> `/status` -> token health + DB row counts + active campaign audit
6. Visual Report -> `/report/visual` -> Chart.js dashboards with 9 chart types

### CLI

1. Auth: `uv run python cli.py auth` -> prints URL, user pastes code
2. Sync: `uv run python cli.py sync` -> freshness check -> full sync with progress
3. Status: `uv run python cli.py status` -> token + DB summary

---

## Module Relationships

```
main.py / cli.py
    |
    ├── auth/manager.py (AuthManager)
    │       └── core/config, core/constants, utils/logger, utils/errors
    |
    ├── ingestion/client.py (LinkedInClient)
    │       └── auth/manager, core/constants, utils/logger, utils/errors
    |
    ├── ingestion/fetchers.py
    │       └── ingestion/client
    |
    ├── ingestion/metrics.py
    │       └── ingestion/client
    |
    ├── storage/snapshot.py
    │       └── core/config, models/api_models, utils/logger
    |
    ├── storage/repository.py
    │       └── storage/database, models/db_models, core/config, utils/logger, utils/errors
    |
    └── storage/database.py
            └── core/config
```

---

## Sequence: User Action -> Data Display

1. User clicks "Sync Now" -> `main.py` route `/sync`
2. `should_sync(account_id)` -> check freshness gate (4-hour TTL)
3. `start_sync_run(account_id)` -> log sync start
4. `auth_manager.get_access_token()` -> auto-refresh if needed
5. `LinkedInClient(auth_manager)` -> uses token for API calls
6. `fetch_ad_accounts`, `fetch_campaigns`, `fetch_creatives` -> entities
7. `fetch_campaign_metrics`, `fetch_creative_metrics`, `fetch_demographics` -> analytics
8. `resolve_demographic_urns(client, demo_data)` -> human-readable names
9. `assemble_snapshot(...)` -> Pydantic validation -> structured dict
10. `save_snapshot_json(snapshot)` -> JSON file
11. `persist_snapshot(snapshot)` -> SQLAlchemy upserts into SQLite
12. `finish_sync_run(run_id)` -> update sync_log
13. Response rendered with sync log

---

## Common Pitfalls

- **Redirect URI mismatch**: Ensure `LINKEDIN_REDIRECT_URI` matches the LinkedIn app's configured callback URL.
- **Token expiry**: Access tokens expire after ~60 days; refresh uses `refresh_token`. If refresh fails, re-authenticate.
- **Rate limiting**: 429 responses raise `RateLimitError`; check `Retry-After` header.
- **Empty accounts**: If no ad accounts exist, sync returns empty data; verify LinkedIn app permissions and ads access.
- **Pydantic validation**: Invalid API records are logged and skipped (not raised). Check logs if data looks incomplete.
- **Freshness gate**: Sync is skipped if data is less than 4 hours old. Pass `force=True` to override.

---

## Advanced Notes

- **Snapshot structure**: Designed for future LLM analysis; JSON schema is self-contained.
- **Pagination**: `LinkedInClient.get_all_pages()` handles both offset and token-based pagination.
- **Database**: SQLite with WAL mode; dual interface: `get_connection()` for legacy raw SQL, `get_session()` for SQLAlchemy ORM.
- **Upserts**: `INSERT ON CONFLICT DO UPDATE` via SQLAlchemy Core — true upserts, no data loss.
- **Two-layer validation**: API responses validated by Pydantic models (`models/api_models.py`), database writes use SQLModel (`models/db_models.py`).
- **Auth callback**: Web uses Flask's `/callback`; CLI uses FastAPI `auth/callback.py` in a separate flow.
- **Alembic**: Migrations managed via `alembic/`; initial migration matches the raw SQL schema in `database.py`.
