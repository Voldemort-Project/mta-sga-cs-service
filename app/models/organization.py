"""Organization model"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Organization(Base):
    """Organization model"""

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    divisions = relationship("Division", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization", foreign_keys="User.org_id")
    rooms = relationship("Room", back_populates="organization", cascade="all, delete-orphan")
    checkins = relationship("Checkin", back_populates="organization", foreign_keys="Checkin.org_id")
