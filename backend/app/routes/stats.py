from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.stats import ACWRResponse, DailyVolumePoint
from app.services import stats as stats_service

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/acwr", response_model=ACWRResponse)
async def get_acwr(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await stats_service.get_acwr(db, current_user.id)


@router.get("/volume", response_model=list[DailyVolumePoint])
async def get_volume_trends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
):
    return await stats_service.get_volume_trends(db, current_user.id, days=days)
