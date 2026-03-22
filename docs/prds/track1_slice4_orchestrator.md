# PRD: Track 1, Slice 4 — Background Task + Route Hookup

**Depends on:** Slice 1 (models), Slice 2 (schemas), Slice 3 (service + Grok method + prompt) — all complete
**Branch:** `qa/milestone-4-burndown`

---

## Purpose

Wire memory extraction into the live conversation flow. Two deliverables:

1. A background task orchestrator that calls Grok, validates the response, filters by confidence, and persists results
2. A one-line hookup in the `send_message` endpoint so memory extraction runs alongside note extraction

After this slice, every coach message triggers automatic memory extraction in the background — zero user-facing latency.

---

## File 1: `backend/app/services/memory_extraction.py` (NEW)

Single async function mirroring the pattern in `services/extraction.py`.

### Signature

```python
async def extract_and_save_memory(
    db_session_maker,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    user_content: str,
    assistant_content: str,
) -> None:
```

**Why `db_session_maker` as a parameter** (differs from `extract_and_save_notes` which imports `async_session` directly): accepts the session factory as an argument for testability — tests can inject a test-scoped factory without monkeypatching imports.

### Orchestration Flow

```
1. Build messages list:
   [
     {"role": "user", "content": user_content},
     {"role": "assistant", "content": assistant_content},
   ]

2. Call Grok:
   raw = await GrokClient().extract_memory(messages)
   if raw is None → return (Grok call failed, already logged)

3. Validate + filter performance events:
   validated_events = []
   for event_dict in raw.get("performance_events", []):
       extraction = PerformanceEventExtraction(**event_dict)
       if extraction.extraction_confidence >= 0.6:
           validated_events.append(extraction)

4. Validate training state (if present):
   raw_state = raw.get("training_state")
   validated_state = UserTrainingStateExtraction(**raw_state) if raw_state else None

5. Persist (only if there's something to save):
   async with db_session_maker() as db:
       if validated_events:
           await memory_service.save_performance_events(
               db, user_id, conversation_id, validated_events,
           )
       if validated_state:
           await memory_service.upsert_training_state(
               db, user_id, validated_state,
           )

6. Exception handling:
   Entire body wrapped in try/except Exception →
   logger.exception("Background memory extraction failed")
   Never re-raise — background tasks must not crash the worker.
```

### Confidence Threshold: Two-Layer Filter

| Layer | Threshold | Effect |
|-------|-----------|--------|
| Grok prompt | < 0.5 | Grok omits the event entirely (never appears in JSON) |
| Orchestrator | < 0.6 | Event is validated but **not persisted** — logged and discarded |

This means events with confidence 0.5–0.59 are extracted by Grok but filtered out before reaching the database. Only events with >= 0.6 are saved.

### Pydantic Validation Failures

If `PerformanceEventExtraction(**event_dict)` raises `ValidationError`:
- Log the error at WARNING level with the raw dict for debugging
- **Skip that event**, continue processing remaining events
- Do NOT abort the entire extraction — one malformed event should not block others

If `UserTrainingStateExtraction(**raw_state)` raises `ValidationError`:
- Log at WARNING level
- Set `validated_state = None` (skip training state, still save valid events)

### Imports

```python
import logging
import uuid

from pydantic import ValidationError

from app.schemas.memory import PerformanceEventExtraction, UserTrainingStateExtraction
from app.services.grok import GrokClient
from app.services import memory as memory_service
```

Note: does **not** import `async_session` — the session factory is passed in.

---

## File 2: `backend/app/routes/conversation.py` (MODIFY)

Two changes:

### Change 1 — Add import (line ~20)

```python
from app.services.memory_extraction import extract_and_save_memory
```

alongside the existing:
```python
from app.services.extraction import extract_and_save_notes
```

### Change 2 — Add background task (after line 107)

Inside `send_message()`, immediately after the existing `background_tasks.add_task(extract_and_save_notes, ...)` block, add:

```python
background_tasks.add_task(
    extract_and_save_memory,
    db_session_maker=async_session,
    user_id=current_user.id,
    conversation_id=conversation_id,
    user_content=body.content,
    assistant_content=assistant_msg.content,
)
```

This requires one additional import at the top:
```python
from app.core.database import async_session
```

### Final `send_message` endpoint shape

```python
async def send_message(
    request: Request,
    conversation_id: uuid.UUID,
    body: MessageCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_msg, assistant_msg = await conversation_service.send_message(
        db, current_user.id, conversation_id, body.content,
    )
    background_tasks.add_task(
        extract_and_save_notes,
        assistant_content=assistant_msg.content,
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    background_tasks.add_task(
        extract_and_save_memory,
        db_session_maker=async_session,
        user_id=current_user.id,
        conversation_id=conversation_id,
        user_content=body.content,
        assistant_content=assistant_msg.content,
    )
    return [
        MsgResponse.model_validate(user_msg),
        MsgResponse.model_validate(assistant_msg),
    ]
```

Both background tasks run concurrently after the response is sent to the client.

---

## Testing

### Unit tests for `memory_extraction.py`

File: `backend/tests/test_memory_extraction.py`

| Test | What it verifies |
|------|-----------------|
| `test_extract_and_save_memory_happy_path` | Full flow: Grok returns valid data → events + state persisted |
| `test_grok_returns_none_early_exit` | Grok failure → function returns cleanly, no DB calls |
| `test_confidence_below_threshold_filtered` | Event with confidence 0.55 → not persisted; event with 0.75 → persisted |
| `test_validation_error_skips_bad_event` | One malformed event dict → skipped, valid events still saved |
| `test_training_state_null_skipped` | `training_state: null` → only events saved, no upsert call |
| `test_empty_extraction_no_db_calls` | Empty events + null state → no session created at all |
| `test_exception_logged_not_raised` | Unexpected error → logged, never raised |

**Mock strategy:**
- Mock `GrokClient.extract_memory` to return canned dicts
- Pass a real `async_session` test factory (from conftest) as `db_session_maker`
- Assert DB state directly after function completes

### Integration smoke test

After deployment: send a message via the coach chat that includes a sparring debrief. Verify in the database that a `performance_events` row was created with the expected fields.

---

## Out of Scope

- **Routes for memory CRUD** — no `routes/memory.py`, no GET/LIST endpoints (future slice)
- **Context injection** — `_build_system_prompt` not modified to include telemetry (future slice)
- **Alembic migrations** — tables exist from Slice 1
- **Frontend** — none
- **New dependencies** — none needed
- **Modifying `extract_and_save_notes`** — existing note extraction stays as-is
