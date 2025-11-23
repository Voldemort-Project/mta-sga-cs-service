"""Guest repository for database operations"""
from datetime import datetime, date, time
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models.user import User
from app.models.checkin import CheckinRoom
from app.models.room import Room
from app.models.role import Role
from app.models.session import Session
from app.models.message import Message, MessageRole
from app.models.order import Order


class GuestRepository:
    """Repository for guest-related database operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_guest_role(self) -> Optional[Role]:
        """Get the guest role"""
        result = await self.db.execute(
            select(Role).where(Role.code == "guest")
        )
        return result.scalar_one_or_none()

    async def get_room_by_number(self, room_number: str, org_id: Optional[UUID] = None) -> Optional[Room]:
        """Get room by room number"""
        query = select(Room).where(Room.room_number == room_number)
        if org_id:
            query = query.where(Room.org_id == org_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_guest_user(
        self,
        name: str,
        email: str,
        phone: str,
        role_id: UUID,
        org_id: Optional[UUID] = None
    ) -> User:
        """Create a new guest user"""
        user = User(
            name=name,
            email=email,
            mobile_phone=phone,
            role_id=role_id,
            org_id=org_id,
            division_id=None  # guests don't have divisions
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def create_checkin(
        self,
        room_id: UUID,
        checkin_date: date,
        checkin_time: time,
        org_id: UUID,
        user_id: Optional[UUID] = None
    ) -> CheckinRoom:
        """Create a new check-in

        Args:
            room_id: Room ID for check-in
            checkin_date: Check-in date
            checkin_time: Check-in time
            org_id: Organization ID
            user_id: User ID of the admin who registered the guest (optional)
        """
        checkin = CheckinRoom(
            org_id=org_id,
            user_id=user_id,
            room_id=room_id,
            checkin_date=checkin_date,
            checkin_time=checkin_time,
            status="active"
        )
        self.db.add(checkin)
        await self.db.flush()
        return checkin

    async def update_room_booked_status(self, room_id: UUID, is_booked: bool) -> None:
        """Update room booking status"""
        result = await self.db.execute(
            select(Room).where(Room.id == room_id)
        )
        room = result.scalar_one_or_none()
        if room:
            room.is_booked = is_booked
            await self.db.flush()

    async def create_session(
        self,
        user_id: UUID,
        checkin_room_id: UUID,
        status=None,
        mode=None
    ) -> Session:
        """Create a new chat session for guest"""
        from app.models.session import SessionStatus, SessionMode

        session = Session(
            session_id=user_id,
            checkin_room_id=checkin_room_id,
            status=status or SessionStatus.open,
            mode=mode or SessionMode.agent,
            start=datetime.utcnow()
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def create_message(
        self,
        session_id: UUID,
        role: MessageRole,
        text: str
    ) -> Message:
        """Create a new message in a session"""
        message = Message(
            session_id=session_id,
            role=role,
            text=text
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def get_user_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone number"""
        result = await self.db.execute(
            select(User).where(User.mobile_phone == phone)
        )
        return result.scalar_one_or_none()

    async def get_active_session_by_user_id(self, user_id: UUID) -> Optional[Session]:
        """Get active session for a user"""
        from app.models.session import SessionStatus
        result = await self.db.execute(
            select(Session).where(
                Session.session_id == user_id,
                Session.status == SessionStatus.open,
                Session.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_session_by_id(self, session_id: UUID) -> Optional[Session]:
        """Get session by session ID"""
        result = await self.db.execute(
            select(Session).where(
                Session.id == session_id,
                Session.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_session_with_user(self, session_id: UUID) -> Optional[Session]:
        """Get session by session ID with user relationship loaded"""
        from sqlalchemy.orm import joinedload
        result = await self.db.execute(
            select(Session)
            .options(joinedload(Session.user))
            .where(
                Session.id == session_id,
                Session.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def create_order(
        self,
        session_id: UUID,
        guest_id: UUID,
        category: str,
        order_number: str,
        notes: Optional[str] = None,
        additional_notes: Optional[str] = None,
        org_id: Optional[UUID] = None,
        total_amount: float = 0
    ) -> Order:
        """Create a new order

        Args:
            session_id: Session ID
            guest_id: Guest user ID
            category: Order category (housekeeping, room_service, maintenance, concierge)
            order_number: Unique order number
            notes: Order notes (optional)
            additional_notes: Additional order notes (optional)
            org_id: Organization ID (optional)
            total_amount: Total amount (optional, default: 0)
        """
        order = Order(
            session_id=session_id,
            guest_id=guest_id,
            org_id=org_id,
            category=category,
            notes=notes,
            additional_notes=additional_notes,
            order_number=order_number,
            total_amount=total_amount
        )
        self.db.add(order)
        await self.db.flush()
        return order

    def get_guests_query(self, org_id: UUID) -> Select:
        """Get base query for guests filtered by organization

        Query starts from checkin_rooms table, then joins to users and roles.
        Uses sessions table to link checkin_rooms to guest users.

        Args:
            org_id: Organization ID to filter guests

        Returns:
            SQLAlchemy Select query for guests with guest role in the organization
        """
        # Start from checkin_rooms table
        # Join to sessions to get guest user (session.session_id = guest_user.id)
        # Join to users to get user details
        # Join to roles to filter only guest role
        # Use distinct() to avoid duplicate users if they have multiple check-ins
        query = (
            select(User)
            .select_from(CheckinRoom)
            .join(Session, CheckinRoom.id == Session.checkin_room_id)
            .join(User, Session.session_id == User.id)
            .join(Role, User.role_id == Role.id)
            .where(
                CheckinRoom.org_id == org_id,
                CheckinRoom.deleted_at.is_(None),
                Session.deleted_at.is_(None),
                Role.code == "guest",
                User.deleted_at.is_(None)
            )
            .distinct()
        )
        return query
