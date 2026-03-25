# MMAi V2 — Living Portfolio

## Goal

Demonstrate full-stack engineering capability for **Melbourne SportsTech** roles through a production AI coaching application.

## What This Demonstrates

| Capability | Evidence |
|-----------|---------|
| Enterprise DevOps | CI/CD, PM2, nginx reverse proxy, PostgreSQL, zero-downtime deployment |
| AI Integration | Grok API with function calling, intent routing, conversation memory, prompt engineering |
| Full-Stack Proficiency | FastAPI backend, React frontend, JWT auth, real-time features |
| Data Visualization | Training stats, recovery trends, ACWR charts, streak tracking |
| Software Architecture | ADRs, modular services, clean Git history, type safety |
| Modern Tooling | uv package manager, Vite, Pydantic, SQLAlchemy 2.0 async |

## Tech Choice Rationale

**FastAPI** — Async-native, automatic OpenAPI docs, Pydantic validation built-in. Industry standard for Python APIs. Shows I can build performant backends with proper typing.

**Grok (xAI)** — Cost-effective, fast inference, strong persona capabilities. Function calling support enables clean intent routing. Demonstrates I can integrate and evaluate emerging AI providers, not just default to OpenAI.

**Chakra UI** — Accessible by default (WAI-ARIA), composable component system, built-in responsive design. Shows commitment to inclusive, production-quality UIs.

**uv** — 10-100x faster than pip, proper lockfiles, replaces pip + pip-tools + virtualenv. Shows awareness of modern Python ecosystem.

**PostgreSQL** — Battle-tested, UUID support, JSON columns, full-text search. Same instance as V1 but separate database — demonstrates multi-tenant infrastructure thinking.

## Dual Track

1. **Application Development** — This V2 rebuild, showing end-to-end delivery
2. **Open Source Contributions** — Targeted contributions to Python/FastAPI/AI ecosystem projects

## Principles

- **Clean Git History** — Atomic commits, conventional commit messages, meaningful PRs
- **Architecture Decision Records** — Every significant choice documented with rationale
- **Modular Design** — Small, focused modules with clear boundaries
- **Progressive Delivery** — Ship working increments, not big-bang releases
- **Teaching Mode** — Code and docs explain the "why", not just the "what"

## Live URLs

- **Production**: https://www.mmai.coach — Python/FastAPI + React/Chakra UI (V2)
- **Staging**: https://chat.mmai.coach — same V2 codebase, pre-production QA

V1 (JavaScript/Express monolith) has been officially decommissioned.
