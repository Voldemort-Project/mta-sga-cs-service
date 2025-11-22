"""Error response schemas"""
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """
    Standard error response structure

    This response structure is used for all error responses to ensure
    consistent error format across the API.

    Attributes:
        code: Custom error code (e.g., "4_000_000_0000001")
        message: User-friendly error message to display in UI
        data: Error stack or additional error data (only shown in non-production)
        timestamp: Time when the error occurred
    """
    code: str = Field(
        ...,
        description="Custom error code (e.g., '4_000_000_0000001')"
    )
    message: str = Field(
        ...,
        description="User-friendly error message to display in UI"
    )
    data: Optional[Any] = Field(
        default=None,
        description="Error stack or additional error data (only shown in non-production)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Time when the error occurred"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "4_000_000_0000001",
                    "message": "Room not found",
                    "data": {
                        "error_type": "NotFoundError",
                        "error_message": "Room 101 not found",
                        "stack_trace": "..."
                    },
                    "timestamp": "2024-01-15T10:30:00"
                },
                {
                    "code": "4_000_000_0000002",
                    "message": "Room is already booked",
                    "data": None,
                    "timestamp": "2024-01-15T10:30:00"
                }
            ]
        }
    }
