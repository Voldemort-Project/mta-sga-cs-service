"""Order model"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, Enum as SQLEnum, Float
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


class OrderCategory(enum.Enum):
    """Order category enum"""
    housekeeping = "housekeeping"
    room_service = "room_service"
    maintenance = "maintenance"
    concierge = "concierge"


class Order(Base):
    """Order model"""

    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(Text, nullable=False, unique=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=True)
    guest_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    category = Column(SQLEnum(OrderCategory, name="enum_order_category"), nullable=False)
    notes = Column(Text, nullable=True)
    additional_notes = Column(Text, nullable=True)
    status = Column(SQLEnum(OrderStatus, name="enum_order_status"), default=OrderStatus.pending, nullable=True)
    total_amount = Column(Float, default=0, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default="now()", onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    session = relationship("Session", back_populates="orders", foreign_keys=[session_id])
    guest = relationship("User", back_populates="orders", foreign_keys=[guest_id])
    organization = relationship("Organization", back_populates="orders", foreign_keys=[org_id])
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    order_assigners = relationship("OrderAssigner", back_populates="order", foreign_keys="OrderAssigner.order_id")
