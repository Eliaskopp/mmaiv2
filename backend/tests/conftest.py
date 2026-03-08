import pytest
import asyncpg
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.deps import get_db
from app.main import app


def _pg_dsn() -> str:
    return settings.database_url.replace("postgresql+asyncpg://", "postgresql://")


@pytest.fixture
async def client():
    """HTTP client with a per-test DB engine to avoid event loop conflicts."""
    # Clean up BEFORE the test (handles leftover data from failed teardowns)
    conn = await asyncpg.connect(_pg_dsn())
    await conn.execute("DELETE FROM users")
    await conn.close()

    engine = create_async_engine(settings.database_url, echo=False, pool_size=5)
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
