# Available Rooms API

## Overview

The Available Rooms API allows you to retrieve a list of all available (not booked) rooms for your organization. This endpoint is useful when registering new guests to show which rooms are currently free.

## Endpoint

```
GET /api/v1/guests/rooms/available
```

## Authentication

This endpoint requires authentication. You must include a valid JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Request

No request body required. The endpoint uses the organization ID from the authenticated user's token.

## Response

### Success (200 OK)

```json
{
	"success": true,
	"message": "Found 5 available room(s)",
	"data": [
		{
			"id": "123e4567-e89b-12d3-a456-426614174000",
			"room_number": "101",
			"label": "Deluxe Ocean View",
			"type": "deluxe",
			"is_booked": false,
			"created_at": "2024-01-15T10:30:00Z",
			"updated_at": "2024-01-15T10:30:00Z"
		},
		{
			"id": "223e4567-e89b-12d3-a456-426614174001",
			"room_number": "102",
			"label": "Standard Room",
			"type": "standard",
			"is_booked": false,
			"created_at": "2024-01-15T10:30:00Z",
			"updated_at": "2024-01-15T10:30:00Z"
		}
	],
	"metadata": null,
	"error": null
}
```

### Error Responses

#### User Organization Not Found (400)

```json
{
	"success": false,
	"message": "User organization not found. Please ensure you are associated with an organization.",
	"data": null,
	"metadata": null,
	"error": {
		"code": "BAD_REQUEST",
		"message": "User organization not found. Please ensure you are associated with an organization."
	}
}
```

#### Unauthorized (401)

```json
{
	"detail": "Not authenticated"
}
```

#### Internal Server Error (500)

```json
{
	"success": false,
	"message": "Failed to fetch available rooms. Please try again.",
	"data": null,
	"metadata": null,
	"error": {
		"code": "ROOM_NOT_FOUND",
		"message": "Failed to fetch available rooms. Please try again."
	}
}
```

## Request Example

### cURL

```bash
curl -X GET "http://localhost:8000/api/v1/guests/rooms/available" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json"
```

### Python

```python
import requests

url = "http://localhost:8000/api/v1/guests/rooms/available"
headers = {
    "Authorization": "Bearer <your_jwt_token>",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
print(response.json())
```

### JavaScript (Fetch)

```javascript
const url = "http://localhost:8000/api/v1/guests/rooms/available";
const token = "<your_jwt_token>";

fetch(url, {
	method: "GET",
	headers: {
		Authorization: `Bearer ${token}`,
		"Content-Type": "application/json",
	},
})
	.then((response) => response.json())
	.then((data) => console.log(data))
	.catch((error) => console.error("Error:", error));
```

## Features

-   **Organization-Scoped**: Only returns rooms belonging to the authenticated user's organization
-   **Filtered by Availability**: Only shows rooms where `is_booked = false`
-   **Sorted by Room Number**: Results are ordered by room number in ascending order
-   **Excludes Deleted Rooms**: Soft-deleted rooms are automatically excluded from results

## Use Cases

1. **Guest Registration**: Display available rooms when registering a new guest
2. **Room Management**: Check which rooms are currently available for booking
3. **Housekeeping**: View which rooms need to be prepared for new guests
4. **Front Desk Operations**: Quick reference for available room inventory

## Related Endpoints

-   `POST /api/v1/guests/register` - Register a guest (requires a room number)
-   `GET /api/v1/guests` - List all registered guests
-   `POST /api/v1/guests/{guest_id}/checkout` - Checkout a guest (frees up their room)

## Notes

-   Rooms are automatically marked as booked when a guest is registered
-   Rooms become available again after a guest checks out
-   The `is_booked` flag is the primary indicator of room availability
-   All timestamps are in UTC format
