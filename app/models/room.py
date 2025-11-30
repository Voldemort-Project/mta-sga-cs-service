"""Room model"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Room(Base):
    """Room model"""

    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    label = Column(String, nullable=False)
    room_number = Column(String, nullable=False)
    type = Column(String, nullable=False)
    is_booked = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default="now()", onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="rooms")
    checkin_rooms = relationship("CheckinRoom", back_populates="room", foreign_keys="CheckinRoom.room_id")
