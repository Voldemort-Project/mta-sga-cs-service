"""Pagination utilities for database queries"""
from typing import TypeVar, Generic, List, Optional, Type, Any
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from pydantic import BaseModel

# Generic type for models
ModelType = TypeVar("ModelType")


class PaginationParams(BaseModel):
    """Pagination parameters from request"""
    page: int = 1
    per_page: int = 10
    keyword: Optional[str] = None
    order: Optional[str] = None

    class Config:
        """Pydantic config"""
        json_schema_extra = {
            "example": {
                "page": 1,
                "per_page": 10,
                "keyword": "search term",
                "order": "created_at:desc;name:asc"
            }
        }


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[ModelType]):
    """Paginated response with data and metadata"""
    data: List[ModelType]
    meta: PaginationMeta

    class Config:
        """Pydantic config"""
        from_attributes = True


def parse_order_string(order_string: str) -> List[tuple[str, str]]:
    """
    Parse order string into list of (field, direction) tuples

    Args:
        order_string: Order string in format "field:direction;field2:direction2"
                     e.g., "created_at:desc;name:asc"

    Returns:
        List of tuples: [('created_at', 'desc'), ('name', 'asc')]

    Example:
        >>> parse_order_string("created_at:desc;name:asc")
        [('created_at', 'desc'), ('name', 'asc')]
    """
    if not order_string:
        return []

    orders = []
    for order_part in order_string.split(';'):
        order_part = order_part.strip()
        if not order_part:
            continue

        if ':' not in order_part:
            # Default to ascending if no direction specified
            orders.append((order_part, 'asc'))
        else:
            field, direction = order_part.rsplit(':', 1)
            field = field.strip()
            direction = direction.strip().lower()

            # Validate direction
            if direction not in ['asc', 'desc']:
                direction = 'asc'  # Default to asc if invalid

            orders.append((field, direction))

    return orders


def apply_order_to_query(
    query: Select,
    model: Type[ModelType],
    order_string: Optional[str]
) -> Select:
    """
    Apply ordering to SQLAlchemy query based on order string

    Args:
        query: SQLAlchemy Select query
        model: SQLAlchemy model class
        order_string: Order string in format "field:direction;field2:direction2"

    Returns:
        Query with ordering applied

    Example:
        >>> query = select(User)
        >>> query = apply_order_to_query(query, User, "created_at:desc;name:asc")
    """
    if not order_string:
        return query

    orders = parse_order_string(order_string)

    for field_name, direction in orders:
        # Get attribute from model
        if not hasattr(model, field_name):
            # Skip invalid fields
            continue

        field_attr = getattr(model, field_name)

        # Check if it's a SQLAlchemy column
        if isinstance(field_attr, InstrumentedAttribute):
            if direction == 'desc':
                query = query.order_by(field_attr.desc())
            else:
                query = query.order_by(field_attr.asc())

    return query


def apply_keyword_search(
    query: Select,
    model: Type[ModelType],
    keyword: Optional[str],
    search_fields: List[str]
) -> Select:
    """
    Apply keyword search using ILIKE to multiple fields

    Args:
        query: SQLAlchemy Select query
        model: SQLAlchemy model class
        keyword: Search keyword
        search_fields: List of field names to search in

    Returns:
        Query with keyword search applied

    Example:
        >>> query = select(User)
        >>> query = apply_keyword_search(query, User, "john", ["name", "email"])
    """
    if not keyword or not search_fields:
        return query

    # Build OR conditions for each search field
    conditions = []
    for field_name in search_fields:
        if hasattr(model, field_name):
            field_attr = getattr(model, field_name)
            if isinstance(field_attr, InstrumentedAttribute):
                conditions.append(field_attr.ilike(f"%{keyword}%"))

    if conditions:
        query = query.where(or_(*conditions))

    return query


async def paginate_query(
    db: AsyncSession,
    query: Select,
    params: PaginationParams,
    model: Type[ModelType],
    search_fields: Optional[List[str]] = None
) -> PaginatedResponse[ModelType]:
    """
    Apply pagination, search, and ordering to a query and return paginated results

    This is a reusable function that:
    1. Applies keyword search using ILIKE
    2. Applies ordering based on order string
    3. Applies pagination (page, per_page)
    4. Returns paginated data with metadata

    Args:
        db: AsyncSession for database operations
        query: Base SQLAlchemy Select query
        params: Pagination parameters (page, per_page, keyword, order)
        model: SQLAlchemy model class
        search_fields: Optional list of field names to search in (for keyword)

    Returns:
        PaginatedResponse with data and metadata

    Example:
        >>> from app.models.user import User
        >>> from app.core.pagination import PaginationParams, paginate_query
        >>>
        >>> params = PaginationParams(
        ...     page=1,
        ...     per_page=10,
        ...     keyword="john",
        ...     order="created_at:desc;name:asc"
        ... )
        >>>
        >>> query = select(User)
        >>> result = await paginate_query(
        ...     db,
        ...     query,
        ...     params,
        ...     User,
        ...     search_fields=["name", "email"]
        ... )
        >>>
        >>> print(result.data)  # List of User objects
        >>> print(result.meta.total)  # Total count
        >>> print(result.meta.total_pages)  # Total pages
    """
    # Apply keyword search if provided
    if search_fields and params.keyword:
        query = apply_keyword_search(query, model, params.keyword, search_fields)

    # Get total count before pagination and ordering
    # Create a count query with the same filters but without ordering/pagination
    # Use subquery to preserve all WHERE conditions
    count_subquery = query.subquery()
    count_query = select(func.count()).select_from(count_subquery)
    total_result = await db.execute(count_query)
    total = total_result.scalar_one() or 0

    # Apply ordering (after count, before pagination)
    query = apply_order_to_query(query, model, params.order)

    # Apply pagination
    offset = (params.page - 1) * params.per_page
    query = query.offset(offset).limit(params.per_page)

    # Execute query
    result = await db.execute(query)
    items = result.scalars().all()

    # Calculate pagination metadata
    total_pages = (total + params.per_page - 1) // params.per_page if total > 0 else 0

    meta = PaginationMeta(
        page=params.page,
        per_page=params.per_page,
        total=total,
        total_pages=total_pages,
        has_next=params.page < total_pages and total_pages > 0,
        has_prev=params.page > 1 and total_pages > 0
    )

    return PaginatedResponse(
        data=list(items),
        meta=meta
    )
