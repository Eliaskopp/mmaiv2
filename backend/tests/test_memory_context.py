"""Tests for memory telemetry injection into _build_system_prompt (Slice 6)."""

import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError
from app.models.memory import (
    CnsStatus,
    Discipline,
    EventType,
    FailureDomain,
    Outcome,
    PerformanceEvent,
    UserTrainingState,
)


def _make_event(**overrides) -> MagicMock:
    """Create a mock PerformanceEvent with attribute access."""
    defaults = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "conversation_id": None,
        "event_type": EventType.SPARRING,
        "discipline": Discipline.BOXING,
        "outcome": None,
        "finish_type": None,
        "root_causes": [],
        "highlights": [],
        "opponent_description": None,
        "rpe_score": None,
        "failure_domain": None,
        "cns_status": None,
        "event_date": date.today(),
        "extraction_confidence": 0.8,
    }
    defaults.update(overrides)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def _make_state(**overrides) -> MagicMock:
    """Create a mock UserTrainingState with attribute access."""
    defaults = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "current_focus": [],
        "active_injuries": [],
        "short_term_goals": [],
    }
    defaults.update(overrides)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def _mock_db_execute_empty():
    """Return a mock db that returns empty results for training sessions."""
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)
    return mock_db


@pytest.mark.asyncio
async def test_system_prompt_includes_events():
    """Mock get_recent_telemetry to return 3 events — prompt contains Performance Memory lines."""
    from app.services.conversation import _build_system_prompt

    events = [
        _make_event(
            event_date=date.today() - timedelta(days=i),
            event_type=EventType.SPARRING,
            discipline=Discipline.BJJ_GI,
            rpe_score=7,
            failure_domain=FailureDomain.TECHNICAL,
            cns_status=CnsStatus.SLUGGISH,
        )
        for i in range(3)
    ]
    telemetry = {"events": events, "training_state": None}

    mock_db = _mock_db_execute_empty()
    with (
        patch("app.services.profile.get_profile", side_effect=EntityNotFoundError("Profile")),
        patch("app.services.recovery.get_log_by_date", side_effect=EntityNotFoundError("Recovery")),
        patch("app.services.stats.get_acwr", side_effect=Exception("no stats")),
        patch("app.services.memory.get_recent_telemetry", return_value=telemetry) as mock_telem,
    ):
        prompt = await _build_system_prompt(mock_db, uuid.uuid4())

    mock_telem.assert_called_once()
    assert "Performance Memory" in prompt
    assert "Sparring" in prompt
    assert "Bjj Gi" in prompt
    assert "RPE 7" in prompt
    assert "Technical" in prompt
    assert "CNS: Sluggish" in prompt


@pytest.mark.asyncio
async def test_system_prompt_includes_training_state():
    """Mock returns training state — prompt contains Training State line."""
    from app.services.conversation import _build_system_prompt

    state = _make_state(
        current_focus=["guard retention", "takedown defense"],
        active_injuries=["sore left knee"],
        short_term_goals=["compete in April"],
    )
    telemetry = {"events": [], "training_state": state}

    mock_db = _mock_db_execute_empty()
    with (
        patch("app.services.profile.get_profile", side_effect=EntityNotFoundError("Profile")),
        patch("app.services.recovery.get_log_by_date", side_effect=EntityNotFoundError("Recovery")),
        patch("app.services.stats.get_acwr", side_effect=Exception("no stats")),
        patch("app.services.memory.get_recent_telemetry", return_value=telemetry),
    ):
        prompt = await _build_system_prompt(mock_db, uuid.uuid4())

    assert "Training State" in prompt
    assert "guard retention" in prompt
    assert "takedown defense" in prompt
    assert "sore left knee" in prompt
    assert "compete in April" in prompt


@pytest.mark.asyncio
async def test_system_prompt_caps_at_7_events():
    """Return 10 events — only 7 lines in output."""
    from app.services.conversation import _build_system_prompt

    events = [
        _make_event(
            event_date=date.today() - timedelta(days=i),
            event_type=EventType.DRILL,
            discipline=Discipline.MUAY_THAI,
        )
        for i in range(10)
    ]
    telemetry = {"events": events, "training_state": None}

    mock_db = _mock_db_execute_empty()
    with (
        patch("app.services.profile.get_profile", side_effect=EntityNotFoundError("Profile")),
        patch("app.services.recovery.get_log_by_date", side_effect=EntityNotFoundError("Recovery")),
        patch("app.services.stats.get_acwr", side_effect=Exception("no stats")),
        patch("app.services.memory.get_recent_telemetry", return_value=telemetry),
    ):
        prompt = await _build_system_prompt(mock_db, uuid.uuid4())

    # Count pipe-separated event lines under "Performance Memory"
    lines = prompt.split("\n")
    memory_start = None
    for i, line in enumerate(lines):
        if "Performance Memory" in line:
            memory_start = i
            break

    assert memory_start is not None, "Performance Memory header not found"
    # Count event lines after the header (pipe-separated, non-empty)
    event_lines = []
    for line in lines[memory_start + 1:]:
        if "|" in line and line.strip():
            event_lines.append(line)
        elif line.strip() and "|" not in line:
            break  # Hit the next section
    assert len(event_lines) == 7


@pytest.mark.asyncio
async def test_system_prompt_empty_telemetry():
    """Empty events + null state — no memory lines, prompt still valid."""
    from app.services.conversation import _build_system_prompt

    telemetry = {"events": [], "training_state": None}

    mock_db = _mock_db_execute_empty()
    with (
        patch("app.services.profile.get_profile", side_effect=EntityNotFoundError("Profile")),
        patch("app.services.recovery.get_log_by_date", side_effect=EntityNotFoundError("Recovery")),
        patch("app.services.stats.get_acwr", side_effect=Exception("no stats")),
        patch("app.services.memory.get_recent_telemetry", return_value=telemetry),
    ):
        prompt = await _build_system_prompt(mock_db, uuid.uuid4())

    assert "Performance Memory" not in prompt
    assert "Training State" not in prompt
    assert len(prompt) > 50


@pytest.mark.asyncio
async def test_system_prompt_telemetry_error_graceful():
    """get_recent_telemetry raises Exception — no crash, prompt builds without memory section."""
    from app.services.conversation import _build_system_prompt

    mock_db = _mock_db_execute_empty()
    with (
        patch("app.services.profile.get_profile", side_effect=EntityNotFoundError("Profile")),
        patch("app.services.recovery.get_log_by_date", side_effect=EntityNotFoundError("Recovery")),
        patch("app.services.stats.get_acwr", side_effect=Exception("no stats")),
        patch("app.services.memory.get_recent_telemetry", side_effect=Exception("DB down")),
    ):
        prompt = await _build_system_prompt(mock_db, uuid.uuid4())

    assert "Performance Memory" not in prompt
    assert "Training State" not in prompt
    assert len(prompt) > 50
