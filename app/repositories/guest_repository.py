"""Guest repository for database operations"""
from datetime import datetime, date, time, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models.user import User
from app.models.checkin import CheckinRoom
from app.models.room import Room
from app.models.role import Role
from app.models.session import Session
from app.models.message import Message, MessageRole
from app.models.order import Order
from app.models.division import Division


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

    async def get_available_rooms(self, org_id: UUID) -> List[Room]:
        """Get all available (not booked) rooms for an organization

        Args:
            org_id: Organization ID to filter rooms

        Returns:
            List of available Room objects
        """
        result = await self.db.execute(
            select(Room)
            .where(
                Room.org_id == org_id,
                Room.is_booked == False,
                Room.deleted_at.is_(None)
            )
            .order_by(Room.room_number.asc())
        )
        return list(result.scalars().all())

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
        guest_id: Optional[UUID] = None,
        admin_id: Optional[UUID] = None
    ) -> CheckinRoom:
        """Create a new check-in

        Args:
            room_id: Room ID for check-in
            checkin_date: Check-in date
            checkin_time: Check-in time
            org_id: Organization ID
            guest_id: Guest user ID (optional)
            admin_id: Admin user ID who registered the guest (optional)
        """
        checkin = CheckinRoom(
            org_id=org_id,
            guest_id=guest_id,
            admin_id=admin_id,
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
            start=datetime.now(timezone.utc)
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
        """Create a new message in a session and update session.updated_at"""
        # Get session to update its updated_at timestamp
        session = await self.get_session_by_id(session_id)
        if session:
            # Update session.updated_at to current time
            session.updated_at = datetime.now(timezone.utc)

        message = Message(
            session_id=session_id,
            role=role,
            text=text
        )
        self.db.add(message)
        await self.db.flush()
        return message

    async def get_user_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone number (excludes soft-deleted users)"""
        result = await self.db.execute(
            select(User).where(
                User.mobile_phone == phone,
                User.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.deleted_at.is_(None)
            )
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

    async def get_checkin_room_by_id(self, checkin_room_id: UUID) -> Optional[CheckinRoom]:
        """Get checkin room by ID"""
        result = await self.db.execute(
            select(CheckinRoom).where(
                CheckinRoom.id == checkin_room_id,
                CheckinRoom.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_active_checkin_by_guest_id(self, guest_user_id: UUID) -> Optional[CheckinRoom]:
        """Get active checkin room for a guest user

        Args:
            guest_user_id: Guest user ID to find active checkin

        Returns:
            Active CheckinRoom or None if not found
        """
        # Query directly from checkin_rooms table
        result = await self.db.execute(
            select(CheckinRoom)
            .where(
                CheckinRoom.guest_id == guest_user_id,
                CheckinRoom.status == "active",
                CheckinRoom.deleted_at.is_(None)
            )
            .order_by(CheckinRoom.created_at.desc())
            .limit(1)
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

    async def get_division_by_name(self, name: str, org_id: Optional[UUID] = None) -> Optional[Division]:
        """Get division by name

        Args:
            name: Division name to search for
            org_id: Organization ID to filter by (optional)

        Returns:
            Division object or None if not found
        """
        query = select(Division).where(
            Division.name == name,
            Division.deleted_at.is_(None)
        )
        if org_id:
            query = query.where(Division.org_id == org_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_order(
        self,
        session_id: UUID,
        guest_id: UUID,
        division_id: UUID,
        order_number: str,
        notes: Optional[str] = None,
        additional_notes: Optional[str] = None,
        org_id: Optional[UUID] = None,
        total_amount: float = 0,
        checkin_room_id: Optional[UUID] = None
    ) -> Order:
        """Create a new order

        Args:
            session_id: Session ID
            guest_id: Guest user ID
            division_id: Division ID (foreign key to divisions table)
            order_number: Unique order number
            notes: Order notes (optional)
            additional_notes: Additional order notes (optional)
            org_id: Organization ID (optional)
            total_amount: Total amount (optional, default: 0)
            checkin_room_id: Check-in room ID (optional)
        """
        order = Order(
            session_id=session_id,
            guest_id=guest_id,
            org_id=org_id,
            division_id=division_id,
            notes=notes,
            additional_notes=additional_notes,
            order_number=order_number,
            total_amount=total_amount,
            checkin_room_id=checkin_room_id
        )
        self.db.add(order)
        await self.db.flush()
        return order

    def get_messages_query(self, session_id: UUID) -> Select:
        """Get base query for messages filtered by session_id

        Args:
            session_id: Session ID to filter messages

        Returns:
            SQLAlchemy Select query for messages with session_id filter
        """
        query = (
            select(Message)
            .where(
                Message.session_id == session_id,
                Message.deleted_at.is_(None)
            )
        )
        return query

    def get_guests_query(self, org_id: UUID) -> Select:
        """Get base query for guests filtered by organization

        Query starts from checkin_rooms table, joins directly to users and roles.
        Session join is removed since sessions are only created after guest sends WhatsApp message.
        CheckinRoom and Session data will be loaded via selectinload (separate queries).
        Sessions will be filtered to status='open' at service layer.

        Uses subquery to get distinct users with their latest checkin_rooms.created_at for ordering.

        Args:
            org_id: Organization ID to filter guests

        Returns:
            SQLAlchemy Select query for guests with guest role in the organization,
            with checkin_rooms and sessions relationships eagerly loaded
        """
        from sqlalchemy.orm import selectinload

        # Subquery to get distinct user_ids with their latest checkin_rooms.created_at
        # This allows us to order by checkin_rooms.created_at while using DISTINCT
        subquery = (
            select(
                CheckinRoom.guest_id,
                func.max(CheckinRoom.created_at).label('latest_checkin_created_at')
            )
            .where(
                CheckinRoom.org_id == org_id,
                CheckinRoom.deleted_at.is_(None)
            )
            .group_by(CheckinRoom.guest_id)
            .subquery()
        )

        # Main query: select distinct users, join with subquery for ordering
        query = (
            select(User)
            .select_from(subquery)
            .join(User, subquery.c.guest_id == User.id)
            .join(Role, User.role_id == Role.id)
            .options(
                selectinload(User.checkin_rooms).selectinload(CheckinRoom.room),
                selectinload(User.sessions)
            )
            .where(
                Role.code == "guest",
                User.deleted_at.is_(None)
            )
            .order_by(subquery.c.latest_checkin_created_at.desc())
        )
        return query

    async def get_incomplete_orders_by_guest_id(self, guest_id: UUID) -> List[Order]:
        """Get all incomplete orders for a guest

        Incomplete orders are those with status: pending, assigned, or in_progress

        Args:
            guest_id: Guest user ID

        Returns:
            List of incomplete Order objects
        """
        from app.models.order import OrderStatus

        result = await self.db.execute(
            select(Order).where(
                Order.guest_id == guest_id,
                Order.status.in_([
                    OrderStatus.pending,
                    OrderStatus.assigned,
                    OrderStatus.in_progress
                ]),
                Order.deleted_at.is_(None)
            )
        )
        return list(result.scalars().all())

    async def terminate_session(self, session_id: UUID) -> Optional[Session]:
        """Terminate a session by setting status to terminated and calculating duration

        Args:
            session_id: Session ID to terminate

        Returns:
            Updated Session object or None if session not found
        """
        from app.models.session import SessionStatus

        session = await self.get_session_by_id(session_id)
        if not session:
            return None

        # Set end time to current time (timezone-aware UTC)
        end_time = datetime.now(timezone.utc)
        session.end = end_time
        session.status = SessionStatus.terminated

        # Calculate duration if start time exists
        if session.start:
            # Ensure both datetimes are timezone-aware for comparison
            # If session.start is naive, make it timezone-aware (UTC)
            start_time = session.start
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)

            duration_seconds = int((end_time - start_time).total_seconds())
            session.duration = duration_seconds

        await self.db.flush()
        return session

    async def update_session_agent_status(
        self,
        session_id: UUID,
        agent_created: bool,
        category: Optional[str] = None
    ) -> Optional[Session]:
        """Update session agent creation status and category

        Args:
            session_id: Session ID to update
            agent_created: Whether agent has been created
            category: Agent category (e.g., "room_service", "general_information", "customer_service")

        Returns:
            Updated Session object or None if session not found
        """
        session = await self.get_session_by_id(session_id)
        if not session:
            return None

        session.agent_created = agent_created
        if category:
            session.category = category

        await self.db.flush()
        return session

    async def update_checkin_checkout(
        self,
        checkin_room_id: UUID,
        checkout_date: date,
        checkout_time: time,
        status: str = "checkout"
    ) -> Optional[CheckinRoom]:
        """Update checkin room with checkout information

        Args:
            checkin_room_id: CheckinRoom ID to update
            checkout_date: Checkout date
            checkout_time: Checkout time
            status: Status to set (default: "checkout")

        Returns:
            Updated CheckinRoom object or None if not found
        """
        checkin_room = await self.get_checkin_room_by_id(checkin_room_id)
        if not checkin_room:
            return None

        checkin_room.checkout_date = checkout_date
        checkin_room.checkout_time = checkout_time
        checkin_room.status = status

        await self.db.flush()
        return checkin_room
