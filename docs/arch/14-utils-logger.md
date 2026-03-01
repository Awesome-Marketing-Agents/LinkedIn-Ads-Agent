# Module: Logger (Rich Logging)

## Overview

`utils/logger.py` configures application-wide logging with Rich formatting for the console and plain-text output to a file. It provides a default logger and convenience functions for common log patterns.

---

## File Path

`src/linkedin_action_center/utils/logger.py`

---

## Components & Explanation

- **`get_logger(name, level, log_file)`** — Create and configure a logger with Rich console handler and file handler.
  - **Purpose**: Centralized logging setup.
  - **Inputs**: `name` (default: `linkedin_action_center`), `level` (default: INFO), optional `log_file`.
  - **Outputs**: Configured `logging.Logger`.
  - **Note**: Prevents duplicate handlers if logger already configured.

- **`logger`** — Default singleton logger instance. Import this for logging.
- **`set_log_level(level)`** — Change log level for all handlers (int or string like `"DEBUG"`).
- **`log_api_call(method, endpoint, status_code, duration)`** — Log API call with status and duration.
- **`log_sync_progress(step, count, total)`** — Log sync progress (e.g. `SYNC: campaigns [5/10]`).
- **`log_auth_event(event, details)`** — Log auth events (e.g. `AUTH: Token valid - Authenticated as: John Doe`).
- **`log_error(error, context)`** — Log error with traceback and optional context.

### Setup at Import

When the module is imported, it automatically:
1. Installs Rich traceback handler globally (`show_locals=True`).
2. Creates `logs/` directory under project root.
3. Creates the default `logger` singleton with both console and file handlers.

---

## Relationships

- Used by `auth/manager`, `ingestion/client`, `storage/repository`, `storage/snapshot`.
- Creates `logs/` directory and `logs/linkedin_action_center.log`.
- Uses `rich` for console output and tracebacks.
- Reads `BASE_DIR` from `core.config` for log directory path.

---

## Example Code Snippets

```python
from linkedin_action_center.utils.logger import logger, log_auth_event, log_sync_progress

# Basic logging
logger.info("Sync started")
logger.error("API request failed")

# Convenience functions
log_auth_event("Token refresh", "Successfully refreshed")
log_sync_progress("campaigns", 5, 10)  # SYNC: campaigns [5/10]
log_sync_progress("accounts", 1)       # SYNC: accounts [1]
```

```python
# Change log level
from linkedin_action_center.utils.logger import set_log_level
set_log_level("DEBUG")
```

---

## Edge Cases & Tips

- **Duplicate handlers**: `get_logger` checks `logger.handlers` and returns early if already configured.
- **File vs console**: File handler gets DEBUG level (logs everything); console handler uses the configured level (default INFO).
- **Rich traceback**: `install_rich_traceback(show_locals=True)` affects all uncaught exceptions globally.
- **LOGS_DIR**: `BASE_DIR / "logs"`; created at import time.

---

## Architecture / Flow

```
Module import
    |
    └── from linkedin_action_center.utils.logger import logger
            ├── install_rich_traceback()
            ├── LOGS_DIR.mkdir(exist_ok=True)
            └── logger = get_logger()
                    ├── RichHandler (console, colored, shows time/level/path)
                    └── FileHandler (logs/linkedin_action_center.log, plain text)
```

---

## Advanced Notes

- Console formatter: `%(message)s` only; Rich adds level, time, path automatically.
- File formatter: `%(asctime)s | %(name)s | %(levelname)s | %(message)s`.
- `force_terminal=True` on Rich Console ensures colors even when stdout is redirected.
- Log file uses `utf-8` encoding.
