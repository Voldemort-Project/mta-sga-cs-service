"""Order webhook service for handling order creation via webhook"""
import logging
import uuid
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.repositories.guest_repository import GuestRepository
from app.models.session import Session
from app.models.user import User
from app.models.checkin import CheckinRoom
from app.models.order_item import OrderItem
from app.models.order import Order
from app.schemas.webhook import OrderWebhookRequest, OrderRequest
from app.core.exceptions import ComposeError
from app.constants.error_codes import ErrorCode
from fastapi import status

logger = logging.getLogger(__name__)


class OrderWebhookService:
    """Service for handling order webhook events"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = GuestRepository(db)

    async def _get_next_sequence(self) -> int:
        """
        Get the next sequence number for the current month.

        Returns:
            Next sequence number (starts from 1)
        """
        # Get current year and month in YYMM format (e.g., 2512 for December 2025)
        now = datetime.now(timezone.utc)
        yymm = now.strftime("%y%m")
        prefix = f"ORD-{yymm}-"

        # Query the last order number for the current month
        # Find orders that start with the current month prefix
        result = await self.db.execute(
            select(func.max(Order.order_number))
            .where(
                Order.order_number.like(f"{prefix}%"),
                Order.deleted_at.is_(None)
            )
        )
        last_order_number = result.scalar_one_or_none()

        # Extract sequence from last order number or start from 0
        if last_order_number:
            try:
                # Extract sequence part (last 4 digits after the last dash)
                sequence_str = last_order_number.split("-")[-1]
                sequence = int(sequence_str)
            except (ValueError, IndexError):
                # If parsing fails, start from 0
                sequence = 0
        else:
            # No orders found for this month, start from 0
            sequence = 0

        # Return next sequence (increment by 1)
        return sequence + 1

    def _format_order_number(self, sequence: int) -> str:
        """
        Format order number with sequence.

        Args:
            sequence: Sequence number

        Returns:
            Formatted order number: ORD-YYMM-{Sequence}
        """
        # Get current year and month in YYMM format (e.g., 2512 for December 2025)
        now = datetime.now(timezone.utc)
        yymm = now.strftime("%y%m")
        sequence_str = f"{sequence:04d}"
        return f"ORD-{yymm}-{sequence_str}"

    async def _generate_order_number(self) -> str:
        """
        Generate a unique order number with format ORD-YYMM-{Sequence}.

        The sequence resets to 0001 when the month changes.
        Example: ORD-2512-0001, ORD-2512-0002, ORD-2512-0003

        Returns:
            Unique order number in format: ORD-YYMM-{Sequence}
        """
        sequence = await self._get_next_sequence()
        return self._format_order_number(sequence)

    async def create_order_from_webhook(self, request: OrderWebhookRequest) -> List[str]:
        """
        Create orders from webhook request (supports bulk insert).

        Args:
            request: Order webhook request data with multiple orders

        Returns:
            List of created order numbers

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

        # Get org_id from checkin_room.org_id
        if not session.checkin_room_id:
            raise ComposeError(
                error_code=ErrorCode.General.BAD_REQUEST,
                message=f"Session {request.session_id} does not have an associated checkin_room",
                http_status_code=status.HTTP_400_BAD_REQUEST
            )

        # Get checkin_room to retrieve org_id
        checkin_room = await self.db.execute(
            select(CheckinRoom).where(CheckinRoom.id == session.checkin_room_id)
        )
        checkin_room_obj = checkin_room.scalar_one_or_none()

        if not checkin_room_obj:
            raise ComposeError(
                error_code=ErrorCode.General.NOT_FOUND,
                message=f"CheckinRoom not found with ID: {session.checkin_room_id}",
                http_status_code=status.HTTP_404_NOT_FOUND
            )

        org_id = checkin_room_obj.org_id

        try:
            created_order_numbers = []

            # Get starting sequence for bulk operations
            # This ensures sequential numbering when creating multiple orders
            current_sequence = await self._get_next_sequence()

            # Process each order in the request
            for order_request in request.orders:
                # Lookup division by name
                division = await self.repository.get_division_by_name(
                    name=order_request.category.value,
                    org_id=org_id
                )

                if not division:
                    raise ComposeError(
                        error_code=ErrorCode.General.NOT_FOUND,
                        message=f"Division not found with name: {order_request.category.value}",
                        http_status_code=status.HTTP_404_NOT_FOUND
                    )

                # Generate unique order number using current sequence
                order_number = self._format_order_number(current_sequence)
                current_sequence += 1

                # Calculate total amount from items
                total_amount = sum(
                    (item.price or 0) * (item.qty or 1)
                    for item in order_request.items
                )

                # Create order
                order = await self.repository.create_order(
                    session_id=request.session_id,
                    guest_id=guest_id,
                    division_id=division.id,
                    order_number=order_number,
                    notes=order_request.note,
                    additional_notes=order_request.additional_note,
                    org_id=org_id,
                    total_amount=total_amount,
                    checkin_room_id=session.checkin_room_id
                )

                # Create order items
                for item_request in order_request.items:
                    order_item = OrderItem(
                        order_id=order.id,
                        title=item_request.title,
                        description=item_request.description,
                        qty=item_request.qty,
                        price=item_request.price or 0,
                        note=item_request.note
                    )
                    self.db.add(order_item)

                created_order_numbers.append(order_number)

                logger.info(
                    f"Order created successfully: order_id={order.id}, "
                    f"order_number={order_number}, session_id={request.session_id}, "
                    f"guest_id={guest_id}, items_count={len(order_request.items)}"
                )

            # Commit transaction for all orders
            await self.db.commit()

            logger.info(
                f"Bulk order creation completed: session_id={request.session_id}, "
                f"orders_count={len(created_order_numbers)}, order_numbers={created_order_numbers}"
            )

            return created_order_numbers

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error creating orders for session {request.session_id}: {str(e)}",
                exc_info=True
            )
            raise ComposeError(
                error_code=ErrorCode.General.INTERNAL_SERVER_ERROR,
                message=f"Failed to create orders: {str(e)}",
                http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                original_error=e
            )
