"""Custom exception classes for LinkedIn Action Center.

This module provides domain-specific exceptions with rich formatting
for better error handling and debugging throughout the application.
"""

from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


class LinkedInActionCenterError(Exception):
    """Base exception for all LinkedIn Action Center errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
    def display(self) -> None:
        """Display formatted error message using rich."""
        error_text = Text()
        error_text.append(f"{self.__class__.__name__}: ", style="bold red")
        error_text.append(self.message, style="red")
        
        if self.details:
            error_text.append("\n\nDetails:\n", style="yellow")
            for key, value in self.details.items():
                error_text.append(f"  {key}: ", style="cyan")
                error_text.append(f"{value}\n", style="white")
        
        console.print(Panel(error_text, border_style="red", title="Error"))


class AuthenticationError(LinkedInActionCenterError):
    """Raised when authentication or authorization fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)


class TokenExpiredError(AuthenticationError):
    """Raised when an access token has expired."""
    
    def __init__(
        self,
        message: str = "Access token has expired",
        token_info: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, token_info)


class LinkedInAPIError(LinkedInActionCenterError):
    """Raised when LinkedIn API returns an error response."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None
    ):
        details = {}
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
    """Raised when API rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "API rate limit exceeded",
        retry_after: Optional[int] = None,
        endpoint: Optional[str] = None
    ):
        # Initialize parent with basic info
        super().__init__(message, status_code=429, response_data={}, endpoint=endpoint)
        
        # Add retry_after to details after parent initialization
        if retry_after is not None:
            self.details["retry_after_seconds"] = retry_after
        
        self.retry_after = retry_after


class ValidationError(LinkedInActionCenterError):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["invalid_value"] = value
        
        super().__init__(message, details)
        self.field = field
        self.value = value


class ConfigurationError(LinkedInActionCenterError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        expected_type: Optional[str] = None
    ):
        details = {}
        if config_key:
            details["config_key"] = config_key
        if expected_type:
            details["expected_type"] = expected_type
        
        super().__init__(message, details)
        self.config_key = config_key


class StorageError(LinkedInActionCenterError):
    """Raised when database or storage operations fail."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
        
        super().__init__(message, details)
        self.operation = operation
        self.table = table


class DataFetchError(LinkedInActionCenterError):
    """Raised when data fetching operations fail."""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(message, details)
        self.resource_type = resource_type
        self.resource_id = resource_id


def handle_error(error: Exception, show_traceback: bool = False) -> None:
    """
    Handle and display errors with rich formatting.
    
    Args:
        error: The exception to handle
        show_traceback: Whether to display the full traceback
    """
    if isinstance(error, LinkedInActionCenterError):
        error.display()
    else:
        # Handle unexpected errors
        error_text = Text()
        error_text.append(f"{error.__class__.__name__}: ", style="bold red")
        error_text.append(str(error), style="red")
        
        console.print(Panel(error_text, border_style="red", title="Unexpected Error"))
    
    if show_traceback:
        console.print_exception()
