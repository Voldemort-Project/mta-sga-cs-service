"""Order webhook service for handling order creation via webhook"""
import logging
import uuid
from datetime import datetime
from uuid import UUID
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.guest_repository import GuestRepository
from app.models.checkin import CheckinRoom
from app.schemas.webhook import OrderWebhookRequest
from app.core.exceptions import ComposeError
from app.constants.error_codes import ErrorCode
from fastapi import status

logger = logging.getLogger(__name__)


class OrderWebhookService:
    """Service for handling order webhook events"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = GuestRepository(db)

    def _generate_order_number(self) -> str:
        """
        Generate a unique order number.

        Returns:
            Unique order number in format: ORD-{timestamp}-{short_uuid}
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        short_uuid = str(uuid.uuid4())[:8].upper()
        return f"ORD-{timestamp}-{short_uuid}"

    async def create_order_from_webhook(self, request: OrderWebhookRequest) -> UUID:
        """
        Create an order from webhook request.

        Args:
            request: Order webhook request data

        Returns:
            Created order ID

        Raises:
            ComposeError: If session not found or order creation fails
        """
        # Get session by session_id
        session = await self.repository.get_session_by_id(request.session_id)
        if not session:
            raise ComposeError(
                error_code=ErrorCode.General.NOT_FOUND,
                message=f"Session not found with ID: {request.session_id}",
                http_status_code=status.HTTP_404_NOT_FOUND
            )

        # Get checkin_id from session
        if not session.checkin_room_id:
            raise ComposeError(
                error_code=ErrorCode.General.BAD_REQUEST,
                message=f"Session {request.session_id} does not have an associated check-in room",
                http_status_code=status.HTTP_400_BAD_REQUEST
            )

        checkin_id = session.checkin_room_id

        # Get org_id from checkin if available
        checkin = await self.db.execute(
            select(CheckinRoom).where(CheckinRoom.id == checkin_id)
        )
        checkin_obj = checkin.scalar_one_or_none()
        org_id = checkin_obj.org_id if checkin_obj else None

        try:
            # Generate unique order number
            order_number = self._generate_order_number()

            # Create order
            order = await self.repository.create_order(
                checkin_id=checkin_id,
                category=request.category.value,
                title=request.title,
                description=request.description,
                order_number=order_number,
                notes=request.note,
                additional_notes=request.additional_note,
                org_id=org_id
            )

            # Commit transaction
            await self.db.commit()

            logger.info(
                f"Order created successfully: order_id={order.id}, "
                f"order_number={order_number}, checkin_id={checkin_id}"
            )

            return order.id

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error creating order for session {request.session_id}: {str(e)}",
                exc_info=True
            )
            raise ComposeError(
                error_code=ErrorCode.General.INTERNAL_SERVER_ERROR,
                message=f"Failed to create order: {str(e)}",
                http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                original_error=e
            )
