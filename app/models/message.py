"""Message model"""
import uuid
from datetime import datetime
import enum

from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class MessageRole(enum.Enum):
    """Message role enum"""
    System = "System"
    User = "User"


class Message(Base):
    """Message model"""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=True)
    role = Column(SQLEnum(MessageRole, name="enum_message_role"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default="now()", onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    session = relationship("Session", back_populates="messages", foreign_keys=[session_id])
