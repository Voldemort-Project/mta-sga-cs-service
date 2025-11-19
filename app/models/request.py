"""Request model"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Request(Base):
    """Request model"""

    __tablename__ = "requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checkin_id = Column(UUID(as_uuid=True), ForeignKey("checkins.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)  # guest yang membuat request
    category = Column(String, nullable=False)  # damage_report, food_order, cleaning, etc.
    message = Column(Text)
    status = Column(String, nullable=False)  # pending, in_progress, done
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    checkin = relationship("Checkin", back_populates="requests")
    user = relationship("User", back_populates="requests", foreign_keys=[user_id])
    assignments = relationship("RequestAssignment", back_populates="request", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="request", cascade="all, delete-orphan")
