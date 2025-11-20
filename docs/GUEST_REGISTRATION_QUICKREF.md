# Guest Registration - Quick Reference

## 🎯 Endpoint
```
POST /api/v1/guests/register
```

## 📝 Request Body
```json
{
  "full_name": "string",      // Required
  "room_number": "string",    // Required
  "checkin_date": "YYYY-MM-DD", // Required (date only)
  "email": "email@domain.com", // Required (valid email)
  "phone_number": "string"    // Required
}
```

## ✅ Success Response (201)
```json
{
  "user_id": "uuid",
  "checkin_id": "uuid",
  "full_name": "string",
  "room_number": "string",
  "checkin_date": "YYYY-MM-DD",
  "email": "email@domain.com",
  "phone_number": "string",
  "status": "active"
}
```

## ❌ Error Responses
- **404**: Room not found
- **400**: Room not available
- **422**: Invalid data (email format, missing fields)
- **500**: System error (guest role not found)

## 🚀 Quick Test
```bash
curl -X POST http://localhost:8000/api/v1/guests/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"John Doe","room_number":"101","checkin_date":"2024-01-15","email":"john@example.com","phone_number":"+6281234567890"}'
```

## 📋 What Happens
1. ✅ Validates input data
2. ✅ Checks room is available
3. ✅ Creates guest user
4. ✅ Creates check-in record
5. ✅ Updates room status to "occupied"

## 🔧 Setup Required
```bash
# Apply migration
uv run alembic upgrade head

# Start server
uv run uvicorn app.main:app --reload
```

## 🌐 Interactive Docs
```
http://localhost:8000/docs
```
