"""Memory service — CRUD for performance events and training state."""

import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import (
    CnsStatus,
    Discipline,
    EventType,
    FailureDomain,
    Outcome,
    PerformanceEvent,
    UserTrainingState,
)
from app.schemas.memory import (
    PerformanceEventExtraction,
    UserTrainingStateExtraction,
)


async def save_performance_events(
    db: AsyncSession,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID | None,
    events: list[PerformanceEventExtraction],
) -> list[PerformanceEvent]:
    """Bulk insert performance events extracted from a conversation."""
    if not events:
        return []

    rows: list[PerformanceEvent] = []
    for event in events:
        row = PerformanceEvent(
            user_id=user_id,
            conversation_id=conversation_id,
            event_type=EventType(event.event_type),
            discipline=Discipline(event.discipline),
            outcome=Outcome(event.outcome) if event.outcome is not None else None,
            finish_type=event.finish_type,
            root_causes=event.root_causes,
            highlights=event.highlights,
            opponent_description=event.opponent_description,
            rpe_score=event.rpe_score,
            failure_domain=FailureDomain(event.failure_domain) if event.failure_domain is not None else None,
            cns_status=CnsStatus(event.cns_status) if event.cns_status is not None else None,
            event_date=event.event_date or date.today(),
            extraction_confidence=event.extraction_confidence,
        )
        rows.append(row)

    db.add_all(rows)
    await db.commit()
    for row in rows:
        await db.refresh(row)
    return rows


async def upsert_training_state(
    db: AsyncSession,
    user_id: uuid.UUID,
    state: UserTrainingStateExtraction,
) -> UserTrainingState:
    """Insert or replace the user's current training state."""
    result = await db.execute(
        select(UserTrainingState).where(UserTrainingState.user_id == user_id)
    )
    existing = result.scalar_one_or_none()

    if existing is None:
        row = UserTrainingState(
            user_id=user_id,
            current_focus=state.current_focus,
            active_injuries=state.active_injuries,
            short_term_goals=state.short_term_goals,
        )
        db.add(row)
    else:
        existing.current_focus = state.current_focus
        existing.active_injuries = state.active_injuries
        existing.short_term_goals = state.short_term_goals
        row = existing

    await db.commit()
    await db.refresh(row)
    return row


async def get_recent_telemetry(
    db: AsyncSession,
    user_id: uuid.UUID,
    days: int = 14,
) -> dict:
    """Fetch recent performance events and current training state.

    Used for context injection into the coach system prompt.
    Leverages the ix_perf_events_user_date index.
    """
    cutoff = date.today() - timedelta(days=days)

    events_result = await db.execute(
        select(PerformanceEvent)
        .where(
            PerformanceEvent.user_id == user_id,
            PerformanceEvent.event_date >= cutoff,
        )
        .order_by(PerformanceEvent.event_date.desc())
        .limit(50)
    )
    events = list(events_result.scalars().all())

    state_result = await db.execute(
        select(UserTrainingState).where(UserTrainingState.user_id == user_id)
    )
    training_state = state_result.scalar_one_or_none()

    return {
        "events": events,
        "training_state": training_state,
    }
