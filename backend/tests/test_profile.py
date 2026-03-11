import pytest
from httpx import AsyncClient


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _register(client: AsyncClient, email: str = "test@example.com") -> dict:
    resp = await client.post("/api/auth/register", json={
        "email": email,
        "password": "securepass123",
        "display_name": "Test User",
    })
    return resp.json()


def _auth(data: dict) -> dict:
    return {"Authorization": f"Bearer {data['access_token']}"}


# ── Create Profile ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_profile_success(client: AsyncClient):
    data = await _register(client)
    resp = await client.post("/api/profile", json={
        "skill_level": "beginner",
        "martial_arts": ["bjj", "muay_thai"],
        "goals": "Compete in amateur MMA",
    }, headers=_auth(data))
    assert resp.status_code == 201
    body = resp.json()
    assert body["skill_level"] == "beginner"
    assert body["martial_arts"] == ["bjj", "muay_thai"]
    assert body["goals"] == "Compete in amateur MMA"
    assert body["role"] == "fighter"
    assert body["profile_completeness"] > 0
    assert "id" in body
    assert body["user_id"] == data["user"]["id"]


@pytest.mark.asyncio
async def test_create_profile_empty(client: AsyncClient):
    data = await _register(client)
    resp = await client.post("/api/profile", json={}, headers=_auth(data))
    assert resp.status_code == 201
    body = resp.json()
    assert body["profile_completeness"] == 0
    assert body["role"] == "fighter"
    assert body["language_code"] == "en"
    assert body["weight_unit"] == "kg"


@pytest.mark.asyncio
async def test_create_profile_duplicate(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    resp1 = await client.post("/api/profile", json={}, headers=headers)
    assert resp1.status_code == 201
    resp2 = await client.post("/api/profile", json={}, headers=headers)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_create_profile_unauthenticated(client: AsyncClient):
    resp = await client.post("/api/profile", json={})
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_create_profile_invalid_skill_level(client: AsyncClient):
    data = await _register(client)
    resp = await client.post("/api/profile", json={
        "skill_level": "grandmaster",
    }, headers=_auth(data))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_profile_invalid_weight_unit(client: AsyncClient):
    data = await _register(client)
    resp = await client.post("/api/profile", json={
        "weight_unit": "stone",
    }, headers=_auth(data))
    assert resp.status_code == 422


# ── Get Profile ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_profile_success(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    await client.post("/api/profile", json={
        "skill_level": "advanced",
        "martial_arts": ["boxing"],
    }, headers=headers)
    resp = await client.get("/api/profile", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["skill_level"] == "advanced"
    assert resp.json()["martial_arts"] == ["boxing"]


@pytest.mark.asyncio
async def test_get_profile_not_found(client: AsyncClient):
    data = await _register(client)
    resp = await client.get("/api/profile", headers=_auth(data))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_profile_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/profile")
    assert resp.status_code in (401, 403)


# ── Update Profile ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_profile_success(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    await client.post("/api/profile", json={"skill_level": "beginner"}, headers=headers)

    resp = await client.patch("/api/profile", json={
        "skill_level": "intermediate",
        "martial_arts": ["bjj", "wrestling"],
    }, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["skill_level"] == "intermediate"
    assert body["martial_arts"] == ["bjj", "wrestling"]


@pytest.mark.asyncio
async def test_update_profile_partial(client: AsyncClient):
    """PATCH only updates provided fields — others stay unchanged."""
    data = await _register(client)
    headers = _auth(data)
    await client.post("/api/profile", json={
        "skill_level": "beginner",
        "goals": "Stay healthy",
    }, headers=headers)

    resp = await client.patch("/api/profile", json={
        "goals": "Win a tournament",
    }, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["goals"] == "Win a tournament"
    assert body["skill_level"] == "beginner"  # unchanged


@pytest.mark.asyncio
async def test_update_profile_not_found(client: AsyncClient):
    data = await _register(client)
    resp = await client.patch("/api/profile", json={
        "skill_level": "advanced",
    }, headers=_auth(data))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_profile_unauthenticated(client: AsyncClient):
    resp = await client.patch("/api/profile", json={"skill_level": "advanced"})
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_update_profile_invalid_skill_level(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    await client.post("/api/profile", json={}, headers=headers)
    resp = await client.patch("/api/profile", json={
        "skill_level": "grandmaster",
    }, headers=headers)
    assert resp.status_code == 422


# ── Completeness ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_completeness_zero_on_empty_profile(client: AsyncClient):
    data = await _register(client)
    resp = await client.post("/api/profile", json={}, headers=_auth(data))
    assert resp.json()["profile_completeness"] == 0


@pytest.mark.asyncio
async def test_completeness_partial(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    resp = await client.post("/api/profile", json={
        "skill_level": "beginner",
        "martial_arts": ["bjj"],
        "goals": "Learn submissions",
    }, headers=headers)
    body = resp.json()
    # 3 of 7 fields filled → round(3/7 * 100) = 43
    assert body["profile_completeness"] == 43


@pytest.mark.asyncio
async def test_completeness_full(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    await client.post("/api/profile", json={}, headers=headers)

    resp = await client.patch("/api/profile", json={
        "skill_level": "advanced",
        "martial_arts": ["bjj"],
        "goals": "Win competition",
        "weight_class": "middleweight",
        "training_frequency": "5x/week",
        "primary_domain": "ground",
        "game_style": "pressure",
    }, headers=headers)
    assert resp.json()["profile_completeness"] == 100


@pytest.mark.asyncio
async def test_completeness_recalculated_on_update(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    await client.post("/api/profile", json={
        "skill_level": "beginner",
    }, headers=headers)

    # Add more fields
    resp = await client.patch("/api/profile", json={
        "martial_arts": ["muay_thai"],
        "goals": "Fight in Thailand",
    }, headers=headers)
    # 3 of 7 → 43
    assert resp.json()["profile_completeness"] == 43
