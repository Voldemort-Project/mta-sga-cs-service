"""OrderItem model"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class OrderItem(Base):
    """OrderItem model"""

    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    qty = Column(Integer, nullable=True)
    price = Column(Float, default=0, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default="now()", onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="order_items", foreign_keys=[order_id])
