import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# --- Requests ---


class RecoveryLogCreate(BaseModel):
    sleep_quality: int | None = Field(None, ge=1, le=5)
    soreness: int | None = Field(None, ge=1, le=5)
    energy: int | None = Field(None, ge=1, le=5)
    notes: str | None = Field(None, max_length=2000)
    logged_for: date | None = None


# --- Responses ---


class RecoveryLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    sleep_quality: int | None
    soreness: int | None
    energy: int | None
    notes: str | None
    logged_for: date
    created_at: datetime

    model_config = {"from_attributes": True}


class RecoveryLogListResponse(BaseModel):
    items: list[RecoveryLogResponse]
    total: int
    offset: int
    limit: int
