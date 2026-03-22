"""Memory read endpoints — performance events and training state."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.memory import PerformanceEvent, UserTrainingState
from app.models.user import User
from app.schemas.memory import (
    PerformanceEventListResponse,
    PerformanceEventResponse,
    UserTrainingStateResponse,
)

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/events", response_model=PerformanceEventListResponse)
async def list_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    base = select(PerformanceEvent).where(
        PerformanceEvent.user_id == current_user.id,
    )

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    rows_q = (
        base
        .order_by(PerformanceEvent.event_date.desc(), PerformanceEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await db.execute(rows_q)).scalars().all()

    return PerformanceEventListResponse(
        items=[PerformanceEventResponse.model_validate(r) for r in rows],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/state", response_model=UserTrainingStateResponse | None)
async def get_state(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserTrainingState).where(
            UserTrainingState.user_id == current_user.id,
        )
    )
    state = result.scalar_one_or_none()
    if state is None:
        return None
    return UserTrainingStateResponse.model_validate(state)
