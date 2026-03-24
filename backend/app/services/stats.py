import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.journal import TrainingSession


def _risk_zone(ratio: float | None) -> str:
    if ratio is None:
        return "insufficient_data"
    if ratio >= 1.5:
        return "very_high"
    if ratio >= 1.3:
        return "high"
    if ratio >= 0.8:
        return "optimal"
    return "low"


async def get_acwr(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    reference_date: date | None = None,
) -> dict:
    today = reference_date or date.today()
    acute_start = today - timedelta(days=6)
    chronic_start = today - timedelta(days=27)

    base = select(
        func.coalesce(
            func.sum(TrainingSession.exertion_load).filter(
                TrainingSession.session_date >= acute_start,
            ),
            0,
        ).label("acute"),
        func.coalesce(
            func.sum(TrainingSession.exertion_load).filter(
                TrainingSession.session_date >= chronic_start,
            ),
            0,
        ).label("chronic"),
    ).where(
        TrainingSession.user_id == user_id,
        TrainingSession.deleted_at.is_(None),
        TrainingSession.session_date <= today,
    )

    row = (await db.execute(base)).one()
    acute = float(row.acute)
    chronic = float(row.chronic)
    chronic_weekly = chronic / 4.0

    if chronic_weekly == 0:
        ratio = None
    else:
        ratio = round(acute / chronic_weekly, 2)

    # Calibration check: aggregate MIN/MAX date and COUNT in the chronic window
    cal_query = select(
        func.count(TrainingSession.id).label("session_count"),
        func.min(TrainingSession.session_date).label("earliest"),
        func.max(TrainingSession.session_date).label("latest"),
    ).where(
        TrainingSession.user_id == user_id,
        TrainingSession.deleted_at.is_(None),
        TrainingSession.session_date >= chronic_start,
        TrainingSession.session_date <= today,
    )
    cal_row = (await db.execute(cal_query)).one()

    session_count = cal_row.session_count
    if session_count >= 4 and cal_row.earliest is not None:
        span_days = (cal_row.latest - cal_row.earliest).days
        is_calibrating = span_days < 14
    else:
        is_calibrating = True

    effective_ratio = None if is_calibrating else ratio

    return {
        "acute_load": acute,
        "chronic_load": chronic,
        "acwr_ratio": effective_ratio,
        "risk_zone": _risk_zone(effective_ratio),
        "is_calibrating": is_calibrating,
        "session_count": session_count,
    }


async def get_volume_trends(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    days: int = 30,
    reference_date: date | None = None,
) -> list[dict]:
    today = reference_date or date.today()
    start_date = today - timedelta(days=days - 1)

    stmt = (
        select(
            TrainingSession.session_date,
            func.coalesce(func.sum(TrainingSession.exertion_load), 0).label("total_load"),
            func.coalesce(func.sum(TrainingSession.duration_minutes), 0).label("total_duration"),
        )
        .where(
            TrainingSession.user_id == user_id,
            TrainingSession.deleted_at.is_(None),
            TrainingSession.session_date >= start_date,
            TrainingSession.session_date <= today,
        )
        .group_by(TrainingSession.session_date)
    )

    rows = (await db.execute(stmt)).all()
    by_date = {row.session_date: row for row in rows}

    result = []
    for offset in range(days):
        d = start_date + timedelta(days=offset)
        if d in by_date:
            row = by_date[d]
            result.append({
                "date": str(d),
                "total_load": float(row.total_load),
                "total_duration": int(row.total_duration),
            })
        else:
            result.append({
                "date": str(d),
                "total_load": 0.0,
                "total_duration": 0,
            })

    return result
