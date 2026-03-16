import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.schemas.health import HealthResponse, ServiceHealth
from app.services.grok import GrokClient

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    # DB check
    start = time.monotonic()
    try:
        await db.execute(text("SELECT 1"))
        db_latency = round((time.monotonic() - start) * 1000)
        db_health = ServiceHealth(status="connected", latency_ms=db_latency)
    except Exception:
        db_latency = round((time.monotonic() - start) * 1000)
        db_health = ServiceHealth(status="disconnected", latency_ms=db_latency)

    # AI check
    grok = GrokClient()
    ai_result = await grok.health_check()
    ai_health = ServiceHealth(
        status=ai_result["status"],
        latency_ms=ai_result["latency_ms"],
    )

    # Overall status
    if db_health.status == "connected" and ai_health.status == "connected":
        overall = "healthy"
    elif db_health.status == "connected":
        overall = "degraded"
    else:
        overall = "unhealthy"

    return HealthResponse(
        status=overall,
        version="0.1.0",
        database=db_health,
        ai=ai_health,
    )
