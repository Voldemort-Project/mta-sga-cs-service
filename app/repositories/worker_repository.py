"""Worker repository for database operations"""
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.role import Role


class WorkerRepository:
    """Repository for worker-related database operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_workers(self, org_id: UUID | None = None) -> List[User]:
        """Get all workers (users that are NOT 'Keycloak Administrator', 'Administrator', 'Guest')

        Args:
            org_id: Optional organization ID to filter workers by organization

        Returns:
            List of User objects that are workers
        """
        # Build query to get users with their roles
        # Use selectinload to eagerly load the role relationship
        query = (
            select(User)
            .options(selectinload(User.role))
            .join(Role, User.role_id == Role.id)
            .where(
                User.deleted_at.is_(None),
                Role.deleted_at.is_(None),
                Role.code.notin_(["guest", "administrator", "keycloak_administrator"])
            )
        )

        # Filter by organization if provided
        if org_id:
            query = query.where(User.org_id == org_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())
