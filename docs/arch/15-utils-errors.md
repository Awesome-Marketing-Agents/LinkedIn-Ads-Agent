# Module: Custom Exceptions

## Overview

`utils/errors.py` defines domain-specific exception classes for the LinkedIn Action Center. All inherit from `LinkedInActionCenterError` and support Rich-formatted display. They provide structured error handling and debugging across the application.

---

## File Path

`src/linkedin_action_center/utils/errors.py`

---

## Components & Explanation

- **`LinkedInActionCenterError`** — Base exception with `message`, `details` dict, and `display()` for Rich output.
- **`AuthenticationError`** — OAuth failures, missing tokens.
- **`TokenExpiredError`** — Extends `AuthenticationError`; access token expired and refresh failed.
- **`LinkedInAPIError`** — API returned error; has `status_code`, `response_data`, `endpoint`.
- **`RateLimitError`** — Extends `LinkedInAPIError`; 429 status with `retry_after` seconds.
- **`ValidationError`** — Input validation failed; has `field`, `value`.
- **`ConfigurationError`** — Invalid or missing config; has `config_key`, `expected_type`.
- **`StorageError`** — Database or storage failure; has `operation`, `table`.
- **`DataFetchError`** — Data fetching failed; has `resource_type`, `resource_id`.
- **`handle_error(error, show_traceback=False)`** — Display error with Rich formatting; optionally show full traceback.

---

## Relationships

- Raised by `auth/manager`, `ingestion/client`, `storage/repository`.
- Caught by `main.py` (renders error HTML) and CLI (prints to stderr).
- Uses `rich` for `display()` and `handle_error()`.

---

## Example Code Snippets

```python
from linkedin_action_center.utils.errors import (
    AuthenticationError,
    LinkedInAPIError,
    RateLimitError,
    handle_error,
)

# Raise
raise AuthenticationError("Invalid credentials", details={"client_id": "xxx"})

# Catch and display
try:
    client.get("/campaigns")
except LinkedInAPIError as e:
    e.display()  # Rich-formatted panel
    print(f"Status: {e.status_code}, Endpoint: {e.endpoint}")

# Generic handler
try:
    risky_operation()
except Exception as e:
    handle_error(e, show_traceback=True)
```

```python
# RateLimitError
from linkedin_action_center.utils.errors import RateLimitError
# e.retry_after  # seconds to wait
# e.details["retry_after_seconds"]
```

---

## Edge Cases & Tips

- **Details dict**: All exceptions accept optional `details`; use for structured context (status_code, endpoint, etc.).
- **display()**: Only custom exceptions use Rich; generic `Exception` in `handle_error` gets a simple panel.
- **Chaining**: Use `raise ... from e` to preserve original exception when re-raising.
- **TokenExpiredError**: `token_info` is stored in `details`; use for debugging expiry logic.

---

## Architecture / Flow

```
Exception hierarchy
    LinkedInActionCenterError
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

## Advanced Notes

- `RateLimitError` passes `endpoint` to parent; `retry_after` is stored in `details` and as attribute.
- `display()` uses `rich.panel.Panel` and `rich.text.Text` for formatted output.
- `handle_error` catches `LinkedInActionCenterError` and calls `display()`; otherwise uses generic formatting.

---

## Node.js Equivalent

- **Python:** `utils/errors.py` --> **Node.js:** `node-app/src/errors.ts`
- The same class hierarchy is fully ported as TypeScript classes extending the built-in `Error` class.
- All 8 error classes are preserved: `LinkedInActionCenterError`, `AuthenticationError`, `TokenExpiredError`, `LinkedInAPIError`, `RateLimitError`, `ValidationError`, `ConfigurationError`, `StorageError`, `DataFetchError`.
- The same `handleError()` function is ported.
- No Rich dependency; errors use standard `console.error()` output instead of Rich panels.

```typescript
export class LinkedInActionCenterError extends Error {
  details: Record<string, unknown>;

  constructor(message: string, details: Record<string, unknown> = {}) {
    super(message);
    this.name = "LinkedInActionCenterError";
    this.details = details;
  }

  display(): void {
    console.error(`[${this.name}] ${this.message}`);
    if (Object.keys(this.details).length > 0) {
      console.error("Details:", JSON.stringify(this.details, null, 2));
    }
  }
}

export class AuthenticationError extends LinkedInActionCenterError { ... }
export class TokenExpiredError extends AuthenticationError { ... }
export class LinkedInAPIError extends LinkedInActionCenterError { ... }
export class RateLimitError extends LinkedInAPIError { ... }
export class ValidationError extends LinkedInActionCenterError { ... }
export class ConfigurationError extends LinkedInActionCenterError { ... }
export class StorageError extends LinkedInActionCenterError { ... }
export class DataFetchError extends LinkedInActionCenterError { ... }

export function handleError(error: unknown, showTraceback = false): void {
  if (error instanceof LinkedInActionCenterError) {
    error.display();
  } else if (error instanceof Error) {
    console.error(`Error: ${error.message}`);
  }
  if (showTraceback && error instanceof Error) {
    console.error(error.stack);
  }
}
```
