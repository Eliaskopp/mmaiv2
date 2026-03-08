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

## Anti-Hallucination Rules

- **Verify packages on PyPI/npmjs.com** before adding
- **Check existing code** before writing new — prefer editing over creating
- **Ask if uncertain** — do not guess API signatures
- **Reference exact file paths** when citing code
- **Do NOT invent methods** that don't exist in the codebase
- **Do NOT add dependencies** without explicit approval

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
