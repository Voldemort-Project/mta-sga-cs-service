"""Order model"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class OrderStatus(enum.Enum):
    """Order status enum"""
    pending = "pending"
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    rejected = "rejected"
    block = "block"
    suspended = "suspended"


class Order(Base):
    """Order model"""

    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(Text, nullable=False, unique=True)
    checkin_id = Column(UUID(as_uuid=True), ForeignKey("checkin_rooms.id"), nullable=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    additional_notes = Column(Text, nullable=True)
    status = Column(SQLEnum(OrderStatus, name="enum_order_status"), default=OrderStatus.pending, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default="now()", onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    checkin = relationship("CheckinRoom", back_populates="orders", foreign_keys=[checkin_id])
    organization = relationship("Organization", back_populates="orders", foreign_keys=[org_id])
