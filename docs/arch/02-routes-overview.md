# Module: Routes Overview

## Overview

The routes package aggregates all API sub-routers under a single `/api/v1` prefix. Each sub-router handles a specific domain: authentication, sync, reporting, status, and health checks.

---

## File Path

`backend/app/routes/__init__.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `fastapi.APIRouter` | Router aggregation |
| `app.routes.auth` | OAuth endpoints |
| `app.routes.sync` | Sync trigger + SSE stream |
| `app.routes.report` | Data query endpoints |
| `app.routes.status` | System status dashboard |
| `app.routes.health` | Database connectivity check |

---

## Components

### `api_router`

```python
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(sync_router, prefix="/sync", tags=["sync"])
api_router.include_router(report_router, prefix="/report", tags=["report"])
api_router.include_router(status_router, prefix="/status", tags=["status"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
```

---

## Endpoint Table

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/api/v1/auth/status` | `auth_status` | Token expiry info |
| GET | `/api/v1/auth/url` | `auth_url` | OAuth authorization URL |
| GET | `/api/v1/auth/health` | `auth_health` | Validate token against `/me` |
| GET | `/api/v1/auth/callback` | `auth_callback` | OAuth code exchange + redirect |
| POST | `/api/v1/sync` | `start_sync` | Launch sync job, returns job_id |
| GET | `/api/v1/sync/{job_id}/stream` | `sync_stream` | SSE progress events |
| GET | `/api/v1/sync/{job_id}` | `sync_status` | Poll job status |
| GET | `/api/v1/report/campaign-metrics` | `campaign_metrics` | Paginated campaign metrics |
| GET | `/api/v1/report/creative-metrics` | `creative_metrics` | Paginated creative metrics |
| GET | `/api/v1/report/demographics` | `demographics` | Demographics by pivot |
| GET | `/api/v1/report/visual` | `visual_data` | Time series + KPIs for charts |
| GET | `/api/v1/report/creatives` | `creatives_list` | All creatives with campaign name |
| GET | `/api/v1/report/campaigns` | `campaigns_list` | All campaigns with account name |
| GET | `/api/v1/report/accounts` | `accounts_list` | All ad accounts |
| GET | `/api/v1/status` | `status` | Token + DB counts + audit |
| GET | `/api/v1/health` | `health` | DB connectivity check |

---

## Code Snippet

```python
# In main.py
from app.routes import api_router
app.include_router(api_router)
```

---

## Relationships

- **Mounted by**: `app/main.py` via `app.include_router(api_router)`
- **Sub-routers**: See [03-routes-auth.md](03-routes-auth.md), [05-routes-sync.md](05-routes-sync.md), [21-routes-report.md](21-routes-report.md), [22-routes-status-health.md](22-routes-status-health.md)
