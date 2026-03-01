# Changes Summary — Architecture Migration + Interface Design

## Overview

Consolidated a dual-stack application (Python Flask + Node.js Fastify/React) into a single clean stack: **Python FastAPI + React TypeScript**. Then applied a crafted interface design system to replace the default scaffolded UI.

---

## Phase 1: Full-Stack Migration (9 Phases)

### Backend (`backend/`)

**Stack:** FastAPI, SQLModel, PostgreSQL, httpx (async), Alembic, Rich logging

- **`app/main.py`** — FastAPI app with CORS, request context middleware (UUID request_id via contextvars), exception handlers, lifespan
- **`app/models/`** — 8 SQLModel table files: AdAccount, Campaign, Creative, CampaignDailyMetric, CreativeDailyMetric, AudienceDemographic, SyncLog, plus Pydantic validation models and response schemas
- **`app/routes/`** — 5 routers under `/api/v1`: auth, sync (SSE streaming), report (6 endpoints), status, health
- **`app/crud/`** — PostgreSQL upserts via `sqlalchemy.dialects.postgresql.insert`, paginated queries, visual aggregation, freshness gate
- **`app/services/`** — Sync orchestration with `asyncio.Queue` for SSE, snapshot assembly with validation
- **`app/linkedin/`** — Async httpx client with pagination, rate limit handling, parallel metric fetching via `asyncio.gather()`
- **`app/core/`** — Pydantic Settings config, SQLAlchemy engine, async AuthManager (httpx), dependency injection
- **`app/utils/logging.py`** — Unified logging: Rich console, 4 file handlers (app/error/api/json), request_id context propagation
- **`app/errors/`** — Exception hierarchy (AuthenticationError, TokenExpiredError, LinkedInAPIError, RateLimitError, etc.)
- **`alembic/`** — PostgreSQL migrations (7 tables)
- **`tests/`** — 31 tests: auth, client, CRUD, errors, routes. SQLite in-memory with StaticPool.

### Frontend (`frontend/`)

**Stack:** React 19, TypeScript, TanStack Router + Query, Tailwind CSS v4, Chart.js, Lucide icons

- **6 routes:** Overview, Connection (auth), Sync, Performance (visual), Tables (report), System (status)
- **Components:** Layout (sidebar), StatBlock, ChartCard, DataTable
- **Hooks:** useAuth, useSync, useReport (TanStack Query)
- **Build:** Vite 6, API proxy to backend

### Infrastructure

- **`compose.yml`** — PostgreSQL 16 + Backend + Frontend with healthchecks
- **`compose.override.yml`** — Dev overrides (volume mounts, --reload)
- **`Makefile`** — up, down, build, logs, migrate, test targets

### Cleanup

Deleted: `node-app/`, `src/`, root-level `tests/`, `alembic/`, `scripts/`, `main.py`, `cli.py`, `ui.py`, `bootstrap.py`, `alembic.ini`, root `pyproject.toml`, `uv.lock`

---

## Phase 2: Interface Design System

### Direction

Professional, data-dense, temporally-aware operations console. Bloomberg Terminal meets Linear. Information density with breathing room.

### Design Tokens (index.css)

Replaced default shadcn slate palette with intentional blue-gray foundation (oklch hue ~250):

| Token | Purpose |
|-------|---------|
| `--canvas` | Base background — cool blue-gray |
| `--surface` | Cards, panels — one step up |
| `--elevated` | Dropdowns, table headers — two steps up |
| `--edge` / `--edge-soft` | Border hierarchy |
| `--ink` / `--ink-secondary` / `--ink-faint` | Text hierarchy (4 levels) |
| `--accent` / `--accent-muted` | Desaturated LinkedIn blue |
| `--signal-positive/warning/error` | Semantic states |
| `--control-bg` | Input backgrounds (inset feel) |

Token names evoke the product domain — `ink`, `canvas`, `signal`, `edge` — not generic `gray-700`.

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Borders-only depth** | Data-dense interfaces — shadows compete with metrics for attention |
| **Inter typeface** | Neutral professional, excellent tabular figures, clean at 11-13px |
| **4px base spacing** | Dense but breathable |
| **Same-canvas sidebar** | Sidebar shares background with content — no color fragmentation |
| **Numbers-first StatBlock** | 2xl font-semibold tabular-nums — media buyers scan numbers, not icons |
| **Terminal-style sync log** | Monospace, dark inset, line-prefix indicators (>, OK, ERR) |
| **Underline tabs (report)** | Not button pills — cleaner for data-dense views |
| **Token expiry progress bars** | Temporal awareness signature — visualize how much time remains |
| **Freshness indicator in sidebar** | Always visible connection status — connected/disconnected pulse |
| **Chart palette from CHART_COLORS** | Desaturated professional palette, not random Tailwind hex values |
| **Whisper-quiet elevation** | 2-3% lightness shifts between surface levels — felt, not seen |

### Signature Element

**Temporal awareness:** Every view subtly communicates data freshness and connection health. The sidebar shows connection status. The dashboard shows token expiry and data volume. The auth page has progress bars for token lifetime. The sync page timestamps output.

### Files Changed

| File | Change |
|------|--------|
| `frontend/index.html` | Added Inter font via Google Fonts |
| `frontend/src/index.css` | Complete rewrite — intentional blue-gray tokens, domain-specific names |
| `frontend/tsconfig.json` | Added `vite/client` types |
| `frontend/src/routeTree.gen.ts` | Fixed TanStack Router v1.80 compatibility |
| `frontend/src/components/layout/Layout.tsx` | Redesigned: same-canvas sidebar, tighter density, freshness indicator |
| `frontend/src/components/charts/StatBlock.tsx` | Numbers-first with optional trend indicator |
| `frontend/src/components/charts/ChartCard.tsx` | Dark-mode chart defaults, system color palette |
| `frontend/src/components/tables/DataTable.tsx` | Dense rows, elevated headers, outline pagination |
| `frontend/src/routes/index.tsx` | Operations overview: system pulse + workflow steps with status pills |
| `frontend/src/routes/auth.tsx` | Token expiry progress bars, connected/disconnected states |
| `frontend/src/routes/sync.tsx` | Terminal-aesthetic log output, inline controls |
| `frontend/src/routes/visual.tsx` | Grid layout charts, system CHART_COLORS palette |
| `frontend/src/routes/report.tsx` | Underline tab navigation, no wrapper card |
| `frontend/src/routes/status.tsx` | Compact token stats, inline table, audit badges |

---

## Verification

- **Backend:** 31/31 tests pass (`pytest -v`)
- **Frontend:** TypeScript compiles clean (`tsc --noEmit`)
- **Frontend:** Production build succeeds (580KB JS, 19KB CSS)
