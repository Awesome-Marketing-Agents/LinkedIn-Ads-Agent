# LinkedIn Ads Action Center

Full-stack application for managing and analyzing LinkedIn advertising campaigns. Built with **FastAPI** (Python) + **React** (TypeScript).

## Architecture

```
/
├── backend/          # FastAPI + SQLModel + PostgreSQL
│   ├── app/
│   │   ├── main.py           # FastAPI app entry
│   │   ├── models/           # SQLModel table definitions
│   │   ├── routes/           # API endpoints (/api/v1)
│   │   ├── crud/             # Database operations
│   │   ├── services/         # Sync orchestration, snapshot assembly
│   │   ├── linkedin/         # Async LinkedIn API client
│   │   ├── core/             # Config, DB, auth, dependencies
│   │   ├── utils/            # Unified logging system
│   │   └── errors/           # Exception hierarchy
│   ├── alembic/              # Database migrations
│   └── tests/                # Pytest suite
├── frontend/         # React + TypeScript + TanStack Router + Tailwind
│   ├── src/
│   │   ├── routes/           # File-based routing pages
│   │   ├── components/       # UI components, charts, tables
│   │   ├── hooks/            # React hooks (auth, sync, report)
│   │   └── lib/              # Utilities, logger
│   └── ...
├── compose.yml       # Docker Compose (PostgreSQL + Backend + Frontend)
└── Makefile          # Common commands
```

## Quick Start

### Docker (recommended)

```bash
cp .env.example .env
# Edit .env with your LinkedIn OAuth credentials
docker compose up -d
```

- Backend: http://localhost:8000/docs (Swagger UI)
- Frontend: http://localhost:5173

### Local Development

```bash
# Backend
cd backend
uv sync
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Workflow

1. **Authenticate** - Connect your LinkedIn account via OAuth
2. **Sync** - Pull campaigns, creatives, metrics, and demographics
3. **Explore** - View visual charts and tabular reports
4. **Monitor** - Check token health and database status

## API Endpoints

All endpoints are under `/api/v1`:

| Route | Method | Description |
|-------|--------|-------------|
| `/auth/status` | GET | Token status |
| `/auth/url` | GET | OAuth authorization URL |
| `/auth/callback` | GET | OAuth callback |
| `/auth/health` | GET | Token health check |
| `/sync` | POST | Start sync job |
| `/sync/{job_id}/stream` | GET | SSE progress stream |
| `/report/visual` | GET | Chart data (time series, KPIs) |
| `/report/campaign-metrics` | GET | Paginated campaign metrics |
| `/report/creative-metrics` | GET | Paginated creative metrics |
| `/report/demographics` | GET | Audience demographics |
| `/report/campaigns` | GET | Campaign list |
| `/report/accounts` | GET | Account list |
| `/status` | GET | System status |
| `/health` | GET | Health check |

## Testing

```bash
cd backend
pytest
```

## Tech Stack

**Backend:** FastAPI, SQLModel, PostgreSQL, httpx (async), Alembic, Rich logging
**Frontend:** React 19, TypeScript, TanStack Router + Query, Tailwind CSS, Chart.js
**Infrastructure:** Docker Compose, PostgreSQL 16, Nginx

## License

This project is licensed under the MIT License.
