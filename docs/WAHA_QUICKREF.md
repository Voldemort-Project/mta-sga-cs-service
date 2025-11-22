# WAHA Integration - Quick Reference

## Configuration (.env)

```env
WAHA_HOST=http://localhost:3000
WAHA_API_PATH=/api/sendText
WAHA_SESSION=default
WAHA_API_KEY=your-secret-api-key-here
```

> **Note:** `WAHA_API_KEY` is optional. Leave empty if WAHA doesn't require authentication.

## Features

✅ Auto welcome message saat guest check-in
✅ Auto-reply untuk pesan guest
✅ Semua chat tersimpan di database
✅ Session management otomatis

## Flow

### 1. Guest Registration
```
POST /api/v1/guests/register
  ↓
Create User → Create CheckIn → Create Session
  ↓
Save Welcome Message (DB)
  ↓
Send Welcome Message (WhatsApp) ✅
```

### 2. Incoming Message
```
Guest sends WhatsApp → WAHA → POST /api/v1/waha/webhook
  ↓
Find User & Session
  ↓
Save Guest Message (role: User)
  ↓
Save Auto-Reply (role: System)
  ↓
Send Auto-Reply (WhatsApp) ✅
```

## Phone Format

| Context | Format | Example |
|---------|--------|---------|
| Database | `0xxxxxxxxxx` | `081234567890` |
| WAHA API | `62xxxxxxxxx@c.us` | `6281234567890@c.us` |

Auto-converted by service ✅

## Database Tables

### sessions
- `id` - UUID primary key
- `session_id` - FK to users (guest)
- `checkin_room_id` - FK to checkin_rooms
- `is_active` - Boolean
- `start` / `end` - Timestamps

### messages
- `id` - UUID primary key
- `session_id` - FK to sessions
- `role` - Enum: `User` | `System`
- `text` - Message content

## API Examples

### Register Guest (triggers welcome message)

```bash
curl -X POST http://localhost:8000/api/v1/guests/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "room_number": "101",
    "checkin_date": "2025-11-22",
    "email": "john@example.com",
    "phone_number": "081234567890"
  }'
```

### Webhook (from WAHA)

```bash
curl -X POST http://localhost:8000/api/v1/waha/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event": "message",
    "payload": {
      "from": "6281234567890@c.us",
      "body": "Hello, need help",
      "fromMe": false
    }
  }'
```

## Code Usage

### Send Message

```python
from app.integrations.waha import WahaService

waha = WahaService()
await waha.send_text_message("081234567890", "Hello!")
```

### Create Session & Message

```python
from app.repositories.guest_repository import GuestRepository
from app.models.message import MessageRole

repo = GuestRepository(db)

# Create session
session = await repo.create_session(user_id, checkin_id)

# Create message
message = await repo.create_message(
    session_id=session.id,
    role=MessageRole.System,
    text="Welcome!"
)
```

## Message Templates

**Welcome:**
```
Halo {name}! 👋
Selamat datang di hotel kami.
Anda telah check-in di kamar {room}.
...
```

**Auto-Reply:**
```
Terima kasih atas pesan Anda. 🙏
Tim kami akan segera merespons.
Waktu respon normal: 5-10 menit
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No WA message | Check WAHA service, logs show error |
| User not found | Verify phone format in DB |
| No auto-reply | Check webhook reachable, session active |
| WAHA connection | Verify WAHA_HOST, service running |

## Files Modified/Created

### Created:
- `app/integrations/waha/waha_service.py` - WAHA API client
- `app/integrations/waha/__init__.py` - Package init
- `app/services/webhook_service.py` - Webhook handler

### Modified:
- `app/core/config.py` - Added WAHA config
- `app/services/guest_service.py` - Added session & welcome msg
- `app/repositories/guest_repository.py` - Added session/message methods
- `app/api/v1/webhook_router.py` - Added webhook handling

## Next Steps

1. ✅ Set WAHA config in `.env`
2. ✅ Run migrations (if any)
3. ✅ Start WAHA service
4. ✅ Test guest registration
5. ✅ Test webhook with real WhatsApp

## Links

- Full Documentation: `docs/WAHA_INTEGRATION.md`
- WAHA Docs: https://waha.devlike.pro/
