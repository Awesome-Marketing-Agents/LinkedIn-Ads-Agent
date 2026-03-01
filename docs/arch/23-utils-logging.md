# Module: Logging System

## Overview

Unified logging system providing Rich console output, four rotating file handlers, JSON structured logging, and request ID propagation via `contextvars`. Every module uses `get_logger(__name__)` for consistent log output.

---

## File Path

`backend/app/utils/logging.py`

---

## Dependencies

| Import | Purpose |
|--------|---------|
| `logging` | Standard library logging |
| `contextvars.ContextVar` | Async-safe request ID propagation |
| `rich.console.Console` | Terminal output |
| `rich.logging.RichHandler` | Pretty log formatting |
| `rich.traceback.install` | Enhanced tracebacks |

---

## Constants

| Name | Value | Purpose |
|------|-------|---------|
| `request_id_var` | `ContextVar("request_id", default="-")` | Per-request trace ID |
| `LOGS_DIR` | `Path("logs")` or `$LOGS_DIR` | Log file directory |

---

## Components

### `ContextFilter`

```python
class ContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get("-")
        return True
```

**Purpose**: Inject `request_id` into every log record. Attached to all handlers.

### `JSONFormatter`

**Purpose**: Format log records as JSON for machine parsing. Fields: `timestamp`, `level`, `logger`, `message`, `request_id`, `exception` (if present).

### `setup_logging(log_level: str) -> None`

**Purpose**: Configure all handlers. Called once during app lifespan.

**Handlers**:

| Handler | File | Rotation | Level | Format |
|---------|------|----------|-------|--------|
| Console | stderr | — | Configurable | Rich with tracebacks |
| App log | `logs/app.log` | Daily, 30 days | DEBUG | `timestamp \| name \| level \| [request_id] message` |
| Error log | `logs/error.log` | 10MB, 5 backups | ERROR | Same + file:line |
| JSON log | `logs/app.json.log` | Daily, 30 days | DEBUG | JSON (`JSONFormatter`) |
| API log | `logs/api.log` | Daily, 30 days | INFO | `timestamp \| [request_id] message` |

**Uvicorn capture**: Clears default uvicorn handlers and routes through the app's console + app handlers.

### `get_logger(name: str) -> logging.Logger`

**Purpose**: Return a logger under the `app` hierarchy.

**Behavior**: Prepends `app.` if the name doesn't start with it. Calls `setup_logging()` on first use.

### `generate_request_id() -> str`

**Purpose**: Generate a 12-character hex UUID.

### Domain Helpers

#### `log_api_call(method, endpoint, status_code, duration) -> None`

Logs to the `app.api.access` logger: `"OK GET /adAccounts -> 200 (0.45s)"`.

#### `log_sync_progress(step, count, total) -> None`

Logs sync step progress: `"SYNC 1/6 [5]"`.

#### `log_auth_event(event, details) -> None`

Logs auth events: `"AUTH: Token refreshed"`.

---

## Code Snippet

```python
from app.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Processing %d campaigns", count)
```

---

## Relationships

- **Used by**: Every module in the application
- **Request ID set by**: `main.py` request context middleware
- **ContextVar consumed by**: `ContextFilter` on every log record
