from datetime import date, timedelta

import pytest
from httpx import AsyncClient


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _register(client: AsyncClient, email: str = "recovery@example.com") -> dict:
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "securepass123",
        "display_name": "Recovery User",
    })
    return resp.json()


def _auth(data: dict) -> dict:
    return {"Authorization": f"Bearer {data['access_token']}"}


async def _create_log(
    client: AsyncClient, headers: dict, **overrides,
) -> dict:
    payload = {**overrides}
    resp = await client.post("/api/v1/recovery/logs", json=payload, headers=headers)
    assert resp.status_code == 200
    return resp.json()


# ── Upsert / Create ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_create_all_fields(client: AsyncClient):
    data = await _register(client)
    today = date.today().isoformat()
    body = await _create_log(
        client, _auth(data),
        sleep_quality=4,
        soreness=2,
        energy=3,
        notes="Feeling decent",
        logged_for=today,
    )
    assert body["sleep_quality"] == 4
    assert body["soreness"] == 2
    assert body["energy"] == 3
    assert body["notes"] == "Feeling decent"
    assert body["logged_for"] == today
    assert body["user_id"] == data["user"]["id"]
    assert "id" in body
    assert "created_at" in body


@pytest.mark.asyncio
async def test_upsert_create_minimal(client: AsyncClient):
    data = await _register(client)
    today = date.today().isoformat()
    body = await _create_log(client, _auth(data), logged_for=today)
    assert body["sleep_quality"] is None
    assert body["soreness"] is None
    assert body["energy"] is None
    assert body["notes"] is None
    assert body["logged_for"] == today


@pytest.mark.asyncio
async def test_upsert_default_date(client: AsyncClient):
    data = await _register(client)
    body = await _create_log(client, _auth(data), sleep_quality=3)
    assert body["logged_for"] == date.today().isoformat()


@pytest.mark.asyncio
async def test_upsert_same_date_updates(client: AsyncClient):
    """POST twice for the same date must update, not duplicate."""
    data = await _register(client)
    headers = _auth(data)
    today = date.today().isoformat()

    first = await _create_log(
        client, headers,
        sleep_quality=3, soreness=2, energy=4,
        notes="Morning check-in", logged_for=today,
    )
    first_id = first["id"]
    first_created = first["created_at"]

    second = await _create_log(
        client, headers,
        sleep_quality=5, soreness=1, energy=5,
        notes="Updated after nap", logged_for=today,
    )

    # Same row was updated (same id)
    assert second["id"] == first_id
    # created_at is immutable
    assert second["created_at"] == first_created
    # Values are updated
    assert second["sleep_quality"] == 5
    assert second["soreness"] == 1
    assert second["energy"] == 5
    assert second["notes"] == "Updated after nap"

    # Verify only one log exists for today
    resp = await client.get("/api/v1/recovery/logs", headers=headers)
    assert resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_upsert_invalid_metric(client: AsyncClient):
    data = await _register(client)
    resp = await client.post("/api/v1/recovery/logs", json={
        "sleep_quality": 6,
    }, headers=_auth(data))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_upsert_unauthenticated(client: AsyncClient):
    resp = await client.post("/api/v1/recovery/logs", json={"sleep_quality": 3})
    assert resp.status_code in (401, 403)


# ── List ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_logs_empty(client: AsyncClient):
    data = await _register(client)
    resp = await client.get("/api/v1/recovery/logs", headers=_auth(data))
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["offset"] == 0
    assert body["limit"] == 20


@pytest.mark.asyncio
async def test_list_logs_own_only(client: AsyncClient):
    user1 = await _register(client, "rec_u1@example.com")
    user2 = await _register(client, "rec_u2@example.com")
    await _create_log(client, _auth(user1), sleep_quality=4)
    await _create_log(client, _auth(user2), sleep_quality=2)

    resp = await client.get("/api/v1/recovery/logs", headers=_auth(user1))
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["sleep_quality"] == 4


@pytest.mark.asyncio
async def test_list_logs_pagination(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    today = date.today()
    for i in range(5):
        d = (today - timedelta(days=i)).isoformat()
        await _create_log(client, headers, sleep_quality=i + 1, logged_for=d)

    resp = await client.get("/api/v1/recovery/logs?limit=2&offset=0", headers=headers)
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["offset"] == 0
    assert body["limit"] == 2

    resp2 = await client.get("/api/v1/recovery/logs?limit=2&offset=4", headers=headers)
    body2 = resp2.json()
    assert len(body2["items"]) == 1
    assert body2["total"] == 5


@pytest.mark.asyncio
async def test_list_logs_date_range(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    today = date.today()
    yesterday = today - timedelta(days=1)
    await _create_log(client, headers, sleep_quality=3, logged_for=yesterday.isoformat())
    await _create_log(client, headers, sleep_quality=5, logged_for=today.isoformat())

    resp = await client.get(
        f"/api/v1/recovery/logs?date_from={today.isoformat()}&date_to={today.isoformat()}",
        headers=headers,
    )
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["sleep_quality"] == 5


@pytest.mark.asyncio
async def test_list_logs_order_by_date_desc(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    today = date.today()
    yesterday = today - timedelta(days=1)
    await _create_log(client, headers, sleep_quality=2, logged_for=yesterday.isoformat())
    await _create_log(client, headers, sleep_quality=5, logged_for=today.isoformat())

    resp = await client.get("/api/v1/recovery/logs", headers=headers)
    items = resp.json()["items"]
    assert items[0]["sleep_quality"] == 5  # today first
    assert items[1]["sleep_quality"] == 2  # yesterday second


# ── Get by Date ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_log_by_date_success(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    today = date.today().isoformat()
    await _create_log(client, headers, sleep_quality=4, logged_for=today)

    resp = await client.get(f"/api/v1/recovery/logs/{today}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["sleep_quality"] == 4
    assert resp.json()["logged_for"] == today


@pytest.mark.asyncio
async def test_get_log_by_date_not_found(client: AsyncClient):
    data = await _register(client)
    resp = await client.get("/api/v1/recovery/logs/2020-01-01", headers=_auth(data))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_log_by_date_other_user(client: AsyncClient):
    user1 = await _register(client, "rec_owner@example.com")
    user2 = await _register(client, "rec_intruder@example.com")
    today = date.today().isoformat()
    await _create_log(client, _auth(user1), sleep_quality=3, logged_for=today)

    resp = await client.get(f"/api/v1/recovery/logs/{today}", headers=_auth(user2))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_log_by_date_unauthenticated(client: AsyncClient):
    resp = await client.get(f"/api/v1/recovery/logs/{date.today().isoformat()}")
    assert resp.status_code in (401, 403)


# ── Validation ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invalid_sleep_quality_above_range(client: AsyncClient):
    data = await _register(client)
    resp = await client.post("/api/v1/recovery/logs", json={
        "sleep_quality": 6,
    }, headers=_auth(data))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_soreness_below_range(client: AsyncClient):
    data = await _register(client)
    resp = await client.post("/api/v1/recovery/logs", json={
        "soreness": 0,
    }, headers=_auth(data))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_energy_out_of_range(client: AsyncClient):
    data = await _register(client)
    resp = await client.post("/api/v1/recovery/logs", json={
        "energy": -1,
    }, headers=_auth(data))
    assert resp.status_code == 422
