# Module: System Overview

## Overview

The LinkedIn Ads Action Center is a full-stack application for managing and analyzing LinkedIn advertising campaigns. It syncs data from the LinkedIn Marketing REST API into PostgreSQL, assembles structured snapshots, and serves metrics through a FastAPI backend consumed by a React 19 frontend. This is a single-user tool — there is no user authentication; LinkedIn OAuth exists solely for API access.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  React 19 Frontend (port 5173)                                      │
│  TanStack Router + Query · Tailwind CSS v4 · Chart.js               │
└────────────────────────┬────────────────────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────▼────────────────────────────────────────────┐
│  FastAPI Backend (port 8000)                                        │
│  /api/v1 — auth, sync, report, status, health                       │
│                                                                     │
│  ┌──────────┐  ┌────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ routes/  │→ │ services/  │→ │  linkedin/   │→ │ LinkedIn API │  │
│  │          │  │ sync.py    │  │  client.py   │  │ (REST)       │  │
│  │          │  │ snapshot.py│  │  fetchers.py │  └──────────────┘  │
│  │          │  └─────┬──────┘  │  metrics.py  │                    │
│  │          │        │         └──────────────┘                    │
│  │          │        ▼                                              │
│  │          │  ┌────────────┐  ┌──────────────┐                    │
│  │          │→ │   crud/    │→ │ PostgreSQL   │                    │
│  └──────────┘  └────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend framework | FastAPI 0.115+ | Async HTTP, OpenAPI, dependency injection |
| ORM / models | SQLModel + SQLAlchemy 2.0 | Table definitions, queries, PostgreSQL upserts |
| Database | PostgreSQL 16 | Primary data store (7 tables) |
| Migrations | Alembic | Schema versioning (3 migrations) |
| HTTP client | httpx (async) | LinkedIn API calls with auto-pagination |
| Auth | LinkedIn OAuth 2.0 | Token management, refresh, introspection |
| SSE | sse-starlette | Real-time sync progress streaming |
| Logging | Rich + stdlib logging | Console + 4 rotating file handlers |
| Config | Pydantic Settings | Typed env vars, `.env` file support |
| Frontend | React 19, TypeScript | SPA with file-based routing |
| UI routing | TanStack Router | Type-safe client routing |
| Data fetching | TanStack Query | Server state management |
| Styling | Tailwind CSS v4 | Utility-first with design tokens |
| Charts | Chart.js | Campaign performance visualization |
| Infrastructure | Docker Compose | PostgreSQL + backend + frontend + Nginx |

---

## Data Flow

### Sync Pipeline (triggered via `POST /api/v1/sync`)

1. **Auth check** — `AuthManager` verifies token validity, auto-refreshes if within 5min of expiry
2. **Fetch accounts** — `fetch_ad_accounts()` retrieves all ad accounts via paginated API calls
3. **Fetch campaigns** — Per-account `fetch_campaigns()` with status filter (ACTIVE, PAUSED, DRAFT)
4. **Fetch creatives** — Per-account `fetch_creatives()` filtered by campaign IDs
5. **Fetch metrics** — Parallel `asyncio.gather` for campaign metrics, creative metrics, and demographics (6 pivot types) with batch size of 20 campaigns per API call
6. **Resolve content names** — `resolve_content_references()` derives human-readable names from URNs
7. **Assemble snapshot** — `assemble_snapshot()` validates via Pydantic, aggregates metrics, resolves demographics
8. **Save JSON** — Timestamped snapshot written to `data/snapshots/`
9. **Persist to DB** — PostgreSQL upserts for all entities via `INSERT ON CONFLICT DO UPDATE`
10. **Update sync_log** — Record success/failure with stats

Progress events stream to the frontend in real-time via SSE (`asyncio.Queue`).

---

## Module Map

| Directory | Purpose | Docs |
|-----------|---------|------|
| `app/main.py` | FastAPI app, CORS, middleware, error handler | [01-main.md](01-main.md) |
| `app/core/config.py` | Pydantic Settings configuration | [13-core-config.md](13-core-config.md) |
| `app/core/db.py` | SQLAlchemy engine and session factory | [09-core-db.md](09-core-db.md) |
| `app/core/deps.py` | FastAPI dependency injection | [10-core-deps.md](10-core-deps.md) |
| `app/core/security.py` | OAuth token management | [04-core-security.md](04-core-security.md) |
| `app/linkedin/constants.py` | API version, URLs, scopes | [14-linkedin-constants.md](14-linkedin-constants.md) |
| `app/linkedin/client.py` | Async httpx client with pagination | [06-linkedin-client.md](06-linkedin-client.md) |
| `app/linkedin/fetchers.py` | Entity fetchers (accounts, campaigns, creatives) | [07-linkedin-fetchers.md](07-linkedin-fetchers.md) |
| `app/linkedin/metrics.py` | Analytics and demographics fetchers | [08-linkedin-metrics.md](08-linkedin-metrics.md) |
| `app/models/` | SQLModel tables + Pydantic schemas | [18](18-models-tables.md), [19](19-models-api-validation.md), [20](20-models-responses.md) |
| `app/crud/` | PostgreSQL upserts and queries | [15](15-crud-accounts-campaigns.md), [16](16-crud-metrics-demographics.md), [17](17-crud-sync-log.md) |
| `app/services/sync.py` | Sync orchestration with SSE | [11-services-sync.md](11-services-sync.md) |
| `app/services/snapshot.py` | Snapshot assembly and validation | [12-services-snapshot.md](12-services-snapshot.md) |
| `app/routes/` | API endpoints under `/api/v1` | [02](02-routes-overview.md), [03](03-routes-auth.md), [05](05-routes-sync.md), [21](21-routes-report.md), [22](22-routes-status-health.md) |
| `app/utils/logging.py` | Rich logging + request_id context | [23-utils-logging.md](23-utils-logging.md) |
| `app/errors/exceptions.py` | 9-class exception hierarchy | [24-errors-exceptions.md](24-errors-exceptions.md) |
| `tests/` | 31 tests with SQLite StaticPool | [25-testing.md](25-testing.md) |
| `alembic/` | 3 PostgreSQL migrations | [26-alembic-migrations.md](26-alembic-migrations.md) |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `POSTGRES_HOST` | `localhost` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_USER` | `app` | Database user |
| `POSTGRES_PASSWORD` | `changeme` | Database password |
| `POSTGRES_DB` | `linkedin_ads` | Database name |
| `LINKEDIN_CLIENT_ID` | — | OAuth app client ID |
| `LINKEDIN_CLIENT_SECRET` | — | OAuth app client secret |
| `LINKEDIN_REDIRECT_URI` | `http://localhost:8000/api/v1/auth/callback` | OAuth redirect |
| `OAUTH_STATE` | `supersecretstate` | CSRF state parameter |
| `BACKEND_CORS_ORIGINS` | `["http://localhost:5173", "http://localhost:3000"]` | Allowed CORS origins |
| `FRESHNESS_TTL_MINUTES` | `240` | Min minutes between syncs |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## Known Gaps

1. **No rate limit retry** — `LinkedInClient.get()` raises `RateLimitError` but never retries with backoff
2. **In-memory job store** — `_jobs` dict in `services/sync.py` is lost on process restart
3. **No API auth** — Single-user tool by design; no middleware protecting endpoints
4. **Missing OpenAPI response_model** — Routes lack `response_model=` so Swagger has no response schemas
5. **No connection pool tuning** — Default SQLAlchemy pool settings used
6. **Mixed sync/async routes** — DB-only routes use sync `def`; I/O routes use `async def`
