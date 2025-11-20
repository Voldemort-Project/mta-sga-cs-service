"""Guest service for business logic"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.guest_repository import GuestRepository
from app.schemas.guest import GuestRegisterRequest, GuestRegisterResponse


class GuestService:
    """Service for guest registration and check-in"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = GuestRepository(db)

    async def register_guest(
        self,
        request: GuestRegisterRequest,
        org_id: Optional[UUID] = None
    ) -> GuestRegisterResponse:
        """
        Register a new guest and create check-in

        Args:
            request: Guest registration request data
            org_id: Organization ID (optional)

        Returns:
            GuestRegisterResponse: Registration and check-in details

        Raises:
            HTTPException: If guest role not found or room not available
        """
        # Get guest role
        guest_role = await self.repository.get_guest_role()
        if not guest_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Guest role not found in system. Please contact administrator."
            )

        # Get room by number
        room = await self.repository.get_room_by_number(request.room_number, org_id)
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Room {request.room_number} not found"
            )

        # Check if room is available
        if room.status != "available":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Room {request.room_number} is not available. Current status: {room.status}"
            )

        try:
            # Create guest user
            user = await self.repository.create_guest_user(
                name=request.full_name,
                email=request.email,
                phone=request.phone_number,
                role_id=guest_role.id,
                org_id=org_id
            )

            # Convert date to datetime for checkin_time
            checkin_datetime = datetime.combine(request.checkin_date, datetime.min.time())

            # Create check-in
            checkin = await self.repository.create_checkin(
                user_id=user.id,
                room_id=room.id,
                checkin_time=checkin_datetime,
                org_id=org_id
            )

            # Update room status to occupied
            await self.repository.update_room_status(room.id, "occupied")

            # Commit transaction
            await self.db.commit()

            # Return response
            return GuestRegisterResponse(
                user_id=user.id,
                checkin_id=checkin.id,
                full_name=user.name,
                room_number=room.room_number,
                checkin_date=request.checkin_date,
                email=request.email,
                phone_number=user.phone,
                status=checkin.status
            )

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to register guest: {str(e)}"
            )
