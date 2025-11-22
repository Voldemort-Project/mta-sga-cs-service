"""Guest repository for database operations"""
from datetime import datetime, date, time
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.checkin import CheckinRoom
from app.models.room import Room
from app.models.role import Role
from app.models.session import Session
from app.models.message import Message, MessageRole


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
        room_ids: List[UUID],
        checkin_date: date,
        checkin_time: time,
        org_id: UUID
    ) -> CheckinRoom:
        """Create a new check-in"""
        checkin = CheckinRoom(
            org_id=org_id,
            room_id=room_ids,
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
        checkin_room_id: UUID
    ) -> Session:
        """Create a new chat session for guest"""
        session = Session(
            session_id=user_id,
            checkin_room_id=checkin_room_id,
            is_active=True,
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
        result = await self.db.execute(
            select(Session).where(
                Session.session_id == user_id,
                Session.is_active == True
            )
        )
        return result.scalar_one_or_none()
