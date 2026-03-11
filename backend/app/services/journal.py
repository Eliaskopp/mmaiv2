import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.journal import TrainingSession


def _compute_exertion_load(
    rpe: int | None, duration: int | None,
) -> float | None:
    if rpe is not None and duration is not None:
        return float(rpe * duration)
    return None


async def create_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: dict,
) -> TrainingSession:
    exertion_load = _compute_exertion_load(
        data.get("intensity_rpe"), data.get("duration_minutes"),
    )
    session = TrainingSession(user_id=user_id, exertion_load=exertion_load, **data)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def list_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
    offset: int = 0,
    limit: int = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    session_type: str | None = None,
) -> tuple[list[TrainingSession], int]:
    base = select(TrainingSession).where(
        TrainingSession.user_id == user_id,
        TrainingSession.deleted_at.is_(None),
    )
    if date_from is not None:
        base = base.where(TrainingSession.session_date >= date_from)
    if date_to is not None:
        base = base.where(TrainingSession.session_date <= date_to)
    if session_type is not None:
        base = base.where(TrainingSession.session_type == session_type)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    rows_q = base.order_by(TrainingSession.session_date.desc()).offset(offset).limit(limit)
    rows = (await db.execute(rows_q)).scalars().all()
    return rows, total


async def get_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
) -> TrainingSession:
    result = await db.execute(
        select(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.user_id == user_id,
            TrainingSession.deleted_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return session


async def update_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    data: dict,
) -> TrainingSession:
    session = await get_session(db, user_id, session_id)
    for key, value in data.items():
        setattr(session, key, value)
    session.exertion_load = _compute_exertion_load(
        session.intensity_rpe, session.duration_minutes,
    )
    await db.commit()
    await db.refresh(session)
    return session


async def delete_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
) -> None:
    session = await get_session(db, user_id, session_id)
    session.deleted_at = func.now()
    await db.commit()
