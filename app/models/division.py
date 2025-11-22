"""Division model"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Division(Base):
    """Division model"""

    __tablename__ = "divisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default="now()", onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="divisions")
    users = relationship("User", back_populates="division", foreign_keys="User.division_id")
