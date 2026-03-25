# PRD: Track 1, Slices 5 & 6 — Read Endpoints + State Injection

**Depends on:** Slice 1 (models), Slice 2 (schemas), Slice 3 (service + Grok + prompt), Slice 4 (background orchestrator) — all complete
**Branch:** `qa/milestone-4-burndown`

---

## Purpose

Complete Track 1 by delivering the final two capabilities:

1. **Slice 5 — Read Endpoints:** Create `routes/memory.py` with two read-only endpoints exposing performance events and training state. No mutations — all writes happen via background extraction (Slice 4).

2. **Slice 6 — State Injection:** Modify `_build_system_prompt()` in `services/conversation.py` to inject recent memory telemetry into the coach's context window, so Grok can reference the athlete's real training history when coaching.

After these slices, the memory system is end-to-end: extraction → storage → API access → coach context.

---

## Slice 5: Read Endpoints

### File 1: `backend/app/routes/memory.py` (NEW)

Read-only router following the `note.py` pattern: protected via `get_current_user`, paginated list endpoint + single resource endpoint.

#### Router setup

```python
from fastapi import APIRouter

router = APIRouter(prefix="/memory", tags=["memory"])
```

#### Endpoint 1: `GET /memory/events`

Paginated list of performance events for the authenticated user.

```python
@router.get("/events", response_model=PerformanceEventListResponse)
async def list_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
```

**Implementation:**

1. Query `PerformanceEvent` where `user_id == current_user.id`
2. Order by `event_date DESC`, then `created_at DESC` (newest first)
3. Apply `offset` and `limit`
4. Count total rows (same filter, no offset/limit)
5. Return `PerformanceEventListResponse(items=[...], total=total, offset=offset, limit=limit)`

**SQL shape (via SQLAlchemy):**

```python
base = select(PerformanceEvent).where(PerformanceEvent.user_id == current_user.id)

count_q = select(func.count()).select_from(base.subquery())
total = (await db.execute(count_q)).scalar_one()

rows_q = (
    base
    .order_by(PerformanceEvent.event_date.desc(), PerformanceEvent.created_at.desc())
    .offset(offset)
    .limit(limit)
)
rows = (await db.execute(rows_q)).scalars().all()
```

This mirrors the pagination pattern used in `note.py:list_notes` and `conversation.py:list_conversations`.

#### Endpoint 2: `GET /memory/state`

Returns the current `UserTrainingState` for the authenticated user, or `null` if none exists.

```python
@router.get("/state", response_model=UserTrainingStateResponse | None)
async def get_state(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
```

**Implementation:**

1. Query `UserTrainingState` where `user_id == current_user.id`
2. If `None` → return `None` (200 with `null` body)
3. If found → return `UserTrainingStateResponse.model_validate(state)`

**Why return null instead of 404:** Training state is created lazily by the background extractor. A user who has never discussed training context won't have a row, and that's a normal state — not an error. Returning `null` lets the frontend handle "no state yet" without error branching.

#### Imports

```python
import uuid

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
```

### File 2: `backend/app/main.py` (MODIFY)

Two changes:

#### Change 1 — Add import (line 12)

```python
from app.routes import auth, conversation, health, journal, memory, note, profile, recovery, stats
```

(Add `memory` to the existing multi-import, keeping alphabetical order.)

#### Change 2 — Register router (after line 45, after `note.router`)

```python
app.include_router(memory.router, prefix="/api/v1")
```

Place it after `note.router` and before `stats.router` to maintain rough alphabetical grouping.

---

## Slice 6: State Injection

### File 3: `backend/app/services/conversation.py` (MODIFY)

Modify `_build_system_prompt()` to call `memory_service.get_recent_telemetry()` and inject the result into the athlete context.

#### Change 1 — Add import (inside `_build_system_prompt`, lazy import block)

```python
from app.services import memory as memory_service
```

Following the existing pattern of lazy imports inside the function (see `profile_service`, `recovery_service`, `stats_service`).

#### Change 2 — Add memory telemetry block

Insert a new block **after** the ACWR block (after line 104) and **before** the final `athlete_context` join (line 106).

```python
# Fetch memory telemetry — recent performance events + training state
try:
    telemetry = await memory_service.get_recent_telemetry(db, user_id)
    telemetry_events = telemetry.get("events", [])
    telemetry_state = telemetry.get("training_state")

    # Format up to 7 most recent events as compact entries
    if telemetry_events:
        event_lines: list[str] = []
        for e in telemetry_events[:7]:
            parts = [
                str(e.event_date),
                e.event_type.value.replace("_", " ").title(),
            ]
            if e.discipline:
                parts.append(e.discipline.value.replace("_", " ").title())
            if e.rpe_score is not None:
                parts.append(f"RPE {e.rpe_score}")
            if e.failure_domain:
                parts.append(e.failure_domain.value.title())
            if e.cns_status:
                parts.append(f"CNS: {e.cns_status.value.title()}")
            if e.outcome:
                parts.append(e.outcome.value.title())
            event_lines.append(" | ".join(parts))
        context_lines.append(
            "Performance Memory (last 14 days):\n" + "\n".join(event_lines)
        )

    # Append training state if it exists
    if telemetry_state:
        state_parts: list[str] = []
        if telemetry_state.current_focus:
            state_parts.append(f"Focus: {', '.join(telemetry_state.current_focus)}")
        if telemetry_state.active_injuries:
            state_parts.append(f"Injuries: {', '.join(telemetry_state.active_injuries)}")
        if telemetry_state.short_term_goals:
            state_parts.append(f"Goals: {', '.join(telemetry_state.short_term_goals)}")
        if state_parts:
            context_lines.append("Training State: " + ". ".join(state_parts) + ".")
except Exception:
    pass
```

#### Format Rationale

**Events** are formatted as pipe-separated compact lines mirroring the existing "Recent Sessions" format:

```
Performance Memory (last 14 days):
2026-03-20 | Sparring | Bjj Gi | RPE 7 | Technical | CNS: Sluggish | Loss
2026-03-18 | Drill | Muay Thai | RPE 5 | CNS: Optimal
2026-03-15 | Competition | Mma | RPE 9 | Physical | CNS: Depleted | Win
```

**Training State** is formatted as a single line:

```
Training State: Focus: guard retention, takedown defense. Injuries: sore left knee. Goals: compete in April.
```

#### Cap at 7 events

The `[:7]` slice caps context injection at 7 events. This keeps the system prompt bounded while covering roughly two weeks of typical training (3-4 sessions/week). The service still fetches up to 50 for the API endpoint — the cap is only applied at the formatting layer.

#### Graceful Degradation

- If `get_recent_telemetry()` throws → caught by `except Exception: pass`, no crash
- If events list is empty → no "Performance Memory" line added
- If training state is `None` → no "Training State" line added
- If all three JSONB fields on training state are empty lists → no line added (the `if state_parts` guard)

The coach prompt still works perfectly with zero memory data — it just has less context.

#### Final `_build_system_prompt` shape

```python
async def _build_system_prompt(db: AsyncSession, user_id: uuid.UUID) -> str:
    from app.services import profile as profile_service
    from app.services import recovery as recovery_service
    from app.services import memory as memory_service   # NEW

    context_lines: list[str] = []

    # ... existing profile block ...
    # ... existing recovery block ...
    # ... existing recent sessions block ...
    # ... existing ACWR block ...
    # ... NEW memory telemetry block ...

    athlete_context = "\n".join(context_lines) if context_lines else "No profile or recovery data available."
    return COACH_SYSTEM_PROMPT.replace("{athlete_context}", athlete_context)
```

---

## Testing

### Slice 5 Tests

File: `backend/tests/test_memory_routes.py` (NEW)

| Test | What it verifies |
|------|-----------------|
| `test_list_events_empty` | Authenticated user with no events → `{"items": [], "total": 0, ...}` |
| `test_list_events_returns_own_data` | Events created for user A are returned; user B sees nothing |
| `test_list_events_pagination` | `offset=1&limit=2` on 5 events → correct slice, correct total |
| `test_list_events_order` | Events returned newest-first by `event_date` |
| `test_get_state_null` | User with no training state → `null` response (200, not 404) |
| `test_get_state_returns_data` | User with training state → correct JSON shape |
| `test_endpoints_require_auth` | Both endpoints return 401 without Bearer token |

**Strategy:** Use the memory service directly in test setup to insert known data, then hit the HTTP endpoints via `AsyncClient`.

### Slice 6 Tests

File: `backend/tests/test_memory_context.py` (NEW)

| Test | What it verifies |
|------|-----------------|
| `test_system_prompt_includes_events` | Mock `get_recent_telemetry` to return 3 events → prompt contains "Performance Memory" + pipe-separated lines |
| `test_system_prompt_includes_training_state` | Mock returns training state → prompt contains "Training State: Focus: ..." |
| `test_system_prompt_caps_at_7_events` | Return 10 events → only 7 lines in output |
| `test_system_prompt_empty_telemetry` | Empty events + null state → no memory lines, prompt still valid |
| `test_system_prompt_telemetry_error_graceful` | Mock raises `Exception` → no crash, prompt builds without memory section |

**Strategy:** Mock `memory_service.get_recent_telemetry` to return canned data, then call `_build_system_prompt()` and assert on the resulting string.

---

## Out of Scope

- **Mutations via API** — no POST/PATCH/DELETE on memory endpoints. All writes happen via background extraction (Slice 4).
- **Filtering/search** — no query params for discipline, event_type, date range, etc. (future enhancement)
- **Frontend** — no React components for viewing memory data (separate track)
- **Alembic migrations** — tables exist from Slice 1
- **New dependencies** — none needed
- **Grok prompt changes** — extraction prompt is complete from Slice 3
- **Memory extraction orchestrator** — complete from Slice 4
