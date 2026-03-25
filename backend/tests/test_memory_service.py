"""Tests for memory extraction prompt, GrokClient.extract_memory, and memory service."""

import os
import uuid
from datetime import date, timedelta

import asyncpg
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.memory import (
    CnsStatus,
    Discipline,
    EventType,
    FailureDomain,
    Outcome,
    PerformanceEvent,
    UserTrainingState,
)
from app.schemas.memory import PerformanceEventExtraction, UserTrainingStateExtraction

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://mmai:mmai123@localhost:5432/mmai_v2_test",
)


def _pg_dsn() -> str:
    return TEST_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
async def db_session():
    """Yield an AsyncSession for direct service-layer tests."""
    conn = await asyncpg.connect(_pg_dsn())
    await conn.execute("DELETE FROM performance_events")
    await conn.execute("DELETE FROM user_training_state")
    await conn.execute("DELETE FROM users")
    await conn.close()

    engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_size=5)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_user_id(db_session: AsyncSession) -> uuid.UUID:
    """Insert a minimal user row and return its UUID."""
    from app.models.user import User

    user = User(
        email="memory-test@example.com",
        hashed_password="$2b$12$fakehashfortest000000000000000000000000000000",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user.id


# ── Issue 1: Memory Extraction Prompt ────────────────────────────────────────


class TestMemoryExtractionPrompt:
    """Verify the extraction prompt contains all required enum values and structure."""

    def test_prompt_is_nonempty_string(self):
        from app.prompts.memory_extraction import MEMORY_EXTRACTION_PROMPT

        assert isinstance(MEMORY_EXTRACTION_PROMPT, str)
        assert len(MEMORY_EXTRACTION_PROMPT) > 100

    def test_prompt_contains_event_types(self):
        from app.prompts.memory_extraction import MEMORY_EXTRACTION_PROMPT

        for val in ("sparring", "competition", "drill", "open_mat"):
            assert val in MEMORY_EXTRACTION_PROMPT, f"Missing event_type: {val}"

    def test_prompt_contains_disciplines(self):
        from app.prompts.memory_extraction import MEMORY_EXTRACTION_PROMPT

        for val in ("muay_thai", "bjj_gi", "bjj_nogi", "boxing", "mma", "wrestling"):
            assert val in MEMORY_EXTRACTION_PROMPT, f"Missing discipline: {val}"

    def test_prompt_contains_outcomes(self):
        from app.prompts.memory_extraction import MEMORY_EXTRACTION_PROMPT

        for val in ("win", "loss", "draw", "no_contest", "mixed"):
            assert val in MEMORY_EXTRACTION_PROMPT, f"Missing outcome: {val}"

    def test_prompt_contains_failure_domains(self):
        from app.prompts.memory_extraction import MEMORY_EXTRACTION_PROMPT

        for val in ("technical", "tactical", "physical", "mental"):
            assert val in MEMORY_EXTRACTION_PROMPT, f"Missing failure_domain: {val}"

    def test_prompt_contains_cns_statuses(self):
        from app.prompts.memory_extraction import MEMORY_EXTRACTION_PROMPT

        for val in ("optimal", "sluggish", "depleted"):
            assert val in MEMORY_EXTRACTION_PROMPT, f"Missing cns_status: {val}"

    def test_prompt_contains_json_keys(self):
        from app.prompts.memory_extraction import MEMORY_EXTRACTION_PROMPT

        assert "performance_events" in MEMORY_EXTRACTION_PROMPT
        assert "training_state" in MEMORY_EXTRACTION_PROMPT


# ── Issue 2: GrokClient.extract_memory ───────────────────────────────────────


class TestExtractMemoryStub:
    """Test extract_memory in stub mode (no API key)."""

    @pytest.mark.asyncio
    async def test_stub_mode_returns_empty(self):
        from app.services.grok import GrokClient

        client = GrokClient()
        result = await client.extract_memory(
            [{"role": "user", "content": "Had a great sparring session"}]
        )
        assert result == {"performance_events": [], "training_state": None}


# ── Issue 3: save_performance_events ─────────────────────────────────────────


class TestSavePerformanceEvents:
    """Test bulk insertion of performance events from Pydantic extractions."""

    @pytest.mark.asyncio
    async def test_save_single_event(self, db_session, test_user_id):
        from app.services.memory import save_performance_events

        extraction = PerformanceEventExtraction(
            event_type="sparring",
            discipline="bjj_gi",
            outcome="loss",
            finish_type="rear naked choke",
            root_causes=["poor guard retention"],
            highlights=["sweep from half guard"],
            rpe_score=7,
            failure_domain="technical",
            cns_status="sluggish",
            extraction_confidence=0.85,
        )
        rows = await save_performance_events(
            db_session, test_user_id, None, [extraction]
        )

        assert len(rows) == 1
        row = rows[0]
        assert row.user_id == test_user_id
        assert row.conversation_id is None
        assert row.event_type == EventType.SPARRING
        assert row.discipline == Discipline.BJJ_GI
        assert row.outcome == Outcome.LOSS
        assert row.finish_type == "rear naked choke"
        assert row.root_causes == ["poor guard retention"]
        assert row.highlights == ["sweep from half guard"]
        assert row.rpe_score == 7
        assert row.failure_domain == FailureDomain.TECHNICAL
        assert row.cns_status == CnsStatus.SLUGGISH
        assert row.extraction_confidence == pytest.approx(0.85)

    @pytest.mark.asyncio
    async def test_save_multiple_events(self, db_session, test_user_id):
        from app.services.memory import save_performance_events

        extractions = [
            PerformanceEventExtraction(
                event_type="sparring", discipline="boxing", extraction_confidence=0.8,
            ),
            PerformanceEventExtraction(
                event_type="drill", discipline="muay_thai", extraction_confidence=0.7,
            ),
            PerformanceEventExtraction(
                event_type="competition", discipline="mma", extraction_confidence=0.9,
            ),
        ]
        rows = await save_performance_events(
            db_session, test_user_id, None, extractions
        )
        assert len(rows) == 3

    @pytest.mark.asyncio
    async def test_save_empty_list(self, db_session, test_user_id):
        from app.services.memory import save_performance_events

        rows = await save_performance_events(
            db_session, test_user_id, uuid.uuid4(), []
        )
        assert rows == []

    @pytest.mark.asyncio
    async def test_event_date_defaults_to_today(self, db_session, test_user_id):
        from app.services.memory import save_performance_events

        extraction = PerformanceEventExtraction(
            event_type="drill",
            discipline="wrestling",
            event_date=None,
            extraction_confidence=0.6,
        )
        rows = await save_performance_events(
            db_session, test_user_id, None, [extraction]
        )
        assert rows[0].event_date == date.today()

    @pytest.mark.asyncio
    async def test_nullable_enums_stored_as_none(self, db_session, test_user_id):
        from app.services.memory import save_performance_events

        extraction = PerformanceEventExtraction(
            event_type="open_mat",
            discipline="bjj_nogi",
            outcome=None,
            failure_domain=None,
            cns_status=None,
            extraction_confidence=0.5,
        )
        rows = await save_performance_events(
            db_session, test_user_id, None, [extraction]
        )
        row = rows[0]
        assert row.outcome is None
        assert row.failure_domain is None
        assert row.cns_status is None

    @pytest.mark.asyncio
    async def test_literal_to_enum_mapping(self, db_session, test_user_id):
        from app.services.memory import save_performance_events

        extraction = PerformanceEventExtraction(
            event_type="open_mat",
            discipline="bjj_nogi",
            outcome="mixed",
            failure_domain="mental",
            cns_status="depleted",
            extraction_confidence=0.75,
        )
        rows = await save_performance_events(
            db_session, test_user_id, None, [extraction]
        )
        row = rows[0]
        assert row.event_type == EventType.OPEN_MAT
        assert row.discipline == Discipline.BJJ_NOGI
        assert row.outcome == Outcome.MIXED
        assert row.failure_domain == FailureDomain.MENTAL
        assert row.cns_status == CnsStatus.DEPLETED


# ── Issue 4: upsert_training_state ───────────────────────────────────────────


class TestUpsertTrainingState:
    """Test insert and replace semantics for mutable training state."""

    @pytest.mark.asyncio
    async def test_insert_new_state(self, db_session, test_user_id):
        from app.services.memory import upsert_training_state

        state = UserTrainingStateExtraction(
            current_focus=["guard retention", "takedown defense"],
            active_injuries=["sore left knee"],
            short_term_goals=["compete in April"],
        )
        row = await upsert_training_state(db_session, test_user_id, state)

        assert row.user_id == test_user_id
        assert row.current_focus == ["guard retention", "takedown defense"]
        assert row.active_injuries == ["sore left knee"]
        assert row.short_term_goals == ["compete in April"]
        assert row.created_at is not None

    @pytest.mark.asyncio
    async def test_update_replaces_state(self, db_session, test_user_id):
        from app.services.memory import upsert_training_state

        state_v1 = UserTrainingStateExtraction(
            current_focus=["guard retention"],
            active_injuries=["sore left knee"],
            short_term_goals=["compete in April"],
        )
        await upsert_training_state(db_session, test_user_id, state_v1)

        state_v2 = UserTrainingStateExtraction(
            current_focus=["leg kicks", "clinch work"],
            active_injuries=[],
            short_term_goals=["compete in June"],
        )
        row = await upsert_training_state(db_session, test_user_id, state_v2)

        assert row.current_focus == ["leg kicks", "clinch work"]
        assert row.active_injuries == []
        assert row.short_term_goals == ["compete in June"]

    @pytest.mark.asyncio
    async def test_created_at_not_modified_on_update(self, db_session, test_user_id):
        from app.services.memory import upsert_training_state

        state_v1 = UserTrainingStateExtraction(current_focus=["boxing basics"])
        row1 = await upsert_training_state(db_session, test_user_id, state_v1)
        created_at_v1 = row1.created_at

        state_v2 = UserTrainingStateExtraction(current_focus=["wrestling"])
        row2 = await upsert_training_state(db_session, test_user_id, state_v2)

        assert row2.created_at == created_at_v1

    @pytest.mark.asyncio
    async def test_updated_at_changes_on_update(self, db_session, test_user_id):
        from app.services.memory import upsert_training_state
        import asyncio

        state_v1 = UserTrainingStateExtraction(current_focus=["boxing basics"])
        row1 = await upsert_training_state(db_session, test_user_id, state_v1)

        # Small delay so timestamps differ
        await asyncio.sleep(0.05)

        state_v2 = UserTrainingStateExtraction(current_focus=["wrestling"])
        row2 = await upsert_training_state(db_session, test_user_id, state_v2)

        assert row2.updated_at is not None
        # On first insert, updated_at may be None or same as created_at
        # On second upsert, updated_at must be set
        if row1.updated_at is not None:
            assert row2.updated_at >= row1.updated_at

    @pytest.mark.asyncio
    async def test_empty_lists_stored(self, db_session, test_user_id):
        from app.services.memory import upsert_training_state

        state = UserTrainingStateExtraction(
            current_focus=[],
            active_injuries=[],
            short_term_goals=[],
        )
        row = await upsert_training_state(db_session, test_user_id, state)

        assert row.current_focus == []
        assert row.active_injuries == []
        assert row.short_term_goals == []


# ── Issue 5: get_recent_telemetry ────────────────────────────────────────────


class TestGetRecentTelemetry:
    """Test lightweight telemetry query for context injection."""

    @pytest.mark.asyncio
    async def test_returns_events_within_range(self, db_session, test_user_id):
        from app.services.memory import save_performance_events, get_recent_telemetry

        # Insert an event dated 3 days ago
        extraction = PerformanceEventExtraction(
            event_type="sparring",
            discipline="boxing",
            event_date=date.today() - timedelta(days=3),
            extraction_confidence=0.8,
        )
        await save_performance_events(
            db_session, test_user_id, None, [extraction]
        )

        result = await get_recent_telemetry(db_session, test_user_id, days=14)
        assert len(result["events"]) == 1
        assert result["events"][0].event_type == EventType.SPARRING

    @pytest.mark.asyncio
    async def test_excludes_old_events(self, db_session, test_user_id):
        from app.services.memory import save_performance_events, get_recent_telemetry

        # Insert an event dated 15 days ago
        extraction = PerformanceEventExtraction(
            event_type="drill",
            discipline="muay_thai",
            event_date=date.today() - timedelta(days=15),
            extraction_confidence=0.7,
        )
        await save_performance_events(
            db_session, test_user_id, None, [extraction]
        )

        result = await get_recent_telemetry(db_session, test_user_id, days=14)
        assert len(result["events"]) == 0

    @pytest.mark.asyncio
    async def test_no_training_state(self, db_session, test_user_id):
        from app.services.memory import get_recent_telemetry

        result = await get_recent_telemetry(db_session, test_user_id)
        assert result["training_state"] is None

    @pytest.mark.asyncio
    async def test_empty_db(self, db_session, test_user_id):
        from app.services.memory import get_recent_telemetry

        result = await get_recent_telemetry(db_session, test_user_id)
        assert result["events"] == []
        assert result["training_state"] is None
