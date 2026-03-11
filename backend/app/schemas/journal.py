import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

SessionTypeLiteral = Literal[
    "muay_thai", "bjj_gi", "bjj_nogi", "boxing",
    "mma", "wrestling", "conditioning", "strength", "other",
]
SessionSourceLiteral = Literal["manual", "voice", "ai"]


# --- Requests ---


class SessionCreate(BaseModel):
    session_type: SessionTypeLiteral
    session_date: date | None = None
    title: str | None = Field(None, max_length=200)
    notes: str | None = Field(None, max_length=5000)
    duration_minutes: int | None = Field(None, ge=1, le=599)
    rounds: int | None = Field(None, ge=0, le=100)
    round_duration_minutes: float | None = Field(None, gt=0, le=99.9)
    intensity_rpe: int | None = Field(None, ge=1, le=10)
    mood_before: int | None = Field(None, ge=1, le=5)
    mood_after: int | None = Field(None, ge=1, le=5)
    energy_level: int | None = Field(None, ge=1, le=5)
    techniques: list[str] | None = None
    training_partner: str | None = Field(None, max_length=100)
    gym_name: str | None = Field(None, max_length=100)
    source: SessionSourceLiteral = "manual"


class SessionUpdate(BaseModel):
    session_type: SessionTypeLiteral | None = None
    session_date: date | None = None
    title: str | None = Field(None, max_length=200)
    notes: str | None = Field(None, max_length=5000)
    duration_minutes: int | None = Field(None, ge=1, le=599)
    rounds: int | None = Field(None, ge=0, le=100)
    round_duration_minutes: float | None = Field(None, gt=0, le=99.9)
    intensity_rpe: int | None = Field(None, ge=1, le=10)
    mood_before: int | None = Field(None, ge=1, le=5)
    mood_after: int | None = Field(None, ge=1, le=5)
    energy_level: int | None = Field(None, ge=1, le=5)
    techniques: list[str] | None = None
    training_partner: str | None = Field(None, max_length=100)
    gym_name: str | None = Field(None, max_length=100)
    source: SessionSourceLiteral | None = None


# --- Responses ---


class SessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    session_type: str
    session_date: date
    title: str | None
    notes: str | None
    duration_minutes: int | None
    rounds: int | None
    round_duration_minutes: float | None
    intensity_rpe: int | None
    mood_before: int | None
    mood_after: int | None
    energy_level: int | None
    techniques: list | None
    training_partner: str | None
    gym_name: str | None
    source: str
    exertion_load: float | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}

    @field_validator("round_duration_minutes", mode="before")
    @classmethod
    def coerce_decimal(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        return v


class SessionListResponse(BaseModel):
    items: list[SessionResponse]
    total: int
    offset: int
    limit: int
