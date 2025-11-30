"""Guest schemas for registration and check-in"""
from datetime import date, datetime, time
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.room import RoomListItem


class GuestRegisterRequest(BaseModel):
    """Request schema for guest registration"""
    full_name: str = Field(..., min_length=1, max_length=255, description="Guest full name")
    room_number: str = Field(..., min_length=1, max_length=50, description="Room number")
    checkin_date: date = Field(..., description="Check-in date (date only)")
    email: EmailStr = Field(..., description="Guest email address")
    phone_number: str = Field(..., min_length=1, max_length=20, description="Guest phone number")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "full_name": "John Doe",
                    "room_number": "101",
                    "checkin_date": "2024-01-15",
                    "email": "john.doe@example.com",
                    "phone_number": "+6281234567890"
                }
            ]
        }
    }


class GuestRegisterResponse(BaseModel):
    """Response schema for guest registration"""
    user_id: UUID = Field(..., description="Guest user ID")
    checkin_id: UUID = Field(..., description="Check-in ID")
    full_name: str = Field(..., description="Guest full name")
    room_number: str = Field(..., description="Room number")
    checkin_date: date = Field(..., description="Check-in date")
    email: str = Field(..., description="Guest email address")
    phone_number: str = Field(..., description="Guest phone number")
    status: str = Field(..., description="Check-in status")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
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
            ]
        }
    }


class CheckinRoomInfo(BaseModel):
    """Schema for checkin room information"""
    id: UUID = Field(..., description="Check-in room ID")
    checkin_date: Optional[date] = Field(None, description="Check-in date")
    checkin_time: Optional[time] = Field(None, description="Check-in time")
    checkout_date: Optional[date] = Field(None, description="Check-out date")
    checkout_time: Optional[time] = Field(None, description="Check-out time")
    status: Optional[str] = Field(None, description="Check-in status")
    room_id: Optional[UUID] = Field(None, description="Room ID")
    room: Optional[RoomListItem] = Field(None, description="Room details")

    model_config = {
        "from_attributes": True
    }


class SessionInfo(BaseModel):
    """Schema for session information"""
    id: UUID = Field(..., description="Session ID")
    status: Optional[str] = Field(None, description="Session status")
    mode: Optional[str] = Field(None, description="Session mode")
    start: Optional[datetime] = Field(None, description="Session start time")
    end: Optional[datetime] = Field(None, description="Session end time")
    duration: Optional[int] = Field(None, description="Session duration in seconds")
    category: Optional[str] = Field(None, description="Session category")
    agent_created: Optional[bool] = Field(None, description="Whether agent has been created")

    model_config = {
        "from_attributes": True
    }


class GuestListItem(BaseModel):
    """Schema for guest list item with checkin rooms and sessions"""
    id: UUID = Field(..., description="Guest user ID")
    name: str = Field(..., description="Guest full name")
    email: str = Field(..., description="Guest email address")
    mobile_phone: str | None = Field(None, description="Guest phone number")
    created_at: datetime = Field(..., description="Registration date")
    updated_at: datetime = Field(..., description="Last update date")
    checkin_rooms: List[CheckinRoomInfo] = Field(default_factory=list, description="List of guest check-in rooms")
    sessions: List[SessionInfo] = Field(default_factory=list, description="List of open sessions only (status='open')")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "mobile_phone": "+6281234567890",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                    "checkin_rooms": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174001",
                            "checkin_date": "2024-01-15",
                            "checkin_time": "14:00:00.000000",
                            "checkout_date": None,
                            "checkout_time": None,
                            "status": "active",
                            "room_id": "123e4567-e89b-12d3-a456-426614174002",
                            "room": {
                                "id": "123e4567-e89b-12d3-a456-426614174002",
                                "room_number": "101",
                                "label": "Deluxe Ocean View",
                                "type": "deluxe",
                                "is_booked": True,
                                "created_at": "2024-01-15T10:30:00Z",
                                "updated_at": "2024-01-15T10:30:00Z"
                            }
                        }
                    ],
                    "sessions": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174003",
                            "status": "open",
                            "mode": "agent",
                            "start": "2024-01-15T15:30:00Z",
                            "end": None,
                            "duration": None,
                            "category": "room_service",
                            "agent_created": True
                        }
                    ]
                }
            ]
        }
    }


class GuestCheckoutResponse(BaseModel):
    """Response schema for guest checkout"""
    guest_id: UUID = Field(..., description="Guest user ID")
    session_id: UUID | None = Field(None, description="Terminated session ID (None if no active session)")
    status: str = Field(..., description="Checkout status")
    session_terminated_at: str | None = Field(None, description="Session termination timestamp")
    session_duration_seconds: int | None = Field(None, description="Session duration in seconds")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "guest_id": "123e4567-e89b-12d3-a456-426614174000",
                    "session_id": "123e4567-e89b-12d3-a456-426614174002",
                    "status": "checked_out",
                    "session_terminated_at": "2024-01-20T14:30:00Z",
                    "session_duration_seconds": 432000
                },
                {
                    "guest_id": "123e4567-e89b-12d3-a456-426614174000",
                    "session_id": None,
                    "status": "checked_out",
                    "session_terminated_at": None,
                    "session_duration_seconds": None
                }
            ]
        }
    }
