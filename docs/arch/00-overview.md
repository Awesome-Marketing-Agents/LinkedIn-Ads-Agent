# Architecture Overview: LinkedIn Ads Action Center

## Overview

The **LinkedIn Ads Action Center** is a modular Python application that lets you authenticate with the LinkedIn API, ingest ad campaign data, and view performance metrics through either a web dashboard or a command-line interface. Data flows from the LinkedIn REST API into a local SQLite database and JSON snapshots, enabling offline analysis and historical tracking.

This document provides a high-level view of the system. For detailed per-module documentation, see the other files in this folder.

---

## File Path

`docs/arch/00-overview.md`

---

## System Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Auth** | `auth/` | OAuth 2.0 flow, token storage, refresh |
| **Ingestion** | `ingestion/` | HTTP client, API fetchers, metrics |
| **Storage** | `storage/` | SQLite schema, repository, snapshot assembly |
| **Core** | `core/` | Config, constants |
| **Utils** | `utils/` | Logging, custom exceptions |
| **Web Dashboard** | `main.py` | Flask app with routes for auth, sync, status |
| **CLI** | `cli.py` | Scriptable commands (`auth`, `sync`, `status`) |
| **OAuth Callback** | `auth/callback.py` | FastAPI server for CLI auth flow |

---

## Data Flow: LinkedIn API → Local Storage

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. User initiates action (Web or CLI)                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. AuthManager.get_access_token()                                           │
│    - Loads tokens from tokens.json                                           │
│    - Auto-refreshes if expired (5 min buffer)                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. ingestion/fetchers + metrics                                             │
│    a) fetch_ad_accounts(client)                                              │
│    b) For each account: fetch_campaigns(client, account_id)                   │
│    c) For each campaign: fetch_creatives(client, account_id, campaign_ids)   │
│    d) fetch_campaign_metrics(client, campaign_ids, date_start, date_end)     │
│    e) fetch_creative_metrics(client, campaign_ids, dates)                     │
│    f) fetch_demographics(client, campaign_ids, dates)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. storage/snapshot.assemble_snapshot()                                      │
│    - Combines raw API data into a structured dict                            │
│    - Aggregates metrics, computes CTR, CPC, etc.                             │
│    - Indexes demographics by pivot type                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 5. Persistence                                                               │
│    a) save_snapshot_json(snapshot) → data/snapshots/snapshot_YYYYMMDD.json   │
│    b) persist_snapshot(snapshot) → data/linkedin_ads.db (SQLite)            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 6. User sees results (status page, sync log, CLI output)                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Environment & Config

| Variable | Purpose | Required |
|----------|---------|----------|
| `LINKEDIN_CLIENT_ID` | LinkedIn app client ID | Yes |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn app secret | Yes |
| `LINKEDIN_REDIRECT_URI` | OAuth callback URL (e.g. `http://localhost:5000/callback`) | Yes |
| `OAUTH_STATE` | CSRF protection string | No (default: `supersecretstate`) |

Config is loaded from `.env` via `python-dotenv` in `core/config.py`. Paths are derived from `BASE_DIR`:

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
| Database | SQLite |
| Config | python-dotenv |
| Logging | rich |
| Python | 3.13+ |

---

## User Interaction Flow

### Web Dashboard

1. Start: `uv run python main.py`
2. Open: http://127.0.0.1:5000
3. Authenticate → `/auth` → redirect to LinkedIn → callback at `/callback`
4. Sync → `/sync` → fetches all data, persists, shows log
5. Status → `/status` → token health + DB row counts + active campaign audit

### CLI

1. Auth: `uv run python cli.py auth` → prints URL, user pastes code
2. Sync: `uv run python cli.py sync` → full sync with progress
3. Status: `uv run python cli.py status` → token + DB summary

---

## Module Relationships

```
main.py / cli.py
    │
    ├── auth/manager.py (AuthManager)
    │       └── core/config, core/constants, utils/logger, utils/errors
    │
    ├── ingestion/client.py (LinkedInClient)
    │       └── auth/manager, core/constants, utils/logger, utils/errors
    │
    ├── ingestion/fetchers.py
    │       └── ingestion/client
    │
    ├── ingestion/metrics.py
    │       └── ingestion/client
    │
    ├── storage/snapshot.py
    │       └── core/config
    │
    └── storage/repository.py
            └── storage/database, utils/logger, utils/errors
```

---

## Sequence: User Action → Data Display

1. User clicks "Sync Now" → `main.py` route `/sync`
2. `auth_manager.is_authenticated()` → `auth_manager.get_access_token()` if needed
3. `LinkedInClient(auth_manager)` → uses token for API calls
4. `fetch_ad_accounts`, `fetch_campaigns`, `fetch_creatives` → entities
5. `fetch_campaign_metrics`, `fetch_creative_metrics`, `fetch_demographics` → analytics
6. `assemble_snapshot(...)` → structured dict
7. `save_snapshot_json(snapshot)` → JSON file
8. `persist_snapshot(snapshot)` → SQLite
9. Response rendered with sync log

---

## Common Pitfalls

- **Redirect URI mismatch**: Ensure `LINKEDIN_REDIRECT_URI` matches the LinkedIn app’s configured callback URL.
- **Token expiry**: Access tokens expire after ~60 days; refresh uses `refresh_token`. If refresh fails, re‑authenticate.
- **Rate limiting**: 429 responses raise `RateLimitError`; check `Retry-After` header.
- **Empty accounts**: If no ad accounts exist, sync returns empty data; verify LinkedIn app permissions and ads access.

---

## Advanced Notes

- **Snapshot structure**: Designed for future LLM analysis; JSON schema is self-contained.
- **Pagination**: `LinkedInClient.get_all_pages()` handles both offset and token-based pagination.
- **Database**: SQLite with WAL mode; schema is applied on every `get_connection()`.
- **Auth callback**: Web uses Flask’s `/callback`; CLI uses FastAPI `auth/callback.py` in a separate flow.
