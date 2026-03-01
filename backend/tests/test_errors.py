"""Tests for custom exception hierarchy."""

from app.errors.exceptions import (
    AuthenticationError,
    ConfigurationError,
    DataFetchError,
    LinkedInAPIError,
    LinkedInActionCenterError,
    RateLimitError,
    StorageError,
    TokenExpiredError,
    ValidationError,
)


def test_base_error():
    err = LinkedInActionCenterError("test error", {"key": "value"})
    assert str(err) == "test error"
    assert err.details == {"key": "value"}


def test_auth_error():
    err = AuthenticationError()
    assert "Authentication failed" in str(err)


def test_token_expired_error():
    err = TokenExpiredError(token_info={"expires_at": 12345})
    assert "expired" in str(err)
    assert err.details.get("expires_at") == 12345


def test_api_error():
    err = LinkedInAPIError("fail", status_code=500, endpoint="/test")
    assert err.status_code == 500
    assert err.endpoint == "/test"
    assert "status_code" in err.details


def test_rate_limit_error():
    err = RateLimitError(retry_after=60)
    assert err.retry_after == 60
    assert err.details["retry_after_seconds"] == 60


def test_validation_error():
    err = ValidationError("bad field", field="email", value="not-email")
    assert err.field == "email"
    assert err.value == "not-email"


def test_configuration_error():
    err = ConfigurationError("missing", config_key="API_KEY")
    assert err.config_key == "API_KEY"


def test_storage_error():
    err = StorageError("db fail", operation="insert", table="accounts")
    assert err.operation == "insert"
    assert err.table == "accounts"


def test_data_fetch_error():
    err = DataFetchError("fetch fail", resource_type="campaign", resource_id="123")
    assert err.resource_type == "campaign"
