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
from app.schemas.room import RoomListItem
from app.schemas.response import StandardResponse, create_paginated_response, create_success_response
from app.models.user import User
from app.integrations.h2h.h2h_service import H2HAgentRouterService
from app.utils.phone_utils import format_phone_number

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
            # Format phone number: remove '+' and replace leading '0' with '62'
            formatted_phone = format_phone_number(request.phone_number)
            logger.info(f"Formatted phone number from {request.phone_number} to {formatted_phone}")

            # Check if user with this phone number already exists
            existing_user = await self.repository.get_user_by_phone(formatted_phone)

            if existing_user:
                # User has stayed at the hotel before, reuse existing data
                logger.info(f"Found existing user with phone {formatted_phone}, reusing user data")
                user = existing_user
            else:
                # Create new guest user
                logger.info(f"Creating new guest user with phone {formatted_phone}")
                user = await self.repository.create_guest_user(
                    name=request.full_name,
                    email=request.email,
                    phone=formatted_phone,
                    role_id=guest_role.id,
                    org_id=org_id
                )

            # Create memory block for user via H2H Agent Router
            try:
                h2h_service = H2HAgentRouterService()
                await h2h_service.create_memory_block(user.id)
                logger.info(f"Memory block created successfully for user {user.id}")
            except Exception as e:
                # Log error but don't fail registration - memory block creation is not critical
                logger.warning(
                    f"Failed to create memory block for user {user.id}: {str(e)}",
                    exc_info=True
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

        # Convert User objects to GuestListItem (with checkin_rooms and filtered sessions)
        from app.models.session import SessionStatus

        guest_items = []
        for user in result.data:
            # Filter sessions to only include 'open' status
            open_sessions = [
                session for session in user.sessions
                if session.status == SessionStatus.open and session.deleted_at is None
            ]

            # Create dict from user and override sessions with filtered list
            user_dict = {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "mobile_phone": user.mobile_phone,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "checkin_rooms": user.checkin_rooms,
                "sessions": open_sessions
            }

            guest_items.append(GuestListItem.model_validate(user_dict))


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
        Checkout a guest by terminating their session (if exists)

        This method will:
        1. Check if guest has any incomplete orders (pending, assigned, in_progress)
        2. If incomplete orders exist, raise an error
        3. Get the active session for the guest (optional)
        4. If session exists, terminate it
        5. Update room status to not booked
        6. Return success response

        Args:
            guest_id: Guest user ID to checkout

        Returns:
            StandardResponse[dict]: Success response with checkout details

        Raises:
            ComposeError: If guest not found or incomplete orders exist
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

        # Get active session for the guest (optional)
        session = await self.repository.get_active_session_by_user_id(guest_id)

        try:
            session_id = None
            session_terminated_at = None
            session_duration_seconds = None

            # 1. Get active checkin by guest_id
            active_checkin = await self.repository.get_active_checkin_by_guest_id(guest_id)
            if not active_checkin:
                raise ComposeError(
                    error_code=ErrorCode.Guest.GUEST_NOT_FOUND,
                    message=f"No active checkin found for guest {guest_id}",
                    http_status_code=status.HTTP_404_NOT_FOUND
                )

            # 2. Update checkin with checkout information
            current_date = datetime.now().date()
            current_time = datetime.now().time()
            updated_checkin = await self.repository.update_checkin_checkout(
                checkin_room_id=active_checkin.id,
                checkout_date=current_date,
                checkout_time=current_time,
                status="checkout"
            )
            if updated_checkin:
                logger.info(f"Checkin {active_checkin.id} updated with checkout information for guest {guest_id}")

            # 3. Update room status to not booked
            if active_checkin.room_id:
                await self.repository.update_room_booked_status(active_checkin.room_id, False)
                logger.info(f"Room {active_checkin.room_id} status updated to not booked for guest {guest_id}")

            # 4. If session exists, terminate it
            if session:
                terminated_session = await self.repository.terminate_session(session.id)
                if terminated_session:
                    session_id = str(terminated_session.id)
                    session_terminated_at = terminated_session.end.isoformat() if terminated_session.end else None
                    session_duration_seconds = terminated_session.duration
                    logger.info(f"Session {session.id} terminated for guest {guest_id}")
                else:
                    logger.warning(f"Failed to terminate session {session.id} for guest {guest_id}")
            else:
                logger.info(f"No active session found for guest {guest_id}, skipping session termination")

            # Commit transaction
            await self.db.commit()
            logger.info(f"Guest {guest_id} checked out successfully")

            # Return success response
            return create_success_response(
                data={
                    "guest_id": str(guest_id),
                    "session_id": session_id,
                    "status": "checked_out",
                    "checkout_date": current_date.isoformat(),
                    "checkout_time": current_time.isoformat(),
                    "session_terminated_at": session_terminated_at,
                    "session_duration_seconds": session_duration_seconds
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

    async def get_available_rooms(self, org_id: UUID) -> StandardResponse[List[RoomListItem]]:
        """
        Get list of available rooms for an organization

        Args:
            org_id: Organization ID to filter rooms

        Returns:
            StandardResponse[List[RoomListItem]]: List of available rooms

        Raises:
            ComposeError: If there's an error fetching rooms
        """
        try:
            rooms = await self.repository.get_available_rooms(org_id)

            # Convert to schema
            room_items = [RoomListItem.model_validate(room) for room in rooms]

            return create_success_response(
                data=room_items,
                message=f"Found {len(room_items)} available room(s)"
            )
        except Exception as e:
            logger.error(f"Failed to fetch available rooms for org {org_id}: {str(e)}", exc_info=True)
            raise ComposeError(
                error_code=ErrorCode.Guest.ROOM_NOT_FOUND,
                message="Failed to fetch available rooms. Please try again.",
                http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                original_error=e
            )
