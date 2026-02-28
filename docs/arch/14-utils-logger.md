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

- **`logger`** — Default singleton logger instance.
- **`set_log_level(level)`** — Change log level for all handlers (int or string like `"DEBUG"`).
- **`log_api_call(method, endpoint, status_code, duration)`** — Log API call with status and duration.
- **`log_sync_progress(step, count, total)`** — Log sync progress (e.g. `SYNC: campaigns [5/10]`).
- **`log_auth_event(event, details)`** — Log auth events (e.g. `AUTH: Token valid - Authenticated as: John Doe`).
- **`log_error(error, context)`** — Log error with traceback and optional context.

---

## Relationships

- Used by `auth/manager`, `ingestion/client`, `storage/repository`.
- Creates `logs/` directory and `logs/linkedin_action_center.log`.
- Uses `rich` for console output and tracebacks; `install_rich_traceback()` runs at import.

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
- **File vs console**: File gets DEBUG; console uses the configured level (default INFO).
- **Rich traceback**: `install_rich_traceback(show_locals=True)` affects all uncaught exceptions.
- **LOGS_DIR**: `BASE_DIR / "logs"`; created at import.

---

## Architecture / Flow

```
Module import
    │
    └── from linkedin_action_center.utils.logger import logger
            ├── install_rich_traceback()
            ├── LOGS_DIR.mkdir(exist_ok=True)
            └── logger = get_logger()  # RichHandler + FileHandler
```

---

## Advanced Notes

- Console formatter: `%(message)s` only; Rich adds level, time, path.
- File formatter: `%(asctime)s | %(name)s | %(levelname)s | %(message)s`.
- `force_terminal=True` on Rich Console ensures colors even when stdout is redirected.

---

## Node.js Equivalent

- **Python:** `utils/logger.py` (Rich) --> **Node.js:** `node-app/src/logger.ts` (Pino)
- Pino is the default logger for Fastify, making it the natural choice for the Node.js migration. It provides structured JSON logging out of the box.
- Uses Pino multistream to output to two destinations simultaneously:
  - Pretty-printed console output (via `pino-pretty`) for development.
  - JSON file output to `logs/app.log` for production and log aggregation.
- The same convenience function pattern is preserved, but implemented as Pino child loggers rather than standalone functions. Child loggers automatically inherit the parent configuration and add contextual fields.

```typescript
import pino from "pino";
import fs from "node:fs";
import path from "node:path";

const logsDir = path.join(__dirname, "../..", "logs");
fs.mkdirSync(logsDir, { recursive: true });

const streams = [
  { stream: require("pino-pretty")({ colorize: true }) },
  { stream: fs.createWriteStream(path.join(logsDir, "app.log"), { flags: "a" }) },
];

export const logger = pino({ level: "info" }, pino.multistream(streams));

// Child loggers for domain-specific logging
export const apiLogger = logger.child({ module: "api" });
export const authLogger = logger.child({ module: "auth" });
export const syncLogger = logger.child({ module: "sync" });
```
