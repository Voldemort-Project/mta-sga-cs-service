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
    to: Optional[str] = None
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
    room_service = "room_service"
    maintenance = "maintenance"
    concierge = "concierge"
    restaurant = "restaurant"


class OrderItemRequest(BaseModel):
    """Request schema for order item"""
    title: str = Field(..., description="Order item title (required)")
    description: Optional[str] = Field(None, description="Order item description (optional)")
    qty: Optional[int] = Field(None, description="Quantity (optional)")
    price: Optional[float] = Field(0, description="Price (optional, default: 0)")
    note: Optional[str] = Field(None, description="Order item note (optional)")


class OrderRequest(BaseModel):
    """Request schema for a single order in bulk order webhook"""
    category: OrderCategory = Field(..., description="Order category: 'housekeeping', 'room_service', 'maintenance', or 'concierge' (required)")
    items: List[OrderItemRequest] = Field(..., description="List of order items (required)")
    note: Optional[str] = Field(None, description="Order note (optional, nullable)")
    additional_note: Optional[str] = Field(None, description="Order additional note (optional, nullable)")


class OrderWebhookRequest(BaseModel):
    """Request schema for order webhook (supports bulk orders)"""
    session_id: UUID = Field(..., description="Session ID (required)")
    orders: List[OrderRequest] = Field(..., description="List of orders to create (required)")


class OrderWebhookResponse(BaseModel):
    """Response schema for order webhook"""
    status: str
    message: str
    order_numbers: List[str] = Field(default_factory=list, description="List of created order numbers")


class SendMessageRequest(BaseModel):
    """Request schema for send message webhook"""
    session_id: UUID = Field(..., description="Session ID (required)")
    message: str = Field(..., description="Message text to send (required)")
