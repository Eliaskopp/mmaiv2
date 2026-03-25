# PRD: Track 1, Slice 3 — Service + Grok Method + Extraction Prompt

**Depends on:** Slice 1 (`models/memory.py` — complete), Slice 2 (`schemas/memory.py` — complete)
**Branch:** `qa/milestone-4-burndown`

---

## Purpose

Wire the extraction pipeline from Grok output to database. Three deliverables:

1. A system prompt teaching Grok to map natural language to our domain enums
2. A new `extract_memory()` method on `GrokClient` using structured JSON output
3. A `memory.py` service with CRUD operations for performance events and training state

No routes, no integration into `conversation.py`, no frontend changes.

---

## File 1: `backend/app/prompts/memory_extraction.py` (NEW)

Single module-level constant `MEMORY_EXTRACTION_PROMPT` — follows the pattern of `backend/app/prompts/coach.py`.

### Output Schema

The prompt instructs Grok to return **exactly** this JSON shape:

```json
{
  "performance_events": [
    {
      "event_type": "sparring|competition|drill|open_mat",
      "discipline": "muay_thai|bjj_gi|bjj_nogi|boxing|mma|wrestling",
      "outcome": "win|loss|draw|no_contest|mixed" or null,
      "finish_type": "string (max 100)" or null,
      "root_causes": ["string (max 200)", ...],
      "highlights": ["string (max 200)", ...],
      "opponent_description": "string (max 200)" or null,
      "rpe_score": 1-10 or null,
      "failure_domain": "technical|tactical|physical|mental" or null,
      "cns_status": "optimal|sluggish|depleted" or null,
      "event_date": "YYYY-MM-DD" or null,
      "extraction_confidence": 0.0-1.0
    }
  ],
  "training_state": {
    "current_focus": ["string (max 200)", ...],
    "active_injuries": ["string (max 200)", ...],
    "short_term_goals": ["string (max 200)", ...]
  } or null
}
```

### Natural-Language-to-Enum Mapping Guidance

**`failure_domain`:**

| Natural language | Maps to |
|-----------------|---------|
| "heavy legs", "gassed out", "cardio failed" | `"physical"` |
| "didn't see the sweep", "wrong read", "bad positioning" | `"tactical"` |
| "couldn't finish the armbar", "bad hand position", "sloppy technique" | `"technical"` |
| "froze up", "panicked", "lost composure" | `"mental"` |

**`cns_status`:**

| Natural language | Maps to |
|-----------------|---------|
| "sharp", "everything clicked", "reactions were fast" | `"optimal"` |
| "slow reactions", "foggy", "couldn't string combinations" | `"sluggish"` |
| "completely flat", "no power", "moving through mud" | `"depleted"` |

### Confidence Scoring Rules

| Confidence | When to use |
|-----------|-------------|
| 0.9-1.0 | Explicit, detailed account — athlete clearly described the event |
| 0.7-0.89 | Clear event but some inference needed |
| 0.5-0.69 | Moderate inference — event mentioned in passing |
| < 0.5 | **Do not extract** — skip the event entirely |

### Extraction Rules

- Consolidate multiple rounds of the same session into **one** performance event
- `event_date` = `null` when the athlete doesn't specify a date (service layer defaults to today)
- `training_state` = `null` when nothing about focus, injuries, or goals is mentioned
- Lists capped at 5 items, strings at 200 chars
- Return ONLY valid JSON — no markdown fences, no commentary

### Few-Shot Examples

**Example 1 — Rich sparring debrief:**

Input:
> "Had 5 rounds of BJJ sparring today, gi. Got submitted twice — rear naked choke and a triangle. Managed to sweep one blue belt from half guard though. Legs felt heavy, RPE was probably a 7. I've been focusing on guard retention and takedown defense lately. Knee is still a bit dodgy from last week."

Output:
```json
{
  "performance_events": [
    {
      "event_type": "sparring",
      "discipline": "bjj_gi",
      "outcome": "loss",
      "finish_type": "rear naked choke, triangle",
      "root_causes": ["poor guard retention", "back exposure"],
      "highlights": ["sweep from half guard"],
      "opponent_description": "blue belt",
      "rpe_score": 7,
      "failure_domain": "technical",
      "cns_status": "sluggish",
      "event_date": null,
      "extraction_confidence": 0.85
    }
  ],
  "training_state": {
    "current_focus": ["guard retention", "takedown defense"],
    "active_injuries": ["sore left knee"],
    "short_term_goals": []
  }
}
```

**Example 2 — No extractable data:**

Input:
> "Hey coach, what's a good way to improve my jab?"

Output:
```json
{
  "performance_events": [],
  "training_state": null
}
```

**Example 3 — Training state only, no events:**

Input:
> "I've decided to focus on leg kicks and clinch work for the next few weeks. Want to compete in April. My shoulder is feeling better now."

Output:
```json
{
  "performance_events": [],
  "training_state": {
    "current_focus": ["leg kicks", "clinch work"],
    "active_injuries": [],
    "short_term_goals": ["compete in April"]
  }
}
```

---

## File 2: `backend/app/services/grok.py` (MODIFY)

Add one method to the existing `GrokClient` class, after `extract_notes()`.

### `extract_memory()`

```python
async def extract_memory(
    self,
    messages: list[dict],
    model: str = "grok-3-mini",
) -> dict | None:
```

**Key differences from `extract_notes()`:**

| Aspect | `extract_notes()` | `extract_memory()` |
|--------|-------------------|-------------------|
| Input | Single `assistant_content: str` | Full `messages: list[dict]` |
| JSON mode | Prompt-only ("Return ONLY valid JSON") | `response_format={"type": "json_object"}` |
| System prompt | Inline string | Import from `prompts/memory_extraction.py` |

**Stub mode:** Returns `{"performance_events": [], "training_state": None}`.

**Error handling:** `try/except Exception` -> `logger.exception("extract_memory failed")` -> return `None`.

---

## File 3: `backend/app/services/memory.py` (NEW)

Three async functions. Standard service pattern: function-based, `db: AsyncSession` first param.

### Function 1: `save_performance_events`

```python
async def save_performance_events(
    db: AsyncSession,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    events: list[PerformanceEventExtraction],
) -> list[PerformanceEvent]:
```

- Iterates `events`, creates `PerformanceEvent` rows
- **Literal-to-Enum mapping:** `EventType("sparring")` -> `EventType.SPARRING` (str enums)
- Nullable enums: check `is not None` before calling constructor
- `event_date`: defaults to `date.today()` when `None`
- Uses `db.add_all(rows)` + single `db.commit()`

### Function 2: `upsert_training_state`

```python
async def upsert_training_state(
    db: AsyncSession,
    user_id: uuid.UUID,
    state: UserTrainingStateExtraction,
) -> UserTrainingState:
```

**Strategy: REPLACE, not merge.**

- SELECT existing row by `user_id`
- If `None` -> INSERT new `UserTrainingState`
- If exists -> overwrite the three JSONB fields
- `created_at` is **never touched** (immutable constraint)
- `updated_at` handled by `TimestampMixin.onupdate=func.now()` automatically

### Function 3: `get_recent_telemetry`

```python
async def get_recent_telemetry(
    db: AsyncSession,
    user_id: uuid.UUID,
    days: int = 14,
) -> dict:
```

**Return shape:**
```python
{
    "events": list[PerformanceEvent],          # desc by event_date, limit 50
    "training_state": UserTrainingState | None,
}
```

---

## Out of Scope

- **Routes** — no `routes/memory.py`, no new endpoints (future slice)
- **Integration into `conversation.py`** — `_build_system_prompt` not modified (future slice)
- **Background extraction orchestrator** — `extract_and_save_memory()` is Slice 4
- **Alembic migrations** — tables exist from Slice 1
- **Frontend** — none
- **New dependencies** — none needed
