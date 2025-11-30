"""User model"""
import uuid
from datetime import datetime

from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """User model"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    mobile_phone = Column(Text, nullable=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    division_id = Column(UUID(as_uuid=True), ForeignKey("divisions.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default="now()", onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="users", foreign_keys=[org_id])
    division = relationship("Division", back_populates="users", foreign_keys=[division_id])
    role = relationship("Role", back_populates="users", foreign_keys=[role_id])
    sessions = relationship("Session", back_populates="user", foreign_keys="Session.session_id")
    orders = relationship("Order", back_populates="guest", foreign_keys="Order.guest_id")
    assigned_orders = relationship("OrderAssigner", back_populates="worker", foreign_keys="OrderAssigner.worker_id")
    checkin_rooms = relationship("CheckinRoom", foreign_keys="CheckinRoom.guest_id", viewonly=True)
