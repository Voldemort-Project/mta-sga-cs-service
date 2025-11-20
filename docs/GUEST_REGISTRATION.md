# Guest Registration API

## Overview

The Guest Registration API allows you to register a new guest and automatically check them into a room. This endpoint creates a user record with guest role and a check-in record in a single transaction.

## Endpoint

```
POST /api/v1/guests/register
```

## Request Body

| Field         | Type   | Required | Description                          |
|---------------|--------|----------|--------------------------------------|
| full_name     | string | Yes      | Guest's full name                    |
| room_number   | string | Yes      | Room number to check into            |
| checkin_date  | date   | Yes      | Check-in date (YYYY-MM-DD format)    |
| email         | string | Yes      | Guest's email address (validated)    |
| phone_number  | string | Yes      | Guest's phone number                 |

## Request Example

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

## Response

### Success (201 Created)

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

### Error Responses

#### Room Not Found (404)

```json
{
  "detail": "Room 101 not found"
}
```

#### Room Not Available (400)

```json
{
  "detail": "Room 101 is not available. Current status: occupied"
}
```

#### Guest Role Not Found (500)

```json
{
  "detail": "Guest role not found in system. Please contact administrator."
}
```

#### Validation Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

## Business Logic

When a guest is registered, the system will:

1. Validate that the room exists
2. Verify that the room is available (status = "available")
3. Retrieve the "guest" role from the database
4. Create a new user record with:
   - Guest role
   - Full name
   - Email address
   - Phone number
   - No organization or division (guests are not affiliated)
5. Create a check-in record with:
   - Status: "active"
   - Check-in time: converted from the check-in date
   - Link to user and room
6. Update the room status to "occupied"
7. Commit the transaction (or rollback if any step fails)

## Database Schema Changes

The User model now includes an `email` field:

```sql
-- Migration: add_email_to_users
ALTER TABLE users ADD COLUMN email VARCHAR;
```

## Prerequisites

Before using this endpoint, ensure:

1. The database has a role named "guest" (created during initial setup)
2. Rooms are created and have status "available"
3. The email field migration has been applied: `alembic upgrade head`

## Testing

You can test the endpoint using the FastAPI interactive documentation:

```
http://localhost:8000/docs
```

Navigate to the "Guests" section and try the "Register Guest" endpoint.

## Notes

- Email validation is performed using Pydantic's `EmailStr` type
- Room status transitions: available → occupied
- Check-in status is automatically set to "active"
- The check-in time is set to midnight (00:00:00) of the check-in date
- If any error occurs, the entire transaction is rolled back
