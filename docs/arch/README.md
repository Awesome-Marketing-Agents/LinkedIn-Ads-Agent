# Architecture Documentation

Documentation for the **LinkedIn Ads Action Center** backend. Each document covers a module or file in detail so you can understand, debug, and extend any part of the system.

---

## Quick Start

- **New to the project?** Start with [00-overview.md](00-overview.md) for the high-level architecture.
- **Working on a specific module?** Use the index below to jump to the right doc.

---

## Document Index

| # | Document | Module / File | Description |
|---|----------|--------------|-------------|
| 00 | [00-overview.md](00-overview.md) | System Overview | Architecture, data flow, tech stack, module map |
| 01 | [01-main.md](01-main.md) | `app/main.py` | FastAPI app, CORS, request context middleware, error handler |
| 02 | [02-routes-overview.md](02-routes-overview.md) | `routes/__init__.py` | Router aggregator, endpoint table |
| 03 | [03-routes-auth.md](03-routes-auth.md) | `routes/auth.py` | OAuth endpoints: status, url, health, callback |
| 04 | [04-core-security.md](04-core-security.md) | `core/security.py` | AuthManager: OAuth flow, token refresh, health check |
| 05 | [05-routes-sync.md](05-routes-sync.md) | `routes/sync.py` | Sync trigger, SSE stream, job polling |
| 06 | [06-linkedin-client.md](06-linkedin-client.md) | `linkedin/client.py` | Async httpx client, auto-auth, pagination |
| 07 | [07-linkedin-fetchers.md](07-linkedin-fetchers.md) | `linkedin/fetchers.py` | Entity fetchers: accounts, campaigns, creatives |
| 08 | [08-linkedin-metrics.md](08-linkedin-metrics.md) | `linkedin/metrics.py` | Analytics and demographics fetchers, batching |
| 09 | [09-core-db.md](09-core-db.md) | `core/db.py` | PostgreSQL engine, session factory |
| 10 | [10-core-deps.md](10-core-deps.md) | `core/deps.py` | FastAPI dependencies: get_db(), get_auth() |
| 11 | [11-services-sync.md](11-services-sync.md) | `services/sync.py` | SyncJob, 10-step pipeline, SSE events |
| 12 | [12-services-snapshot.md](12-services-snapshot.md) | `services/snapshot.py` | Snapshot assembly, validation, aggregation |
| 13 | [13-core-config.md](13-core-config.md) | `core/config.py` | Pydantic Settings, env vars, DB URI |
| 14 | [14-linkedin-constants.md](14-linkedin-constants.md) | `linkedin/constants.py` | API version, base URLs, scopes |
| 15 | [15-crud-accounts-campaigns.md](15-crud-accounts-campaigns.md) | `crud/accounts.py`, `crud/campaigns.py` | Account and campaign upserts + queries |
| 16 | [16-crud-metrics-demographics.md](16-crud-metrics-demographics.md) | `crud/metrics.py`, `crud/demographics.py` | Metrics upserts, pagination, visual data |
| 17 | [17-crud-sync-log.md](17-crud-sync-log.md) | `crud/sync_log.py` | Freshness gate, sync lifecycle, audit |
| 18 | [18-models-tables.md](18-models-tables.md) | `models/*.py` | 7 SQLModel table definitions |
| 19 | [19-models-api-validation.md](19-models-api-validation.md) | `models/linkedin_api.py` | Pydantic models for API responses |
| 20 | [20-models-responses.md](20-models-responses.md) | `models/responses.py` | Shared API response schemas |
| 21 | [21-routes-report.md](21-routes-report.md) | `routes/report.py` | 7 report GET endpoints |
| 22 | [22-routes-status-health.md](22-routes-status-health.md) | `routes/status.py`, `routes/health.py` | Status dashboard + health check |
| 23 | [23-utils-logging.md](23-utils-logging.md) | `utils/logging.py` | Rich console, file handlers, request_id |
| 24 | [24-errors-exceptions.md](24-errors-exceptions.md) | `errors/exceptions.py` | 9-class exception hierarchy |
| 25 | [25-testing.md](25-testing.md) | `tests/` | Test infra: SQLite StaticPool, fixtures |
| 26 | [26-alembic-migrations.md](26-alembic-migrations.md) | `alembic/` | 3 PostgreSQL migrations |

---

## Common Commands

```bash
# Backend
cd backend && uv sync                    # Install deps
cd backend && pytest                     # Run tests
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev

# Docker
docker compose up -d
```

---

## Data Flow Summary

```
React Frontend (port 5173)
    → FastAPI routes (/api/v1)
    → services/sync.py (10-step pipeline)
    → linkedin/ fetchers + metrics (async httpx)
    → services/snapshot.py (Pydantic validation + aggregation)
    → crud/ upserts (PostgreSQL INSERT ON CONFLICT)
    → SSE progress events back to frontend
```

---

## Search Tips

- **Authentication**: 03-routes-auth, 04-core-security
- **Sync pipeline**: 05-routes-sync, 11-services-sync, 12-services-snapshot
- **API calls**: 06-linkedin-client, 07-linkedin-fetchers, 08-linkedin-metrics
- **Database**: 09-core-db, 15 through 17 (CRUD), 18 (models)
- **Config / env**: 13-core-config, 14-linkedin-constants
- **Data models**: 18 (DB), 19 (API validation), 20 (response schemas)
- **Logging / errors**: 23-utils-logging, 24-errors-exceptions
- **Testing**: 25-testing
- **Migrations**: 26-alembic-migrations
