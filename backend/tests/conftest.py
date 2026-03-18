import os

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.deps import get_db
from app.core.limiter import limiter
from app.main import app

# TECH DEBT: Test DB schema is not automatically synced. Run pg_dump from mmai_v2 if schema changes.
# PGPASSWORD=mmai123 pg_dump -U mmai -h localhost -s mmai_v2 | PGPASSWORD=mmai123 psql -U mmai -h localhost mmai_v2_test
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://mmai:mmai123@localhost:5432/mmai_v2_test",
)


def _pg_dsn() -> str:
    return TEST_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


async def db_fetchval(query: str, *args):
    """Open a short-lived asyncpg connection, fetch one value, close."""
    conn = await asyncpg.connect(_pg_dsn())
    try:
        return await conn.fetchval(query, *args)
    finally:
        await conn.close()


async def db_execute(query: str, *args):
    """Open a short-lived asyncpg connection, execute a statement, close."""
    conn = await asyncpg.connect(_pg_dsn())
    try:
        await conn.execute(query, *args)
    finally:
        await conn.close()


@pytest.fixture
async def client():
    """HTTP client with a per-test DB engine. Rate limiting disabled for tests."""
    # Clean up BEFORE the test (handles leftover data from failed teardowns)
    conn = await asyncpg.connect(_pg_dsn())
    await conn.execute("DELETE FROM users")
    await conn.close()

    # Disable rate limiting for tests
    limiter.enabled = False

    engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_size=5)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()
    limiter.enabled = True
