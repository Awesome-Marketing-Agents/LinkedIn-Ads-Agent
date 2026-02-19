"""Unit tests for custom exception classes."""

import pytest
from linkedin_action_center.utils.errors import (
    LinkedInActionCenterError,
    AuthenticationError,
    TokenExpiredError,
    LinkedInAPIError,
    RateLimitError,
    ValidationError,
    ConfigurationError,
    StorageError,
    DataFetchError,
)


class TestBaseException:
    """Test the base LinkedInActionCenterError."""
    
    def test_base_exception_creation(self):
        """Test creating a base exception with message and details."""
        error = LinkedInActionCenterError("Test error", {"key": "value"})
        assert error.message == "Test error"
        assert error.details == {"key": "value"}
        assert str(error) == "Test error"
    
    def test_base_exception_without_details(self):
        """Test creating exception without optional details."""
        error = LinkedInActionCenterError("Simple error")
        assert error.message == "Simple error"
        assert error.details == {}


class TestAuthenticationError:
    """Test authentication-related exceptions."""
    
    def test_authentication_error_defaults(self):
        """Test default authentication error message."""
        error = AuthenticationError()
        assert error.message == "Authentication failed"
        assert error.details == {}
    
    def test_authentication_error_with_details(self):
        """Test auth error with custom message and details."""
        error = AuthenticationError(
            "OAuth failed",
            details={"status_code": 401, "endpoint": "/oauth/token"}
        )
        assert error.message == "OAuth failed"
        assert error.details["status_code"] == 401
    
    def test_token_expired_error(self):
        """Test TokenExpiredError as subclass of AuthenticationError."""
        error = TokenExpiredError(token_info={"expires_at": 1234567890})
        assert isinstance(error, AuthenticationError)
        assert "expired" in error.message.lower()


class TestLinkedInAPIError:
    """Test API-related exceptions."""
    
    def test_api_error_with_full_context(self):
        """Test API error with all context fields."""
        error = LinkedInAPIError(
            "API request failed",
            status_code=500,
            response_data={"error": "Internal Server Error"},
            endpoint="/campaigns"
        )
        assert error.message == "API request failed"
        assert error.status_code == 500
        assert error.endpoint == "/campaigns"
        assert error.details["status_code"] == 500
        assert error.details["endpoint"] == "/campaigns"
    
    def test_rate_limit_error(self):
        """Test RateLimitError with retry_after."""
        error = RateLimitError(retry_after=60, endpoint="/analytics")
        assert isinstance(error, LinkedInAPIError)
        assert error.status_code == 429
        assert error.retry_after == 60
        assert error.details["retry_after_seconds"] == 60


class TestValidationError:
    """Test validation exceptions."""
    
    def test_validation_error_with_field(self):
        """Test validation error with field information."""
        error = ValidationError(
            "Invalid email format",
            field="email",
            value="not-an-email"
        )
        assert error.message == "Invalid email format"
        assert error.field == "email"
        assert error.value == "not-an-email"
        assert error.details["field"] == "email"


class TestStorageError:
    """Test storage/database exceptions."""
    
    def test_storage_error_with_context(self):
        """Test storage error with operation and table info."""
        error = StorageError(
            "Database insert failed",
            operation="INSERT",
            table="campaigns"
        )
        assert error.message == "Database insert failed"
        assert error.operation == "INSERT"
        assert error.table == "campaigns"
        assert error.details["operation"] == "INSERT"
        assert error.details["table"] == "campaigns"


class TestDataFetchError:
    """Test data fetching exceptions."""
    
    def test_data_fetch_error_with_resource_info(self):
        """Test fetch error with resource context."""
        error = DataFetchError(
            "Failed to fetch campaign",
            resource_type="campaign",
            resource_id="12345"
        )
        assert error.message == "Failed to fetch campaign"
        assert error.resource_type == "campaign"
        assert error.resource_id == "12345"


class TestConfigurationError:
    """Test configuration exceptions."""
    
    def test_configuration_error(self):
        """Test config error with key and type info."""
        error = ConfigurationError(
            "Missing required config",
            config_key="CLIENT_ID",
            expected_type="str"
        )
        assert error.message == "Missing required config"
        assert error.config_key == "CLIENT_ID"
        assert error.details["expected_type"] == "str"
