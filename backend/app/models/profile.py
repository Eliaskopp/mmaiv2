import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class TrainingProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "training_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False,
    )

    # Fighter identity
    skill_level: Mapped[str | None] = mapped_column(String(20))
    martial_arts: Mapped[dict | None] = mapped_column(JSONB, server_default="[]")
    goals: Mapped[str | None] = mapped_column(Text)
    weight_class: Mapped[str | None] = mapped_column(String(30))
    training_frequency: Mapped[str | None] = mapped_column(String(30))
    injuries: Mapped[dict | None] = mapped_column(JSONB, server_default="[]")
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="fighter",
    )

    # Danaher framework
    primary_domain: Mapped[str | None] = mapped_column(String(30))
    game_style: Mapped[str | None] = mapped_column(String(20))
    strategic_leaks: Mapped[dict | None] = mapped_column(JSONB, server_default="[]")

    # AI-enriched
    conversation_insights: Mapped[dict | None] = mapped_column(
        JSONB, server_default="{}",
    )
    profile_completeness: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0",
    )

    # Preferences
    language_code: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="en",
    )
    weight_unit: Mapped[str] = mapped_column(
        String(5), nullable=False, server_default="kg",
    )

    # Embedded streak state
    current_streak: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0",
    )
    longest_streak: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0",
    )
    last_active_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    grace_days_remaining: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1",
    )

    __table_args__ = (
        Index("ix_training_profiles_martial_arts", "martial_arts", postgresql_using="gin"),
        Index("ix_training_profiles_injuries", "injuries", postgresql_using="gin"),
        Index("ix_training_profiles_strategic_leaks", "strategic_leaks", postgresql_using="gin"),
        Index("ix_training_profiles_conversation_insights", "conversation_insights", postgresql_using="gin"),
    )
