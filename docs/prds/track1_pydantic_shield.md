# PRD: Track 1 — Pydantic Extraction Shield

**File:** `backend/app/schemas/memory.py`
**Depends on:** `backend/app/models/memory.py` (Slice 1 — complete)
**Branch:** `qa/milestone-4-burndown`

---

## Purpose

Define the Pydantic validation layer ("shield") that sits between the Grok AI extraction output and the database. Every field extracted from chat by the AI must pass through these schemas before reaching `PerformanceEvent` or `UserTrainingState`. The shield enforces strict type/range/cardinality boundaries and rejects hallucinated keys.

---

## Schema Classes

### 1. Literal Type Aliases (module-level)

Following the established codebase pattern (journal.py, note.py), all enums are expressed as `Literal` type aliases — not Python `enum.Enum`.

| Alias | Values |
|-------|--------|
| `EventTypeLiteral` | `"sparring"`, `"competition"`, `"drill"`, `"open_mat"` |
| `DisciplineLiteral` | `"muay_thai"`, `"bjj_gi"`, `"bjj_nogi"`, `"boxing"`, `"mma"`, `"wrestling"` |
| `OutcomeLiteral` | `"win"`, `"loss"`, `"draw"`, `"no_contest"`, `"mixed"` |
| `FailureDomainLiteral` | `"technical"`, `"tactical"`, `"physical"`, `"mental"` |
| `CnsStatusLiteral` | `"optimal"`, `"sluggish"`, `"depleted"` |

---

### 2. `PerformanceEventExtraction` — AI Extraction Input

**Role:** Validates the raw JSON the Grok function-call returns. This is the primary shield.

**Config:** `model_config = {"extra": "forbid"}` — any key not listed below causes a `ValidationError`. This is a deliberate departure from the codebase default (which ignores extra fields) because AI output must be strictly gated.

| Field | Type | Constraint | Notes |
|-------|------|-----------|-------|
| `event_type` | `EventTypeLiteral` | required | — |
| `discipline` | `DisciplineLiteral` | required | — |
| `outcome` | `OutcomeLiteral \| None` | optional | — |
| `finish_type` | `str \| None` | `max_length=100` | e.g. "rear naked choke" |
| `root_causes` | `list[str]` | default `[]`, `max_length=5` on Field | Each string max 200 chars |
| `highlights` | `list[str]` | default `[]`, `max_length=5` on Field | Each string max 200 chars |
| `opponent_description` | `str \| None` | `max_length=200` | — |
| `rpe_score` | `int \| None` | `ge=1, le=10` | Strict 1-10 range |
| `failure_domain` | `FailureDomainLiteral \| None` | optional | — |
| `cns_status` | `CnsStatusLiteral \| None` | optional | — |
| `event_date` | `date \| None` | optional | Falls back to `func.current_date()` at DB level |
| `extraction_confidence` | `float` | `ge=0.0, le=1.0`, default `0.0` | AI self-assessed confidence |

**Validators:**
- `@field_validator("root_causes", "highlights", mode="before")`: coerce `None` to `[]` (AI may omit the field entirely).
- `@field_validator("root_causes", "highlights")`: validate each element is a string with `len <= 200`.

---

### 3. `PerformanceEventResponse` — API Read Model

**Role:** Serialises a `PerformanceEvent` ORM instance for API responses.

**Config:** `model_config = {"from_attributes": True}`

| Field | Type | Notes |
|-------|------|-------|
| `id` | `uuid.UUID` | — |
| `user_id` | `uuid.UUID` | — |
| `conversation_id` | `uuid.UUID \| None` | — |
| `event_type` | `str` | — |
| `discipline` | `str` | — |
| `outcome` | `str \| None` | — |
| `finish_type` | `str \| None` | — |
| `root_causes` | `list \| None` | — |
| `highlights` | `list \| None` | — |
| `opponent_description` | `str \| None` | — |
| `rpe_score` | `int \| None` | — |
| `failure_domain` | `str \| None` | — |
| `cns_status` | `str \| None` | — |
| `event_date` | `date` | — |
| `extraction_confidence` | `float` | — |
| `created_at` | `datetime` | Immutable |

No `updated_at` — PerformanceEvent is append-only.

---

### 4. `PerformanceEventListResponse` — Paginated List

| Field | Type |
|-------|------|
| `items` | `list[PerformanceEventResponse]` |
| `total` | `int` |
| `offset` | `int` |
| `limit` | `int` |

---

### 5. `UserTrainingStateExtraction` — AI Extraction Input

**Role:** Validates the AI's extraction of mutable training context. Same strict gating as PerformanceEventExtraction.

**Config:** `model_config = {"extra": "forbid"}`

| Field | Type | Constraint | Notes |
|-------|------|-----------|-------|
| `current_focus` | `list[str]` | default `[]`, `max_length=5` | Active training priorities |
| `active_injuries` | `list[str]` | default `[]`, `max_length=5` | Current injury notes |
| `short_term_goals` | `list[str]` | default `[]`, `max_length=5` | Near-term goals |

**Validators:**
- `@field_validator("current_focus", "active_injuries", "short_term_goals", mode="before")`: coerce `None` to `[]`.
- Each element: `str`, `len <= 200`.

---

### 6. `UserTrainingStateResponse` — API Read Model

**Config:** `model_config = {"from_attributes": True}`

| Field | Type |
|-------|------|
| `id` | `uuid.UUID` |
| `user_id` | `uuid.UUID` |
| `current_focus` | `list \| None` |
| `active_injuries` | `list \| None` |
| `short_term_goals` | `list \| None` |
| `created_at` | `datetime` |
| `updated_at` | `datetime \| None` |

---

## Rejection Behaviour Summary

| Scenario | Outcome |
|----------|---------|
| AI returns `rpe_score: 15` | `ValidationError` — outside 1-10 |
| AI returns `rpe_score: 0` | `ValidationError` — below minimum 1 |
| AI returns `{"mood": "happy"}` (hallucinated key) | `ValidationError` — `extra = "forbid"` |
| AI returns 8 root_causes | `ValidationError` — max_length=5 |
| AI returns `failure_domain: "cardio"` | `ValidationError` — not in Literal |
| AI returns `cns_status: "tired"` | `ValidationError` — not in Literal |
| AI returns `extraction_confidence: 1.5` | `ValidationError` — above 1.0 |
| AI omits `root_causes` entirely | Coerced to `[]` by validator |

---

## File Structure

```
backend/app/schemas/memory.py
```

Follows the established pattern:
1. Imports
2. Literal type aliases
3. Extraction models (with `extra = "forbid"`)
4. Response models (with `from_attributes = True`)
5. List wrappers

---

## Out of Scope

- Route/endpoint definitions (Slice 3+)
- Service layer logic (Slice 3+)
- Grok function-call schema registration (separate track)
- `UserTrainingState` update endpoint schemas (deferred — upsert logic is service-layer concern)
