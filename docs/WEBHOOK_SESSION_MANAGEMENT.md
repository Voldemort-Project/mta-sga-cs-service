# Webhook Session Management

## Overview

This document describes the session management flow implemented in the webhook service for handling incoming WhatsApp messages.

## Flow Description

### 1. Session Detection and Management

When a WhatsApp message is received from a guest, the system:

1. **Finds the user** by phone number
2. **Checks for active session**:
   - If no session exists → Create new session
   - If session exists → Check if expired (last updated > 30 minutes)
     - If expired → Terminate old session and create new session
     - If not expired → Use existing session

### 2. New Session Creation Flow

When a new session needs to be created, the system:

1. **Gets active checkin room** for the guest user
2. **Creates new session** with:
   - Status: `open`
   - Mode: `agent`
   - Linked to user and checkin room
3. **Creates H2H agent** via Agent Router API
   - Uses session ID as `identifier_id`
   - Continues even if agent creation fails (logged but non-blocking)
4. **Sends welcome message** via WAHA
   - Saves message to database with `System` role
   - Sends via WhatsApp with personalized greeting

### 3. Message Processing

After ensuring an active session exists:

1. **Saves incoming message** to database with `User` role
2. **Creates auto-reply message**:
   - "Terima kasih atas pesan Anda..." (Thank you for your message...)
   - Saved to database with `System` role
3. **Sends auto-reply** via WAHA to WhatsApp

## Key Features

### Session Expiration (30 Minutes)

Sessions automatically expire after 30 minutes of inactivity (based on `updated_at` timestamp). This ensures:
- Fresh agent context for new conversations
- Proper session lifecycle management
- Clean conversation history

### Error Handling

The implementation includes robust error handling:
- **Agent creation failures**: Logged but don't block session creation
- **Welcome message failures**: Logged but don't block message processing
- **WAHA send failures**: Logged but don't fail database operations
- **Database rollbacks**: Triggered on any message processing errors

### Timezone Awareness

All datetime comparisons use timezone-aware UTC timestamps to ensure consistency across different server environments.

## Code Changes

### Files Modified

1. **`app/services/webhook_service.py`**:
   - Added `H2HAgentRouterService` integration
   - Added `_create_new_session_with_agent()` helper method
   - Updated `handle_incoming_message()` with session management logic

2. **`app/repositories/guest_repository.py`**:
   - Added `get_active_checkin_by_guest_id()` method to find active checkin room for guest users

## Message Examples

### Welcome Message (Bahasa Indonesia)

```
Halo {user_name}! 👋

Selamat datang kembali! Kami siap membantu Anda.

Jika Anda membutuhkan bantuan atau memiliki pertanyaan,
silakan kirim pesan dan kami akan segera merespons.

Terima kasih! 🏨
```

### Auto-Reply Message (Bahasa Indonesia)

```
Terima kasih atas pesan Anda. 🙏

Tim kami akan segera merespons pertanyaan Anda.
Mohon menunggu sebentar.

Waktu respon normal: 5-10 menit
```

## Integration Points

### H2H Agent Router

- **Endpoint**: Configured via `h2h_agent_router_host` and `h2h_agent_router_path` in settings
- **Authentication**: Uses `h2h_agent_router_api_key` (X-API-Key header)
- **Payload**: `{ "identifier_id": "<session_id>" }`

### WAHA (WhatsApp HTTP API)

- **Endpoint**: Configured via `waha_host` and `waha_api_path` in settings
- **Authentication**: Uses `waha_api_key` (X-API-Key header)
- **Phone Format**: Converts local format (081234567890) to international (6281234567890@c.us)

## Configuration

Required environment variables:

```env
# H2H Agent Router
H2H_AGENT_ROUTER_HOST=http://localhost:8000
H2H_AGENT_ROUTER_PATH=/v2/agents/create
H2H_AGENT_ROUTER_API_KEY=your-api-key

# WAHA
WAHA_HOST=http://localhost:3000
WAHA_API_PATH=/api/sendText
WAHA_SESSION=default
WAHA_API_KEY=your-api-key
```

## Testing Considerations

When testing this flow:

1. **First message**: Should create new session and send welcome message
2. **Follow-up messages (< 30 min)**: Should use existing session, no welcome message
3. **Messages after 30 min**: Should terminate old session, create new session, send welcome message
4. **Agent creation failure**: Should still create session and send welcome message
5. **WAHA send failure**: Should still save messages to database

## Future Improvements

Potential enhancements:

1. Make session timeout configurable (currently hardcoded to 30 minutes)
2. Add metrics/monitoring for agent creation success rate
3. Add retry logic for failed H2H agent creation
4. Support different welcome message templates based on guest preferences
5. Add session resumption notification (different from first welcome)
