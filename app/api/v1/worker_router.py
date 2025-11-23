"""Worker router"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.auth import TokenData
from app.schemas.worker import WorkerListItem
from app.schemas.response import StandardResponse, create_success_response
from app.services.worker_service import WorkerService

router = APIRouter(prefix="/workers", tags=["Workers"])


@router.get(
    "",
    response_model=StandardResponse[List[WorkerListItem]],
    status_code=status.HTTP_200_OK,
    summary="List Workers",
    description="Get list of workers (users that are NOT 'Keycloak Administrator', 'Administrator', 'Guest')"
)
async def list_workers(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StandardResponse[List[WorkerListItem]]:
    """
    Get list of workers for the current user's organization.

    This endpoint will:
    - Filter workers by the organization of the currently logged-in user (if available)
    - Exclude users with roles: 'Keycloak Administrator', 'Administrator', 'Guest'
    - Return all workers without pagination

    Args:
        current_user: Current authenticated user (from token)
        db: Database session dependency

    Returns:
        StandardResponse[List[WorkerListItem]]: List of workers

    Raises:
        401: Unauthorized (if token is invalid)
    """
    # Get organization ID from current user (optional)
    org_id = None
    if current_user.organization_id:
        try:
            org_id = uuid.UUID(current_user.organization_id)
        except ValueError:
            # If organization_id is invalid, continue without filtering
            pass

    service = WorkerService(db)
    workers = await service.list_workers(org_id=org_id)

    return create_success_response(
        data=workers,
        message="Workers retrieved successfully"
    )
