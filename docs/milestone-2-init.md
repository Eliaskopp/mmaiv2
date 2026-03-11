# Milestone 2 — Initialize Message

> Paste the block below into a new Claude Code session to enter plan mode with the Milestone 2 plan.

---

Enter plan mode. Here is the plan for Milestone 2.

## Context: What's Built (Milestone 1 Complete)

| PR | What | Status |
|----|------|--------|
| #1 | FastAPI skeleton + health endpoint | Merged |
| #2 | JWT auth (register, login, refresh, verify-email) | Merged |
| #3 | Frontend scaffold (Vite + React 19 + Chakra UI v2 + API layer) | Merged |
| #4 | Phase A hardening (CORS, token expiry, logout) | Merged |
| #5 | Phase B (email via Resend, rate limiting, password reset) | Merged |
| #6 | Core domain models & gamification layer (11 tables, Alembic migration) | Merged |

**Auth is feature-complete.** 18 tests. All 11 domain tables exist in the DB. No routes, schemas, or services exist yet for the new domain models.

**Current backend structure:**
- `models/` — user, conversation, profile, journal, note, achievement, streak (all built)
- `routes/` — auth, health (only these two)
- `schemas/` — auth, health (only these two)
- `services/` — auth, email (only these two)
- `frontend/src/features/` — auth (only this one)

---

## Milestone 2: Training Profile & Journal CRUD

**Goal:** Bring the three core data domains to life — Profile, Training Sessions, Recovery Logs. These are the foundation everything else depends on (AI coach reads profiles, stats need journal data, gamification evaluates sessions).

### Phase 2A: Training Profile (backend + frontend)

**Branch:** `feat/profile-crud`

**Backend:**
1. `schemas/profile.py` — Pydantic models: `ProfileCreate`, `ProfileUpdate`, `ProfileResponse`
   - JSONB fields map to `list[str]` (martial_arts, injuries, strategic_leaks, conversation_insights)
   - All fields optional on update (PATCH semantics)
   - Validate `skill_level` enum, `training_frequency` range, `weight_class` options
2. `services/profile.py` — Business logic:
   - `get_or_create_profile(user_id)` — auto-create on first access (upsert pattern)
   - `update_profile(user_id, data)` — partial update, recalculate `profile_completeness`
   - `profile_completeness` formula: count non-null fields / total optional fields × 100
3. `routes/profile.py` — Thin REST layer:
   - `GET /api/profile` — returns current user's profile (auto-creates if missing)
   - `PATCH /api/profile` — partial update
   - Both require `get_current_user` dependency
4. Tests: get profile (auto-create), update profile, completeness calculation, invalid data rejection

**Frontend:**
5. `features/profile/` — Profile setup/edit page
   - Multi-step form or single-page form (Chakra UI)
   - Fields: skill level, martial arts (multi-select), goals, weight class, training frequency, injuries, role
   - Completeness progress bar
   - React Query mutations for save

**PR:** Open PR, merge to main.

### Phase 2B: Training Journal — Sessions (backend + frontend)

**Branch:** `feat/journal-sessions`

**Backend:**
1. `schemas/journal.py` — `SessionCreate`, `SessionUpdate`, `SessionResponse`, `SessionListResponse`
   - Validate RPE (1-10), duration (1-599), mood (1-5), energy (1-5) at Pydantic level
   - `session_type` enum matching the DB enum
   - `training_score` as computed read-only field in response
2. `services/journal.py` — Business logic:
   - `create_session(user_id, data)` — log a training session
   - `list_sessions(user_id, offset, limit, filters)` — paginated, filterable by date range and type
   - `get_session(user_id, session_id)` — single session detail
   - `update_session(user_id, session_id, data)` — edit a logged session
   - `delete_session(user_id, session_id)` — hard delete (user owns their journal data)
   - `compute_training_score(rpe, duration, session_type)` — formula from ADR: `(RPE × duration × type_weight) / 10`
3. `routes/journal.py` — REST endpoints:
   - `POST /api/journal/sessions` — log new session
   - `GET /api/journal/sessions` — list with pagination + filters
   - `GET /api/journal/sessions/{id}` — single session
   - `PATCH /api/journal/sessions/{id}` — update
   - `DELETE /api/journal/sessions/{id}` — delete
   - All scoped to `get_current_user` — users can only access their own sessions
4. Tests: CRUD operations, pagination, date filtering, score calculation, ownership enforcement

**Frontend:**
5. `features/journal/` — Training log UI
   - Session log form (type, duration, RPE slider, mood, techniques)
   - Session list view (cards or table, sorted by date)
   - Session detail view

**PR:** Open PR, merge to main.

### Phase 2C: Recovery Logs (backend + frontend)

**Branch:** `feat/recovery-logs`

**Backend:**
1. `schemas/recovery.py` — `RecoveryCreate`, `RecoveryUpdate`, `RecoveryResponse`
   - Validate sleep_quality, soreness, energy (1-5)
   - `logged_for` date field (defaults to today)
   - Enforce one log per day per user at service level
2. `services/recovery.py` — Business logic:
   - `log_recovery(user_id, data)` — create or update today's recovery log (upsert on user_id + logged_for)
   - `get_recovery_log(user_id, date)` — single day
   - `list_recovery_logs(user_id, start_date, end_date)` — date range query
3. `routes/recovery.py` — REST endpoints:
   - `POST /api/recovery` — log today's recovery (upsert)
   - `GET /api/recovery` — list with date range filter
   - `GET /api/recovery/{date}` — single day lookup
4. Tests: create, upsert (same day overwrites), date range queries, validation

**Frontend:**
5. `features/recovery/` — Daily wellness check-in
   - Simple form: sleep quality, soreness, energy (1-5 scales), notes
   - Calendar or list view of past entries

**PR:** Open PR, merge to main.

---

## Decisions to Confirm Before Starting

1. **Profile auto-creation:** Should `GET /api/profile` auto-create an empty profile, or should we require an explicit `POST /api/profile` first?
2. **Journal deletion:** Hard delete or soft delete for training sessions? (ADR says `deleted_at` is only on conversations.)
3. **Recovery upsert:** Should `POST /api/recovery` for the same day overwrite the existing entry, or return 409 Conflict?
4. **Frontend routing:** Add React Router routes now (`/profile`, `/journal`, `/recovery`), or wait until we have a nav shell?
5. **Testing strategy:** Full integration tests (HTTP → DB) like the auth tests, or add unit tests for services too?

## What This Unlocks (Milestone 3 preview)

With Profile + Journal + Recovery in place:
- **AI Coach** can read user profiles for personalized coaching
- **Stats & Charts** can compute ACWR, volume trends, streak data from sessions + recovery
- **Gamification** evaluators can query real training data
- **Notes** can link back to sessions and conversations

---

## Deliverables Checklist

- [ ] Phase 2A: Profile CRUD (backend + frontend) — PR merged
- [ ] Phase 2B: Journal Sessions CRUD (backend + frontend) — PR merged
- [ ] Phase 2C: Recovery Logs CRUD (backend + frontend) — PR merged
- [ ] All new endpoints tested (integration tests)
- [ ] ADR/Sync Block drafted for each phase
- [ ] Obsidian vault updated

---

## Appendix: Obsidian Documentation Workflow

### Why This Exists

The developer has ADHD. Manual documentation doesn't happen reliably. The solution is a **propose-then-approve interlock** built into the Claude Code workflow — the AI drafts docs, but the human must read and approve before anything is written. This forces engagement with the content instead of just generating docs nobody reads.

### Vault Structure & Note Types

```
~/Digital Mind/                          # Obsidian vault root
├── 1 - Rough Notes/                     # Quick captures
├── 2 - Source Material/                 # Freeform reference notes (no template)
│   ├── AI Models/
│   ├── Books/
│   ├── Database/
│   └── Videos/
├── 3 - Tags/                           # Tag index pages
├── 4 - Indexes/                        # MOCs (Maps of Content)
├── 5 - Tamplates/                      # Obsidian templates
│   └── Full Note.md                    # The Zettelkasten template
├── MMAi-V2/                            # All MMAi V2 project docs
│   ├── 2026-03-09-Domain-Models-Gamification.md
│   ├── 2026-03-09-Phase-B-Complete.md
│   ├── 2026-03-09-V1-V2-Domain-Entity-Schema.md
│   └── MMAi-V2-Project-Overview.md
├── Zettelkasten/                        # Permanent knowledge notes (use template)
│   ├── Access and Refresh Tokens.md
│   ├── Async Python.md
│   ├── FastAPI.md
│   └── ...
```

The vault has **two types of notes**:

| Type | Location | Format | Purpose |
|------|----------|--------|---------|
| **Zettelkasten notes** | `Zettelkasten/` or `MMAi-V2/` | **Template-based** (structured) | Knowledge notes, ADRs, sync blocks |
| **Source notes** | `2 - Source Material/` | **Freeform** (no template) | Raw reference material, bookmarks, quotes |

**Zettelkasten notes follow a template. Source notes are free.** This distinction is fundamental to how the vault works.

---

### The Zettelkasten Template

Every Zettelkasten note is created from this template (`5 - Tamplates/Full Note.md`):

```
{{date}} {{time}}

Status:

Tags:

# {{title}}




# Reference
```

Obsidian auto-fills `{{date}}`, `{{time}}`, and `{{title}}` on creation. The developer fills in Status, Tags, and the body.

#### Template Fields Explained

**Date line** — `2026-03-09 00:00` at the top of the file. Obsidian uses this for sorting and timeline views. Always present.

**Status** — A growth-metaphor tag indicating note maturity:

| Status | Meaning |
|--------|---------|
| `#baby` | New note — stub or first draft, needs development |
| `#child` | Developing — has real content but not fully mature |
| `#adult` | Mature — comprehensive, well-linked, reviewed |

Example: A new note about `[[FastAPI]]` starts as `#baby` with a few bullet points. As more knowledge is added and it gets cross-linked, it graduates to `#child`, then `#adult`.

**Tags** — `[[wikilinks]]` that connect this note to other notes in the vault's knowledge graph:
```
Tags: [[ai]] [[mmai-v2]] [[backend]]
```
- `[[FastAPI]]` creates a clickable link to the FastAPI note
- `[[Services Throw Routes Catch]]` links to the architecture pattern note
- These build the graph — Obsidian visualises all connections between notes
- Tags are **wikilinks** (not hashtags) — they link to real notes, not just labels

**`# Reference`** — Empty section at the bottom. Obsidian automatically displays backlinks here (other notes that link to this one). It's a convention, not content — never write in it.

#### Real Zettelkasten Note Example

From `Zettelkasten/Access and Refresh Tokens.md`:
```markdown
2026-03-09 00:00

Status: #baby

Tags: [[mmai-v2]] [[JWT Authentication]]

# Access and Refresh Tokens

A dual-token strategy for authentication. Balances security
(short-lived access) with usability (don't make users log in constantly).

## The Two Tokens

| | Access Token | Refresh Token |
|---|---|---|
| Purpose | Proves "I am user X" on each request | Gets a new access token |
| Lifetime | 30 minutes | 7 days |
| If stolen | 30 min of access | Can generate new tokens |

## Why Two Tokens?
If you had one long-lived token, a stolen token gives access for days...

## Frontend Flow ([[Axios]])
1. Request fails with 401 — access token expired
2. Axios interceptor calls `/api/auth/refresh`...

## Key Files
- `app/core/security.py` — `create_access_token()`, `create_refresh_token()`
- `app/services/auth.py` — `refresh_access_token()`

# Reference
```

Note how `[[Axios]]` and `[[JWT Authentication]]` are wikilinks — they create graph connections to other knowledge notes.

---

### MMAi-V2 Project Docs

All MMAi V2 documentation lives in `/Digital Mind/MMAi-V2/`. These are project-specific notes, separate from general Zettelkasten knowledge.

We write **three types** of docs in this folder:

#### 1. ADRs (Architecture Decision Records)

For significant technical decisions. These use **YAML frontmatter** instead of the Zettelkasten template header — this is the one exception to the template rule, because ADRs need machine-readable metadata.

**Format:**
```yaml
---
type: adr
status: accepted
date: 2026-03-09
tags: [mmai-v2, domain-models, gamification, sqlalchemy]
branch: feat/domain-models-gamification
---

# ADR-003: Core Domain Models & Gamification Layer

## Status
Accepted

## Context
Why this decision was needed...

## Decision
What was decided — subsections for tables, enums, design choices, files...

## Consequences
- What follows from this decision
- Trade-offs, what's unlocked, what's deferred
```

**YAML frontmatter fields:**

| Field | Required | Purpose |
|-------|----------|---------|
| `type` | Yes | Always `adr` |
| `status` | Yes | `accepted`, `proposed`, or `superseded` |
| `date` | Yes | ISO-8601 date |
| `tags` | Yes | YAML array — always includes `mmai-v2` |
| `branch` | Yes | Git branch where the work was done |

**Body conventions:**
- Tables for structured data (models, columns, relationships)
- `**Bold label** — explanation` pattern for design choices
- Inline code for technical terms: `` `conversations` ``, `` `trigger_key` ``
- Bullet lists for enums, files changed, consequences

**File naming:** `YYYY-MM-DD-Topic-Name.md`

#### 2. Sync Blocks (Milestone Summaries)

For milestone completions — lighter than ADRs. These **use the Zettelkasten template** (date, status, tags, title, `# Reference`).

**Format:**
```markdown
2026-03-09 00:00

Status: #child

Tags: [[ai]] [[mmai-v2]] [[backend]]

# Phase B — Email Sending, Rate Limiting, Password Reset

## Decision
One-line summary of what was done, with [[wikilinks]] to relevant concepts.

## What Was Built
- **Feature** — [[Wikilink]] description of what was built
- **Feature** — description

## Consequences
- What this enables or changes
- Test coverage summary

## Files Changed
- `backend/app/services/email.py` (new)
- `backend/app/core/limiter.py` (new)
- `backend/app/main.py`

## Git
- Branch: `feat/branch-name`
- PR: #N (merged to main)
- Commit: abc1234

# Reference
```

Key difference from ADRs: Sync Blocks use `[[wikilinks]]` heavily in the body to connect to knowledge notes (e.g., `[[Resend Email]]`, `[[Async Python]]`).

**File naming:** `YYYY-MM-DD-Topic-Name.md`

#### 3. Project Overview (living document)

Single file: `MMAi-V2-Project-Overview.md`. Uses the Zettelkasten template. Updated after each milestone with a new row in the milestones table and checkboxes ticked in "What's Next."

**File naming:** No date prefix — it's a living document, not a point-in-time record.

---

### Formatting Inconsistency to Resolve

The two ADRs currently have slightly different frontmatter fields:

| ADR | Has `title`? | Has `branch`? |
|-----|-------------|---------------|
| `Domain-Models-Gamification.md` | No | Yes |
| `V1-V2-Domain-Entity-Schema.md` | Yes | No |

Going forward, **standardize all ADRs** to use: `type`, `status`, `date`, `tags`, `branch` (no `title` — the `# heading` serves as the title).

---

### The Interlock Process

This is the critical workflow. It is **non-negotiable**.

```
1. Developer completes a milestone or makes a key decision
2. Developer says: "Draft the ADR" or "Draft the Sync Block"
3. Claude Code synthesizes context from:
   - Git commits and PR details
   - Files changed
   - Technical decisions made
   - Consequences and trade-offs
4. Claude Code outputs the full drafted Markdown in the chat
5. Claude Code STOPS and WAITS for explicit approval
   - "approve", "yes", "lgtm" → proceed to write
   - Developer may request edits first
6. Only after approval: Claude Code writes to ~/Digital Mind/MMAi-V2/
7. Claude Code also updates MMAi-V2-Project-Overview.md milestones table
```

**Why the wait?** The approval step forces the developer to actually read the document. Without it, AI-generated docs become noise. The friction is intentional — it's a self-review checkpoint that works with ADHD, not against it.

**When to draft which type:**

| Trigger | Document Type |
|---------|--------------|
| New schema, library choice, architecture pattern | ADR (YAML frontmatter) |
| Feature shipped, milestone completed, PR merged | Sync Block (Obsidian metadata) |
| Any PR merged | Update Project Overview milestones table |

---

### Rules Summary

| Rule | Detail |
|------|--------|
| All MMAi docs go in | `~/Digital Mind/MMAi-V2/` |
| File naming | `YYYY-MM-DD-Topic-Name.md` (ISO-8601) |
| Never write without approval | Propose in chat → wait for "approve" → then write |
| ADRs get YAML frontmatter | `type`, `status`, `date`, `tags`, `branch` |
| Sync Blocks get Obsidian metadata | Date, Status `#child`, Tags with `[[wikilinks]]` |
| Wikilinks in body text | Sync Blocks: heavy. ADRs: sparingly. |
| Update Project Overview | After every PR merge |
| `# Reference` section | Empty — Obsidian backlink convention |
| No duplicate docs | Check what exists before creating |
