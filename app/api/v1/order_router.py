"""Order router"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.pagination import PaginationParams
from app.core.security import get_current_user
from app.schemas.auth import TokenData
from app.schemas.order import OrderListItem, AssignOrderRequest, OrderAssignerResponse, UpdateOrderStatusRequest, UpdateOrderStatusResponse
from app.schemas.response import StandardResponse
from app.services.order_service import OrderService
from app.services.order_assigner_service import OrderAssignerService

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
    keyword: Optional[str] = Query(None, description="Search keyword (searches in order_number)"),
    order: Optional[str] = Query(None, description="Order string (e.g., 'created_at:desc;order_number:asc')"),
    division_id: Optional[uuid.UUID] = Query(None, description="Filter by division ID"),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StandardResponse[List[OrderListItem]]:
    """
    Get paginated list of orders for the current user's organization.

    This endpoint will:
    - Filter orders by the organization of the currently logged-in user
    - Support pagination, search, ordering, and filtering by division
    - Return orders with nested relationships (Session, Guest, CheckinRoom, Room, OrderItems, Division)

    Args:
        page: Page number (starts from 1)
        per_page: Number of items per page (1-100)
        keyword: Optional search keyword to filter by order_number
        order: Optional order string in format "field:direction;field2:direction2"
               e.g., "created_at:desc;order_number:asc"
        division_id: Optional filter by division ID
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
    return await service.list_orders(org_id=org_id, params=params, division_id=division_id)


@router.post(
    "/{order_number}/assign-worker",
    response_model=StandardResponse[OrderAssignerResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Assign Order to Worker",
    description="Assign an order to a worker. Worker can only handle maximum 5 active orders at a time."
)
async def assign_order_to_worker(
    order_number: str = Path(..., description="Order number to assign"),
    request: AssignOrderRequest = ...,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StandardResponse[OrderAssignerResponse]:
    """
    Assign an order to a worker.

    This endpoint will:
    - Validate that the order exists
    - Validate that the worker exists
    - Check if worker has reached the maximum limit of 5 active orders
    - Check if order is already assigned to this worker
    - Create the assignment and update order status to "assigned"

    Business Rules:
    - Worker can only handle maximum 5 active orders at a time
      (active = assigned, pick_up, or in_progress status)
    - Order cannot be assigned to the same worker twice
    - Order status will be updated to "assigned" if it's currently "pending"

    Args:
        order_number: Order number to assign (e.g., "ORD-001")
        request: Request body containing worker_id
        current_user: Current authenticated user (from token)
        db: Database session dependency

    Returns:
        StandardResponse[OrderAssignerResponse]: Created assignment information

    Raises:
        400: Bad request (worker max orders reached, order already assigned)
        404: Order or worker not found
        401: Unauthorized (if token is invalid)
        500: Internal server error
    """
    service = OrderAssignerService(db)
    return await service.assign_order_to_worker(
        order_number=order_number,
        worker_id=request.worker_id
    )


@router.get(
    "/{order_number}",
    response_model=StandardResponse[OrderListItem],
    status_code=status.HTTP_200_OK,
    summary="Get Order Detail",
    description="Get detailed information about a specific order by order number"
)
async def get_order_detail(
    order_number: str = Path(..., description="Order number to retrieve"),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StandardResponse[OrderListItem]:
    """
    Get detailed information about a specific order by order number.

    This endpoint will:
    - Retrieve the order by order_number
    - Return order with all nested relationships (OrderItems, Session, Guest, CheckinRoom, Room)
    - Validate that the order exists

    Args:
        order_number: Order number to retrieve (e.g., "ORD-001")
        current_user: Current authenticated user (from token)
        db: Database session dependency

    Returns:
        StandardResponse[OrderListItem]: Order detail with all relationships

    Raises:
        404: Order not found
        401: Unauthorized (if token is invalid)
        500: Internal server error
    """
    service = OrderService(db)
    return await service.get_order_detail_by_order_number(order_number=order_number)


@router.patch(
    "/{order_id}/status",
    response_model=StandardResponse[UpdateOrderStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Update Order Status",
    description="Update the status of an order"
)
async def update_order_status(
    order_id: uuid.UUID = Path(..., description="Order ID to update"),
    request: UpdateOrderStatusRequest = ...,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StandardResponse[UpdateOrderStatusResponse]:
    """
    Update the status of an order.

    This endpoint will:
    - Validate that the order exists
    - Update the order status to the new status
    - Return the updated order information

    Args:
        order_id: Order ID to update
        request: Request body containing the new status
        current_user: Current authenticated user (from token)
        db: Database session dependency

    Returns:
        StandardResponse[UpdateOrderStatusResponse]: Updated order information

    Raises:
        404: Order not found
        400: Invalid status
        401: Unauthorized (if token is invalid)
        500: Internal server error
    """
    service = OrderService(db)
    return await service.update_order_status(
        order_id=order_id,
        new_status=request.status
    )
