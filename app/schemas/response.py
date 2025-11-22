"""Standard response schemas for API responses"""
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field

from app.core.pagination import PaginationMeta

# Generic type for response data
DataType = TypeVar("DataType")


class StandardResponse(BaseModel, Generic[DataType]):
    """
    Standard API response structure

    This response structure is used across all API endpoints to ensure
    consistent response format.

    Attributes:
        message: System message. If None, defaults to "Requested resources successfully"
        data: Response data. Can be string, number, array, or JSON object. Nullable.
        meta: Metadata for pagination. Optional and nullable.
    """
    message: str = Field(
        default="Requested resources successfully",
        description="System message"
    )
    data: Optional[DataType] = Field(
        default=None,
        description="Response data (string, number, array, or JSON object). Nullable."
    )
    meta: Optional[PaginationMeta] = Field(
        default=None,
        description="Metadata for pagination. Optional and nullable."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Requested resources successfully",
                    "data": {
                        "id": "a6f156bd-0e8d-49b9-87e7-80e3e9f825e3",
                        "name": "Anisa Bella Indriani",
                        "email": "anisabella@mail.com"
                    }
                },
                {
                    "message": "Requested resources successfully",
                    "data": [
                        {
                            "id": "a6f156bd-0e8d-49b9-87e7-80e3e9f825e3",
                            "name": "Anisa Bella Indriani"
                        }
                    ],
                    "meta": {
                        "page": 1,
                        "per_page": 10,
                        "total": 1,
                        "total_pages": 1,
                        "has_next": False,
                        "has_prev": False
                    }
                }
            ]
        }
    }


def create_response(
    data: Optional[DataType] = None,
    message: Optional[str] = None,
    meta: Optional[PaginationMeta] = None
) -> StandardResponse[DataType]:
    """
    Create a standard API response

    This is a reusable function to transform service results into
    the standard JSON response format.

    Args:
        data: Response data. Can be any type (string, number, array, object).
              If None, data will be set to None.
        message: System message. If None, defaults to "Requested resources successfully"
        meta: Pagination metadata. Optional. If None, meta will be omitted from response.

    Returns:
        StandardResponse with the provided data, message, and meta

    Examples:
        >>> # Simple response with data
        >>> response = create_response(
        ...     data={"id": "123", "name": "John"}
        ... )

        >>> # Response with custom message
        >>> response = create_response(
        ...     data={"id": "123"},
        ...     message="User created successfully"
        ... )

        >>> # Paginated response
        >>> from app.core.pagination import PaginationMeta
        >>> meta = PaginationMeta(
        ...     page=1,
        ...     per_page=10,
        ...     total=100,
        ...     total_pages=10,
        ...     has_next=True,
        ...     has_prev=False
        ... )
        >>> response = create_response(
        ...     data=[{"id": "1"}, {"id": "2"}],
        ...     meta=meta
        ... )

        >>> # Delete response (null data)
        >>> response = create_response(
        ...     data=None,
        ...     message="Resource deleted successfully"
        ... )
    """
    return StandardResponse(
        message=message or "Requested resources successfully",
        data=data,
        meta=meta
    )


def create_paginated_response(
    data: List[DataType],
    page: int,
    per_page: int,
    total: int,
    message: Optional[str] = None
) -> StandardResponse[List[DataType]]:
    """
    Create a standard paginated API response

    This is a convenience function to create paginated responses with
    automatically calculated pagination metadata.

    Args:
        data: List of items for the current page
        page: Current page number (1-indexed)
        per_page: Number of items per page
        total: Total number of items across all pages
        message: System message. If None, defaults to "Requested resources successfully"

    Returns:
        StandardResponse with paginated data and metadata

    Examples:
        >>> # Paginated list response
        >>> items = [{"id": "1", "name": "John"}, {"id": "2", "name": "Jane"}]
        >>> response = create_paginated_response(
        ...     data=items,
        ...     page=1,
        ...     per_page=10,
        ...     total=25
        ... )
        >>> # Response will include meta with has_next=True, has_prev=False, total_pages=3
    """
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0

    # Create pagination metadata
    meta = PaginationMeta(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages and total_pages > 0,
        has_prev=page > 1 and total_pages > 0
    )

    return StandardResponse(
        message=message or "Requested resources successfully",
        data=data,
        meta=meta
    )


def create_success_response(
    data: Optional[DataType] = None,
    message: Optional[str] = None
) -> StandardResponse[DataType]:
    """
    Create a simple success response without pagination

    Convenience function for non-paginated responses (create, update, delete, etc.)

    Args:
        data: Response data. Can be any type. If None, data will be None.
        message: System message. If None, defaults to "Requested resources successfully"

    Returns:
        StandardResponse without meta

    Examples:
        >>> # Create/Update response
        >>> response = create_success_response(
        ...     data={"id": "123", "name": "John"},
        ...     message="User created successfully"
        ... )

        >>> # Delete response
        >>> response = create_success_response(
        ...     data=None,
        ...     message="User deleted successfully"
        ... )
    """
    return StandardResponse(
        message=message or "Requested resources successfully",
        data=data,
        meta=None
    )
