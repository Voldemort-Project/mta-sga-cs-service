"""Error handler middleware for FastAPI"""
import traceback
import logging
from typing import Any
from datetime import datetime

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import ComposeError
from app.core.config import settings
from app.constants.error_codes import ErrorCode
from app.schemas.error import ErrorResponse

logger = logging.getLogger(__name__)


def is_production() -> bool:
    """Check if the application is running in production environment"""
    return settings.env.lower() == "production"


def format_error_data(error: Any) -> dict:
    """
    Format error data for response

    Args:
        error: The original error/exception

    Returns:
        Dictionary containing error information
    """
    if error is None:
        return None

    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }

    # Add stack trace if it's an exception
    if isinstance(error, Exception):
        error_data["stack_trace"] = traceback.format_exception(
            type(error),
            error,
            error.__traceback__
        )

    return error_data


async def compose_error_handler(request: Request, exc: ComposeError) -> JSONResponse:
    """
    Exception handler for ComposeError

    This handler catches ComposeError exceptions raised at the service layer
    and formats them into a standard ErrorResponse.

    Args:
        request: FastAPI request object
        exc: ComposeError exception

    Returns:
        JSONResponse with ErrorResponse format
    """
    # Format error data (only include in non-production)
    error_data = None
    if not is_production() and exc.original_error is not None:
        error_data = format_error_data(exc.original_error)

    # Create error response
    error_response = ErrorResponse(
        code=exc.error_code,
        message=exc.message,
        data=error_data,
        timestamp=datetime.now()
    )

    # Log the error
    logger.error(
        f"ComposeError: {exc.error_code} - {exc.message}",
        exc_info=exc.original_error if exc.original_error else None
    )

    return JSONResponse(
        status_code=exc.http_status_code,
        content=error_response.model_dump(mode='json', exclude_none=True)
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Exception handler for FastAPI HTTPException

    Converts standard HTTPException to ErrorResponse format.

    Args:
        request: FastAPI request object
        exc: HTTPException

    Returns:
        JSONResponse with ErrorResponse format
    """
    # Default error code for HTTP exceptions
    error_code = f"4_{exc.status_code:03d}_000_0000000"

    error_response = ErrorResponse(
        code=error_code,
        message=exc.detail if isinstance(exc.detail, str) else "An error occurred",
        data=None,
        timestamp=datetime.now()
    )

    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json', exclude_none=True)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Exception handler for request validation errors

    Converts Pydantic validation errors to ErrorResponse format.

    Args:
        request: FastAPI request object
        exc: RequestValidationError

    Returns:
        JSONResponse with ErrorResponse format
    """
    error_code = ErrorCode.General.VALIDATION_ERROR

    # Format validation errors
    errors = exc.errors()
    error_messages = []
    for error in errors:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Invalid value")
        error_messages.append(f"{field}: {message}")

    error_message = "Validation error: " + "; ".join(error_messages)

    # Include detailed validation errors in data (only in non-production)
    error_data = None
    if not is_production():
        error_data = {
            "validation_errors": errors,
            "error_type": "RequestValidationError"
        }

    error_response = ErrorResponse(
        code=error_code,
        message=error_message,
        data=error_data,
        timestamp=datetime.now()
    )

    logger.warning(f"ValidationError: {error_message}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode='json', exclude_none=True)
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Exception handler for unhandled exceptions

    Catches any unhandled exceptions and formats them into ErrorResponse.
    This is a fallback handler for unexpected errors.

    Args:
        request: FastAPI request object
        exc: Any unhandled exception

    Returns:
        JSONResponse with ErrorResponse format
    """
    error_code = ErrorCode.General.INTERNAL_SERVER_ERROR

    # Format error data (only include in non-production)
    error_data = None
    if not is_production():
        error_data = format_error_data(exc)

    error_response = ErrorResponse(
        code=error_code,
        message="An unexpected error occurred. Please contact support if the problem persists.",
        data=error_data,
        timestamp=datetime.now()
    )

    # Log the full error with stack trace
    logger.error(
        f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
        exc_info=exc
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json', exclude_none=True)
    )
