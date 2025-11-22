"""Guest service for business logic"""
from datetime import datetime
from typing import Optional
from uuid import UUID
import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.guest_repository import GuestRepository
from app.schemas.guest import GuestRegisterRequest, GuestRegisterResponse
from app.models.message import MessageRole
from app.integrations.waha import WahaService

logger = logging.getLogger(__name__)


class GuestService:
    """Service for guest registration and check-in"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = GuestRepository(db)
        self.waha_service = WahaService()

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
        if room.is_booked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Room {request.room_number} is already booked"
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

            # Create check-in with current time
            current_time = datetime.now().time()
            checkin = await self.repository.create_checkin(
                room_ids=[room.id],
                checkin_date=request.checkin_date,
                checkin_time=current_time,
                org_id=org_id or room.org_id
            )

            # Update room status to booked
            await self.repository.update_room_booked_status(room.id, True)

            # Create chat session for the guest
            session = await self.repository.create_session(
                user_id=user.id,
                checkin_room_id=checkin.id
            )

            # Create welcome message and save to database
            welcome_text = (
                f"Halo {user.name}! 👋\n\n"
                f"Selamat datang di hotel kami. Anda telah berhasil check-in di kamar {room.room_number}.\n\n"
                f"Jika Anda membutuhkan bantuan atau memiliki pertanyaan, "
                f"silakan balas pesan ini dan kami akan segera membantu Anda.\n\n"
                f"Terima kasih telah memilih hotel kami. Semoga Anda menikmati masa menginap Anda! 🏨"
            )

            await self.repository.create_message(
                session_id=session.id,
                role=MessageRole.System,
                text=welcome_text
            )

            # Send welcome message via WAHA (must succeed before commit)
            # This is part of the atomic transaction - if this fails, everything rolls back
            logger.info(f"Sending welcome message to guest {user.name} at {user.mobile_phone}")
            await self.waha_service.send_text_message(
                phone_number=user.mobile_phone,
                text=welcome_text
            )
            logger.info(f"Welcome message sent successfully to {user.mobile_phone}")

            # Commit transaction (only if everything above succeeded)
            await self.db.commit()
            logger.info(f"Guest registration completed successfully for {user.name}")

            # Return response
            return GuestRegisterResponse(
                user_id=user.id,
                checkin_id=checkin.id,
                full_name=user.name,
                room_number=room.room_number,
                checkin_date=request.checkin_date,
                email=request.email,
                phone_number=user.mobile_phone,
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
