"""OrderAssigner repository for database operations"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order_assigner import OrderAssigner, OrderAssignerStatus
from app.models.order import Order
from app.models.user import User


class OrderAssignerRepository:
    """Repository for order assigner-related database operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def count_active_assignments_by_worker(self, worker_id: UUID) -> int:
        """Count active order assignments for a worker

        Active assignments are those with status:
        - assigned
        - pick_up
        - in_progress

        Args:
            worker_id: Worker (user) ID

        Returns:
            Number of active assignments
        """
        result = await self.db.execute(
            select(func.count(OrderAssigner.id))
            .where(
                OrderAssigner.worker_id == worker_id,
                OrderAssigner.deleted_at.is_(None),
                OrderAssigner.status.in_([
                    OrderAssignerStatus.assigned,
                    OrderAssignerStatus.pick_up,
                    OrderAssignerStatus.in_progress
                ])
            )
        )
        return result.scalar() or 0

    async def get_order_by_id(self, order_id: UUID) -> Optional[Order]:
        """Get order by ID

        Args:
            order_id: Order ID

        Returns:
            Order object or None
        """
        result = await self.db.execute(
            select(Order).where(
                Order.id == order_id,
                Order.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_order_by_order_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number

        Args:
            order_number: Order number

        Returns:
            Order object or None
        """
        result = await self.db.execute(
            select(Order).where(
                Order.order_number == order_number,
                Order.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID

        Args:
            user_id: User ID

        Returns:
            User object or None
        """
        result = await self.db.execute(
            select(User).where(
                User.id == user_id,
                User.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_assignment_by_order_and_worker(
        self,
        order_id: UUID,
        worker_id: UUID
    ) -> Optional[OrderAssigner]:
        """Get existing assignment by order and worker

        Args:
            order_id: Order ID
            worker_id: Worker (user) ID

        Returns:
            OrderAssigner object or None
        """
        result = await self.db.execute(
            select(OrderAssigner).where(
                OrderAssigner.order_id == order_id,
                OrderAssigner.worker_id == worker_id,
                OrderAssigner.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def create_assignment(
        self,
        order_id: UUID,
        worker_id: UUID,
        status: OrderAssignerStatus = OrderAssignerStatus.assigned
    ) -> OrderAssigner:
        """Create a new order assignment

        Args:
            order_id: Order ID
            worker_id: Worker (user) ID
            status: Assignment status (default: assigned)

        Returns:
            Created OrderAssigner object
        """
        assignment = OrderAssigner(
            order_id=order_id,
            worker_id=worker_id,
            status=status
        )
        self.db.add(assignment)
        await self.db.flush()
        await self.db.refresh(assignment)
        return assignment

    async def get_assignment_by_id(self, assignment_id: UUID) -> Optional[OrderAssigner]:
        """Get assignment by ID

        Args:
            assignment_id: Assignment ID

        Returns:
            OrderAssigner object or None
        """
        result = await self.db.execute(
            select(OrderAssigner).where(
                OrderAssigner.id == assignment_id,
                OrderAssigner.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()
