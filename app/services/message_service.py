"""Message service for handling message operations"""
import logging
from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginationParams, paginate_query
from app.repositories.guest_repository import GuestRepository
from app.models.message import Message
from app.schemas.message import MessageItem
from app.schemas.response import StandardResponse, create_paginated_response

logger = logging.getLogger(__name__)


class MessageService:
    """Service for handling message operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = GuestRepository(db)

    async def list_messages(
        self,
        session_id: UUID,
        params: PaginationParams
    ) -> StandardResponse[List[MessageItem]]:
        """
        Get paginated list of messages for a session, ordered by created_at ascending (oldest first).

        Args:
            session_id: Session ID to filter messages
            params: Pagination parameters (page, per_page, keyword, order)

        Returns:
            StandardResponse[List[MessageItem]]: Standard response with paginated list of messages
        """
        # Get base query for messages with session_id filter
        query = self.repository.get_messages_query(session_id)

        # Apply pagination, search, and ordering
        # Default order is created_at:asc (oldest first) if no order specified
        if not params.order:
            params.order = "created_at:asc"

        result = await paginate_query(
            db=self.db,
            query=query,
            params=params,
            model=Message,
            search_fields=["text"]  # Allow searching in message text
        )

        # Convert Message models to MessageItem schemas
        message_items = [
            MessageItem(
                id=str(message.id),
                role=message.role.value,
                message=message.text
            )
            for message in result.data
        ]

        # Return standard response with pagination
        return create_paginated_response(
            data=message_items,
            page=result.meta.page,
            per_page=result.meta.per_page,
            total=result.meta.total
        )
