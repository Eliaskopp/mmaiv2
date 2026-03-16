import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError
from app.models.note import Note, NoteSource, NoteStatus, NoteType


def _coerce_enums(data: dict) -> dict:
    """Convert string values to enum instances for Note model fields."""
    out = dict(data)
    if "type" in out and isinstance(out["type"], str):
        out["type"] = NoteType(out["type"])
    if "status" in out and isinstance(out["status"], str):
        out["status"] = NoteStatus(out["status"])
    if "source" in out and isinstance(out["source"], str):
        out["source"] = NoteSource(out["source"])
    return out


async def create_note(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: dict,
) -> Note:
    note = Note(user_id=user_id, source=NoteSource.MANUAL, **_coerce_enums(data))
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


async def create_ai_note(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: dict,
    conversation_id: uuid.UUID,
) -> Note:
    note = Note(
        user_id=user_id,
        source=NoteSource.AI,
        source_conversation_id=conversation_id,
        **_coerce_enums(data),
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


async def list_notes(
    db: AsyncSession,
    user_id: uuid.UUID,
    offset: int = 0,
    limit: int = 20,
    type_filter: str | None = None,
    status_filter: str | None = None,
    pinned_filter: bool | None = None,
) -> tuple[list[Note], int]:
    base = select(Note).where(Note.user_id == user_id)

    if type_filter is not None:
        base = base.where(Note.type == type_filter)
    if status_filter is not None:
        base = base.where(Note.status == status_filter)
    if pinned_filter is not None:
        base = base.where(Note.pinned == pinned_filter)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    rows_q = base.order_by(Note.created_at.desc()).offset(offset).limit(limit)
    rows = (await db.execute(rows_q)).scalars().all()
    return rows, total


async def get_note(
    db: AsyncSession,
    user_id: uuid.UUID,
    note_id: uuid.UUID,
) -> Note:
    result = await db.execute(
        select(Note).where(
            Note.id == note_id,
            Note.user_id == user_id,
        )
    )
    note = result.scalar_one_or_none()
    if note is None:
        raise EntityNotFoundError("Note")
    return note


async def update_note(
    db: AsyncSession,
    user_id: uuid.UUID,
    note_id: uuid.UUID,
    data: dict,
) -> Note:
    note = await get_note(db, user_id, note_id)
    coerced = _coerce_enums(data)
    for key, value in coerced.items():
        setattr(note, key, value)
    await db.commit()
    await db.refresh(note)
    return note


async def delete_note(
    db: AsyncSession,
    user_id: uuid.UUID,
    note_id: uuid.UUID,
) -> None:
    note = await get_note(db, user_id, note_id)
    await db.delete(note)
    await db.commit()
