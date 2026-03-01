# Sprint 4: FastAPI Consolidation & Data Pipeline Maturation

**Start Date**: February 28, 2026
**End Date**: March 1, 2026
**Status**: Completed

---

## Objectives

1. Consolidate backend from Flask to FastAPI with full async support
2. Migrate database from SQLite to PostgreSQL
3. Replace synchronous `requests` with async `httpx` throughout
4. Add React 19 frontend with TanStack Router/Query
5. Fix multi-account sync data isolation bug
6. Add CI/CD pipeline with ruff linting
7. Enrich creatives with human-readable content names

---

## Problems Addressed

### Problem 1: Flask → FastAPI Migration (HIGH)
- **Symptom**: Flask app lacked async support, dependency injection, and modern middleware patterns.
- **Root cause**: Original stack was Flask + CLI + synchronous `requests`.
- **Fix**: Full rewrite to FastAPI with lifespan, CORS middleware, request context middleware (contextvars), and structured exception handler. Removed `bootstrap.py`, `cli.py`, `ui.py`, `auth/callback.py`.

### Problem 2: Metrics Not Persisting (HIGH)
- **Symptom**: Sync completed successfully but campaign/creative metrics were not appearing in the database.
- **Root cause**: The sync pipeline's persist step wasn't iterating the snapshot structure correctly — daily metrics and creative metrics were skipped.
- **Fix**: Rewired `run_sync()` persistence loop to iterate `account → campaign → metrics → creatives → creative_metrics → demographics`, added `upsert_creatives()` and proper `upsert_creative_daily_metrics()` calls.

### Problem 3: Multi-Account Sync Bug (MEDIUM)
- **Symptom**: All campaigns assigned to the first account when multiple ad accounts existed.
- **Root cause**: Flat `campaigns_list` with no account association. `assemble_snapshot()` assigned all campaigns to every account.
- **Fix**: Tag each campaign with `_account_id` during fetch, build `campaigns_by_account` dict in `assemble_snapshot()`, only assign campaigns to their actual account.

### Problem 4: No CI/CD (MEDIUM)
- **Symptom**: No automated testing or linting on push/PR.
- **Root cause**: No GitHub Actions workflow existed.
- **Fix**: Added CI workflow with Python 3.12, `uv sync`, `ruff check`, and `pytest`. Updated workflow for `backend/` directory structure.

### Problem 5: Creatives Lack Human-Readable Names (LOW)
- **Symptom**: Creative entities only show opaque URNs (e.g., `urn:li:share:7123456789`), making the dashboard hard to read.
- **Root cause**: No content name resolution.
- **Fix**: Added `resolve_content_references()` to derive labels from URN type + ID (e.g., "Sponsored Post #456789"), added `content_name` column via migration 0003, wired through snapshot → CRUD → frontend.

---

## Completed Work

### Fix A: FastAPI + React Consolidation

**Commit**: `57c7e1c` — "Consolidate to FastAPI + React stack with crafted design system"
**PR**: #11

Complete rewrite of the application architecture:

**Backend changes**:
- Replaced Flask `main.py` with FastAPI app (`app/main.py`): lifespan, CORS, request context middleware, exception handler
- Created `app/routes/` package: `auth.py`, `sync.py`, `report.py`, `status.py`, `health.py`
- Created `app/core/deps.py`: FastAPI dependency injection (`get_db`, `get_auth`)
- Rewrote `core/security.py`: all token operations now async via `httpx`
- Rewrote `linkedin/client.py`: `LinkedInClient` now uses `httpx.AsyncClient` with 30s timeout
- Created `app/services/sync.py`: `SyncJob` class with `asyncio.Queue` for SSE progress streaming
- Created `app/models/responses.py`: shared Pydantic response schemas
- Migrated `core/config.py` to PostgreSQL fields with `SQLALCHEMY_DATABASE_URI` computed property
- Rewrote `core/db.py`: PostgreSQL engine with `pool_pre_ping=True`
- Split monolithic `storage/repository.py` into 4 CRUD modules: `accounts.py`, `campaigns.py`, `metrics.py`, `demographics.py`, `sync_log.py`
- Added `sse-starlette` and `psycopg[binary]` dependencies

**Frontend** (new):
- React 19 + TypeScript SPA with TanStack Router (file-based routing)
- TanStack Query for server state management
- Tailwind CSS v4 with custom design tokens (blue-gray, borders-only depth)
- 6 pages: index, auth, sync, visual, report, status
- Chart.js visualizations for campaign performance
- Docker Compose with Nginx reverse proxy

**Removed**: `bootstrap.py`, `cli.py`, `ui.py`, `auth/callback.py`, Flask templates, `storage/` directory

### Fix B: Data Pipeline Persistence Fix

**Commit**: `50e67e3` — "Fix data pipeline: persist all fetched metrics, wire sync_log, add creatives route"
**PR**: #12

- Fixed `run_sync()` to correctly iterate snapshot and call all upsert functions
- Wired `start_sync_run()` / `finish_sync_run()` into the sync pipeline
- Added `GET /report/creatives` endpoint
- Added `upsert_creatives()` function in `crud/metrics.py`
- Fixed `get_creative_metrics_paginated()` to JOIN with Creative and Campaign for names

### Fix C: Multi-Account Sync Fix

**Commits**: `d97069c`, `a4a4e92` — "Fix sync to fetch all accounts and correct config/proxy ports"
**PR**: #10

- Fixed `fetch_campaigns()` and `fetch_creatives()` to accept `account_id` parameter
- Tagged campaigns with `_account_id` in `run_sync()` for account association
- Added `campaigns_by_account` mapping in `assemble_snapshot()` to prevent cross-account data mixing
- Fixed config `LINKEDIN_REDIRECT_URI` to use port 8000 (FastAPI)
- Fixed Nginx proxy configuration for correct port routing

### Fix D: CI/CD + Ruff Linting

**Commits**: `27cb98a`, `d11675d` — "Update CI workflow for backend/ structure and add ruff linting"
**PR**: #12

- Added GitHub Actions workflow: Python 3.12 setup, `uv sync`, `ruff check backend/`, `pytest`
- Updated CI for `backend/` directory structure (not root-level)
- Added `ruff>=0.8.0` to dev dependencies
- Fixed linting issues across codebase

### Fix E: Creative Content Name Resolution

**Commit**: `3c2ea48` — "Add human-readable content names for creatives"
**PR**: #13

- Added `resolve_content_references()` in `linkedin/fetchers.py`: derives display names from URN type + ID without extra API calls
- Added `content_name` column to `Creative` model
- Added Alembic migration `0003_add_content_name`
- Wired `content_names` through `assemble_snapshot()` → `upsert_creatives()` → frontend display
- Type labels: share→"Sponsored Post", adInMailContent→"InMail", video→"Video Ad", ugcPost→"UGC Post", adCreativeV2→"Creative"

### Fix F: Build Artifacts Cleanup

**Commit**: `6926ee3` — "Remove tracked build artifacts and update .gitignore"
**PR**: #13

- Removed tracked `frontend/dist/` build artifacts from git
- Updated `.gitignore` to exclude build outputs, `__pycache__`, `.env`, `tokens.json`, `logs/`, `data/`

---

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `backend/app/main.py` | REWRITTEN | FastAPI app with lifespan, CORS, request middleware, error handler |
| `backend/app/routes/__init__.py` | NEW | Router aggregator under `/api/v1` |
| `backend/app/routes/auth.py` | NEW | OAuth routes: status, url, health, callback |
| `backend/app/routes/sync.py` | NEW | Sync trigger + SSE stream + job polling |
| `backend/app/routes/report.py` | NEW | 7 report endpoints with pagination |
| `backend/app/routes/status.py` | NEW | System status dashboard |
| `backend/app/routes/health.py` | NEW | Database connectivity check |
| `backend/app/core/deps.py` | NEW | FastAPI dependency injection |
| `backend/app/core/config.py` | REWRITTEN | PostgreSQL fields, computed URI |
| `backend/app/core/db.py` | REWRITTEN | PostgreSQL engine, `pool_pre_ping` |
| `backend/app/core/security.py` | REWRITTEN | Async httpx for all token operations |
| `backend/app/services/sync.py` | NEW | SyncJob, 10-step pipeline, SSE via asyncio.Queue |
| `backend/app/services/snapshot.py` | UPDATED | content_names support, campaigns_by_account mapping |
| `backend/app/linkedin/client.py` | REWRITTEN | Async httpx client with 30s timeout |
| `backend/app/linkedin/fetchers.py` | UPDATED | Async, account_id params, resolve_content_references |
| `backend/app/linkedin/metrics.py` | UPDATED | Async with asyncio.gather batching |
| `backend/app/linkedin/constants.py` | UPDATED | API version "202602" |
| `backend/app/crud/accounts.py` | NEW | PostgreSQL upsert + query |
| `backend/app/crud/campaigns.py` | NEW | PostgreSQL upsert + JOIN query |
| `backend/app/crud/metrics.py` | NEW | Metrics upserts, pagination, visual SQL |
| `backend/app/crud/demographics.py` | NEW | Demographics upsert + filtered query |
| `backend/app/crud/sync_log.py` | NEW | Freshness gate, sync lifecycle, audit |
| `backend/app/models/creative.py` | UPDATED | Added content_name column, BigInteger timestamps |
| `backend/app/models/responses.py` | NEW | Shared Pydantic response schemas |
| `backend/alembic/versions/0002_*.py` | NEW | Add follows/leads/opens/sends + serving_hold_reasons |
| `backend/alembic/versions/0003_*.py` | NEW | Add content_name to creatives |
| `backend/tests/conftest.py` | REWRITTEN | SQLite StaticPool + FastAPI TestClient override |
| `backend/tests/test_*.py` | NEW | 31 tests across 5 files |
| `frontend/` | NEW | Complete React 19 SPA |
| `compose.yml` | NEW | PostgreSQL + backend + frontend |
| `.github/workflows/ci.yml` | NEW | CI with ruff + pytest |
| `.gitignore` | UPDATED | Exclude build artifacts, env, data |

---

## PRs

| PR | Title | Key Changes | Commits |
|----|-------|-------------|---------|
| #9 | Docs update | Updated arch docs for Python-only focus | `c56976a` |
| #10 | Fix multi-account sync | Account-scoped campaigns + config/port fixes | `d97069c`, `a4a4e92` |
| #11 | FastAPI + React consolidation | Full stack rewrite, async, PostgreSQL, SSE, React frontend | `57c7e1c` |
| #12 | CI/CD + data pipeline fixes | GitHub Actions, ruff, metrics persistence, creatives route | `50e67e3`, `27cb98a`, `d11675d` |
| #13 | Creative content names | Content reference labels, migration 0003, .gitignore cleanup | `3c2ea48`, `6926ee3` |

---

## What Was Explicitly Deferred

These items were scoped for future sprints:

- **Redis caching** for freshness gate (currently uses sync_log table)
- **S3 raw storage** (bronze layer for raw API responses)
- **Rate limit retry** with exponential backoff (RateLimitError raised but not retried)
- **LLM agent integration** for automated campaign optimization
- **Persistent job store** (replace in-memory `_jobs` dict with Redis or database)
- **Connection pool tuning** for PostgreSQL under production load
- **OpenAPI response models** (routes lack `response_model=` for Swagger docs)
- **PostgreSQL upsert tests** (test suite uses SQLite which doesn't support dialect-specific upserts)
