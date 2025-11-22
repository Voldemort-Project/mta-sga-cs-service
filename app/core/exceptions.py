"""Custom exceptions for the application"""
from typing import Optional, Any
from fastapi import status


class ComposeError(Exception):
    """
    Custom exception for service-level errors

    This exception is used at the service layer to raise errors with
    custom error codes and messages. The exception handler middleware
    will catch this and format it into a standard error response.

    Attributes:
        error_code: Custom error code (e.g., "4_000_000_0000001")
        message: User-friendly error message
        http_status_code: HTTP status code (default: 500)
        original_error: Original exception or error data (optional)
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        http_status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        original_error: Optional[Any] = None
    ):
        """
        Initialize ComposeError

        Args:
            error_code: Custom error code (e.g., "4_000_000_0000001")
            message: User-friendly error message
            http_status_code: HTTP status code (default: 500)
            original_error: Original exception or error data (optional)
        """
        self.error_code = error_code
        self.message = message
        self.http_status_code = http_status_code
        self.original_error = original_error
        super().__init__(self.message)
