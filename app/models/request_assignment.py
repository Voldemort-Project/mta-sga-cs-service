"""Request Assignment model"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class RequestAssignment(Base):
    """Request Assignment model"""

    __tablename__ = "request_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)  # worker yang mengerjakan
    assigned_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)

    # Relationships
    request = relationship("Request", back_populates="assignments")
    worker = relationship("User", back_populates="request_assignments", foreign_keys=[user_id])
