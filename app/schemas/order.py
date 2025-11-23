"""Order schemas for listing orders"""
from datetime import date, datetime
from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.order import OrderStatus
from app.models.order_item import OrderItem
from app.models.order_assigner import OrderAssignerStatus


class RoomItem(BaseModel):
    """Schema for room item in order response"""
    id: UUID = Field(..., description="Room ID")
    label: str = Field(..., description="Room label")
    room_number: str = Field(..., description="Room number")
    type: str = Field(..., description="Room type")
    is_booked: bool = Field(..., description="Room booking status")

    model_config = {
        "from_attributes": True
    }


class CheckinRoomItem(BaseModel):
    """Schema for checkin room item in order response"""
    id: UUID = Field(..., description="Checkin room ID")
    checkin_date: Optional[date] = Field(None, description="Check-in date")
    checkin_time: Optional[str] = Field(None, description="Check-in time")
    checkout_date: Optional[date] = Field(None, description="Check-out date")
    checkout_time: Optional[str] = Field(None, description="Check-out time")
    status: Optional[str] = Field(None, description="Check-in status")
    rooms: List[RoomItem] = Field(default_factory=list, description="List of rooms")

    model_config = {
        "from_attributes": True
    }


class GuestItem(BaseModel):
    """Schema for guest (user) item in order response"""
    id: UUID = Field(..., description="Guest user ID")
    name: str = Field(..., description="Guest name")
    email: str = Field(..., description="Guest email")
    mobile_phone: Optional[str] = Field(None, description="Guest phone number")

    model_config = {
        "from_attributes": True
    }


class OrderItemSchema(BaseModel):
    """Schema for order item in order response"""
    id: UUID = Field(..., description="Order item ID")
    title: str = Field(..., description="Order item title")
    description: Optional[str] = Field(None, description="Order item description")
    qty: Optional[int] = Field(None, description="Quantity")
    price: Optional[float] = Field(None, description="Price")
    note: Optional[str] = Field(None, description="Order item note")

    model_config = {
        "from_attributes": True
    }


class SessionItem(BaseModel):
    """Schema for session item in order response"""
    id: UUID = Field(..., description="Session ID")
    status: Optional[str] = Field(None, description="Session status")
    mode: Optional[str] = Field(None, description="Session mode")
    start: Optional[datetime] = Field(None, description="Session start time")
    end: Optional[datetime] = Field(None, description="Session end time")
    duration: Optional[int] = Field(None, description="Session duration")
    guest: Optional[GuestItem] = Field(None, description="Associated guest")

    model_config = {
        "from_attributes": True
    }


class OrderListItem(BaseModel):
    """Schema for order list item with nested relationships"""
    id: UUID = Field(..., description="Order ID")
    order_number: str = Field(..., description="Order number")
    order_date: Optional[date] = Field(None, description="Order date")
    order_status: Optional[OrderStatus] = Field(None, description="Order status")
    category: str = Field(..., description="Order category")
    note: Optional[str] = Field(None, description="Order notes")
    additional_note: Optional[str] = Field(None, description="Additional order notes")
    total_amount: Optional[float] = Field(None, description="Total amount")
    items: List[OrderItemSchema] = Field(default_factory=list, description="List of order items")
    session: Optional[SessionItem] = Field(None, description="Associated session")
    checkin_rooms: Optional[CheckinRoomItem] = Field(None, description="Associated check-in room")
    created_at: datetime = Field(..., description="Order creation date")
    updated_at: datetime = Field(..., description="Order last update date")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "order_number": "1234567890",
                "order_date": "2025-01-01",
                "order_status": "pending",
                "category": "housekeeping",
                "note": "Note",
                "additional_note": "Additional Note",
                "total_amount": 100.0,
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174005",
                        "title": "Item Title",
                        "description": "Item Description",
                        "qty": 1,
                        "price": 100.0,
                        "note": "Item note"
                    }
                ],
                "session": {
                    "id": "123e4567-e89b-12d3-a456-426614174001",
                    "status": "open",
                    "mode": "agent",
                    "start": "2025-01-01T10:00:00Z",
                    "end": None,
                    "duration": None,
                    "guest": {
                        "id": "123e4567-e89b-12d3-a456-426614174002",
                        "name": "John Doe",
                        "email": "john.doe@example.com",
                        "mobile_phone": "+6281234567890"
                    }
                },
                "checkin_rooms": {
                    "id": "123e4567-e89b-12d3-a456-426614174003",
                    "checkin_date": "2025-01-01",
                    "checkin_time": "10:00:00",
                    "checkout_date": None,
                    "checkout_time": None,
                    "status": "active",
                    "rooms": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174004",
                            "label": "Standard Room",
                            "room_number": "101",
                            "type": "standard",
                            "is_booked": True
                        }
                    ]
                },
                "created_at": "2025-01-01T10:00:00Z",
                "updated_at": "2025-01-01T10:00:00Z"
            }
        }
    }


class AssignOrderRequest(BaseModel):
    """Schema for assigning order to worker"""
    worker_id: UUID = Field(..., description="Worker (user) ID to assign the order to")

    model_config = {
        "json_schema_extra": {
            "example": {
                "worker_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    }


class OrderAssignerResponse(BaseModel):
    """Schema for order assigner response"""
    id: UUID = Field(..., description="Order assigner ID")
    order_id: UUID = Field(..., description="Order ID")
    worker_id: UUID = Field(..., description="Worker (user) ID")
    assigned_at: datetime = Field(..., description="Assignment timestamp")
    status: OrderAssignerStatus = Field(..., description="Assignment status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "order_id": "123e4567-e89b-12d3-a456-426614174001",
                "worker_id": "123e4567-e89b-12d3-a456-426614174002",
                "assigned_at": "2025-01-01T10:00:00Z",
                "status": "assigned",
                "created_at": "2025-01-01T10:00:00Z",
                "updated_at": "2025-01-01T10:00:00Z"
            }
        }
    }
