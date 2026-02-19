from __future__ import annotations

import logging
import sys  # noqa: F401
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

from linkedin_action_center.core.config import BASE_DIR

# Install rich traceback handler globally
install_rich_traceback(show_locals=True, suppress=[])

# Create logs directory
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configure rich console
console = Console(stderr=True, force_terminal=True)


def get_logger(
    name: str = "linkedin_action_center",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """
    Create and configure a logger with rich formatting.

    Args:
        name: Logger name (typically the module name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, uses default log file.

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Console handler with rich formatting
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_level=True,
        show_path=True,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
    )
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "%(message)s",
        datefmt="[%X]",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (plain text, no colors)
    if log_file is None:
        log_file = LOGS_DIR / "linkedin_action_center.log"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


# Create default logger instance
logger = get_logger()


def set_log_level(level: int | str):
    """
    Change the log level for all handlers.

    Args:
        level: Logging level (can be int or string like 'DEBUG', 'INFO', etc.)
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper())

    logger.setLevel(level)
    for handler in logger.handlers:
        if isinstance(handler, RichHandler):
            handler.setLevel(level)


# Convenience functions for common log patterns
def log_api_call(method: str, endpoint: str, status_code: int, duration: float):
    """Log an API call with structured information."""
    status = "SUCCESS" if 200 <= status_code < 300 else "FAILED"
    logger.info(
        f"[{status}] {method} {endpoint} -> {status_code} ({duration:.2f}s)",
        extra={
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration": duration,
        },
    )


def log_sync_progress(step: str, count: int, total: Optional[int] = None):
    """Log data sync progress with visual indicators."""
    if total:
        progress = f"[{count}/{total}]"
    else:
        progress = f"[{count}]"
    logger.info(f"SYNC: {step} {progress}")


def log_auth_event(event: str, details: Optional[str] = None):
    """Log authentication-related events."""
    msg = f"AUTH: {event}"
    if details:
        msg += f" - {details}"
    logger.info(msg)


def log_error(error: Exception, context: Optional[str] = None):
    """Log an error with full traceback and context."""
    msg = "ERROR"
    if context:
        msg += f" in {context}"
    msg += f": {type(error).__name__}: {error}"
    logger.error(msg, exc_info=True)
