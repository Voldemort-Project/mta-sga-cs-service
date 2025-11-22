"""Role model"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Role(Base):
    """Role model - guest, worker, housekeeping, admin, supervisor, etc."""

    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    code = Column(String, nullable=True, unique=True)  # e.g., "keycloak_user", "guest", "admin"
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default="now()", nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default="now()", onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    users = relationship("User", back_populates="role", foreign_keys="User.role_id")
