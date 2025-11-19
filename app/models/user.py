"""User model"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """User model"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)  # guest bisa null
    division_id = Column(UUID(as_uuid=True), ForeignKey("divisions.id", ondelete="SET NULL"), nullable=True)  # guest tidak punya divisi
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String)
    id_card_number = Column(String)  # hanya diisi guest atau bisa null
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="users", foreign_keys=[org_id])
    division = relationship("Division", back_populates="users", foreign_keys=[division_id])
    role = relationship("Role", back_populates="users", foreign_keys=[role_id])
    checkins = relationship("Checkin", back_populates="user", foreign_keys="Checkin.user_id")
    requests = relationship("Request", back_populates="user", foreign_keys="Request.user_id")
    request_assignments = relationship("RequestAssignment", back_populates="worker", foreign_keys="RequestAssignment.user_id")
    chat_messages = relationship("Chat", back_populates="sender", foreign_keys="Chat.sender_id")
