from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.core.exceptions import ComposeError
from app.constants.error_codes import ErrorCode
from app.schemas.webhook import (
    WahaWebhookRequest,
    WahaWebhookResponse,
    OrderWebhookRequest,
    OrderWebhookResponse,
    SendMessageRequest
)
from app.schemas.response import StandardResponse, create_success_response
from app.models.session import Session
from app.models.user import User
from app.services.webhook_service import WebhookService
from app.services.order_webhook_service import OrderWebhookService
from app.integrations.waha.waha_service import WahaService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["Webhook"])


@router.post("/waha", response_model=WahaWebhookResponse)
async def waha_webhook(
    request: Request,
    webhook_data: WahaWebhookRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook endpoint to receive callbacks from WAHA service.

    This endpoint receives WhatsApp message events and other notifications
    from the WAHA (WhatsApp HTTP API) service.
    """
    try:
        # Log the incoming webhook
        logger.info(f"Received WAHA webhook: event={webhook_data.event}, session={webhook_data.session}")
        logger.debug(f"Webhook payload: {webhook_data.model_dump_json()}")

        # Handle different event types
        if webhook_data.event == "message":
            await handle_message_event(webhook_data, db)
        else:
            logger.info(f"Unhandled event type: {webhook_data.event}")

        return WahaWebhookResponse(
            status="success",
            message="Webhook received and processed successfully"
        )

    except Exception as e:
        logger.error(f"Error processing WAHA webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


async def handle_message_event(webhook_data: WahaWebhookRequest, db: AsyncSession):
    """
    Handle incoming message events from WAHA.

    Args:
        webhook_data: The webhook data containing the message payload
        db: Database session
    """
    payload = webhook_data.payload

    # Log message details
    logger.info(
        f"Processing message: from={payload.from_}, "
        f"body={payload.body}, hasMedia={payload.hasMedia}, "
        f"fromMe={payload.fromMe}"
    )

    # Use webhook service to handle the message
    webhook_service = WebhookService(db)
    await webhook_service.handle_incoming_message(webhook_data)

    if payload.hasMedia and payload.media:
        logger.info(f"Message contains media: {payload.media.mimetype}")

    if payload.replyTo:
        logger.info(f"Message is a reply to: {payload.replyTo.id}")


@router.post("/order", response_model=OrderWebhookResponse)
async def order_webhook(
    request: Request,
    webhook_data: OrderWebhookRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook endpoint to receive order creation requests.

    This endpoint receives order data and creates an order in the system.
    It is separate from the WAHA webhook endpoint.

    Request body:
    - session_id (required): Session ID
    - category (required): Order category ('housekeeping', 'room_service', 'maintenance', or 'concierge')
    - items (required): List of order items, each with title, description (optional), qty (optional), price (optional)
    - note (optional): Order note
    - additional_note (optional): Additional order note
    """
    try:
        # Log the incoming webhook
        logger.info(
            f"Received order webhook: session_id={webhook_data.session_id}, "
            f"category={webhook_data.category}, items_count={len(webhook_data.items)}"
        )

        # Create order via service
        order_service = OrderWebhookService(db)
        order_id = await order_service.create_order_from_webhook(webhook_data)

        return OrderWebhookResponse(
            status="success",
            message="Order created successfully",
            order_id=order_id
        )

    except ComposeError:
        # Let ComposeError pass through to be handled by error handler middleware
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing order webhook: {str(e)}", exc_info=True)
        # Re-raise to let general exception handler handle it
        raise


@router.post("/send-message", response_model=StandardResponse[dict])
async def send_message(
    request: Request,
    webhook_data: SendMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook endpoint to send WhatsApp message to user via WAHA.

    This endpoint receives a session_id and message, retrieves the user's
    mobile phone number from the session, and sends the message via WAHA.

    Request body:
    - session_id (required): Session ID
    - message (required): Message text to send
    """
    try:
        # Log the incoming webhook
        logger.info(
            f"Received send-message webhook: session_id={webhook_data.session_id}, "
            f"message_length={len(webhook_data.message)}"
        )

        # Get session with joined user to get mobile_phone
        result = await db.execute(
            select(Session)
            .options(joinedload(Session.user))
            .where(
                Session.id == webhook_data.session_id,
                Session.deleted_at.is_(None)
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ComposeError(
                error_code=ErrorCode.General.NOT_FOUND,
                message=f"Session {webhook_data.session_id} not found",
                http_status_code=404
            )

        if not session.user:
            raise ComposeError(
                error_code=ErrorCode.General.NOT_FOUND,
                message=f"User not found for session {webhook_data.session_id}",
                http_status_code=404
            )

        if not session.user.mobile_phone:
            raise ComposeError(
                error_code=ErrorCode.General.BAD_REQUEST,
                message=f"User {session.user.id} does not have a mobile phone number",
                http_status_code=400
            )

        # Send message via WAHA
        waha_service = WahaService()
        await waha_service.send_text_message(
            phone_number=session.user.mobile_phone,
            text=webhook_data.message
        )

        logger.info(
            f"Message sent successfully to {session.user.mobile_phone} "
            f"for session {webhook_data.session_id}"
        )

        return create_success_response(
            data={"session_id": str(webhook_data.session_id)},
            message="Message sent successfully"
        )

    except ComposeError:
        # Let ComposeError pass through to be handled by error handler middleware
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing send-message webhook: {str(e)}", exc_info=True)
        # Re-raise to let general exception handler handle it
        raise
