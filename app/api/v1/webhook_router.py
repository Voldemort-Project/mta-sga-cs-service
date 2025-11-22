from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.webhook import WahaWebhookRequest, WahaWebhookResponse
from app.services.webhook_service import WebhookService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhook/waha", response_model=WahaWebhookResponse)
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
