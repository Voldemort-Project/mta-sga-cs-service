"""Room schemas"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class RoomListItem(BaseModel):
    """Schema for room list item"""
    id: UUID = Field(..., description="Room ID")
    room_number: str = Field(..., description="Room number")
    label: str = Field(..., description="Room label/name")
    type: str = Field(..., description="Room type (e.g., standard, deluxe, suite)")
    is_booked: bool = Field(..., description="Whether the room is currently booked")
    created_at: datetime = Field(..., description="Room creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "room_number": "101",
                    "label": "Deluxe Ocean View",
                    "type": "deluxe",
                    "is_booked": False,
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z"
                }
            ]
        }
    }
