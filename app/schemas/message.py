"""Message schemas for request/response validation"""
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.message import MessageRole


class MessageItem(BaseModel):
    """Message item schema for list response"""
    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Message role (System or User)")
    message: str = Field(..., description="Message text content")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "a6f156bd-0e8d-49b9-87e7-80e3e9f825e3",
                    "role": "User",
                    "message": "Hello, I need help with my room"
                },
                {
                    "id": "b7g267ce-1f9e-5a0a-98f8-91f4f0g936f4",
                    "role": "System",
                    "message": "Terima kasih atas pesan Anda. Tim kami akan segera merespons."
                }
            ]
        }
    }
