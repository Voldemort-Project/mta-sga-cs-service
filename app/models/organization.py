"""Organization model"""
import uuid
from datetime import datetime

from sqlalchemy import Column, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Organization(Base):
    """Organization model"""

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default="now()", onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    divisions = relationship("Division", back_populates="organization")
    users = relationship("User", back_populates="organization", foreign_keys="User.org_id")
    rooms = relationship("Room", back_populates="organization")
    checkin_rooms = relationship("CheckinRoom", back_populates="organization", foreign_keys="CheckinRoom.org_id")
    orders = relationship("Order", back_populates="organization", foreign_keys="Order.org_id")
