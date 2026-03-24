# Backend — Claude Code Instructions

## Database Rules

- UUID primary keys everywhere
- Parameterized queries only — never `f"... {variable} ..."` in SQL
- All FKs reference UUID columns
- SQLAlchemy models with Alembic migrations
- **`created_at` is permanently immutable** — never update it during upsert, PATCH, or any operation. Use a separate `updated_at` column via TimestampMixin.

## Python Code Style

- Type-hinted, Pydantic models for all request/response shapes (no raw dicts)
- Small focused modules, single responsibility
- Services throw → routes catch (`app/routes/health.py` is the reference pattern)

## AI Integration

- **Grok API (xAI) only** — no OpenAI, no DeepSeek, no Anthropic API
- Use function calling for intent routing
- Token budget: respect cost limits, cache responses where possible

## Key Patterns

- `get_db` dependency in `app/core/deps.py` yields AsyncSession
- `get_current_user` extracts Bearer token, validates JWT `type="access"`
- Config via pydantic-settings in `app/core/config.py`, reads from `.env`
- JWT: HS256, access tokens 30min, refresh tokens 7 days, `type` claim prevents cross-use
- bcrypt used directly (not passlib) — passlib has compatibility issues with bcrypt>=4.x on Python 3.12+

## Commands

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8001   # Dev server
uv run pytest -x                                     # Run tests
uv run alembic upgrade head                           # Apply migrations
uv run alembic revision --autogenerate -m "desc"      # Create migration
```
