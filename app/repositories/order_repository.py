"""Order repository for database operations"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from app.models.order import Order
from app.models.checkin import CheckinRoom
from app.models.session import Session
from app.models.user import User
from app.models.room import Room
from app.models.order_item import OrderItem


class OrderRepository:
    """Repository for order-related database operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_orders_query(self, org_id: Optional[UUID] = None, category: Optional = None) -> Select:
        """Get base query for orders with all relationships

        Query starts from orders table, then joins to:
        - Session (via session_id)
        - User (via guest_id, which is the guest user)
        - CheckinRoom (via session.checkin_room_id)
        - Room (via checkin_room.room_id)
        - OrderItems (via order_id)
        - Organization (via org_id)

        Args:
            org_id: Optional organization ID to filter orders
            category: Optional order category to filter by

        Returns:
            SQLAlchemy Select query for orders with relationships
        """
        # Start from orders table
        # Use selectinload to eagerly load relationships
        query = (
            select(Order)
            .options(
                selectinload(Order.session).selectinload(Session.checkin_room),
                selectinload(Order.guest),
                selectinload(Order.organization),
                selectinload(Order.order_items)
            )
            .where(Order.deleted_at.is_(None))
        )

        # Filter by organization if provided
        if org_id:
            query = query.where(Order.org_id == org_id)

        # Filter by category if provided
        if category:
            query = query.where(Order.category == category)

        return query

    async def get_rooms_by_ids(self, room_ids: list[UUID]) -> list[Room]:
        """Get rooms by their IDs

        Args:
            room_ids: List of room IDs

        Returns:
            List of Room objects
        """
        if not room_ids:
            return []

        result = await self.db.execute(
            select(Room).where(
                Room.id.in_(room_ids),
                Room.deleted_at.is_(None)
            )
        )
        return list(result.scalars().all())

    async def get_session_by_checkin_room_id(self, checkin_room_id: UUID) -> Optional[Session]:
        """Get session by checkin room ID

        Args:
            checkin_room_id: Check-in room ID

        Returns:
            Session object or None
        """
        result = await self.db.execute(
            select(Session).where(
                Session.checkin_room_id == checkin_room_id,
                Session.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID

        Args:
            user_id: User ID

        Returns:
            User object or None
        """
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_room_by_id(self, room_id: UUID) -> Optional[Room]:
        """Get room by ID

        Args:
            room_id: Room ID

        Returns:
            Room object or None
        """
        result = await self.db.execute(
            select(Room).where(
                Room.id == room_id,
                Room.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_order_items_by_order_id(self, order_id: UUID) -> list[OrderItem]:
        """Get order items by order ID

        Args:
            order_id: Order ID

        Returns:
            List of OrderItem objects
        """
        result = await self.db.execute(
            select(OrderItem).where(
                OrderItem.order_id == order_id,
                OrderItem.deleted_at.is_(None)
            )
        )
        return list(result.scalars().all())

    async def get_order_by_id(self, order_id: UUID) -> Optional[Order]:
        """Get order by ID

        Args:
            order_id: Order ID

        Returns:
            Order object or None
        """
        result = await self.db.execute(
            select(Order).where(
                Order.id == order_id,
                Order.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_order_by_order_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number with all relationships

        Args:
            order_number: Order number

        Returns:
            Order object with relationships loaded or None
        """
        result = await self.db.execute(
            select(Order)
            .options(
                selectinload(Order.session).selectinload(Session.checkin_room),
                selectinload(Order.guest),
                selectinload(Order.organization),
                selectinload(Order.order_items)
            )
            .where(
                Order.order_number == order_number,
                Order.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def update_order_status(self, order_id: UUID, status) -> Optional[Order]:
        """Update order status

        Args:
            order_id: Order ID
            status: New order status (OrderStatus enum)

        Returns:
            Updated Order object or None if order not found
        """
        order = await self.get_order_by_id(order_id)
        if order:
            order.status = status
            await self.db.commit()
            await self.db.refresh(order)
        return order

    async def get_session_by_id(self, session_id: UUID) -> Optional[Session]:
        """Get session by ID

        Args:
            session_id: Session ID

        Returns:
            Session object or None
        """
        result = await self.db.execute(
            select(Session).where(
                Session.id == session_id,
                Session.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    def get_orders_by_session_query(self, user_id: UUID) -> Select:
        """Get query for orders by user_id with all relationships

        Query starts from orders table, then joins to:
        - Session (via session_id)
        - User/Guest (via guest_id)
        - Organization (via org_id)
        - OrderItems (via order_id)
        - CheckinRoom (via session.checkin_room_id)
        - Room (via checkin_room.room_id)

        Args:
            user_id: User ID to filter orders by guest_id

        Returns:
            SQLAlchemy Select query for orders with relationships
        """
        # Start from orders table with eager loading
        query = (
            select(Order)
            .options(
                selectinload(Order.session).selectinload(Session.checkin_room),
                selectinload(Order.guest),
                selectinload(Order.organization),
                selectinload(Order.order_items)
            )
            .where(
                Order.guest_id == user_id,
                Order.deleted_at.is_(None)
            )
        )

        return query
