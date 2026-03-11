from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.recovery import (
    RecoveryLogCreate,
    RecoveryLogListResponse,
    RecoveryLogResponse,
)
from app.services import recovery as recovery_service

router = APIRouter(prefix="/recovery/logs", tags=["recovery"])


@router.post("", response_model=RecoveryLogResponse)
async def upsert_log(
    body: RecoveryLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    log = await recovery_service.upsert_log(
        db, current_user.id, body.model_dump(exclude_unset=True),
    )
    return RecoveryLogResponse.model_validate(log)


@router.get("", response_model=RecoveryLogListResponse)
async def list_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
):
    items, total = await recovery_service.list_logs(
        db, current_user.id,
        offset=offset, limit=limit,
        date_from=date_from, date_to=date_to,
    )
    return RecoveryLogListResponse(
        items=[RecoveryLogResponse.model_validate(log) for log in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{log_date}", response_model=RecoveryLogResponse)
async def get_log_by_date(
    log_date: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    log = await recovery_service.get_log_by_date(db, current_user.id, log_date)
    return RecoveryLogResponse.model_validate(log)
