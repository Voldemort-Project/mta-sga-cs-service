"""Guest registration router"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.guest import GuestRegisterRequest, GuestRegisterResponse
from app.services.guest_service import GuestService

router = APIRouter(prefix="/guests", tags=["Guests"])


@router.post(
    "/register",
    response_model=GuestRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Guest",
    description="Register a new guest and automatically check them in to a room"
)
async def register_guest(
    request: GuestRegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> GuestRegisterResponse:
    """
    Register a new guest and check them in.

    This endpoint will:
    - Create a new user with guest role
    - Create a check-in record
    - Update room status to occupied

    Args:
        request: Guest registration details including full name, room number,
                check-in date, email, and phone number
        db: Database session dependency

    Returns:
        GuestRegisterResponse: Created guest and check-in details

    Raises:
        400: Room is not available
        404: Room not found
        500: Guest role not found or internal error
    """
    service = GuestService(db)
    return await service.register_guest(request)
