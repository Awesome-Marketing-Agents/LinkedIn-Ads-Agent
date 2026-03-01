# Module: FastAPI Application Entry Point

## Overview

`main.py` is the FastAPI application entry point. It creates the app instance, configures CORS middleware, adds request context middleware for tracing, registers a global exception handler for domain errors, and mounts all API routes.

---

## File Path

`backend/app/main.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `fastapi.FastAPI` | Application instance |
| `fastapi.middleware.cors.CORSMiddleware` | Cross-origin request support |
| `app.core.config.settings` | CORS origins, log level |
| `app.errors.exceptions.LinkedInActionCenterError` | Base exception for error handler |
| `app.routes.api_router` | Aggregated API router |
| `app.utils.logging.request_id_var` | ContextVar for request tracing |
| `app.utils.logging.setup_logging` | Logging initialization |
| `app.utils.logging.generate_request_id` | UUID request ID generator |

---

## Components

### Lifespan Context Manager

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)
    logger.info("Starting LinkedIn Ads Action Center")
    yield
    logger.info("Shutting down")
```

**Purpose**: Initializes logging on startup. Runs once when the app starts, yields control to serve requests, then logs shutdown.

### FastAPI App Instance

```python
app = FastAPI(
    title="LinkedIn Ads Action Center",
    version="0.1.0",
    lifespan=lifespan,
)
```

### CORS Middleware

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Behavior**: Allows requests from `http://localhost:5173` (Vite dev) and `http://localhost:3000`. Configured via `BACKEND_CORS_ORIGINS` env var.

### Request Context Middleware

```python
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
```

**Purpose**: Sets a unique `request_id` for every request, propagated through async code via `contextvars`.

**Behavior**:
1. Reads `X-Request-ID` header or generates a new 12-char UUID
2. Sets `request_id_var` ContextVar (picked up by all loggers)
3. Calls the next handler and times the response
4. Logs `METHOD /path -> STATUS (duration)` on completion
5. Adds `X-Request-ID` response header
6. Resets the ContextVar token in `finally` block

### Exception Handler

```python
@app.exception_handler(LinkedInActionCenterError)
async def app_error_handler(request: Request, exc: LinkedInActionCenterError):
```

**Purpose**: Maps domain exceptions to HTTP responses.

**Behavior**:
- If exception has a `status_code` attribute, uses it
- If class name contains `"Authentication"`, returns 401
- Otherwise returns 500
- Response body: `{"error": exc.message, "details": exc.details}`

### Route Mounting

```python
app.include_router(api_router)
```

Mounts all routes under `/api/v1` (prefix defined in `routes/__init__.py`).

---

## Code Snippet

```python
# Run the app
import uvicorn
uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

---

## Relationships

- **Called by**: Uvicorn ASGI server
- **Calls**: `routes/` (via `api_router`), `utils/logging` (setup + request_id), `core/config` (settings)
- **Error handler catches**: All `LinkedInActionCenterError` subclasses from any route

---

## Known Gaps

- No startup database connection check — relies on first request to discover DB issues
- CORS allows all methods and headers — acceptable for single-user tool
