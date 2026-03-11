import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class SessionType(str, enum.Enum):
    MUAY_THAI = "muay_thai"
    BJJ_GI = "bjj_gi"
    BJJ_NOGI = "bjj_nogi"
    BOXING = "boxing"
    MMA = "mma"
    WRESTLING = "wrestling"
    CONDITIONING = "conditioning"
    STRENGTH = "strength"
    OTHER = "other"


class SessionSource(str, enum.Enum):
    MANUAL = "manual"
    VOICE = "voice"
    AI = "ai"


class TrainingSession(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "training_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    session_type: Mapped[SessionType] = mapped_column(
        SAEnum(SessionType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)

    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    rounds: Mapped[int | None] = mapped_column(Integer)
    round_duration_minutes: Mapped[float | None] = mapped_column(Numeric(4, 1))

    intensity_rpe: Mapped[int | None] = mapped_column(Integer)
    mood_before: Mapped[int | None] = mapped_column(Integer)
    mood_after: Mapped[int | None] = mapped_column(Integer)
    energy_level: Mapped[int | None] = mapped_column(Integer)

    techniques: Mapped[dict | None] = mapped_column(JSONB, server_default="[]")
    training_partner: Mapped[str | None] = mapped_column(String(100))
    gym_name: Mapped[str | None] = mapped_column(String(100))

    source: Mapped[SessionSource] = mapped_column(
        SAEnum(SessionSource, values_callable=lambda e: [m.value for m in e]),
        nullable=False, server_default=SessionSource.MANUAL.value,
    )
    exertion_load: Mapped[float | None] = mapped_column(Float)
    session_date: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    __table_args__ = (
        CheckConstraint("duration_minutes > 0 AND duration_minutes < 600", name="ck_duration_range"),
        CheckConstraint("rounds >= 0 AND rounds <= 100", name="ck_rounds_range"),
        CheckConstraint("intensity_rpe >= 1 AND intensity_rpe <= 10", name="ck_rpe_range"),
        CheckConstraint("mood_before >= 1 AND mood_before <= 5", name="ck_mood_before_range"),
        CheckConstraint("mood_after >= 1 AND mood_after <= 5", name="ck_mood_after_range"),
        CheckConstraint("energy_level >= 1 AND energy_level <= 5", name="ck_energy_range"),
        Index("ix_training_sessions_user_date", "user_id", "session_date"),
        Index("ix_training_sessions_user_type", "user_id", "session_type"),
        Index("ix_training_sessions_techniques", "techniques", postgresql_using="gin"),
    )


class RecoveryLog(UUIDMixin, Base):
    __tablename__ = "recovery_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    sleep_quality: Mapped[int | None] = mapped_column(Integer)
    soreness: Mapped[int | None] = mapped_column(Integer)
    energy: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    logged_for: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "logged_for", name="uq_recovery_user_date"),
        CheckConstraint("sleep_quality >= 1 AND sleep_quality <= 5", name="ck_sleep_range"),
        CheckConstraint("soreness >= 1 AND soreness <= 5", name="ck_soreness_range"),
        CheckConstraint("energy >= 1 AND energy <= 5", name="ck_energy_log_range"),
        Index("ix_recovery_logs_user_date", "user_id", "logged_for"),
    )
