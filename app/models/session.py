"""Session model"""
import uuid
from datetime import datetime
import enum

from sqlalchemy import Column, BigInteger, TIMESTAMP, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SessionStatus(enum.Enum):
    """Session status enum"""
    open = "open"
    terminated = "terminated"


class SessionMode(enum.Enum):
    """Session mode enum"""
    agent = "agent"
    manual = "manual"


class Session(Base):
    """Session model"""

    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(SQLEnum(SessionStatus, name="enum_session_status"), default=SessionStatus.open, nullable=True)
    mode = Column(SQLEnum(SessionMode, name="enum_session_mode"), default=SessionMode.agent, nullable=True)
    start = Column(TIMESTAMP(timezone=True), nullable=True)
    end = Column(TIMESTAMP(timezone=True), nullable=True)
    duration = Column(BigInteger, nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    checkin_room_id = Column(UUID(as_uuid=True), ForeignKey("checkin_rooms.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default="now()", onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions", foreign_keys=[session_id])
    checkin_room = relationship("CheckinRoom", back_populates="sessions", foreign_keys=[checkin_room_id])
    messages = relationship("Message", back_populates="session", foreign_keys="Message.session_id")
    orders = relationship("Order", back_populates="session", foreign_keys="Order.session_id")
