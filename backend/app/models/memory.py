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
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


# ── Enums ─────────────────────────────────────────────────────────


class EventType(str, enum.Enum):
    SPARRING = "sparring"
    COMPETITION = "competition"
    DRILL = "drill"
    OPEN_MAT = "open_mat"


class Discipline(str, enum.Enum):
    MUAY_THAI = "muay_thai"
    BJJ_GI = "bjj_gi"
    BJJ_NOGI = "bjj_nogi"
    BOXING = "boxing"
    MMA = "mma"
    WRESTLING = "wrestling"


class Outcome(str, enum.Enum):
    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"
    NO_CONTEST = "no_contest"
    MIXED = "mixed"


class FailureDomain(str, enum.Enum):
    TECHNICAL = "technical"
    TACTICAL = "tactical"
    PHYSICAL = "physical"
    MENTAL = "mental"


class CnsStatus(str, enum.Enum):
    OPTIMAL = "optimal"
    SLUGGISH = "sluggish"
    DEPLETED = "depleted"


# ── Table 1: Immutable event log ──────────────────────────────────


class PerformanceEvent(UUIDMixin, Base):
    """Append-only log of performance events extracted from chat."""

    __tablename__ = "performance_events"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True,
    )

    event_type: Mapped[EventType] = mapped_column(
        SAEnum(EventType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    discipline: Mapped[Discipline] = mapped_column(
        SAEnum(Discipline, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    outcome: Mapped[Outcome | None] = mapped_column(
        SAEnum(Outcome, values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )
    finish_type: Mapped[str | None] = mapped_column(String(100))
    root_causes: Mapped[list | None] = mapped_column(JSONB, server_default="[]")
    highlights: Mapped[list | None] = mapped_column(JSONB, server_default="[]")
    opponent_description: Mapped[str | None] = mapped_column(String(200))

    # Invisible telemetry fields
    rpe_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failure_domain: Mapped[FailureDomain | None] = mapped_column(
        SAEnum(FailureDomain, values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )
    cns_status: Mapped[CnsStatus | None] = mapped_column(
        SAEnum(CnsStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )

    event_date: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date(),
    )
    extraction_confidence: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.0",
    )

    # Immutable — no TimestampMixin, no updated_at
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "rpe_score >= 1 AND rpe_score <= 10",
            name="ck_perf_rpe_range",
        ),
        CheckConstraint(
            "extraction_confidence >= 0.0 AND extraction_confidence <= 1.0",
            name="ck_perf_confidence_range",
        ),
        Index("ix_perf_events_user_date", "user_id", "event_date"),
        Index("ix_perf_events_user_type", "user_id", "event_type"),
        Index("ix_perf_events_root_causes", "root_causes", postgresql_using="gin"),
        Index("ix_perf_events_highlights", "highlights", postgresql_using="gin"),
    )


# ── Table 2: Mutable temporal state (one row per user) ───────────


class UserTrainingState(UUIDMixin, TimestampMixin, Base):
    """Current training context. Upserted — one row per user."""

    __tablename__ = "user_training_state"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )

    current_focus: Mapped[list | None] = mapped_column(JSONB, server_default="[]")
    active_injuries: Mapped[list | None] = mapped_column(JSONB, server_default="[]")
    short_term_goals: Mapped[list | None] = mapped_column(JSONB, server_default="[]")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_training_state_user"),
        Index("ix_training_state_focus", "current_focus", postgresql_using="gin"),
        Index("ix_training_state_injuries", "active_injuries", postgresql_using="gin"),
        Index("ix_training_state_goals", "short_term_goals", postgresql_using="gin"),
    )
