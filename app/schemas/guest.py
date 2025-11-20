"""Guest schemas for registration and check-in"""
from datetime import date
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


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
