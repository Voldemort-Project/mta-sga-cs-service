"""Worker schemas"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class WorkerListItem(BaseModel):
    """Schema for worker list item"""
    id: UUID = Field(..., description="Worker user ID")
    name: str = Field(..., description="Worker full name")
    email: str = Field(..., description="Worker email address")
    mobile_phone: str | None = Field(None, description="Worker phone number")
    role_id: UUID = Field(..., description="Worker role ID")
    role_name: str | None = Field(None, description="Worker role name")
    org_id: UUID | None = Field(None, description="Organization ID")
    division_id: UUID | None = Field(None, description="Division ID")
    created_at: datetime = Field(..., description="Registration date")
    updated_at: datetime = Field(..., description="Last update date")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "mobile_phone": "+6281234567890",
                    "role_id": "123e4567-e89b-12d3-a456-426614174001",
                    "role_name": "Housekeeping",
                    "org_id": "123e4567-e89b-12d3-a456-426614174002",
                    "division_id": "123e4567-e89b-12d3-a456-426614174003",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z"
                }
            ]
        }
    }
