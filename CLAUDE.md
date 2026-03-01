# LinkedIn Ads Action Center

## What This Is

Full-stack app for managing and analyzing LinkedIn advertising campaigns. Single-user tool — no user auth, LinkedIn OAuth is for API access only.

## Stack

- **Backend:** Python 3.12+, FastAPI, SQLModel, PostgreSQL 16, httpx (async), Alembic, Rich logging
- **Frontend:** React 19, TypeScript, TanStack Router + Query, Tailwind CSS v4, Chart.js, Lucide icons
- **Infrastructure:** Docker Compose, Nginx reverse proxy

## Project Structure

```
/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, request context middleware, exception handlers
│   │   ├── models/              # SQLModel tables (7 tables + Pydantic schemas)
│   │   ├── routes/              # API endpoints under /api/v1 (auth, sync, report, status, health)
│   │   ├── crud/                # Database ops — PostgreSQL upserts, paginated queries, freshness gate
│   │   ├── services/            # Sync orchestration (asyncio.Queue SSE), snapshot assembly
│   │   ├── linkedin/            # Async httpx client, entity fetchers, metric fetchers
│   │   ├── core/                # Config (Pydantic Settings), DB engine, AuthManager, dependency injection
│   │   ├── utils/logging.py     # Unified logging: Rich console + 4 rotating file handlers + request_id
│   │   └── errors/              # Exception hierarchy
│   ├── alembic/                 # PostgreSQL migrations
│   ├── tests/                   # 31 tests — SQLite in-memory with StaticPool
│   └── pyproject.toml           # uv-managed dependencies
├── frontend/
│   ├── src/
│   │   ├── routes/              # 6 pages: index, auth, sync, visual, report, status
│   │   ├── components/          # Layout, StatBlock, ChartCard, DataTable
│   │   ├── hooks/               # useAuth, useSync, useReport (TanStack Query)
│   │   ├── lib/                 # utils.ts (cn), logger.ts
│   │   ├── types/               # TypeScript interfaces for all API responses
│   │   └── index.css            # Design tokens — blue-gray foundation, borders-only depth
│   └── package.json
├── compose.yml                  # PostgreSQL + backend + frontend
├── compose.override.yml         # Dev overrides
├── docs/                        # Architecture docs, sprint notes
└── Makefile                     # Common commands
```

## Key Commands

```bash
# Backend
cd backend && uv sync                    # Install deps
cd backend && pytest                     # Run 31 tests
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install               # Install deps
cd frontend && npx tsc --noEmit          # Type-check
cd frontend && npm run build             # Production build
cd frontend && npm run dev               # Dev server (port 5173)

# Docker
docker compose up -d                     # Full stack
make test                                # Backend tests
```

## API Structure

All endpoints under `/api/v1`:

- `GET /auth/status|url|health|callback` — OAuth flow
- `POST /sync` → `GET /sync/{job_id}/stream` — SSE sync
- `GET /report/campaign-metrics|creative-metrics|demographics|visual|campaigns|accounts`
- `GET /status` — Token + DB counts + campaign audit
- `GET /health` — DB connectivity check

## Architecture Decisions

- **httpx async** everywhere — FastAPI async handlers, sync I/O blocks event loop
- **PostgreSQL upserts** via `sqlalchemy.dialects.postgresql.insert().on_conflict_do_update()`
- **SSE** via `sse-starlette` + `asyncio.Queue` for real-time sync progress
- **TanStack Router** — file-based routing (routeTree.gen.ts is manually maintained)
- **Borders-only depth** — no shadows, data-dense interface
- **StaticPool** in tests — SQLite in-memory needs shared pool for TestClient threads

## Design System

Tokens defined in `frontend/src/index.css`. Blue-gray foundation (oklch hue ~250). Key tokens:

- `--canvas/surface/elevated` — 3-level surface elevation
- `--edge/edge-soft` — border hierarchy
- `--ink/ink-secondary/ink-faint` — text hierarchy
- `--accent/accent-muted` — desaturated LinkedIn blue
- `--signal-positive/warning/error` — semantic states

Typography: Inter, 4px base spacing, tabular-nums for all metrics.

## Conventions

- All logging via `from app.utils.logging import get_logger; logger = get_logger(__name__)`
- Request context: `contextvars` request_id set in middleware, propagated through async
- CRUD functions take `Session` as first arg, routes use `Depends(get_db)`
- Frontend hooks wrap TanStack Query, pages are in `routes/`, shared UI in `components/`
