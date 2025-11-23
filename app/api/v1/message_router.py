"""Message router for message-related endpoints"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.pagination import PaginationParams
from app.schemas.message import MessageItem
from app.schemas.response import StandardResponse
from app.services.message_service import MessageService

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.get(
    "",
    response_model=StandardResponse[List[MessageItem]],
    status_code=status.HTTP_200_OK,
    summary="List History Messages",
    description="Get paginated list of messages for a session, ordered by created_at ascending (oldest first) by default"
)
async def list_messages(
    session_id: UUID = Query(..., description="Session ID (required)"),
    page: int = Query(1, ge=1, description="Current page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    keyword: Optional[str] = Query(None, description="Search keyword (searches in message text)"),
    order: Optional[str] = Query(None, description="Order string (e.g., 'created_at:desc'). Default is 'created_at:asc'"),
    db: AsyncSession = Depends(get_db)
) -> StandardResponse[List[MessageItem]]:
    """
    Get paginated list of messages for a session.

    This endpoint retrieves messages for a given session_id from the messages table,
    with pagination support. By default, messages are ordered by created_at ascending
    (oldest messages first).

    Args:
        session_id: Session ID (required query parameter)
        page: Page number (starts from 1)
        per_page: Number of items per page (1-100)
        keyword: Optional search keyword to filter by message text
        order: Optional order string in format "field:direction"
               e.g., "created_at:desc". Default is "created_at:asc"
        db: Database session dependency

    Returns:
        StandardResponse[List[MessageItem]]: Paginated list of messages with id, role, and message fields

    Raises:
        200: Success with paginated list of messages
    """
    # Create pagination params
    params = PaginationParams(
        page=page,
        per_page=per_page,
        keyword=keyword,
        order=order
    )

    service = MessageService(db)
    return await service.list_messages(session_id=session_id, params=params)
