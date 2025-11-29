"""Guest service for business logic"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
import logging

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginationParams, paginate_query
from app.core.exceptions import ComposeError
from app.constants.error_codes import ErrorCode
from app.repositories.guest_repository import GuestRepository
from app.schemas.guest import GuestRegisterRequest, GuestRegisterResponse, GuestListItem
from app.schemas.response import StandardResponse, create_paginated_response, create_success_response
from app.models.user import User

logger = logging.getLogger(__name__)


class GuestService:
    """Service for guest registration and check-in"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = GuestRepository(db)

    async def register_guest(
        self,
        request: GuestRegisterRequest,
        user_id: Optional[UUID] = None,
        org_id: Optional[UUID] = None
    ) -> GuestRegisterResponse:
        """
        Register a new guest and create check-in

        Args:
            request: Guest registration request data
            user_id: User ID of the admin who is registering the guest
            org_id: Organization ID (optional)

        Returns:
            GuestRegisterResponse: Registration and check-in details

        Raises:
            HTTPException: If guest role not found or room not available
        """
        # Get guest role
        guest_role = await self.repository.get_guest_role()
        if not guest_role:
            raise ComposeError(
                error_code=ErrorCode.Guest.GUEST_ROLE_NOT_FOUND,
                message="Guest role not found in system. Please contact administrator.",
                http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Get room by number
        room = await self.repository.get_room_by_number(request.room_number, org_id)
        if not room:
            raise ComposeError(
                error_code=ErrorCode.Guest.ROOM_NOT_FOUND,
                message=f"Room {request.room_number} not found",
                http_status_code=status.HTTP_404_NOT_FOUND
            )

        # Check if room is available
        if room.is_booked:
            raise ComposeError(
                error_code=ErrorCode.Guest.ROOM_ALREADY_BOOKED,
                message=f"Room {request.room_number} is already booked",
                http_status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check if user with this phone number already exists
            existing_user = await self.repository.get_user_by_phone(request.phone_number)

            if existing_user:
                # User has stayed at the hotel before, reuse existing data
                logger.info(f"Found existing user with phone {request.phone_number}, reusing user data")
                user = existing_user
            else:
                # Create new guest user
                logger.info(f"Creating new guest user with phone {request.phone_number}")
                user = await self.repository.create_guest_user(
                    name=request.full_name,
                    email=request.email,
                    phone=request.phone_number,
                    role_id=guest_role.id,
                    org_id=org_id
                )

            # Create check-in with current time
            current_time = datetime.now().time()
            checkin = await self.repository.create_checkin(
                room_id=room.id,
                checkin_date=request.checkin_date,
                checkin_time=current_time,
                org_id=org_id or room.org_id,
                guest_id=user.id,
                admin_id=user_id
            )

            # Update room status to booked
            await self.repository.update_room_booked_status(room.id, True)

            # Commit transaction (only if everything above succeeded)
            await self.db.commit()
            logger.info(f"Guest registration completed successfully for {user.name}")

            # Return response
            return GuestRegisterResponse(
                user_id=user.id,
                checkin_id=checkin.id,
                full_name=user.name,
                room_number=room.room_number,
                checkin_date=request.checkin_date,
                email=request.email,
                phone_number=user.mobile_phone,
                status=checkin.status
            )

        except ComposeError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise ComposeError(
                error_code=ErrorCode.Guest.REGISTRATION_FAILED,
                message="Failed to register guest. Please try again or contact support.",
                http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                original_error=e
            )

    async def list_guests(
        self,
        org_id: UUID,
        params: PaginationParams
    ) -> StandardResponse[List[GuestListItem]]:
        """
        List guests for an organization with pagination

        Args:
            org_id: Organization ID to filter guests
            params: Pagination parameters (page, per_page, keyword, order)

        Returns:
            StandardResponse[List[GuestListItem]]: Standard response with paginated list of guests
        """
        # Get base query for guests in the organization
        query = self.repository.get_guests_query(org_id)

        # Apply pagination, search, and ordering
        result = await paginate_query(
            db=self.db,
            query=query,
            params=params,
            model=User,
            search_fields=["name", "email", "mobile_phone"]
        )

        # Convert User objects to GuestListItem
        guest_items = [
            GuestListItem(
                id=user.id,
                name=user.name,
                email=user.email,
                mobile_phone=user.mobile_phone,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in result.data
        ]

        # Return standard response with pagination
        return create_paginated_response(
            data=guest_items,
            page=result.meta.page,
            per_page=result.meta.per_page,
            total=result.meta.total
        )

    async def checkout_guest(
        self,
        guest_id: UUID
    ) -> StandardResponse[dict]:
        """
        Checkout a guest by terminating their session

        This method will:
        1. Check if guest has any incomplete orders (pending, assigned, in_progress)
        2. If incomplete orders exist, raise an error
        3. Get the active session for the guest
        4. Terminate the session
        5. Return success response

        Args:
            guest_id: Guest user ID to checkout

        Returns:
            StandardResponse[dict]: Success response with checkout details

        Raises:
            ComposeError: If guest not found, incomplete orders exist, or session not found
        """
        # Check if guest exists
        guest = await self.repository.get_user_by_id(guest_id)
        if not guest:
            raise ComposeError(
                error_code=ErrorCode.Guest.GUEST_NOT_FOUND,
                message=f"Guest with ID {guest_id} not found",
                http_status_code=status.HTTP_404_NOT_FOUND
            )

        # Check if guest has incomplete orders
        incomplete_orders = await self.repository.get_incomplete_orders_by_guest_id(guest_id)
        if incomplete_orders:
            order_numbers = [order.order_number for order in incomplete_orders]
            raise ComposeError(
                error_code=ErrorCode.Guest.INCOMPLETE_ORDERS_EXIST,
                message=f"Guest has incomplete orders that must be completed before checkout. Order numbers: {', '.join(order_numbers)}",
                http_status_code=status.HTTP_400_BAD_REQUEST
            )

        # Get active session for the guest
        session = await self.repository.get_active_session_by_user_id(guest_id)
        if not session:
            raise ComposeError(
                error_code=ErrorCode.Guest.SESSION_NOT_FOUND,
                message=f"Active session not found for guest {guest_id}",
                http_status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            # Terminate the session
            terminated_session = await self.repository.terminate_session(session.id)
            if not terminated_session:
                raise ComposeError(
                    error_code=ErrorCode.Guest.SESSION_NOT_FOUND,
                    message=f"Failed to terminate session {session.id}",
                    http_status_code=status.HTTP_404_NOT_FOUND
                )

            # Get checkin room to find the room_id
            checkin_room = await self.repository.get_checkin_room_by_id(session.checkin_room_id)
            if checkin_room and checkin_room.room_id:
                # Update room status to not booked
                await self.repository.update_room_booked_status(checkin_room.room_id, False)
                logger.info(f"Room {checkin_room.room_id} status updated to not booked for guest {guest_id}")

            # Commit transaction
            await self.db.commit()
            logger.info(f"Guest {guest_id} checked out successfully. Session {session.id} terminated.")

            # Return success response
            return create_success_response(
                data={
                    "guest_id": str(guest_id),
                    "session_id": str(terminated_session.id),
                    "status": "checked_out",
                    "session_terminated_at": terminated_session.end.isoformat() if terminated_session.end else None,
                    "session_duration_seconds": terminated_session.duration
                },
                message="Guest checked out successfully"
            )

        except ComposeError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to checkout guest {guest_id}: {str(e)}", exc_info=True)
            raise ComposeError(
                error_code=ErrorCode.Guest.CHECKOUT_FAILED,
                message="Failed to checkout guest. Please try again or contact support.",
                http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                original_error=e
            )
