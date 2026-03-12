# MMAi V2 — Claude Code Instructions

## What This Is

AI martial arts coaching platform V2 — a "Living Portfolio" app targeting Melbourne SportsTech roles. Served at **chat.mmai.coach**, fully isolated from the live monolith at **www.mmai.coach**.

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

- Backend: `8000`
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

## Zero Downtime Rule

**CRITICAL**: NEVER modify:
- `~/mmai-monolith/` (any file)
- nginx configs for `www.mmai.coach`
- PM2 process `mmai`
- Database `mmai` (the V1 database)

V2 is fully isolated. If you need to touch shared infrastructure (nginx, PostgreSQL), document what's needed and ask first.

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
