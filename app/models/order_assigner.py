"""OrderAssigner model"""
import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, TIMESTAMP, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class OrderAssignerStatus(enum.Enum):
    """Order assigner status enum"""
    assigned = "assigned"
    pick_up = "pick_up"
    in_progress = "in_progress"
    cancel = "cancel"
    completed = "completed"


class OrderAssigner(Base):
    """OrderAssigner model - links orders to workers"""

    __tablename__ = "order_assigners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_at = Column(TIMESTAMP(timezone=True), server_default="now()", nullable=False)
    status = Column(SQLEnum(OrderAssignerStatus, name="enum_order_assigner_status"), default=OrderAssignerStatus.assigned, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default="now()", onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="order_assigners", foreign_keys=[order_id])
    worker = relationship("User", back_populates="assigned_orders", foreign_keys=[worker_id])
