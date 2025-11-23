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
from app.schemas.order import OrderListItem, SessionItem, GuestItem, CheckinRoomItem, RoomItem, OrderItemSchema, UpdateOrderStatusResponse
from app.schemas.response import StandardResponse, create_paginated_response, create_success_response
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem

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
                search_fields=["order_number", "category"]
            )

            # Convert Order objects to OrderListItem with nested relationships
            order_items = []
            for order in result.data:
                # Get order items
                order_item_objs = await self.repository.get_order_items_by_order_id(order.id)
                items = [
                    OrderItemSchema(
                        id=item.id,
                        title=item.title,
                        description=item.description,
                        qty=item.qty,
                        price=item.price,
                        note=item.note
                    )
                    for item in order_item_objs
                ]

                # Get session if available
                session = None
                checkin_room = None
                rooms = []

                if order.session_id:
                    # Get session (already loaded via relationship)
                    session_obj = order.session
                    if session_obj:
                        # Get guest user
                        guest = None
                        if order.guest_id:
                            guest_obj = await self.repository.get_user_by_id(order.guest_id)
                            if guest_obj:
                                guest = GuestItem(
                                    id=guest_obj.id,
                                    name=guest_obj.name,
                                    email=guest_obj.email,
                                    mobile_phone=guest_obj.mobile_phone
                                )

                        # Build session item with guest nested inside
                        session = SessionItem(
                            id=session_obj.id,
                            status=session_obj.status.value if session_obj.status else None,
                            mode=session_obj.mode.value if session_obj.mode else None,
                            start=session_obj.start,
                            end=session_obj.end,
                            duration=session_obj.duration,
                            guest=guest
                        )

                        # Get checkin room if available
                        if session_obj.checkin_room_id:
                            checkin_room_obj = session_obj.checkin_room
                            if checkin_room_obj:
                                # Get room for this checkin
                                if checkin_room_obj.room_id:
                                    room_obj = await self.repository.get_room_by_id(checkin_room_obj.room_id)
                                    if room_obj:
                                        rooms = [
                                            RoomItem(
                                                id=room_obj.id,
                                                label=room_obj.label,
                                                room_number=room_obj.room_number,
                                                type=room_obj.type,
                                                is_booked=room_obj.is_booked
                                            )
                                        ]

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
                    category=order.category.value if hasattr(order.category, 'value') else order.category,
                    note=order.notes,
                    additional_note=order.additional_notes,
                    total_amount=order.total_amount,
                    items=items,
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

    async def update_order_status(
        self,
        order_id: UUID,
        new_status: OrderStatus
    ) -> StandardResponse[UpdateOrderStatusResponse]:
        """
        Update order status

        Args:
            order_id: Order ID to update
            new_status: New order status

        Returns:
            StandardResponse[UpdateOrderStatusResponse]: Standard response with updated order information

        Raises:
            ComposeError: If order not found or update fails
        """
        try:
            # Get order by ID
            order = await self.repository.get_order_by_id(order_id)
            if not order:
                raise ComposeError(
                    error_code=ErrorCode.Order.ORDER_NOT_FOUND,
                    message=f"Order with ID {order_id} not found.",
                    http_status_code=status.HTTP_404_NOT_FOUND
                )

            # Update order status
            updated_order = await self.repository.update_order_status(order_id, new_status)
            if not updated_order:
                raise ComposeError(
                    error_code=ErrorCode.Order.UPDATE_STATUS_FAILED,
                    message="Failed to update order status. Please try again or contact support.",
                    http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Build response
            response_data = UpdateOrderStatusResponse(
                id=updated_order.id,
                order_number=updated_order.order_number,
                status=updated_order.status,
                updated_at=updated_order.updated_at
            )

            return create_success_response(
                data=response_data,
                message="Order status updated successfully"
            )

        except ComposeError:
            # Re-raise ComposeError as-is
            raise
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}", exc_info=True)
            raise ComposeError(
                error_code=ErrorCode.Order.UPDATE_STATUS_FAILED,
                message="Failed to update order status. Please try again or contact support.",
                http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                original_error=e
            )
