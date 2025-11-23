"""Worker service for business logic"""
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.worker_repository import WorkerRepository
from app.schemas.worker import WorkerListItem


class WorkerService:
    """Service for worker-related operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = WorkerRepository(db)

    async def list_workers(self, org_id: UUID | None = None) -> List[WorkerListItem]:
        """
        List all workers (users that are NOT 'Keycloak Administrator', 'Administrator', 'Guest')

        Args:
            org_id: Optional organization ID to filter workers by organization

        Returns:
            List of WorkerListItem objects
        """
        # Get workers from repository
        workers = await self.repository.get_workers(org_id=org_id)

        # Convert User objects to WorkerListItem
        worker_items = [
            WorkerListItem(
                id=user.id,
                name=user.name,
                email=user.email,
                mobile_phone=user.mobile_phone,
                role_id=user.role_id,
                role_name=user.role.name if user.role else None,
                org_id=user.org_id,
                division_id=user.division_id,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in workers
        ]

        return worker_items
