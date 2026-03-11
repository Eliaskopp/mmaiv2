import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

SkillLevel = Literal["beginner", "intermediate", "advanced", "professional"]
WeightUnit = Literal["kg", "lb"]
Role = Literal["fighter", "coach", "hobbyist"]


# --- Requests ---


class ProfileCreate(BaseModel):
    skill_level: SkillLevel | None = None
    martial_arts: list[str] | None = None
    goals: str | None = Field(None, max_length=2000)
    weight_class: str | None = Field(None, max_length=30)
    training_frequency: str | None = Field(None, max_length=30)
    injuries: list[str] | None = None
    role: Role = "fighter"
    primary_domain: str | None = Field(None, max_length=30)
    game_style: str | None = Field(None, max_length=20)
    strategic_leaks: list[str] | None = None
    language_code: str = Field("en", max_length=10)
    weight_unit: WeightUnit = "kg"


class ProfileUpdate(BaseModel):
    skill_level: SkillLevel | None = None
    martial_arts: list[str] | None = None
    goals: str | None = Field(None, max_length=2000)
    weight_class: str | None = Field(None, max_length=30)
    training_frequency: str | None = Field(None, max_length=30)
    injuries: list[str] | None = None
    role: Role | None = None
    primary_domain: str | None = Field(None, max_length=30)
    game_style: str | None = Field(None, max_length=20)
    strategic_leaks: list[str] | None = None
    language_code: str | None = Field(None, max_length=10)
    weight_unit: WeightUnit | None = None


# --- Responses ---


class ProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    skill_level: str | None
    martial_arts: list | None
    goals: str | None
    weight_class: str | None
    training_frequency: str | None
    injuries: list | None
    role: str
    primary_domain: str | None
    game_style: str | None
    strategic_leaks: list | None
    conversation_insights: dict | None
    profile_completeness: int
    language_code: str
    weight_unit: str
    current_streak: int
    longest_streak: int
    last_active_date: date | None
    grace_days_remaining: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
