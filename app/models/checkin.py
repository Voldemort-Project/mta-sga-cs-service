"""CheckinRoom model"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Date, Time, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CheckinRoom(Base):
    """CheckinRoom model"""

    __tablename__ = "checkin_rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    room_id = Column(UUID(as_uuid=True), nullable=True)
    checkin_date = Column(Date, nullable=True)
    checkin_time = Column(Time, nullable=True)
    checkout_date = Column(Date, nullable=True)
    checkout_time = Column(Time, nullable=True)
    status = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default="now()", onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="checkin_rooms", foreign_keys=[org_id])
    user = relationship("User", foreign_keys=[user_id])
    sessions = relationship("Session", back_populates="checkin_room", foreign_keys="Session.checkin_room_id")
