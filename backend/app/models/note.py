import enum
import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class NoteType(str, enum.Enum):
    TECHNIQUE = "technique"
    DRILL = "drill"
    GOAL = "goal"
    GEAR = "gear"
    GYM = "gym"
    INSIGHT = "insight"


class NoteStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class NoteSource(str, enum.Enum):
    AI = "ai"
    MANUAL = "manual"


class Note(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "notebook_entries"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    type: Mapped[NoteType] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    user_notes: Mapped[str | None] = mapped_column(Text)

    status: Mapped[NoteStatus] = mapped_column(
        nullable=False, server_default=NoteStatus.ACTIVE.value,
    )
    pinned: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false",
    )
    source: Mapped[NoteSource] = mapped_column(
        nullable=False, server_default=NoteSource.AI.value,
    )
    source_conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True,
    )

    __table_args__ = (
        Index("ix_notebook_entries_user_type", "user_id", "type"),
        Index("ix_notebook_entries_user_pinned", "user_id", "pinned",
              postgresql_where="pinned = true"),
    )
