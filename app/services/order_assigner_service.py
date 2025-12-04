"""OrderAssigner service for business logic"""
from uuid import UUID
import logging

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ComposeError
from app.constants.error_codes import ErrorCode
from app.repositories.order_assigner_repository import OrderAssignerRepository
from app.schemas.order import OrderAssignerResponse
from app.schemas.response import StandardResponse, create_success_response
from app.models.order import OrderStatus
from app.models.order_assigner import OrderAssignerStatus

logger = logging.getLogger(__name__)

# Maximum number of active orders a worker can handle
MAX_ACTIVE_ORDERS_PER_WORKER = 5


class OrderAssignerService:
    """Service for order assignment operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = OrderAssignerRepository(db)

    async def assign_order_to_worker(
        self,
        order_number: str,
        worker_id: UUID
    ) -> StandardResponse[OrderAssignerResponse]:
        """
        Assign an order to a worker

        Business rules:
        - Order must exist and not be deleted
        - Worker must exist and not be deleted
        - Worker can only have maximum 5 active orders at a time
          (active = assigned, pick_up, or in_progress status)
        - Order cannot be already assigned to the same worker

        Args:
            order_number: Order number to assign
            worker_id: Worker (user) ID to assign the order to

        Returns:
            StandardResponse[OrderAssignerResponse]: Standard response with created assignment information

        Raises:
            ComposeError: If validation fails or assignment cannot be created
        """
        try:
            # Check if order exists
            order = await self.repository.get_order_by_order_number(order_number)
            if not order:
                raise ComposeError(
                    error_code=ErrorCode.OrderAssigner.ORDER_NOT_FOUND,
                    message="Order not found",
                    http_status_code=status.HTTP_404_NOT_FOUND
                )

            # Get order_id from the order object
            order_id = order.id

            # Check if worker exists
            worker = await self.repository.get_user_by_id(worker_id)
            if not worker:
                raise ComposeError(
                    error_code=ErrorCode.OrderAssigner.WORKER_NOT_FOUND,
                    message="Worker not found",
                    http_status_code=status.HTTP_404_NOT_FOUND
                )

            # Check if order is already assigned to this worker
            existing_assignment = await self.repository.get_assignment_by_order_and_worker(
                order_id=order_id,
                worker_id=worker_id
            )
            if existing_assignment:
                raise ComposeError(
                    error_code=ErrorCode.OrderAssigner.ORDER_ALREADY_ASSIGNED,
                    message="Order is already assigned to this worker",
                    http_status_code=status.HTTP_400_BAD_REQUEST
                )

            # Check if worker has reached maximum active orders limit
            active_count = await self.repository.count_active_assignments_by_worker(worker_id)
            if active_count >= MAX_ACTIVE_ORDERS_PER_WORKER:
                raise ComposeError(
                    error_code=ErrorCode.OrderAssigner.WORKER_MAX_ORDERS_REACHED,
                    message=f"Worker has reached the maximum limit of {MAX_ACTIVE_ORDERS_PER_WORKER} active orders",
                    http_status_code=status.HTTP_400_BAD_REQUEST
                )

            # Create the assignment
            assignment = await self.repository.create_assignment(
                order_id=order_id,
                worker_id=worker_id,
                status=OrderAssignerStatus.assigned
            )

            # Update order status to "assigned" if it's still "pending"
            # if order.status == OrderStatus.pending:
            #     order.status = OrderStatus.assigned
            #     self.db.add(order)

            # Commit transaction
            await self.db.commit()
            await self.db.refresh(assignment)

            logger.info(
                f"Order assigned successfully: order_id={order_id}, "
                f"worker_id={worker_id}, assignment_id={assignment.id}"
            )

            # Return response
            response_data = OrderAssignerResponse(
                id=assignment.id,
                order_id=assignment.order_id,
                worker_id=assignment.worker_id,
                assigned_at=assignment.assigned_at,
                status=assignment.status,
                created_at=assignment.created_at,
                updated_at=assignment.updated_at
            )

            return create_success_response(
                data=response_data,
                message="Order assigned to worker successfully"
            )

        except ComposeError:
            # Re-raise ComposeError as-is
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error assigning order to worker: {str(e)}", exc_info=True)
            raise ComposeError(
                error_code=ErrorCode.OrderAssigner.ASSIGNMENT_FAILED,
                message="Failed to assign order to worker. Please try again or contact support.",
                http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                original_error=e
            )
