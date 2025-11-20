# Guest Registration Implementation Summary

## ✅ Completed Implementation

### 1. Database Schema Changes

**File**: `app/models/user.py`
- Added `email` field to User model
- Email is optional (nullable) for staff, but required for guests through validation

**Migration**: `alembic/versions/f8e96862b7ab_add_email_to_users.py`
- Auto-generated migration to add email column to users table
- Run with: `uv run alembic upgrade head`

### 2. Schemas Created

**File**: `app/schemas/guest.py`
- `GuestRegisterRequest`: Validates incoming registration data
  - full_name (required, string)
  - room_number (required, string)
  - checkin_date (required, date only)
  - email (required, validated email format)
  - phone_number (required, string)

- `GuestRegisterResponse`: Returns registration result
  - user_id (UUID)
  - checkin_id (UUID)
  - full_name (string)
  - room_number (string)
  - checkin_date (date)
  - email (string)
  - phone_number (string)
  - status (string)

### 3. Repository Layer

**File**: `app/repositories/guest_repository.py`
- `GuestRepository`: Handles all database operations
  - `get_guest_role()`: Retrieves the guest role from database
  - `get_room_by_number()`: Finds room by room number
  - `create_guest_user()`: Creates new user with guest role
  - `create_checkin()`: Creates check-in record
  - `update_room_status()`: Updates room status to occupied

### 4. Service Layer

**File**: `app/services/guest_service.py`
- `GuestService`: Business logic for guest registration
  - Validates guest role exists
  - Validates room exists and is available
  - Creates user and check-in in a transaction
  - Updates room status to occupied
  - Handles rollback on errors
  - Returns comprehensive response

### 5. API Router

**File**: `app/api/v1/guest_router.py`
- Endpoint: `POST /api/v1/guests/register`
- Response: 201 Created on success
- Fully documented with OpenAPI/Swagger
- Error handling for all scenarios

**File**: `app/api/router.py`
- Registered guest router in API v1 router

### 6. Documentation

**File**: `docs/GUEST_REGISTRATION.md`
- Complete API documentation
- Request/response examples
- Error scenarios
- Business logic explanation
- Testing instructions

## 📋 API Endpoint Details

```
POST /api/v1/guests/register
```

### Request Example:
```json
{
  "full_name": "John Doe",
  "room_number": "101",
  "checkin_date": "2024-01-15",
  "email": "john.doe@example.com",
  "phone_number": "+6281234567890"
}
```

### Response Example (201):
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "checkin_id": "123e4567-e89b-12d3-a456-426614174001",
  "full_name": "John Doe",
  "room_number": "101",
  "checkin_date": "2024-01-15",
  "email": "john.doe@example.com",
  "phone_number": "+6281234567890",
  "status": "active"
}
```

## 🔄 Business Flow

1. **Request Validation**: Pydantic validates all input fields
2. **Guest Role Check**: Verifies "guest" role exists in database
3. **Room Validation**: Confirms room exists and status is "available"
4. **User Creation**: Creates user record with guest role
5. **Check-in Creation**: Creates active check-in record
6. **Room Update**: Changes room status to "occupied"
7. **Transaction Commit**: All changes committed together
8. **Response**: Returns complete registration details

## ⚠️ Error Handling

- **404 Not Found**: Room doesn't exist
- **400 Bad Request**: Room is not available (occupied/maintenance)
- **422 Validation Error**: Invalid email format or missing required fields
- **500 Internal Error**: Guest role not found or database error

All errors trigger automatic transaction rollback.

## 🚀 How to Use

### 1. Apply Database Migration
```bash
cd /Users/a666hn/Projects/mta/sga-cs-service
uv run alembic upgrade head
```

### 2. Start the Application
```bash
uv run uvicorn app.main:app --reload
```

### 3. Access API Documentation
```
http://localhost:8000/docs
```

### 4. Test the Endpoint
```bash
curl -X POST "http://localhost:8000/api/v1/guests/register" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "room_number": "101",
    "checkin_date": "2024-01-15",
    "email": "john.doe@example.com",
    "phone_number": "+6281234567890"
  }'
```

## 📦 Files Created/Modified

### New Files:
- `app/schemas/guest.py`
- `app/repositories/guest_repository.py`
- `app/services/guest_service.py`
- `app/api/v1/guest_router.py`
- `alembic/versions/f8e96862b7ab_add_email_to_users.py`
- `docs/GUEST_REGISTRATION.md`
- `docs/GUEST_REGISTRATION_SUMMARY.md`

### Modified Files:
- `app/models/user.py` - Added email field
- `app/api/router.py` - Registered guest router

## 📝 Prerequisites

Before using this endpoint, ensure:

1. ✅ Database connection is configured
2. ✅ "guest" role exists in roles table
3. ✅ Rooms are created with "available" status
4. ✅ Email migration is applied

## 🧪 Testing

The endpoint can be tested using:
- FastAPI interactive docs (`/docs`)
- Postman/Insomnia
- curl commands
- Python httpx/requests

## 🔒 Security Considerations

- Email validation using Pydantic EmailStr
- Transaction rollback on errors
- SQL injection protection via SQLAlchemy ORM
- Input sanitization through Pydantic models

## 🎯 Next Steps (Optional Enhancements)

1. Add authentication/authorization
2. Send confirmation email to guest
3. Add check-out endpoint
4. Add guest profile management
5. Add room assignment optimization
6. Add duplicate guest detection
7. Add audit logging
8. Add rate limiting
