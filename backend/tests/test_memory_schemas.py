"""TDD tests for backend/app/schemas/memory.py — the Pydantic extraction shield."""

import uuid
from datetime import date, datetime

import pytest
from pydantic import ValidationError


# ── Issue 2.1: PerformanceEventExtraction ────────────────────────

class TestPerformanceEventExtraction:
    """Validate the AI extraction shield for PerformanceEvent."""

    @pytest.fixture
    def valid_payload(self):
        return {
            "event_type": "sparring",
            "discipline": "bjj_gi",
            "outcome": "win",
            "finish_type": "rear naked choke",
            "root_causes": ["poor guard retention"],
            "highlights": ["landed sweep from half guard"],
            "opponent_description": "blue belt, ~80kg",
            "rpe_score": 7,
            "failure_domain": "technical",
            "cns_status": "optimal",
            "event_date": "2026-03-22",
            "extraction_confidence": 0.85,
        }

    def test_valid_extraction_passes(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        result = PerformanceEventExtraction(**valid_payload)
        assert result.event_type == "sparring"
        assert result.discipline == "bjj_gi"
        assert result.rpe_score == 7
        assert result.extraction_confidence == 0.85

    def test_minimal_required_fields_only(self):
        from app.schemas.memory import PerformanceEventExtraction

        result = PerformanceEventExtraction(
            event_type="drill",
            discipline="muay_thai",
        )
        assert result.outcome is None
        assert result.rpe_score is None
        assert result.root_causes == []
        assert result.highlights == []
        assert result.extraction_confidence == 0.0

    # ── rpe_score: strictly 1-10 ──

    @pytest.mark.parametrize("val", [1, 5, 10])
    def test_rpe_score_valid_range(self, valid_payload, val):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["rpe_score"] = val
        result = PerformanceEventExtraction(**valid_payload)
        assert result.rpe_score == val

    @pytest.mark.parametrize("val", [0, -1, 11, 100])
    def test_rpe_score_rejects_out_of_range(self, valid_payload, val):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["rpe_score"] = val
        with pytest.raises(ValidationError):
            PerformanceEventExtraction(**valid_payload)

    def test_rpe_score_none_allowed(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["rpe_score"] = None
        result = PerformanceEventExtraction(**valid_payload)
        assert result.rpe_score is None

    # ── failure_domain: Literal enforcement ──

    @pytest.mark.parametrize("val", ["technical", "tactical", "physical", "mental"])
    def test_failure_domain_accepts_valid(self, valid_payload, val):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["failure_domain"] = val
        result = PerformanceEventExtraction(**valid_payload)
        assert result.failure_domain == val

    @pytest.mark.parametrize("val", ["cardio", "endurance", "speed", ""])
    def test_failure_domain_rejects_invalid(self, valid_payload, val):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["failure_domain"] = val
        with pytest.raises(ValidationError):
            PerformanceEventExtraction(**valid_payload)

    # ── cns_status: Literal enforcement ──

    @pytest.mark.parametrize("val", ["optimal", "sluggish", "depleted"])
    def test_cns_status_accepts_valid(self, valid_payload, val):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["cns_status"] = val
        result = PerformanceEventExtraction(**valid_payload)
        assert result.cns_status == val

    @pytest.mark.parametrize("val", ["tired", "wired", "fresh", ""])
    def test_cns_status_rejects_invalid(self, valid_payload, val):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["cns_status"] = val
        with pytest.raises(ValidationError):
            PerformanceEventExtraction(**valid_payload)

    # ── root_causes / highlights: max 5 items, each <= 200 chars ──

    def test_root_causes_accepts_up_to_5(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["root_causes"] = ["a", "b", "c", "d", "e"]
        result = PerformanceEventExtraction(**valid_payload)
        assert len(result.root_causes) == 5

    def test_root_causes_rejects_more_than_5(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["root_causes"] = ["a", "b", "c", "d", "e", "f"]
        with pytest.raises(ValidationError):
            PerformanceEventExtraction(**valid_payload)

    def test_root_causes_rejects_long_string(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["root_causes"] = ["x" * 201]
        with pytest.raises(ValidationError):
            PerformanceEventExtraction(**valid_payload)

    def test_root_causes_accepts_200_char_string(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["root_causes"] = ["x" * 200]
        result = PerformanceEventExtraction(**valid_payload)
        assert len(result.root_causes[0]) == 200

    def test_highlights_accepts_up_to_5(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["highlights"] = ["a", "b", "c", "d", "e"]
        result = PerformanceEventExtraction(**valid_payload)
        assert len(result.highlights) == 5

    def test_highlights_rejects_more_than_5(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["highlights"] = ["a", "b", "c", "d", "e", "f"]
        with pytest.raises(ValidationError):
            PerformanceEventExtraction(**valid_payload)

    def test_highlights_rejects_long_string(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["highlights"] = ["x" * 201]
        with pytest.raises(ValidationError):
            PerformanceEventExtraction(**valid_payload)

    # ── None → [] coercion ──

    def test_root_causes_none_coerced_to_empty_list(self):
        from app.schemas.memory import PerformanceEventExtraction

        result = PerformanceEventExtraction(
            event_type="sparring", discipline="mma", root_causes=None,
        )
        assert result.root_causes == []

    def test_highlights_none_coerced_to_empty_list(self):
        from app.schemas.memory import PerformanceEventExtraction

        result = PerformanceEventExtraction(
            event_type="sparring", discipline="mma", highlights=None,
        )
        assert result.highlights == []

    # ── extra = "forbid" ──

    def test_extra_fields_rejected(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["mood"] = "happy"
        with pytest.raises(ValidationError, match="mood"):
            PerformanceEventExtraction(**valid_payload)

    def test_multiple_extra_fields_rejected(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["foo"] = 1
        valid_payload["bar"] = 2
        with pytest.raises(ValidationError):
            PerformanceEventExtraction(**valid_payload)

    # ── extraction_confidence: 0.0-1.0 ──

    @pytest.mark.parametrize("val", [0.0, 0.5, 1.0])
    def test_extraction_confidence_valid(self, valid_payload, val):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["extraction_confidence"] = val
        result = PerformanceEventExtraction(**valid_payload)
        assert result.extraction_confidence == val

    @pytest.mark.parametrize("val", [-0.1, 1.1, 2.0])
    def test_extraction_confidence_rejects_out_of_range(self, valid_payload, val):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["extraction_confidence"] = val
        with pytest.raises(ValidationError):
            PerformanceEventExtraction(**valid_payload)

    # ── String length constraints ──

    def test_finish_type_rejects_over_100_chars(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["finish_type"] = "x" * 101
        with pytest.raises(ValidationError):
            PerformanceEventExtraction(**valid_payload)

    def test_opponent_description_rejects_over_200_chars(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["opponent_description"] = "x" * 201
        with pytest.raises(ValidationError):
            PerformanceEventExtraction(**valid_payload)

    # ── event_type / discipline: Literal enforcement ──

    def test_event_type_rejects_invalid(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["event_type"] = "training"
        with pytest.raises(ValidationError):
            PerformanceEventExtraction(**valid_payload)

    def test_discipline_rejects_invalid(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["discipline"] = "karate"
        with pytest.raises(ValidationError):
            PerformanceEventExtraction(**valid_payload)

    def test_outcome_rejects_invalid(self, valid_payload):
        from app.schemas.memory import PerformanceEventExtraction

        valid_payload["outcome"] = "victory"
        with pytest.raises(ValidationError):
            PerformanceEventExtraction(**valid_payload)


# ── Issue 2.2: UserTrainingStateExtraction ───────────────────────

class TestUserTrainingStateExtraction:
    """Validate the AI extraction shield for UserTrainingState."""

    def test_valid_extraction(self):
        from app.schemas.memory import UserTrainingStateExtraction

        result = UserTrainingStateExtraction(
            current_focus=["takedown defense"],
            active_injuries=["sore left knee"],
            short_term_goals=["compete in April"],
        )
        assert result.current_focus == ["takedown defense"]

    def test_all_defaults(self):
        from app.schemas.memory import UserTrainingStateExtraction

        result = UserTrainingStateExtraction()
        assert result.current_focus == []
        assert result.active_injuries == []
        assert result.short_term_goals == []

    @pytest.mark.parametrize("field", ["current_focus", "active_injuries", "short_term_goals"])
    def test_list_accepts_up_to_5(self, field):
        from app.schemas.memory import UserTrainingStateExtraction

        result = UserTrainingStateExtraction(**{field: ["a", "b", "c", "d", "e"]})
        assert len(getattr(result, field)) == 5

    @pytest.mark.parametrize("field", ["current_focus", "active_injuries", "short_term_goals"])
    def test_list_rejects_more_than_5(self, field):
        from app.schemas.memory import UserTrainingStateExtraction

        with pytest.raises(ValidationError):
            UserTrainingStateExtraction(**{field: ["a", "b", "c", "d", "e", "f"]})

    @pytest.mark.parametrize("field", ["current_focus", "active_injuries", "short_term_goals"])
    def test_element_rejects_over_200_chars(self, field):
        from app.schemas.memory import UserTrainingStateExtraction

        with pytest.raises(ValidationError):
            UserTrainingStateExtraction(**{field: ["x" * 201]})

    @pytest.mark.parametrize("field", ["current_focus", "active_injuries", "short_term_goals"])
    def test_element_accepts_200_chars(self, field):
        from app.schemas.memory import UserTrainingStateExtraction

        result = UserTrainingStateExtraction(**{field: ["x" * 200]})
        assert len(getattr(result, field)[0]) == 200

    @pytest.mark.parametrize("field", ["current_focus", "active_injuries", "short_term_goals"])
    def test_none_coerced_to_empty_list(self, field):
        from app.schemas.memory import UserTrainingStateExtraction

        result = UserTrainingStateExtraction(**{field: None})
        assert getattr(result, field) == []

    def test_extra_fields_rejected(self):
        from app.schemas.memory import UserTrainingStateExtraction

        with pytest.raises(ValidationError, match="belt_rank"):
            UserTrainingStateExtraction(belt_rank="purple")


# ── Issue 2.3: Response Models + List Wrappers ───────────────────

class TestPerformanceEventResponse:
    """Validate ORM → response serialisation."""

    @pytest.fixture
    def orm_dict(self):
        return {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "conversation_id": uuid.uuid4(),
            "event_type": "sparring",
            "discipline": "bjj_gi",
            "outcome": "win",
            "finish_type": "armbar",
            "root_causes": ["bad posture"],
            "highlights": ["clean sweep"],
            "opponent_description": "purple belt",
            "rpe_score": 8,
            "failure_domain": "technical",
            "cns_status": "optimal",
            "event_date": date(2026, 3, 22),
            "extraction_confidence": 0.9,
            "created_at": datetime(2026, 3, 22, 12, 0, 0),
        }

    def test_from_attributes(self, orm_dict):
        from app.schemas.memory import PerformanceEventResponse

        result = PerformanceEventResponse.model_validate(orm_dict)
        assert result.event_type == "sparring"
        assert result.id == orm_dict["id"]

    def test_no_updated_at_field(self):
        from app.schemas.memory import PerformanceEventResponse

        fields = PerformanceEventResponse.model_fields
        assert "updated_at" not in fields

    def test_created_at_present(self, orm_dict):
        from app.schemas.memory import PerformanceEventResponse

        result = PerformanceEventResponse.model_validate(orm_dict)
        assert result.created_at == orm_dict["created_at"]


class TestPerformanceEventListResponse:

    def test_list_shape(self):
        from app.schemas.memory import PerformanceEventListResponse

        result = PerformanceEventListResponse(items=[], total=0, offset=0, limit=20)
        assert result.items == []
        assert result.total == 0


class TestUserTrainingStateResponse:

    @pytest.fixture
    def orm_dict(self):
        return {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "current_focus": ["guard passing"],
            "active_injuries": [],
            "short_term_goals": ["compete"],
            "created_at": datetime(2026, 3, 22, 12, 0, 0),
            "updated_at": datetime(2026, 3, 22, 13, 0, 0),
        }

    def test_from_attributes(self, orm_dict):
        from app.schemas.memory import UserTrainingStateResponse

        result = UserTrainingStateResponse.model_validate(orm_dict)
        assert result.current_focus == ["guard passing"]

    def test_updated_at_present(self, orm_dict):
        from app.schemas.memory import UserTrainingStateResponse

        result = UserTrainingStateResponse.model_validate(orm_dict)
        assert result.updated_at == orm_dict["updated_at"]

    def test_updated_at_nullable(self, orm_dict):
        from app.schemas.memory import UserTrainingStateResponse

        orm_dict["updated_at"] = None
        result = UserTrainingStateResponse.model_validate(orm_dict)
        assert result.updated_at is None
