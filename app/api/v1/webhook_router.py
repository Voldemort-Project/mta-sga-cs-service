from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ComposeError
from typing import List
from uuid import UUID
from fastapi import Query

from app.schemas.webhook import (
    WahaWebhookRequest,
    WahaWebhookResponse,
    OrderWebhookRequest,
    OrderWebhookResponse,
    SendMessageRequest
)
from app.schemas.response import StandardResponse, create_success_response
from app.schemas.order import OrderListItem
from app.services.webhook_service import WebhookService
from app.services.order_webhook_service import OrderWebhookService
from app.services.order_service import OrderService
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
    Webhook endpoint to receive order creation requests (supports bulk insert).

    This endpoint receives order data and creates one or more orders in the system.
    It is separate from the WAHA webhook endpoint.

    Request body:
    - session_id (required): Session ID
    - orders (required): List of orders, each with:
      - category (required): Order category ('housekeeping', 'room_service', 'maintenance', or 'concierge')
      - items (required): List of order items, each with title, description (optional), qty (optional), price (optional)
      - note (optional): Order note
      - additional_note (optional): Additional order note
    """
    try:
        # Log the incoming webhook
        logger.info(
            f"Received order webhook: session_id={webhook_data.session_id}, "
            f"orders_count={len(webhook_data.orders)}"
        )

        # Create orders via service
        order_service = OrderWebhookService(db)
        order_numbers = await order_service.create_order_from_webhook(webhook_data)

        return OrderWebhookResponse(
            status="success",
            message=f"{len(order_numbers)} order(s) created successfully",
            order_numbers=order_numbers
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
    The message is recorded in the database as a System message if the
    session mode is 'agent' and status is not 'terminated'.

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

        # Use webhook service to handle the business logic
        webhook_service = WebhookService(db)
        await webhook_service.send_message(
            session_id=webhook_data.session_id,
            message=webhook_data.message
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


@router.get("/orders", response_model=StandardResponse[List[OrderListItem]])
async def list_orders_by_session(
    request: Request,
    session_id: UUID = Query(..., description="Session ID to filter orders"),
    db: AsyncSession = Depends(get_db)
):
    """
    List orders by session_id.

    This endpoint retrieves orders based on session_id, joins with session table.
    The response includes:
    - Order details
    - Order items
    - Guest user information
    - Organization information
    - Room information (via session -> checkin_room -> room)
    - Session information

    Query parameters:
    - session_id (required): Session ID to filter orders

    Example:
    ```
    GET /webhook/orders?session_id=123e4567-e89b-12d3-a456-426614174000
    ```
    """
    try:
        # Log the incoming request
        logger.info(f"Received list orders request: session_id={session_id}")

        # Use order service to handle the business logic
        order_service = OrderService(db)
        return await order_service.list_orders_by_session(session_id=session_id)

    except ComposeError:
        # Let ComposeError pass through to be handled by error handler middleware
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing orders by session: {str(e)}", exc_info=True)
        # Re-raise to let general exception handler handle it
        raise


@router.get("/orders/{order_number}", response_model=StandardResponse[OrderListItem])
async def get_order_detail(
    request: Request,
    order_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get order detail by order_number.

    This endpoint retrieves a single order by order_number with all relationships.
    The response includes:
    - Order details
    - Order items
    - Guest user information
    - Organization information
    - Room information (via session -> checkin_room -> room)
    - Session information

    Path parameters:
    - order_number (required): Order number to retrieve

    Example:
    ```
    GET /webhook/orders/1234567890
    ```
    """
    try:
        # Log the incoming request
        logger.info(f"Received get order detail request: order_number={order_number}")

        # Use order service to handle the business logic
        order_service = OrderService(db)
        return await order_service.get_order_detail_by_order_number(order_number=order_number)

    except ComposeError:
        # Let ComposeError pass through to be handled by error handler middleware
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting order detail: {str(e)}", exc_info=True)
        # Re-raise to let general exception handler handle it
        raise
