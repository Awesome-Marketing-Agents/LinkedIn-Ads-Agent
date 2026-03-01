# Module: API Response Schemas

## Overview

Shared Pydantic models that define the shape of API responses. Used for documentation and type safety but not yet wired as FastAPI `response_model` parameters.

---

## File Path

`backend/app/models/responses.py`

---

## Components

### `PaginatedResponse[T]`

```python
class PaginatedResponse(BaseModel, Generic[T]):
    rows: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
```

**Purpose**: Generic paginated response wrapper. Used by campaign/creative metrics endpoints.

### `StatusResponse`

```python
class StatusResponse(BaseModel):
    token: dict[str, Any]
    database: dict[str, int]
    active_campaign_audit: list[dict[str, Any]]
```

**Purpose**: System status combining token health, table counts, and campaign audit.

### `VisualReportResponse`

```python
class VisualReportResponse(BaseModel):
    time_series: list[dict[str, Any]]
    campaign_comparison: list[dict[str, Any]]
    kpis: dict[str, Any]
```

**Purpose**: Chart.js visualization data structure.

### `SyncJobResponse`

```python
class SyncJobResponse(BaseModel):
    job_id: str
    status: str
```

**Purpose**: Response from `POST /sync`.

### `HealthResponse`

```python
class HealthResponse(BaseModel):
    status: str = "ok"
    database: Optional[str] = None
```

**Purpose**: Health check response.

---

## Code Snippet

```python
from app.models.responses import PaginatedResponse

# These schemas document the API contract but are not yet used as response_model
```

---

## Known Gaps

- Not wired to routes via `response_model=` — Swagger/OpenAPI docs show no response schemas
