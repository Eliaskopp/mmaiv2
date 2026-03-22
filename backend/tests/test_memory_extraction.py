"""Tests for the memory extraction background task orchestrator (Slice 4)."""

import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg
import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.memory import PerformanceEvent, UserTrainingState

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://mmai:mmai123@localhost:5432/mmai_v2_test",
)


def _pg_dsn() -> str:
    return TEST_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


@pytest.fixture
async def db_engine():
    """Create an engine and clean up memory tables before each test."""
    conn = await asyncpg.connect(_pg_dsn())
    await conn.execute("DELETE FROM performance_events")
    await conn.execute("DELETE FROM user_training_state")
    await conn.execute("DELETE FROM users")
    await conn.close()

    engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_size=5)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session_maker(db_engine):
    """Yield an async_sessionmaker — the db_session_maker arg for the orchestrator."""
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def test_user_id(session_maker) -> uuid.UUID:
    """Insert a minimal user row and return its UUID."""
    from app.models.user import User

    async with session_maker() as session:
        user = User(
            email="extraction-test@example.com",
            hashed_password="$2b$12$fakehashfortest000000000000000000000000000000",
            display_name="Extraction Test",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user.id


# ── Issue 1: Grok returns None → early exit ─────────────────────────────────


class TestGrokReturnsNoneEarlyExit:
    """When Grok fails and returns None, the orchestrator exits with no DB calls."""

    @pytest.mark.asyncio
    async def test_grok_returns_none_no_db_calls(self):
        from app.services.memory_extraction import extract_and_save_memory

        mock_session_maker = MagicMock()

        with patch(
            "app.services.memory_extraction.GrokClient"
        ) as MockGrokClient:
            instance = MockGrokClient.return_value
            instance.extract_memory = AsyncMock(return_value=None)

            await extract_and_save_memory(
                db_session_maker=mock_session_maker,
                user_id=uuid.uuid4(),
                conversation_id=uuid.uuid4(),
                user_content="Had a great sparring session today",
                assistant_content="That sounds like a solid session!",
            )

        # Session factory should never have been called
        mock_session_maker.assert_not_called()


# ── Issue 3: Empty extraction → no DB calls ─────────────────────────────────


class TestEmptyExtractionNoDbCalls:
    """When Grok returns valid but empty data, no DB session is created."""

    @pytest.mark.asyncio
    async def test_empty_events_null_state_no_db(self):
        from app.services.memory_extraction import extract_and_save_memory

        mock_session_maker = MagicMock()

        with patch(
            "app.services.memory_extraction.GrokClient"
        ) as MockGrokClient:
            instance = MockGrokClient.return_value
            instance.extract_memory = AsyncMock(
                return_value={"performance_events": [], "training_state": None}
            )

            await extract_and_save_memory(
                db_session_maker=mock_session_maker,
                user_id=uuid.uuid4(),
                conversation_id=uuid.uuid4(),
                user_content="What's a good jab technique?",
                assistant_content="Keep your elbow tucked and rotate your hips.",
            )

        mock_session_maker.assert_not_called()


# ── Issue 5: Confidence threshold filtering ──────────────────────────────────


class TestConfidenceThresholdFiltering:
    """Events below 0.6 confidence are filtered out before persistence."""

    @pytest.mark.asyncio
    async def test_below_threshold_filtered_above_persisted(
        self, session_maker, test_user_id,
    ):
        from app.services.memory_extraction import extract_and_save_memory

        grok_response = {
            "performance_events": [
                {
                    "event_type": "sparring",
                    "discipline": "boxing",
                    "extraction_confidence": 0.55,
                },
                {
                    "event_type": "drill",
                    "discipline": "muay_thai",
                    "extraction_confidence": 0.75,
                },
            ],
            "training_state": None,
        }

        with patch(
            "app.services.memory_extraction.GrokClient"
        ) as MockGrokClient:
            instance = MockGrokClient.return_value
            instance.extract_memory = AsyncMock(return_value=grok_response)

            await extract_and_save_memory(
                db_session_maker=session_maker,
                user_id=test_user_id,
                conversation_id=None,
                user_content="Did some drills and light sparring",
                assistant_content="Nice mix of work today.",
            )

        # Verify DB state
        async with session_maker() as db:
            result = await db.execute(
                select(PerformanceEvent).where(
                    PerformanceEvent.user_id == test_user_id
                )
            )
            rows = result.scalars().all()

        assert len(rows) == 1
        assert rows[0].extraction_confidence == pytest.approx(0.75)
        assert rows[0].discipline.value == "muay_thai"


# ── Issue 7: Happy path — full sparring debrief ─────────────────────────────


class TestHappyPath:
    """Full flow: Grok returns rich data → events + state persisted."""

    @pytest.mark.asyncio
    async def test_events_and_training_state_persisted(
        self, session_maker, test_user_id,
    ):
        from app.services.memory_extraction import extract_and_save_memory

        grok_response = {
            "performance_events": [
                {
                    "event_type": "sparring",
                    "discipline": "bjj_gi",
                    "outcome": "loss",
                    "finish_type": "rear naked choke",
                    "root_causes": ["poor guard retention"],
                    "highlights": ["sweep from half guard"],
                    "opponent_description": "blue belt",
                    "rpe_score": 7,
                    "failure_domain": "technical",
                    "cns_status": "sluggish",
                    "extraction_confidence": 0.85,
                }
            ],
            "training_state": {
                "current_focus": ["guard retention", "takedown defense"],
                "active_injuries": ["sore left knee"],
                "short_term_goals": ["compete in April"],
            },
        }

        with patch(
            "app.services.memory_extraction.GrokClient"
        ) as MockGrokClient:
            instance = MockGrokClient.return_value
            instance.extract_memory = AsyncMock(return_value=grok_response)

            await extract_and_save_memory(
                db_session_maker=session_maker,
                user_id=test_user_id,
                conversation_id=None,
                user_content="Had 5 rounds of BJJ sparring today, gi.",
                assistant_content="Sounds like a tough session!",
            )

        # Verify performance event
        async with session_maker() as db:
            result = await db.execute(
                select(PerformanceEvent).where(
                    PerformanceEvent.user_id == test_user_id
                )
            )
            events = result.scalars().all()

        assert len(events) == 1
        evt = events[0]
        assert evt.event_type.value == "sparring"
        assert evt.discipline.value == "bjj_gi"
        assert evt.outcome.value == "loss"
        assert evt.finish_type == "rear naked choke"
        assert evt.root_causes == ["poor guard retention"]
        assert evt.highlights == ["sweep from half guard"]
        assert evt.opponent_description == "blue belt"
        assert evt.rpe_score == 7
        assert evt.failure_domain.value == "technical"
        assert evt.cns_status.value == "sluggish"
        assert evt.extraction_confidence == pytest.approx(0.85)

        # Verify training state
        async with session_maker() as db:
            result = await db.execute(
                select(UserTrainingState).where(
                    UserTrainingState.user_id == test_user_id
                )
            )
            state = result.scalar_one()

        assert state.current_focus == ["guard retention", "takedown defense"]
        assert state.active_injuries == ["sore left knee"]
        assert state.short_term_goals == ["compete in April"]


# ── Issue 8: Validation error skips bad event ────────────────────────────────


class TestValidationErrorSkipsBadEvent:
    """One malformed event is skipped; valid events still saved."""

    @pytest.mark.asyncio
    async def test_bad_event_skipped_good_event_saved(
        self, session_maker, test_user_id,
    ):
        from app.services.memory_extraction import extract_and_save_memory

        grok_response = {
            "performance_events": [
                {
                    "event_type": "yoga",  # invalid — not in Literal
                    "discipline": "bjj_gi",
                    "extraction_confidence": 0.9,
                },
                {
                    "event_type": "sparring",
                    "discipline": "boxing",
                    "extraction_confidence": 0.8,
                },
            ],
            "training_state": None,
        }

        with patch(
            "app.services.memory_extraction.GrokClient"
        ) as MockGrokClient:
            instance = MockGrokClient.return_value
            instance.extract_memory = AsyncMock(return_value=grok_response)

            await extract_and_save_memory(
                db_session_maker=session_maker,
                user_id=test_user_id,
                conversation_id=None,
                user_content="Did yoga and boxing sparring",
                assistant_content="Nice cross-training!",
            )

        async with session_maker() as db:
            result = await db.execute(
                select(PerformanceEvent).where(
                    PerformanceEvent.user_id == test_user_id
                )
            )
            rows = result.scalars().all()

        assert len(rows) == 1
        assert rows[0].event_type.value == "sparring"


# ── Issue 9: Training state null → events only ──────────────────────────────


class TestTrainingStateNullSkipped:
    """When training_state is null, only events are persisted."""

    @pytest.mark.asyncio
    async def test_null_state_events_only(
        self, session_maker, test_user_id,
    ):
        from app.services.memory_extraction import extract_and_save_memory

        grok_response = {
            "performance_events": [
                {
                    "event_type": "competition",
                    "discipline": "mma",
                    "outcome": "win",
                    "extraction_confidence": 0.95,
                }
            ],
            "training_state": None,
        }

        with patch(
            "app.services.memory_extraction.GrokClient"
        ) as MockGrokClient:
            instance = MockGrokClient.return_value
            instance.extract_memory = AsyncMock(return_value=grok_response)

            await extract_and_save_memory(
                db_session_maker=session_maker,
                user_id=test_user_id,
                conversation_id=None,
                user_content="Won my fight last night!",
                assistant_content="Congratulations!",
            )

        async with session_maker() as db:
            events = (await db.execute(
                select(PerformanceEvent).where(
                    PerformanceEvent.user_id == test_user_id
                )
            )).scalars().all()
            states = (await db.execute(
                select(UserTrainingState).where(
                    UserTrainingState.user_id == test_user_id
                )
            )).scalars().all()

        assert len(events) == 1
        assert len(states) == 0


# ── Issue 10: Exception logged, not raised ───────────────────────────────────


class TestExceptionLoggedNotRaised:
    """Unexpected errors are caught, logged, and never propagate."""

    @pytest.mark.asyncio
    async def test_grok_exception_caught(self):
        from app.services.memory_extraction import extract_and_save_memory

        mock_session_maker = MagicMock()

        with patch(
            "app.services.memory_extraction.GrokClient"
        ) as MockGrokClient:
            instance = MockGrokClient.return_value
            instance.extract_memory = AsyncMock(
                side_effect=RuntimeError("API timeout")
            )

            # Must not raise
            await extract_and_save_memory(
                db_session_maker=mock_session_maker,
                user_id=uuid.uuid4(),
                conversation_id=uuid.uuid4(),
                user_content="Test",
                assistant_content="Test",
            )

        mock_session_maker.assert_not_called()
