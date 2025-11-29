# Webhook Session Management - Quick Reference

## Flow Diagram

```
Incoming WhatsApp Message
         |
         v
   Find User by Phone
         |
         v
   Check Active Session
         |
    +----+----+
    |         |
   YES       NO
    |         |
    v         v
Check Exp.  Create
    |       Session
    |         |
+---+---+     |
|       |     |
NO     YES    |
|       |     |
|       v     v
|   Terminate Old
|   Create New
|       |
+-------+
    |
    v
[Session Ready]
    |
    v
Save Message
    +
Auto-Reply
```

## Key Components

### 1. Session Expiration Check

```python
# Session expires after 30 minutes of inactivity
if time_since_update > timedelta(minutes=30):
    # Terminate old session
    # Create new session
```

### 2. New Session Creation Steps

```
1. Get active checkin room for user
2. Create session (status=open, mode=agent)
3. Create H2H agent (session_id as identifier)
4. Send welcome message via WAHA
```

### 3. Message Processing

```
1. Save incoming message (role=User)
2. Create auto-reply (role=System)
3. Send auto-reply via WAHA
```

## Code Locations

| Component | File | Line |
|-----------|------|------|
| Session Management | `app/services/webhook_service.py` | 102-186 |
| Session Creation | `app/services/webhook_service.py` | 41-100 |
| Get Active Checkin | `app/repositories/guest_repository.py` | 187-209 |
| H2H Agent Service | `app/integrations/h2h/h2h_service.py` | 22-97 |

## Error Handling

| Scenario | Behavior |
|----------|----------|
| User not found | Log warning, return early |
| No active checkin | Log error, return early |
| Agent creation fails | Log error, continue with welcome message |
| Welcome message fails | Log error, continue with processing |
| WAHA send fails | Log error, don't rollback DB |
| Message processing fails | Rollback DB, raise exception |

## Configuration

```bash
# Required environment variables
H2H_AGENT_ROUTER_HOST=http://localhost:8000
H2H_AGENT_ROUTER_PATH=/v2/agents/create
H2H_AGENT_ROUTER_API_KEY=your-key

WAHA_HOST=http://localhost:3000
WAHA_API_PATH=/api/sendText
WAHA_API_KEY=your-key
```

## Testing Checklist

- [ ] First message from guest → Creates new session
- [ ] First message from guest → Creates H2H agent
- [ ] First message from guest → Sends welcome message
- [ ] Message within 30 min → Uses existing session
- [ ] Message within 30 min → No welcome message
- [ ] Message after 30 min → Terminates old session
- [ ] Message after 30 min → Creates new session
- [ ] Message after 30 min → Sends welcome message
- [ ] H2H failure → Session still created
- [ ] WAHA failure → Message still saved to DB

## Phone Number Formats

| Context | Format | Example |
|---------|--------|---------|
| Database (local) | 081234567890 | Leading 0 |
| WAHA (international) | 6281234567890 | Country code 62 |
| WhatsApp chatId | 6281234567890@c.us | With @c.us |

## Session Statuses

| Status | Description |
|--------|-------------|
| `open` | Active session, can receive messages |
| `terminated` | Ended session, no longer active |

## Session Modes

| Mode | Description |
|------|-------------|
| `agent` | AI agent handles conversation |
| `manual` | Human agent handles conversation |

## New Session Trigger Events

1. **No session exists** for user
2. **Session expired** (updated_at > 30 minutes ago)

Both triggers result in:
- Old session terminated (if exists)
- New session created
- H2H agent created
- Welcome message sent
