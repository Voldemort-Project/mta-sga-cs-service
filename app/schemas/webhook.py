from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class MediaS3(BaseModel):
    Bucket: str
    Key: str


class Media(BaseModel):
    url: Optional[str] = None
    mimetype: Optional[str] = None
    filename: Optional[str] = None
    s3: Optional[MediaS3] = None
    error: Optional[str] = None


class Location(BaseModel):
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    live: Optional[bool] = None
    name: Optional[str] = None
    address: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    thumbnail: Optional[str] = None


class ReplyTo(BaseModel):
    id: str
    participant: Optional[str] = None
    body: Optional[str] = None
    _data: Optional[Dict[str, Any]] = None


class MessagePayload(BaseModel):
    id: str
    timestamp: int
    from_: str = Field(..., alias="from")
    fromMe: bool
    source: Optional[str] = None
    to: str
    participant: Optional[str] = None
    body: Optional[str] = None
    hasMedia: bool = False
    media: Optional[Media] = None
    ack: Optional[int] = None
    ackName: Optional[str] = None
    author: Optional[str] = None
    location: Optional[Location] = None
    vCards: Optional[List[str]] = []
    _data: Optional[Dict[str, Any]] = None
    replyTo: Optional[ReplyTo] = None

    model_config = {
        "populate_by_name": True,
    }


class Me(BaseModel):
    id: str
    lid: Optional[str] = None
    jid: Optional[str] = None
    pushName: Optional[str] = None


class Environment(BaseModel):
    version: str
    engine: str
    tier: Optional[str] = None
    browser: Optional[str] = None


class WahaWebhookRequest(BaseModel):
    id: str
    timestamp: int
    session: str
    metadata: Optional[Dict[str, Any]] = None
    engine: str
    event: str
    payload: MessagePayload
    me: Me
    environment: Environment


class WahaWebhookResponse(BaseModel):
    status: str
    message: str


class OrderCategory(str, Enum):
    """Order category enum"""
    housekeeping = "housekeeping"
    restaurant = "restaurant"


class OrderWebhookRequest(BaseModel):
    """Request schema for order webhook"""
    session_id: UUID = Field(..., description="Session ID (required)")
    category: OrderCategory = Field(..., description="Order category: 'housekeeping' or 'restaurant' (required)")
    title: str = Field(..., description="Order title (required)")
    description: str = Field(..., description="Order description (required)")
    note: Optional[str] = Field(None, description="Order note (optional, nullable)")
    additional_note: Optional[str] = Field(None, description="Order additional note (optional, nullable)")


class OrderWebhookResponse(BaseModel):
    """Response schema for order webhook"""
    status: str
    message: str
    order_id: Optional[UUID] = None
