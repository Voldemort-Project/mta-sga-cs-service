"""Order webhook service for handling order creation via webhook"""
import logging
import uuid
from datetime import datetime
from uuid import UUID
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.guest_repository import GuestRepository
from app.models.session import Session
from app.models.user import User
from app.models.order_item import OrderItem
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

        # Get guest_id from session
        if not session.session_id:
            raise ComposeError(
                error_code=ErrorCode.General.BAD_REQUEST,
                message=f"Session {request.session_id} does not have an associated guest user",
                http_status_code=status.HTTP_400_BAD_REQUEST
            )

        guest_id = session.session_id

        # Get org_id from guest user if available
        guest = await self.db.execute(
            select(User).where(User.id == guest_id)
        )
        guest_obj = guest.scalar_one_or_none()
        org_id = guest_obj.org_id if guest_obj else None

        try:
            # Generate unique order number
            order_number = self._generate_order_number()

            # Calculate total amount from items
            total_amount = sum(
                (item.price or 0) * (item.qty or 1)
                for item in request.items
            )

            # Create order
            order = await self.repository.create_order(
                session_id=request.session_id,
                guest_id=guest_id,
                category=request.category.value,
                order_number=order_number,
                notes=request.note,
                additional_notes=request.additional_note,
                org_id=org_id,
                total_amount=total_amount
            )

            # Create order items
            for item_request in request.items:
                order_item = OrderItem(
                    order_id=order.id,
                    title=item_request.title,
                    description=item_request.description,
                    qty=item_request.qty,
                    price=item_request.price or 0,
                    note=item_request.note
                )
                self.db.add(order_item)

            # Commit transaction
            await self.db.commit()

            logger.info(
                f"Order created successfully: order_id={order.id}, "
                f"order_number={order_number}, session_id={request.session_id}, "
                f"guest_id={guest_id}, items_count={len(request.items)}"
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
