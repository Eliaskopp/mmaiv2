import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

NoteTypeLiteral = Literal["technique", "drill", "goal", "gear", "gym", "insight"]
NoteStatusLiteral = Literal["active", "archived"]
NoteSourceLiteral = Literal["ai", "manual"]


# --- Requests ---


class NoteCreate(BaseModel):
    type: NoteTypeLiteral
    title: str = Field(..., min_length=1, max_length=200)
    summary: str | None = None
    user_notes: str | None = None


class NoteUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    summary: str | None = None
    user_notes: str | None = None
    status: NoteStatusLiteral | None = None
    pinned: bool | None = None


# --- Responses ---


class NoteResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    title: str
    summary: str | None
    user_notes: str | None
    status: str
    pinned: bool
    source: str
    source_conversation_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    items: list[NoteResponse]
    total: int
    offset: int
    limit: int


# --- Extraction (AI pipeline) ---


class NoteExtraction(BaseModel):
    has_extractable_content: bool
    type: NoteTypeLiteral | None = None
    title: str | None = Field(None, max_length=200)
    summary: str | None = None

    @model_validator(mode="after")
    def check_fields_when_extractable(self):
        if self.has_extractable_content and (not self.type or not self.title):
            raise ValueError("type and title required when has_extractable_content is True")
        return self
