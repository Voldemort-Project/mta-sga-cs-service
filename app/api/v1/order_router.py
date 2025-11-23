"""Order router"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.pagination import PaginationParams
from app.core.security import get_current_user
from app.schemas.auth import TokenData
from app.schemas.order import OrderListItem
from app.schemas.response import StandardResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get(
    "",
    response_model=StandardResponse[List[OrderListItem]],
    status_code=status.HTTP_200_OK,
    summary="List Orders",
    description="Get paginated list of orders for the current user's organization"
)
async def list_orders(
    page: int = Query(1, ge=1, description="Current page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    keyword: Optional[str] = Query(None, description="Search keyword (searches in order_number, category)"),
    order: Optional[str] = Query(None, description="Order string (e.g., 'created_at:desc;order_number:asc')"),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StandardResponse[List[OrderListItem]]:
    """
    Get paginated list of orders for the current user's organization.

    This endpoint will:
    - Filter orders by the organization of the currently logged-in user
    - Support pagination, search, and ordering
    - Return orders with nested relationships (Session, Guest, CheckinRoom, Room)

    Args:
        page: Page number (starts from 1)
        per_page: Number of items per page (1-100)
        keyword: Optional search keyword to filter by order_number or category
        order: Optional order string in format "field:direction;field2:direction2"
               e.g., "created_at:desc;order_number:asc"
        current_user: Current authenticated user (from token)
        db: Database session dependency

    Returns:
        StandardResponse[List[OrderListItem]]: Paginated list of orders with metadata

    Raises:
        400: Invalid pagination parameters
        401: Unauthorized (if token is invalid)
        500: Internal server error
    """
    # Get organization ID from current user
    org_id = None
    if current_user.organization_id:
        org_id = uuid.UUID(current_user.organization_id)

    # Create pagination params
    params = PaginationParams(
        page=page,
        per_page=per_page,
        keyword=keyword,
        order=order
    )

    service = OrderService(db)
    return await service.list_orders(org_id=org_id, params=params)
