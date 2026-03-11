import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _register(client: AsyncClient, email: str = "journal@example.com") -> dict:
    resp = await client.post("/api/auth/register", json={
        "email": email,
        "password": "securepass123",
        "display_name": "Journal User",
    })
    return resp.json()


def _auth(data: dict) -> dict:
    return {"Authorization": f"Bearer {data['access_token']}"}


async def _create_session(
    client: AsyncClient, headers: dict, **overrides,
) -> dict:
    payload = {"session_type": "muay_thai", **overrides}
    resp = await client.post("/api/journal/sessions", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()


# ── Create ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_session_success(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    body = await _create_session(
        client, headers,
        title="Morning sparring",
        duration_minutes=60,
        intensity_rpe=7,
    )
    assert body["session_type"] == "muay_thai"
    assert body["title"] == "Morning sparring"
    assert body["duration_minutes"] == 60
    assert body["intensity_rpe"] == 7
    assert body["exertion_load"] == 420.0  # 7 * 60
    assert body["source"] == "manual"
    assert "id" in body
    assert body["user_id"] == data["user"]["id"]


@pytest.mark.asyncio
async def test_create_session_minimal(client: AsyncClient):
    data = await _register(client)
    body = await _create_session(client, _auth(data))
    assert body["session_type"] == "muay_thai"
    assert body["title"] is None
    assert body["duration_minutes"] is None
    assert body["exertion_load"] is None


@pytest.mark.asyncio
async def test_create_session_all_fields(client: AsyncClient):
    data = await _register(client)
    today = date.today().isoformat()
    body = await _create_session(
        client, _auth(data),
        session_date=today,
        title="Full session",
        notes="Great workout",
        duration_minutes=90,
        rounds=5,
        round_duration_minutes=3.0,
        intensity_rpe=8,
        mood_before=3,
        mood_after=5,
        energy_level=4,
        techniques=["roundhouse", "teep"],
        training_partner="Alex",
        gym_name="Elite MMA",
        source="voice",
    )
    assert body["session_date"] == today
    assert body["rounds"] == 5
    assert body["round_duration_minutes"] == 3.0
    assert body["mood_before"] == 3
    assert body["mood_after"] == 5
    assert body["energy_level"] == 4
    assert body["techniques"] == ["roundhouse", "teep"]
    assert body["training_partner"] == "Alex"
    assert body["gym_name"] == "Elite MMA"
    assert body["source"] == "voice"
    assert body["exertion_load"] == 720.0  # 8 * 90


@pytest.mark.asyncio
async def test_create_session_invalid_type(client: AsyncClient):
    data = await _register(client)
    resp = await client.post("/api/journal/sessions", json={
        "session_type": "yoga",
    }, headers=_auth(data))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_session_invalid_rpe(client: AsyncClient):
    data = await _register(client)
    resp = await client.post("/api/journal/sessions", json={
        "session_type": "boxing",
        "intensity_rpe": 11,
    }, headers=_auth(data))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_session_invalid_duration(client: AsyncClient):
    data = await _register(client)
    resp = await client.post("/api/journal/sessions", json={
        "session_type": "boxing",
        "duration_minutes": 0,
    }, headers=_auth(data))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_session_unauthenticated(client: AsyncClient):
    resp = await client.post("/api/journal/sessions", json={
        "session_type": "bjj_gi",
    })
    assert resp.status_code in (401, 403)


# ── List ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_sessions_empty(client: AsyncClient):
    data = await _register(client)
    resp = await client.get("/api/journal/sessions", headers=_auth(data))
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["offset"] == 0
    assert body["limit"] == 20


@pytest.mark.asyncio
async def test_list_sessions_own_only(client: AsyncClient):
    user1 = await _register(client, "user1@example.com")
    user2 = await _register(client, "user2@example.com")
    await _create_session(client, _auth(user1), title="User1 session")
    await _create_session(client, _auth(user2), title="User2 session")

    resp = await client.get("/api/journal/sessions", headers=_auth(user1))
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "User1 session"


@pytest.mark.asyncio
async def test_list_sessions_pagination(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    for i in range(5):
        await _create_session(client, headers, title=f"Session {i}")

    resp = await client.get("/api/journal/sessions?limit=2&offset=0", headers=headers)
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["offset"] == 0
    assert body["limit"] == 2

    resp2 = await client.get("/api/journal/sessions?limit=2&offset=4", headers=headers)
    body2 = resp2.json()
    assert len(body2["items"]) == 1
    assert body2["total"] == 5


@pytest.mark.asyncio
async def test_list_sessions_date_range(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    today = date.today()
    yesterday = (today - timedelta(days=1)).isoformat()
    tomorrow = (today + timedelta(days=1)).isoformat()
    await _create_session(client, headers, session_date=yesterday, title="Yesterday")
    await _create_session(client, headers, session_date=today.isoformat(), title="Today")

    resp = await client.get(
        f"/api/journal/sessions?date_from={today.isoformat()}&date_to={tomorrow}",
        headers=headers,
    )
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Today"


@pytest.mark.asyncio
async def test_list_sessions_type_filter(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    await _create_session(client, headers, session_type="boxing", title="Boxing")
    await _create_session(client, headers, session_type="bjj_gi", title="BJJ")

    resp = await client.get("/api/journal/sessions?session_type=boxing", headers=headers)
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Boxing"


@pytest.mark.asyncio
async def test_list_sessions_order_by_date_desc(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    today = date.today()
    yesterday = (today - timedelta(days=1)).isoformat()
    await _create_session(client, headers, session_date=yesterday, title="Older")
    await _create_session(client, headers, session_date=today.isoformat(), title="Newer")

    resp = await client.get("/api/journal/sessions", headers=headers)
    items = resp.json()["items"]
    assert items[0]["title"] == "Newer"
    assert items[1]["title"] == "Older"


# ── Get ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_session_success(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    created = await _create_session(client, headers, title="Test Get")

    resp = await client.get(f"/api/journal/sessions/{created['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test Get"


@pytest.mark.asyncio
async def test_get_session_not_found(client: AsyncClient):
    data = await _register(client)
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/journal/sessions/{fake_id}", headers=_auth(data))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_session_other_user(client: AsyncClient):
    user1 = await _register(client, "owner@example.com")
    user2 = await _register(client, "intruder@example.com")
    created = await _create_session(client, _auth(user1))

    resp = await client.get(
        f"/api/journal/sessions/{created['id']}", headers=_auth(user2),
    )
    assert resp.status_code == 404


# ── Update ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_session_partial(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    created = await _create_session(
        client, headers, title="Original", duration_minutes=30,
    )

    resp = await client.patch(
        f"/api/journal/sessions/{created['id']}",
        json={"title": "Updated"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Updated"
    assert body["duration_minutes"] == 30  # unchanged


@pytest.mark.asyncio
async def test_update_session_exertion_recomputed(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    created = await _create_session(
        client, headers, duration_minutes=60, intensity_rpe=5,
    )
    assert created["exertion_load"] == 300.0

    resp = await client.patch(
        f"/api/journal/sessions/{created['id']}",
        json={"intensity_rpe": 8},
        headers=headers,
    )
    assert resp.json()["exertion_load"] == 480.0  # 8 * 60


@pytest.mark.asyncio
async def test_update_session_not_found(client: AsyncClient):
    data = await _register(client)
    fake_id = str(uuid.uuid4())
    resp = await client.patch(
        f"/api/journal/sessions/{fake_id}",
        json={"title": "Nope"},
        headers=_auth(data),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_session_other_user(client: AsyncClient):
    user1 = await _register(client, "owner2@example.com")
    user2 = await _register(client, "intruder2@example.com")
    created = await _create_session(client, _auth(user1))

    resp = await client.patch(
        f"/api/journal/sessions/{created['id']}",
        json={"title": "Hacked"},
        headers=_auth(user2),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_session_invalid_data(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    created = await _create_session(client, headers)

    resp = await client.patch(
        f"/api/journal/sessions/{created['id']}",
        json={"intensity_rpe": 99},
        headers=headers,
    )
    assert resp.status_code == 422


# ── Delete / Soft Delete ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_session_success(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    created = await _create_session(client, headers, title="To Delete")

    resp = await client.delete(
        f"/api/journal/sessions/{created['id']}", headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Session deleted"

    # Verify gone from GET
    get_resp = await client.get(
        f"/api/journal/sessions/{created['id']}", headers=headers,
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_session_not_found(client: AsyncClient):
    data = await _register(client)
    fake_id = str(uuid.uuid4())
    resp = await client.delete(
        f"/api/journal/sessions/{fake_id}", headers=_auth(data),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_session_other_user(client: AsyncClient):
    user1 = await _register(client, "del_owner@example.com")
    user2 = await _register(client, "del_intruder@example.com")
    created = await _create_session(client, _auth(user1))

    resp = await client.delete(
        f"/api/journal/sessions/{created['id']}", headers=_auth(user2),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_session_unauthenticated(client: AsyncClient):
    resp = await client.delete(f"/api/journal/sessions/{uuid.uuid4()}")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_soft_deleted_not_in_list(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    s1 = await _create_session(client, headers, title="Keep")
    s2 = await _create_session(client, headers, title="Delete Me")

    await client.delete(f"/api/journal/sessions/{s2['id']}", headers=headers)

    resp = await client.get("/api/journal/sessions", headers=headers)
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Keep"


@pytest.mark.asyncio
async def test_soft_deleted_returns_404_on_get(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    created = await _create_session(client, headers)

    await client.delete(f"/api/journal/sessions/{created['id']}", headers=headers)

    resp = await client.get(
        f"/api/journal/sessions/{created['id']}", headers=headers,
    )
    assert resp.status_code == 404


# ── Exertion Load ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_exertion_load_computed(client: AsyncClient):
    data = await _register(client)
    body = await _create_session(
        client, _auth(data), duration_minutes=45, intensity_rpe=6,
    )
    assert body["exertion_load"] == 270.0  # 6 * 45


@pytest.mark.asyncio
async def test_exertion_load_none_when_missing(client: AsyncClient):
    data = await _register(client)
    # Only RPE, no duration
    body = await _create_session(
        client, _auth(data), intensity_rpe=7,
    )
    assert body["exertion_load"] is None

    # Only duration, no RPE
    body2 = await _create_session(
        client, _auth(data), duration_minutes=60,
    )
    assert body2["exertion_load"] is None
