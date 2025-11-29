# Webhook Flow Improvement

## Overview
This document describes the improvements made to the webhook message handling flow to support category-based agent creation and better session management.

## Changes Made

### 1. Session Model Updates
**File:** `app/models/session.py`

Added two new fields to track agent state:
- `agent_created` (Boolean): Tracks whether an agent has been created for the session
- `category` (String): Stores the selected category (e.g., "room_service", "general_information", "customer_service")

### 2. Database Migration
**File:** `alembic/versions/add_agent_fields_to_sessions.py`

Created a new migration to add the `agent_created` and `category` fields to the `sessions` table.

**To apply the migration:**
```bash
make migrate
```

### 3. H2H Service Enhancement
**File:** `app/integrations/h2h/h2h_service.py`

Updated `create_agent()` method to accept an optional `category` parameter that gets sent to the H2H Agent Router API.

### 4. Guest Repository Enhancement
**File:** `app/repositories/guest_repository.py`

Added new method `update_session_agent_status()` to update session's agent_created flag and category.

### 5. Webhook Service Refactoring
**File:** `app/services/webhook_service.py`

Completely refactored the `handle_incoming_message()` method with improved flow logic:

#### New Flow Logic

1. **New Session Creation**
   - When user first chats or after session expires, a new session is created
   - Welcome message is sent with category options:
     - 1. General Information
     - 2. Room Service
     - 3. Customer Service

2. **Category Selection**
   - User responds with 1, 2, or 3
   - System creates agent with the selected category via H2H
   - Confirmation message is sent to user

3. **Normal Conversation**
   - After agent is created, user can chat normally
   - Auto-reply is sent for each message
   - Messages are stored in the database

4. **Session Termination**
   - User sends `/end` to terminate the session
   - Session status is updated to "terminated"
   - Goodbye message is sent to user
   - When user chats again, a new session is created and welcome message is sent

#### New Helper Methods

- `_send_welcome_message()`: Sends welcome message with category options
- `_parse_category_command()`: Parses user input (1, 2, or 3) to category string
- `_create_agent_with_category()`: Creates agent via H2H with specified category

## User Flow Example

### First Time Chat (New Session)

**System:**
```
Halo John! 👋

Selamat datang kembali! Kami siap membantu Anda.

Pilih Salah 1 Kategori dibawah:
1. General Information
2. Room Service
3. Customer Service

Silahkan kirim 1, 2, atau 3 untuk memilih kategori yang Anda inginkan.
Ketik `/end` untuk mengakhiri percakapan.

Terima kasih! 🏨
```

**User:** `2`

**System:**
```
Terima kasih! 🙏

Anda telah memilih kategori: Room Service

Kami siap membantu Anda. Silakan kirim pesan Anda dan tim kami akan segera merespons.

Ketik `/end` kapan saja untuk mengakhiri percakapan.
```

### Normal Conversation

**User:** `Saya ingin memesan makanan`

**System:**
```
Terima kasih atas pesan Anda. 🙏

Tim kami akan segera merespons pertanyaan Anda. Mohon menunggu sebentar.

Waktu respon normal: 5-10 menit
```

### Session Termination

**User:** `/end`

**System:**
```
Terima kasih telah menghubungi kami! 👋

Sesi percakapan telah berakhir.
Silakan kirim pesan baru jika Anda membutuhkan bantuan lagi.

Sampai jumpa! 🏨
```

## Session Management

- Sessions are created when user first chats (not during guest registration)
- Sessions expire after 30 minutes of inactivity
- Expired sessions are automatically terminated when user sends a new message
- Users can manually terminate sessions using `/end` command
- After termination, new messages trigger welcome message and category selection again

## Testing

Before deploying, ensure you:

1. Run the database migration
2. Test the complete flow:
   - New user chat → welcome message
   - Category selection (1, 2, 3)
   - Normal conversation after agent creation
   - Invalid input handling (non-1/2/3 responses)
   - Session termination with `/end`
   - Session expiration after 30 minutes
   - New session after termination

## Notes

- The welcome message typo "Romm Service" has been fixed to "Room Service"
- The termination command has been changed from `/terminate` to `/end` for simplicity
- Agent creation is now deferred until after category selection
- All message exchanges are properly logged with appropriate roles (User/System)
