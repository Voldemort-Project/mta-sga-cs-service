"""Order service for business logic"""
from typing import Optional, List
from uuid import UUID
from datetime import date
import logging

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginationParams, paginate_query
from app.core.exceptions import ComposeError
from app.constants.error_codes import ErrorCode
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderListItem, SessionItem, GuestItem, CheckinRoomItem, RoomItem
from app.schemas.response import StandardResponse, create_paginated_response
from app.models.order import Order

logger = logging.getLogger(__name__)


class OrderService:
    """Service for order operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = OrderRepository(db)

    async def list_orders(
        self,
        org_id: Optional[UUID],
        params: PaginationParams
    ) -> StandardResponse[List[OrderListItem]]:
        """
        List orders for an organization with pagination

        Args:
            org_id: Optional organization ID to filter orders
            params: Pagination parameters (page, per_page, keyword, order)

        Returns:
            StandardResponse[List[OrderListItem]]: Standard response with paginated list of orders

        Raises:
            ComposeError: If pagination fails or other errors occur
        """
        try:
            # Get base query for orders
            query = self.repository.get_orders_query(org_id=org_id)

            # Apply pagination, search, and ordering
            result = await paginate_query(
                db=self.db,
                query=query,
                params=params,
                model=Order,
                search_fields=["order_number", "title", "description", "category"]
            )

            # Convert Order objects to OrderListItem with nested relationships
            order_items = []
            for order in result.data:
                # Get checkin room if available
                checkin_room = None
                session = None
                rooms = []

                if order.checkin_id:
                    # Get checkin room (already loaded via relationship)
                    checkin_room_obj = order.checkin
                    if checkin_room_obj:
                        # Get session for this checkin room
                        session_obj = await self.repository.get_session_by_checkin_room_id(
                            checkin_room_obj.id
                        )

                        # Get guest user if session exists
                        guest = None
                        if session_obj and session_obj.session_id:
                            guest_obj = await self.repository.get_user_by_id(session_obj.session_id)
                            if guest_obj:
                                guest = GuestItem(
                                    id=guest_obj.id,
                                    name=guest_obj.name,
                                    email=guest_obj.email,
                                    mobile_phone=guest_obj.mobile_phone
                                )

                        # Get rooms for this checkin
                        if checkin_room_obj.room_id:
                            room_objs = await self.repository.get_rooms_by_ids(
                                list(checkin_room_obj.room_id)
                            )
                            rooms = [
                                RoomItem(
                                    id=room.id,
                                    label=room.label,
                                    room_number=room.room_number,
                                    type=room.type,
                                    is_booked=room.is_booked
                                )
                                for room in room_objs
                            ]

                        # Build session item with guest nested inside
                        if session_obj:
                            session = SessionItem(
                                id=session_obj.id,
                                is_active=session_obj.is_active,
                                start=session_obj.start,
                                end=session_obj.end,
                                duration=session_obj.duration,
                                guest=guest
                            )

                        # Build checkin room item
                        checkin_room = CheckinRoomItem(
                            id=checkin_room_obj.id,
                            checkin_date=checkin_room_obj.checkin_date,
                            checkin_time=str(checkin_room_obj.checkin_time) if checkin_room_obj.checkin_time else None,
                            checkout_date=checkin_room_obj.checkout_date,
                            checkout_time=str(checkin_room_obj.checkout_time) if checkin_room_obj.checkout_time else None,
                            status=checkin_room_obj.status,
                            rooms=rooms
                        )

                # Extract order_date from created_at
                order_date = order.created_at.date() if order.created_at else None

                # Build order item
                order_item = OrderListItem(
                    id=order.id,
                    order_number=order.order_number,
                    order_date=order_date,
                    order_status=order.status,
                    category=order.category,
                    title=order.title,
                    description=order.description,
                    note=order.notes,
                    additional_note=order.additional_notes,
                    session=session,
                    checkin_rooms=checkin_room,
                    created_at=order.created_at,
                    updated_at=order.updated_at
                )
                order_items.append(order_item)

            # Return standard response with pagination
            return create_paginated_response(
                data=order_items,
                page=result.meta.page,
                per_page=result.meta.per_page,
                total=result.meta.total
            )

        except ComposeError:
            # Re-raise ComposeError as-is
            raise
        except Exception as e:
            logger.error(f"Error listing orders: {str(e)}", exc_info=True)
            raise ComposeError(
                error_code=ErrorCode.Order.LIST_ORDERS_FAILED,
                message="Failed to retrieve orders. Please try again or contact support.",
                http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                original_error=e
            )
