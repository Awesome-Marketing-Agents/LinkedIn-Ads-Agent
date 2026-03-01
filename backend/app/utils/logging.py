"""Unified logging system for the LinkedIn Ads Action Center.

Provides:
- Rich console output with pretty tracebacks
- Daily-rotated app log file (30 days)
- Size-rotated error log file (ERROR+, 10MB, 5 backups)
- Daily-rotated JSON structured log file
- Daily-rotated API access log file
- Request ID propagation via contextvars
- Domain-specific helper functions

Usage in every module::

    from app.utils.logging import get_logger
    logger = get_logger(__name__)
"""

from __future__ import annotations

import logging
import logging.config
import os
import uuid
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

# ---------------------------------------------------------------------------
# Request ID context variable (async-safe)
# ---------------------------------------------------------------------------
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
LOGS_DIR = Path(os.getenv("LOGS_DIR", "logs"))
LOGS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Install rich tracebacks globally
# ---------------------------------------------------------------------------
install_rich_traceback(
    show_locals=True,
    suppress=["uvicorn", "starlette", "fastapi"],
)

# Rich console for RichHandler
_console = Console(stderr=True, force_terminal=True)


# ---------------------------------------------------------------------------
# Context filter — injects request_id into every log record
# ---------------------------------------------------------------------------
class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")  # type: ignore[attr-defined]
        return True


# ---------------------------------------------------------------------------
# JSON formatter (for machine-readable logs)
# ---------------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import datetime, timezone

        log_entry = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


# ---------------------------------------------------------------------------
# Configure logging once at import time
# ---------------------------------------------------------------------------
_configured = False


def setup_logging(log_level: str = "INFO") -> None:
    """Configure all loggers, handlers, and formatters."""
    global _configured
    if _configured:
        return
    _configured = True

    level = getattr(logging, log_level.upper(), logging.INFO)
    ctx_filter = ContextFilter()

    # -- Console handler (Rich) -------------------------------------------
    console_handler = RichHandler(
        console=_console,
        show_time=True,
        show_level=True,
        show_path=True,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        tracebacks_suppress=["uvicorn", "starlette", "fastapi"],
    )
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
    console_handler.addFilter(ctx_filter)

    # -- App log file (daily rotation, 30 days) ---------------------------
    app_handler = TimedRotatingFileHandler(
        LOGS_DIR / "app.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    app_handler.setLevel(logging.DEBUG)
    app_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | [%(request_id)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    app_handler.addFilter(ctx_filter)

    # -- Error log file (size rotation, 10MB, 5 backups) ------------------
    error_handler = RotatingFileHandler(
        LOGS_DIR / "error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | [%(request_id)s] %(message)s\n%(pathname)s:%(lineno)d",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    error_handler.addFilter(ctx_filter)

    # -- JSON log file (daily rotation) -----------------------------------
    json_handler = TimedRotatingFileHandler(
        LOGS_DIR / "app.json.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    json_handler.setLevel(logging.DEBUG)
    json_handler.setFormatter(JSONFormatter())
    json_handler.addFilter(ctx_filter)

    # -- API access log file (daily rotation) -----------------------------
    api_handler = TimedRotatingFileHandler(
        LOGS_DIR / "api.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | [%(request_id)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    api_handler.addFilter(ctx_filter)

    # -- Root app logger --------------------------------------------------
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG)
    app_logger.addHandler(console_handler)
    app_logger.addHandler(app_handler)
    app_logger.addHandler(error_handler)
    app_logger.addHandler(json_handler)

    # -- API access logger ------------------------------------------------
    api_logger = logging.getLogger("app.api.access")
    api_logger.setLevel(logging.INFO)
    api_logger.addHandler(api_handler)
    api_logger.addHandler(console_handler)
    api_logger.propagate = False

    # -- Capture uvicorn logs into same system ----------------------------
    for uv_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(uv_name)
        uv_logger.handlers.clear()
        uv_logger.addHandler(console_handler)
        uv_logger.addHandler(app_handler)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_logger(name: str) -> logging.Logger:
    """Return a logger under the ``app`` hierarchy.

    If *name* starts with ``app.`` it is used as-is; otherwise ``app.`` is
    prepended so that all application loggers share the same handlers.
    """
    setup_logging(os.getenv("LOG_LEVEL", "INFO"))
    if not name.startswith("app"):
        name = f"app.{name}"
    return logging.getLogger(name)


def generate_request_id() -> str:
    """Generate a new UUID request ID."""
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Domain-specific helpers
# ---------------------------------------------------------------------------
_api_logger = None


def _get_api_logger() -> logging.Logger:
    global _api_logger
    if _api_logger is None:
        _api_logger = get_logger("app.api.access")
    return _api_logger


def log_api_call(
    method: str, endpoint: str, status_code: int, duration: float,
) -> None:
    """Log an API call with structured information."""
    status = "OK" if 200 <= status_code < 300 else "FAIL"
    _get_api_logger().info(
        "%s %s %s -> %d (%.2fs)", status, method, endpoint, status_code, duration,
    )


def log_sync_progress(step: str, count: int, total: Optional[int] = None) -> None:
    """Log data sync progress."""
    logger = get_logger("app.services.sync")
    progress = f"[{count}/{total}]" if total else f"[{count}]"
    logger.info("SYNC %s %s", step, progress)


def log_auth_event(event: str, details: Optional[str] = None) -> None:
    """Log authentication-related events."""
    logger = get_logger("app.core.security")
    msg = f"AUTH: {event}"
    if details:
        msg += f" - {details}"
    logger.info(msg)
