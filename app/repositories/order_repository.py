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


class OrderRepository:
    """Repository for order-related database operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_orders_query(self, org_id: Optional[UUID] = None) -> Select:
        """Get base query for orders with all relationships

        Query starts from orders table, then joins to:
        - CheckinRoom (via checkin_id)
        - Session (via checkin_room_id)
        - User (via session_id, which is the guest user)
        - Room (via room_id array in CheckinRoom)

        Args:
            org_id: Optional organization ID to filter orders

        Returns:
            SQLAlchemy Select query for orders with relationships
        """
        # Start from orders table
        # Use selectinload to eagerly load checkin relationship
        query = (
            select(Order)
            .options(selectinload(Order.checkin))
            .where(Order.deleted_at.is_(None))
        )

        # Filter by organization if provided
        if org_id:
            query = query.where(Order.org_id == org_id)

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
