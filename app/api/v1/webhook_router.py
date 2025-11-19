from fastapi import APIRouter, Request, HTTPException
from app.schemas.webhook import WahaWebhookRequest, WahaWebhookResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhook/waha", response_model=WahaWebhookResponse)
async def waha_webhook(request: Request, webhook_data: WahaWebhookRequest):
    """
    Webhook endpoint to receive callbacks from WAHA service.

    This endpoint receives WhatsApp message events and other notifications
    from the WAHA (WhatsApp HTTP API) service.
    """
    try:
        # Log the incoming webhook
        logger.info(f"Received WAHA webhook: event={webhook_data.event}, session={webhook_data.session}")
        logger.info(f"Webhook payload: {webhook_data.model_dump_json()}")

        # Handle different event types
        if webhook_data.event == "message":
            await handle_message_event(webhook_data)
        else:
            logger.info(f"Unhandled event type: {webhook_data.event}")

        return WahaWebhookResponse(
            status="success",
            message="Webhook received and processed successfully"
        )

    except Exception as e:
        logger.error(f"Error processing WAHA webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


async def handle_message_event(webhook_data: WahaWebhookRequest):
    """
    Handle incoming message events from WAHA.

    Args:
        webhook_data: The webhook data containing the message payload
    """
    payload = webhook_data.payload

    # Log message details
    logger.info(
        f"Processing message: from={payload.from_}, "
        f"body={payload.body}, hasMedia={payload.hasMedia}, "
        f"fromMe={payload.fromMe}"
    )

    # TODO: Implement your business logic here
    # For example:
    # - Store the message in database
    # - Trigger automated responses
    # - Forward to relevant handlers
    # - Process media if present

    if payload.hasMedia and payload.media:
        logger.info(f"Message contains media: {payload.media.mimetype}")

    if payload.replyTo:
        logger.info(f"Message is a reply to: {payload.replyTo.id}")
