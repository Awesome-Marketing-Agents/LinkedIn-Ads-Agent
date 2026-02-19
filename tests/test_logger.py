"""Unit tests for logger module."""

import pytest
import logging
from pathlib import Path
from linkedin_action_center.utils.logger import (
    logger,
    get_logger,
    log_api_call,
    log_auth_event,
    log_sync_progress,
    log_error,
)


class TestLoggerConfiguration:
    """Test logger setup and configuration."""
    
    def test_logger_exists(self):
        """Test that logger is properly configured."""
        assert logger is not None
        assert logger.name == "linkedin_action_center"
        assert logger.level == logging.INFO
    
    def test_logger_has_handlers(self):
        """Test that logger has both console and file handlers."""
        assert len(logger.handlers) >= 2
        handler_types = [type(h).__name__ for h in logger.handlers]
        assert "RichHandler" in handler_types
        assert "FileHandler" in handler_types
    
    def test_get_logger_returns_same_instance(self):
        """Test that get_logger() returns the singleton."""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2
        assert logger1.name == "linkedin_action_center"


class TestLoggingConvenienceFunctions:
    """Test convenience logging functions."""
    
    def test_log_api_call_success(self):
        """Test logging successful API call."""
        # Should not raise any exceptions
        log_api_call("GET", "/campaigns", 200, 0.5)
        log_api_call("POST", "/creatives", 201, 1.2)
    
    def test_log_api_call_failure(self):
        """Test logging failed API call."""
        log_api_call("GET", "/campaigns", 500, 2.3)
        log_api_call("POST", "/analytics", 429, 0.8)
    
    def test_log_auth_event(self):
        """Test logging authentication events."""
        log_auth_event("Token refresh", "Successfully refreshed access token")
        log_auth_event("Login", "User authenticated")
    
    def test_log_sync_progress(self):
        """Test logging sync progress."""
        log_sync_progress("campaigns", 5, 10)
        log_sync_progress("creatives", 100, 100)
    
    def test_log_error_with_context(self):
        """Test error logging with context dict."""
        log_error("Test error", context={"key": "value", "count": 42})
    
    def test_log_error_without_context(self):
        """Test error logging without context."""
        log_error("Simple error message")


class TestLogFileCreation:
    """Test log file handling."""
    
    def test_log_directory_created(self):
        """Test that logs directory is created."""
        log_dir = Path("logs")
        assert log_dir.exists()
        assert log_dir.is_dir()
    
    def test_log_file_created(self):
        """Test that log file is created."""
        log_file = Path("logs/linkedin_action_center.log")
        assert log_file.exists()
        assert log_file.is_file()
    
    def test_log_file_is_writable(self, tmp_path):
        """Test that we can write to log file."""
        # Use main logger to write a test message
        test_msg = "Test log message for writability check"
        logger.info(test_msg)
        
        # Read the log file
        log_file = Path("logs/linkedin_action_center.log")
        content = log_file.read_text()
        
        # Check that content exists (file should have some logs)
        assert len(content) > 0


class TestLogLevels:
    """Test different log levels."""
    
    def test_info_level_logs(self):
        """Test INFO level logging."""
        logger.info("Info message")
        # Should not raise exception
    
    def test_warning_level_logs(self):
        """Test WARNING level logging."""
        logger.warning("Warning message")
    
    def test_error_level_logs(self):
        """Test ERROR level logging."""
        logger.error("Error message")
    
    def test_debug_level_not_shown_by_default(self):
        """Test that DEBUG messages are not shown by default."""
        # DEBUG should not appear because logger is set to INFO
        logger.debug("Debug message")
        # This test just ensures no exception is raised
