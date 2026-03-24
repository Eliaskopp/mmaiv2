# MMAi V2 — Claude Code Instructions

AI martial arts coaching platform V2 — "Living Portfolio" app. Production: **www.mmai.coach**, staging: **chat.mmai.coach**.

## Stack & Ports

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI, SQLAlchemy 2.0 + asyncpg (port `8001`) |
| Frontend | React 19, Chakra UI v2, Vite (dev port `5173`) |
| AI | Grok API (xAI) — all AI calls go through xAI only |
| Database | PostgreSQL `mmai_v2` on localhost:5432 |
| Package manager | `uv` (Python), npm (frontend) |
| Process manager | PM2 (production) |

## Git Flow

Feature branches → PR → main. No direct commits to main.

## In Scope

Coach (AI chat), Auth (JWT, email verification), Conversations, Profiles, Training Journal, Recovery Logs, Stats & Charts, Notes, Voice Input, Usage Tracking, Health Monitoring.

## Out of Scope

Do NOT build — V1 only: Shop/Equipment, Gyms/Partners, News/RSS, Stripe, Blog, Admin queue, Knowledge base.

## Infrastructure Rules

- **www.mmai.coach** serves V2 (nginx → `frontend/dist` + proxy to `:8001`)
- **chat.mmai.coach** is the staging mirror (same V2 codebase)
- V1 monolith (`~/mmai-monolith/`, PM2 process `mmai`, database `mmai`) is decommissioned — do not resurrect
- Do not modify nginx configs without explicit user approval

## Strict Override Rules

- **User constraints override plan documents** — follow explicit user instructions exactly. Never override with suggestions from a plan, design doc, or best practice.
- **When in doubt, ask** — if a plan contradicts a prior user instruction, stop and ask.

## Anti-Hallucination Rules

- **Verify packages on PyPI/npmjs.com** before adding
- **Check existing code** before writing new — prefer editing over creating
- **Ask if uncertain** — do not guess API signatures
- **Reference exact file paths** when citing code
- **Do NOT invent methods** that don't exist in the codebase
- **Do NOT add dependencies** without explicit approval

## Agent Management Rules

1. **Read ./STATE.md first** — source of truth for architecture, metrics, and milestones.
2. **Small Bets Only** — one component, one endpoint, or one fix at a time. Commit after each.
3. **Zero V1 Contact** — never touch `~/mmai-monolith/`, PM2 process `mmai`, or database `mmai`.
4. **Strict Typing** — Backend: Pydantic models, no raw dicts. Frontend: TypeScript strict mode.
5. **Commit Cadence** — git commit after every successful small bet. Don't batch unrelated changes.
6. **No Speculative Work** — don't build features not explicitly requested. Discuss scope before coding.

## STATE.md Write Protocol

Never update STATE.md during intermediate steps. Only update upon completion and successful testing of a full Vertical Slice or Milestone.

## ADHD Documentation Interlock

After completing any major feature, Git commit, or ADR, automatically generate a Session Summary (what was built, commands used, files changed). Then tell the user: "Please copy this summary into your Obsidian MMAi-State note. Reply 'Done' when you have saved it."

## Obsidian / Sync Block Format

All Sync Blocks and ADRs written to `~/Digital Mind/MMAi-V2/` **MUST** use the plain-text Zettelkasten template. **Never use YAML frontmatter** (`---`):

```
\n2026-03-11 19:00\n\nStatus: #child\n\nTags: [[tag1]] [[tag2]]\n\n# Title\n\n[Content]\n\n# Reference\n```

## Obsidian Vault Organization

| Folder | Contains |
|--------|----------|
| `MMAi-V2/` | Project ADRs, Sync Blocks, session summaries |
| `Zettelkasten/` | Atomic knowledge cards with real content only |
| `3 - Tags/` | Empty pages as backlink anchors |

- **Never** put empty anchor pages in `Zettelkasten/`
- **Never** put project logs/ADRs in `Zettelkasten/`
- Reusable coding concepts go in `Zettelkasten/` as atomic notes
