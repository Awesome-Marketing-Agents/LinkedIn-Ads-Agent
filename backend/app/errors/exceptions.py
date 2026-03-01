"""Domain-specific exception hierarchy."""

from __future__ import annotations

from typing import Any, Optional


class LinkedInActionCenterError(Exception):
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(LinkedInActionCenterError):
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, details)


class TokenExpiredError(AuthenticationError):
    def __init__(
        self,
        message: str = "Access token has expired",
        token_info: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, token_info)


class LinkedInAPIError(LinkedInActionCenterError):
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[dict[str, Any]] = None,
        endpoint: Optional[str] = None,
    ):
        details: dict[str, Any] = {}
        if status_code is not None:
            details["status_code"] = status_code
        if endpoint:
            details["endpoint"] = endpoint
        if response_data:
            details["response"] = response_data
        super().__init__(message, details)
        self.status_code = status_code
        self.response_data = response_data
        self.endpoint = endpoint


class RateLimitError(LinkedInAPIError):
    def __init__(
        self,
        message: str = "API rate limit exceeded",
        retry_after: Optional[int] = None,
        endpoint: Optional[str] = None,
    ):
        super().__init__(message, status_code=429, response_data={}, endpoint=endpoint)
        if retry_after is not None:
            self.details["retry_after_seconds"] = retry_after
        self.retry_after = retry_after


class ValidationError(LinkedInActionCenterError):
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
    ):
        details: dict[str, Any] = {}
        if field:
            details["field"] = field
        if value is not None:
            details["invalid_value"] = value
        super().__init__(message, details)
        self.field = field
        self.value = value


class ConfigurationError(LinkedInActionCenterError):
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
    ):
        details: dict[str, Any] = {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, details)
        self.config_key = config_key


class StorageError(LinkedInActionCenterError):
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
    ):
        details: dict[str, Any] = {}
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
        super().__init__(message, details)
        self.operation = operation
        self.table = table


class DataFetchError(LinkedInActionCenterError):
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ):
        details: dict[str, Any] = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, details)
        self.resource_type = resource_type
        self.resource_id = resource_id
