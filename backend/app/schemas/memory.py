import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

# ── Literal type aliases ─────────────────────────────────────────

EventTypeLiteral = Literal["sparring", "competition", "drill", "open_mat"]
DisciplineLiteral = Literal[
    "muay_thai", "bjj_gi", "bjj_nogi", "boxing", "mma", "wrestling",
]
OutcomeLiteral = Literal["win", "loss", "draw", "no_contest", "mixed"]
FailureDomainLiteral = Literal["technical", "tactical", "physical", "mental"]
CnsStatusLiteral = Literal["optimal", "sluggish", "depleted"]

# Reusable constrained string for list elements (max 200 chars)
BoundedStr = Annotated[str, Field(max_length=200)]


# ── Extraction models (AI shield — extra = "forbid") ────────────


class PerformanceEventExtraction(BaseModel):
    """Validates raw JSON from Grok function-call extraction."""

    model_config = {"extra": "forbid"}

    event_type: EventTypeLiteral
    discipline: DisciplineLiteral
    outcome: OutcomeLiteral | None = None
    finish_type: str | None = Field(None, max_length=100)
    root_causes: list[BoundedStr] = Field(default_factory=list, max_length=5)
    highlights: list[BoundedStr] = Field(default_factory=list, max_length=5)
    opponent_description: str | None = Field(None, max_length=200)
    rpe_score: int | None = Field(None, ge=1, le=10)
    failure_domain: FailureDomainLiteral | None = None
    cns_status: CnsStatusLiteral | None = None
    event_date: date | None = None
    extraction_confidence: float = Field(0.0, ge=0.0, le=1.0)

    @field_validator("root_causes", "highlights", mode="before")
    @classmethod
    def coerce_none_to_list(cls, v):
        if v is None:
            return []
        return v


class UserTrainingStateExtraction(BaseModel):
    """Validates AI extraction of mutable training context."""

    model_config = {"extra": "forbid"}

    current_focus: list[BoundedStr] = Field(default_factory=list, max_length=5)
    active_injuries: list[BoundedStr] = Field(default_factory=list, max_length=5)
    short_term_goals: list[BoundedStr] = Field(default_factory=list, max_length=5)

    @field_validator("current_focus", "active_injuries", "short_term_goals", mode="before")
    @classmethod
    def coerce_none_to_list(cls, v):
        if v is None:
            return []
        return v


# ── Response models ──────────────────────────────────────────────


class PerformanceEventResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    conversation_id: uuid.UUID | None
    event_type: str
    discipline: str
    outcome: str | None
    finish_type: str | None
    root_causes: list | None
    highlights: list | None
    opponent_description: str | None
    rpe_score: int | None
    failure_domain: str | None
    cns_status: str | None
    event_date: date
    extraction_confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}


class PerformanceEventListResponse(BaseModel):
    items: list[PerformanceEventResponse]
    total: int
    offset: int
    limit: int


class UserTrainingStateResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    current_focus: list | None
    active_injuries: list | None
    short_term_goals: list | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
