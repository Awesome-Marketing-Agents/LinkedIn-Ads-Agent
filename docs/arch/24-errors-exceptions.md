# Module: Exception Hierarchy

## Overview

Nine domain-specific exception classes provide structured error information. The base class carries a `message` and `details` dict, and subclasses add context-specific attributes. The `app_error_handler` in `main.py` maps these to HTTP responses.

---

## File Path

`backend/app/errors/exceptions.py`

---

## Hierarchy

```
LinkedInActionCenterError (base)
├── AuthenticationError
│   └── TokenExpiredError
├── LinkedInAPIError
│   └── RateLimitError
├── ValidationError
├── ConfigurationError
├── StorageError
└── DataFetchError
```

---

## Components

### `LinkedInActionCenterError`

```python
def __init__(self, message: str, details: Optional[dict] = None):
```

Base exception. All subclasses carry `message` and `details`.

### `AuthenticationError`

Default message: `"Authentication failed"`. HTTP 401 (via class name check in error handler).

### `TokenExpiredError(AuthenticationError)`

Adds `token_info` dict with expiry timestamps.

### `LinkedInAPIError`

```python
def __init__(self, message, status_code=None, response_data=None, endpoint=None):
```

Stores `status_code` as both a detail and instance attribute. Used by error handler for HTTP status.

### `RateLimitError(LinkedInAPIError)`

```python
def __init__(self, message="API rate limit exceeded", retry_after=None, endpoint=None):
```

Always status 429. Stores `retry_after` seconds in details.

### `ValidationError`

Stores `field` and `value` for the invalid data.

### `ConfigurationError`

Stores `config_key` for the missing/invalid config.

### `StorageError`

Stores `operation` and `table` for database errors.

### `DataFetchError`

Stores `resource_type` and `resource_id` for fetch failures.

---

## HTTP Mapping (in `main.py`)

```python
@app.exception_handler(LinkedInActionCenterError)
async def app_error_handler(request, exc):
    if hasattr(exc, "status_code") and exc.status_code:
        status_code = exc.status_code      # LinkedInAPIError, RateLimitError
    elif "Authentication" in type(exc).__name__:
        status_code = 401                   # AuthenticationError, TokenExpiredError
    else:
        status_code = 500                   # All others

    return JSONResponse(
        status_code=status_code,
        content={"error": exc.message, "details": exc.details},
    )
```

---

## Code Snippet

```python
from app.errors.exceptions import AuthenticationError, RateLimitError

raise AuthenticationError(
    "Token expired",
    details={"expires_at": 1709312400},
)

raise RateLimitError(endpoint="/adAccounts", retry_after=60)
```

---

## Relationships

- **Raised by**: `core/security.py`, `linkedin/client.py`, `crud/` modules
- **Caught by**: `main.py` exception handler → JSON response
