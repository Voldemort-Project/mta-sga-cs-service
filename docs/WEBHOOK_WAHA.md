# WAHA Webhook Endpoint

This document describes the WAHA (WhatsApp HTTP API) webhook endpoint implementation.

## Endpoint

```
POST /webhook/waha
```

## Overview

This endpoint receives webhooks/callbacks from the WAHA service for WhatsApp events, primarily message events.

## Request Headers

```
Content-Type: application/json
```

## Request Body

The endpoint accepts a JSON payload with the following structure:

```json
{
  "id": "evt_01aaaaaaaaaaaaaaaaaaaaaaaa",
  "timestamp": 1634567890123,
  "session": "default",
  "metadata": {
    "user.id": "123",
    "user.email": "email@example.com"
  },
  "engine": "WEBJS",
  "event": "message",
  "payload": {
    "id": "false_11111111111@c.us_AAAAAAAAAAAAAAAAAAAA",
    "timestamp": 1666943582,
    "from": "11111111111@c.us",
    "fromMe": true,
    "source": "api",
    "to": "11111111111@c.us",
    "participant": "string",
    "body": "string",
    "hasMedia": true,
    "media": {
      "url": "http://localhost:3000/api/files/false_11111111111@c.us_AAAAAAAAAAAAAAAAAAAA.oga",
      "mimetype": "audio/jpeg",
      "filename": "example.pdf",
      "s3": {
        "Bucket": "my-bucket",
        "Key": "default/false_11111111111@c.us_AAAAAAAAAAAAAAAAAAAA.oga"
      },
      "error": null
    },
    "ack": -1,
    "ackName": "string",
    "author": "string",
    "location": {
      "latitude": "string",
      "longitude": "string",
      "live": true,
      "name": "string",
      "address": "string",
      "url": "string",
      "description": "string",
      "thumbnail": "string"
    },
    "vCards": ["string"],
    "_data": {},
    "replyTo": {
      "id": "AAAAAAAAAAAAAAAAAAAA",
      "participant": "11111111111@c.us",
      "body": "Hello!",
      "_data": {}
    }
  },
  "me": {
    "id": "11111111111@c.us",
    "lid": "123123@lid",
    "jid": "123123:123@s.whatsapp.net",
    "pushName": "string"
  },
  "environment": {
    "version": "YYYY.MM.BUILD",
    "engine": "WEBJS",
    "tier": "PLUS",
    "browser": "/usr/path/to/bin/google-chrome"
  }
}
```

## Response

### Success Response

**Status Code:** `200 OK`

```json
{
  "status": "success",
  "message": "Webhook received and processed successfully"
}
```

### Error Response

**Status Code:** `422 Unprocessable Entity`

Returned when the request body doesn't match the expected schema.

**Status Code:** `500 Internal Server Error`

```json
{
  "detail": "Error processing webhook: <error message>"
}
```

## Field Descriptions

### Root Level

- `id` (string, required): Unique event identifier
- `timestamp` (integer, required): Event timestamp in milliseconds
- `session` (string, required): WAHA session identifier
- `metadata` (object, optional): Custom metadata key-value pairs
- `engine` (string, required): WhatsApp engine being used (e.g., "WEBJS", "NOWEB")
- `event` (string, required): Event type (e.g., "message", "status", etc.)
- `payload` (object, required): Event-specific payload data
- `me` (object, required): Information about the bot/account
- `environment` (object, required): WAHA environment information

### Payload (Message Event)

- `id` (string, required): Message ID
- `timestamp` (integer, required): Message timestamp
- `from` (string, required): Sender's WhatsApp ID
- `fromMe` (boolean, required): Whether the message was sent by the bot
- `to` (string, required): Recipient's WhatsApp ID
- `body` (string, optional): Message text content
- `hasMedia` (boolean, optional): Whether message contains media
- `media` (object, optional): Media information if present
- `replyTo` (object, optional): Original message being replied to
- `location` (object, optional): Location data if message contains location
- `vCards` (array, optional): Contact cards if message contains contacts

## Event Types

Currently, the endpoint handles the following event types:

- `message`: Incoming or outgoing WhatsApp messages

## Implementation Details

The webhook endpoint:

1. Validates the incoming payload against the defined schema
2. Logs the event for monitoring and debugging
3. Routes different event types to appropriate handlers
4. Returns a success response immediately (webhook should be fast)

## Business Logic Customization

To customize the webhook behavior, modify the `handle_message_event` function in `/app/api/v1/webhook_router.py`:

```python
async def handle_message_event(webhook_data: WahaWebhookRequest):
    """
    Handle incoming message events from WAHA.

    Add your custom business logic here:
    - Store messages in database
    - Trigger automated responses
    - Forward to customer service agents
    - Process media files
    - etc.
    """
    pass
```

## Testing

Run the webhook tests:

```bash
uv run pytest tests/test_webhook.py -v
```

## Configuration in WAHA

To configure WAHA to send webhooks to this endpoint:

1. Set the webhook URL in your WAHA configuration:
   ```
   http://your-domain.com/webhook/waha
   ```

2. Configure which events to send (recommended: all message events)

3. Set up authentication if required (consider adding authentication middleware)

## Security Considerations

⚠️ **Important**: This endpoint currently doesn't have authentication. Consider adding:

1. **API Key validation**: Verify a secret token in the request headers
2. **IP whitelist**: Only allow requests from known WAHA server IPs
3. **Signature verification**: Verify webhook signatures if WAHA supports it
4. **Rate limiting**: Prevent abuse with rate limiting middleware

Example authentication header check:

```python
from fastapi import Header, HTTPException

@router.post("/webhook/waha")
async def waha_webhook(
    webhook_data: WahaWebhookRequest,
    x_webhook_secret: str = Header(None)
):
    if x_webhook_secret != settings.waha_webhook_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # ... rest of the handler
```

## Monitoring

The endpoint logs all incoming webhooks. Monitor these logs for:

- Webhook delivery success/failure
- Message processing errors
- Performance issues
- Unusual patterns or spam

## Related Documentation

- [WAHA Documentation](https://waha.devlike.pro/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
