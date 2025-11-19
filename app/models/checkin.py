"""Checkin model"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Checkin(Base):
    """Checkin model"""

    __tablename__ = "checkins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)  # bisa null
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)  # user dengan role=guest
    checkin_time = Column(DateTime, nullable=False)
    checkout_time = Column(DateTime)
    status = Column(String, nullable=False)  # active, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="checkins", foreign_keys=[org_id])
    room = relationship("Room", back_populates="checkins", foreign_keys=[room_id])
    user = relationship("User", back_populates="checkins", foreign_keys=[user_id])
    requests = relationship("Request", back_populates="checkin", cascade="all, delete-orphan")
