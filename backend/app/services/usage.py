import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage import UsageRecord


async def increment_message_count(
    db: AsyncSession,
    user_id: uuid.UUID,
    record_date: date | None = None,
) -> None:
    """Upsert a usage record, incrementing message_count by 1."""
    d = record_date or date.today()
    stmt = pg_insert(UsageRecord).values(
        user_id=user_id,
        record_date=d,
        message_count=1,
    )
    stmt = stmt.on_conflict_do_update(
        constraint="uq_usage_user_date",
        set_={"message_count": UsageRecord.message_count + 1},
    )
    await db.execute(stmt)


async def get_daily_usage(
    db: AsyncSession,
    user_id: uuid.UUID,
    record_date: date | None = None,
) -> int:
    """Return message count for a given day (defaults to today)."""
    d = record_date or date.today()
    result = await db.execute(
        select(UsageRecord.message_count).where(
            UsageRecord.user_id == user_id,
            UsageRecord.record_date == d,
        )
    )
    count = result.scalar_one_or_none()
    return count or 0


async def check_quota(
    db: AsyncSession,
    user_id: uuid.UUID,
    daily_limit: int,
) -> bool:
    """Return True if the user is within their daily quota."""
    usage = await get_daily_usage(db, user_id)
    return usage < daily_limit
