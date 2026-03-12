import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# --- Requests ---


class ConversationCreate(BaseModel):
    title: str | None = Field(None, max_length=255)


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


# --- Responses ---


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    metadata_: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse]


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int
    offset: int
    limit: int


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int
    offset: int
    limit: int
