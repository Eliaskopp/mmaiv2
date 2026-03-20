# MMAi V2 — Claude Code Instructions

## What This Is

AI martial arts coaching platform V2 — a "Living Portfolio" app targeting Melbourne SportsTech roles. Production at **www.mmai.coach**, staging at **chat.mmai.coach**. V1 monolith is decommissioned (PM2 process `mmai` stopped).

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0 + asyncpg |
| Frontend | React 19, Chakra UI v2, Vite |
| AI | Grok API (xAI) — all AI calls go through xAI only |
| Database | PostgreSQL `mmai_v2` on localhost:5432 |
| Package manager | `uv` (Python), npm (frontend) |
| Process manager | PM2 (production) |

## Ports

- Backend: `8001`
- Frontend dev server: `5173`

## Database Rules

- UUID primary keys everywhere
- Parameterized queries only — never `f"... {variable} ..."` in SQL
- All FKs reference UUID columns
- Use SQLAlchemy models with Alembic migrations
- **`created_at` is permanently immutable** — never update it during an upsert, PATCH, or any other operation. If a table needs "last modified" tracking, use a separate `updated_at` column via TimestampMixin.

## Code Style

- **Python**: Type-hinted, Pydantic models for validation, small focused modules
- **React**: Functional components, hooks, Chakra UI components
- **Architecture**: Modular, single responsibility, services throw → routes catch
- **Git flow**: Feature branches → PR → main. No direct commits to main.

## AI Integration

- **Grok API (xAI) only** — no OpenAI, no DeepSeek, no Anthropic API
- Use function calling for intent routing
- Token budget: respect cost limits, cache responses where possible
- Explain the "why" behind architectural choices (teaching mode)

## In Scope

- Coach (AI chat)
- Auth (JWT, email verification)
- Conversations (history, persistence)
- Profiles (training preferences, experience level)
- Training Journal (sessions, RPE, duration, type)
- Recovery Logs (daily wellness tracking)
- Stats & Charts (streak, ACWR, volume trends)
- Notes (smart suggestions from conversations)
- Voice Input (Web Speech API)
- Usage Tracking (rate limits, quotas)
- Health Monitoring (service health endpoints)

## Out of Scope

Do NOT build these — they belong to V1 only:
- Shop / Equipment (Shopify integration)
- Gyms / Partners directory
- News / RSS pipeline
- Stripe payments
- Blog / article generation
- Admin queue
- Knowledge base

## Infrastructure Rules

- **www.mmai.coach** serves V2 (nginx → `frontend/dist` + proxy to `:8001`)
- **chat.mmai.coach** is the staging mirror (same V2 codebase)
- V1 monolith (`~/mmai-monolith/`, PM2 process `mmai`, database `mmai`) is decommissioned — do not resurrect it
- Do not modify nginx configs without explicit user approval

## Strict Override Rules

- **User constraints override plan documents** — if the user gives an explicit architectural constraint (e.g. "use soft deletes", "created_at is immutable"), follow it exactly. Never override it with suggestions from a plan, design doc, or general best practice.
- **When in doubt, ask** — if a plan contradicts a prior user instruction, stop and ask. Do not silently pick one.

## Anti-Hallucination Rules

- **Verify packages on PyPI/npmjs.com** before adding
- **Check existing code** before writing new — prefer editing over creating
- **Ask if uncertain** — do not guess API signatures
- **Reference exact file paths** when citing code
- **Do NOT invent methods** that don't exist in the codebase
- **Do NOT add dependencies** without explicit approval

## ADHD Documentation Interlock

The user has ADHD. Do not rely on them to manually document their progress. After completing any major feature, Git commit, or ADR, you must automatically generate a "Session Summary" in standard Markdown. This summary must include:

- What was built.
- The terminal commands used.
- The specific files changed.

Stop your execution and explicitly tell the user: "Please copy this summary into your Obsidian MMAi-State note. Reply 'Done' when you have saved it, and we will move to the next step."

## Obsidian / Sync Block Format

All Sync Blocks and ADRs written to `~/Digital Mind/MMAi-V2/` **MUST** use the plain-text Zettelkasten template. **Never use YAML frontmatter** (`---`). The exact format is:

```
\n2026-03-11 19:00\n\nStatus: #child\n\nTags: [[tag1]] [[tag2]]\n\n# Title\n\n[Content]\n\n# Reference\n```

## Obsidian Vault Organization

The vault at `~/Digital Mind/` follows strict Zettelkasten separation:

| Folder | Contains | Example |
|--------|----------|---------|
| `MMAi-V2/` | Project-specific ADRs, Sync Blocks, session summaries | `2026-03-12-Phase-3A-...md` |
| `Zettelkasten/` | Atomic knowledge cards with real content/explanations | `FastAPI.md`, `PostgreSQL.md` |
| `3 - Tags/` | Empty pages that act as backlink anchors (tags) | `mmai-v2.md`, `backend.md` |

**Rules:**
- **Never** put empty anchor pages in `Zettelkasten/` — they go in `3 - Tags/`
- **Never** put project logs/ADRs in `Zettelkasten/` — they go in `MMAi-V2/`
- Reusable coding concepts learned during the project go in `Zettelkasten/` as atomic notes

## Frontend Commands

```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server on :5173
npm run build        # Production build to frontend/dist/
npm run preview      # Preview production build
npm run lint         # ESLint check
```

## Key Directories (planned)

```
~/mmai-v2/
├── CLAUDE.md           # This file
├── INTENT.md           # Portfolio charter
├── backend/            # FastAPI app
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   └── core/       # config, auth, deps
│   ├── alembic/
│   ├── pyproject.toml
│   └── .env
├── frontend/           # React + Chakra UI
│   ├── src/
│   ├── package.json
│   └── vite.config.js
└── docs/
    └── adr/            # Architecture Decision Records
```

## Agent Management Rules

1. **Read ./STATE.md first** — At the start of every session, read the local `STATE.md` file before proposing any work. This is the source of truth for architecture, metrics, and milestones.
2. **Small Bets Only** — Never refactor multiple pages/modules in one pass. One component, one endpoint, or one fix at a time. Commit after each successful small bet.
3. **Zero V1 Contact** — V1 is decommissioned. Never touch `~/mmai-monolith/`, PM2 process `mmai`, or database `mmai`. Do not modify nginx configs without explicit user approval.
4. **Strict Typing** — Backend: all request/response shapes use Pydantic models, no raw dicts. Frontend: Chakra UI semantic tokens for theming, TypeScript strict mode.
5. **Commit Cadence** — Git commit after every successful small bet (passing test, working component, fixed bug). Don't batch unrelated changes.
6. **No Speculative Work** — Don't build features, abstractions, or "improvements" not explicitly requested. Discuss scope before coding.

# STATE.md Write Protocol

Never update STATE.md during intermediate steps, PRD drafting, or test writing. STATE.md is only to be updated upon the completion and successful testing of a full Vertical Slice (Issue) or Milestone.
