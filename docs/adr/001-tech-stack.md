# ADR 001: Tech Stack Selection

## Status

Accepted

## Date

2026-03-08

## Context

MMAi V2 is a ground-up rebuild of an AI martial arts coaching platform, serving as both a production application and a living portfolio for Melbourne SportsTech roles.

V1 is a JavaScript monolith (Express + React) running at www.mmai.coach. It works but has accumulated technical debt and uses patterns that don't showcase modern full-stack capabilities.

V2 needs to:
- Run alongside V1 without disruption (separate subdomain, database, and process)
- Demonstrate enterprise-grade engineering practices
- Use a stack that's relevant to Australian tech hiring (Python is dominant in AU data/AI roles)
- Be buildable incrementally by a solo developer with AI assistance

## Decision

### Backend: Python 3.12+ with FastAPI
- Async-native with `asyncio` support throughout
- Automatic OpenAPI/Swagger documentation
- Pydantic models for request/response validation and serialization
- Dependency injection system for clean service composition
- Native type hints — no separate type system needed

### ORM: SQLAlchemy 2.0 with asyncpg
- SQLAlchemy 2.0's new async session support
- asyncpg for high-performance PostgreSQL connections
- Alembic for migration management
- UUID primary keys, parameterized queries only

### Frontend: React 19 with Chakra UI v2
- Chakra UI for accessible, composable components (WAI-ARIA compliant)
- Vite for fast dev server and optimized builds
- No TypeScript in V1 worked fine; V2 may adopt it later if complexity warrants

### AI: Grok API (xAI)
- Function calling support for intent routing
- Cost-effective for a portfolio project
- Strong persona capabilities for coaching personality
- Demonstrates ability to evaluate and integrate emerging AI providers

### Package Management: uv
- Replaces pip + pip-tools + virtualenv
- Deterministic lockfiles (`uv.lock`)
- 10-100x faster than pip for installs
- Growing industry adoption

### Database: PostgreSQL (mmai_v2)
- Separate database on the same PostgreSQL instance as V1
- Full isolation — no shared tables, no cross-database queries
- UUID primary keys, JSONB columns where appropriate

### Ports
- Backend API: 8000
- Frontend dev: 5173
- Production: nginx reverse proxy at chat.mmai.coach

## Consequences

### Positive
- Python + FastAPI is highly relevant for AU tech roles, especially in data/AI
- Automatic API docs reduce documentation burden
- Type hints + Pydantic catch errors at development time
- Chakra UI reduces accessibility implementation effort
- uv eliminates Python packaging pain points
- Full isolation from V1 means zero risk to production

### Negative
- Two languages in the portfolio (JavaScript V1, Python V2) — but this shows versatility
- FastAPI ecosystem is smaller than Express — fewer middleware options
- Chakra UI v2 has some breaking changes from v1 docs floating around
- uv is relatively new — may hit edge cases

### Neutral
- Will need nginx config for chat.mmai.coach subdomain (one-time setup)
- PM2 can manage Python processes but systemd is more standard for Python — decide later
- May want to add TypeScript to frontend later — Vite supports this trivially
