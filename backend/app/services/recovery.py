import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError
from app.models.journal import RecoveryLog


async def upsert_log(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: dict,
) -> RecoveryLog:
    values = {"user_id": user_id, **data}
    if "logged_for" not in values or values["logged_for"] is None:
        values.pop("logged_for", None)

    update_fields = {
        k: v for k, v in values.items()
        if k not in ("user_id", "logged_for", "id")
    }

    insert_stmt = pg_insert(RecoveryLog).values(**values)
    if update_fields:
        stmt = insert_stmt.on_conflict_do_update(
            index_elements=["user_id", "logged_for"],
            set_=update_fields,
        )
    else:
        stmt = insert_stmt.on_conflict_do_nothing(
            index_elements=["user_id", "logged_for"],
        )
    await db.execute(stmt)
    await db.commit()

    logged_for = values.get("logged_for")
    q = select(RecoveryLog).where(RecoveryLog.user_id == user_id)
    if logged_for is not None:
        q = q.where(RecoveryLog.logged_for == logged_for)
    else:
        q = q.where(RecoveryLog.logged_for == func.current_date())
    result = await db.execute(q)
    return result.scalar_one()


async def list_logs(
    db: AsyncSession,
    user_id: uuid.UUID,
    offset: int = 0,
    limit: int = 20,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[RecoveryLog], int]:
    base = select(RecoveryLog).where(RecoveryLog.user_id == user_id)
    if date_from is not None:
        base = base.where(RecoveryLog.logged_for >= date_from)
    if date_to is not None:
        base = base.where(RecoveryLog.logged_for <= date_to)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    rows_q = base.order_by(RecoveryLog.logged_for.desc()).offset(offset).limit(limit)
    rows = (await db.execute(rows_q)).scalars().all()
    return rows, total


async def get_log_by_date(
    db: AsyncSession,
    user_id: uuid.UUID,
    log_date: date,
) -> RecoveryLog:
    result = await db.execute(
        select(RecoveryLog).where(
            RecoveryLog.user_id == user_id,
            RecoveryLog.logged_for == log_date,
        )
    )
    log = result.scalar_one_or_none()
    if log is None:
        raise EntityNotFoundError("Recovery log")
    return log
