"""Guest registration router"""
import uuid
import logging
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.pagination import PaginationParams
from app.core.security import get_current_user
from app.schemas.auth import TokenData
from app.schemas.guest import GuestRegisterRequest, GuestRegisterResponse, GuestListItem
from app.schemas.response import StandardResponse, create_success_response
from app.services.guest_service import GuestService
from app.integrations.h2h import H2HAgentRouterService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guests", tags=["Guests"])


@router.post(
    "/register",
    response_model=StandardResponse[GuestRegisterResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register Guest",
    description="Register a new guest and automatically check them in to a room"
)
async def register_guest(
    request: GuestRegisterRequest,
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StandardResponse[GuestRegisterResponse]:
    """
    Register a new guest and check them in.

    This endpoint will:
    - Create a new user with guest role
    - Create a check-in record with user_id of the admin who registered the guest
    - Update room status to occupied
    - Create a chat session for the guest
    - Trigger background task to create agent via H2H Agent Router

    Args:
        request: Guest registration details including full name, room number,
                check-in date, email, and phone number
        background_tasks: FastAPI background tasks for async operations
        current_user: Current authenticated user (admin) who is registering the guest
        db: Database session dependency

    Returns:
        StandardResponse[GuestRegisterResponse]: Created guest and check-in details with session ID

    Raises:
        400: Room is not available
        404: Room not found
        500: Guest role not found or internal error
    """
    # Convert user_id from string to UUID
    admin_user_id = uuid.UUID(current_user.user.user_id)

    service = GuestService(db)
    result = await service.register_guest(request, user_id=admin_user_id)

    # Add background task to create agent via H2H
    background_tasks.add_task(create_agent_via_h2h, session_id=result.session_id)

    # Return standard response
    return create_success_response(
        data=result,
        message="Guest registered successfully"
    )


async def create_agent_via_h2h(session_id: uuid.UUID) -> None:
    """
    Background task to create agent via H2H Agent Router.

    This function runs asynchronously after the guest registration response is returned.
    Errors are logged but do not affect the main registration flow.

    Args:
        session_id: Session ID to use as identifier_id for agent creation
    """
    try:
        h2h_agent_router_service = H2HAgentRouterService()
        await h2h_agent_router_service.create_agent(session_id)
        logger.info(f"Successfully created agent via H2H Agent Router for session {session_id}")
    except Exception as e:
        # Log error but don't raise - this is a background task
        # The guest registration has already succeeded, so we just log the failure
        logger.error(
            f"Failed to create agent via H2H Agent Router for session {session_id}: {str(e)}",
            exc_info=True
        )


@router.get(
    "",
    response_model=StandardResponse[List[GuestListItem]],
    status_code=status.HTTP_200_OK,
    summary="List Guests",
    description="Get paginated list of guests registered under the current user's organization"
)
async def list_guests(
    page: int = Query(1, ge=1, description="Current page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    keyword: str = Query(None, description="Search keyword (searches in name, email, phone)"),
    order: str = Query(None, description="Order string (e.g., 'created_at:desc;name:asc')"),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StandardResponse[List[GuestListItem]]:
    """
    Get paginated list of guests for the current user's organization.

    This endpoint will:
    - Filter guests by the organization of the currently logged-in user
    - Only show users with guest role
    - Support pagination, search, and ordering

    Args:
        page: Page number (starts from 1)
        per_page: Number of items per page (1-100)
        keyword: Optional search keyword to filter by name, email, or phone
        order: Optional order string in format "field:direction;field2:direction2"
               e.g., "created_at:desc;name:asc"
        current_user: Current authenticated user (from token)
        db: Database session dependency

    Returns:
        StandardResponse[List[GuestListItem]]: Paginated list of guests with metadata

    Raises:
        400: Invalid pagination parameters
        401: Unauthorized (if token is invalid)
    """
    # Get organization ID from current user
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User organization not found. Please ensure you are associated with an organization."
        )

    org_id = uuid.UUID(current_user.organization_id)

    # Create pagination params
    params = PaginationParams(
        page=page,
        per_page=per_page,
        keyword=keyword,
        order=order
    )

    service = GuestService(db)
    return await service.list_guests(org_id=org_id, params=params)
