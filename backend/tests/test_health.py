import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "0.1.0"
    # Status depends on Grok API key: "healthy" (both up) or "degraded" (DB up, AI unconfigured)
    assert data["status"] in ("healthy", "degraded")


@pytest.mark.asyncio
async def test_health_database_connected(client: AsyncClient):
    response = await client.get("/api/v1/health")
    data = response.json()
    assert data["database"]["status"] == "connected"
    assert data["database"]["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_health_ai_status(client: AsyncClient):
    response = await client.get("/api/v1/health")
    data = response.json()
    assert data["ai"]["status"] in ("connected", "unconfigured", "disconnected")
    assert data["ai"]["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_health_response_shape(client: AsyncClient):
    response = await client.get("/api/v1/health")
    data = response.json()
    assert set(data.keys()) == {"status", "version", "database", "ai"}
    assert set(data["database"].keys()) == {"status", "latency_ms"}
    assert set(data["ai"].keys()) == {"status", "latency_ms"}
