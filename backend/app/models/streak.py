import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class StreakDayType(str, enum.Enum):
    TRAINING = "training"
    RECOVERY = "recovery"
    REST = "rest"
    MISSED = "missed"


class StreakDay(UUIDMixin, Base):
    __tablename__ = "streak_days"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    day_type: Mapped[StreakDayType] = mapped_column(nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_streak_user_date"),
    )
