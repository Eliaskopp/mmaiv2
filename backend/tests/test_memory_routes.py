"""Tests for memory read endpoints (Slice 5)."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _register(client: AsyncClient, email: str = "memory-route@example.com") -> dict:
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "securepass123",
        "display_name": "Memory Route User",
    })
    return resp.json()


def _auth(data: dict) -> dict:
    return {"Authorization": f"Bearer {data['access_token']}"}


async def _seed_events(client: AsyncClient, headers: dict, db_insert_fn=None) -> None:
    """Seed events via direct DB insert through the service layer.

    We import inside the function to avoid module-level import issues.
    """
    pass  # Placeholder — actual seeding done inline in tests


# ── GET /memory/events ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_events_empty(client: AsyncClient):
    data = await _register(client)
    resp = await client.get("/api/v1/memory/events", headers=_auth(data))

    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["offset"] == 0
    assert body["limit"] == 20


@pytest.mark.asyncio
async def test_list_events_returns_own_data(client: AsyncClient):
    """Events created for user A are returned; user B sees nothing."""
    data_a = await _register(client, "memory-a@example.com")
    data_b = await _register(client, "memory-b@example.com")

    # Seed an event for user A via service layer
    from app.core.deps import get_db
    from app.main import app
    from app.schemas.memory import PerformanceEventExtraction
    from app.services.memory import save_performance_events

    # Get a DB session from the overridden dependency
    db_gen = app.dependency_overrides[get_db]()
    db = await db_gen.__anext__()
    try:
        extraction = PerformanceEventExtraction(
            event_type="sparring",
            discipline="boxing",
            extraction_confidence=0.8,
        )
        user_a_id = uuid.UUID(data_a["user"]["id"])
        await save_performance_events(db, user_a_id, None, [extraction])
    finally:
        try:
            await db_gen.__anext__()
        except StopAsyncIteration:
            pass

    # User A should see 1 event
    resp_a = await client.get("/api/v1/memory/events", headers=_auth(data_a))
    assert resp_a.status_code == 200
    assert resp_a.json()["total"] == 1

    # User B should see 0 events
    resp_b = await client.get("/api/v1/memory/events", headers=_auth(data_b))
    assert resp_b.status_code == 200
    assert resp_b.json()["total"] == 0


@pytest.mark.asyncio
async def test_list_events_pagination(client: AsyncClient):
    data = await _register(client)

    from app.core.deps import get_db
    from app.main import app
    from app.schemas.memory import PerformanceEventExtraction
    from app.services.memory import save_performance_events

    db_gen = app.dependency_overrides[get_db]()
    db = await db_gen.__anext__()
    try:
        user_id = uuid.UUID(data["user"]["id"])
        extractions = [
            PerformanceEventExtraction(
                event_type="sparring",
                discipline="boxing",
                event_date=date.today() - timedelta(days=i),
                extraction_confidence=0.8,
            )
            for i in range(5)
        ]
        await save_performance_events(db, user_id, None, extractions)
    finally:
        try:
            await db_gen.__anext__()
        except StopAsyncIteration:
            pass

    resp = await client.get(
        "/api/v1/memory/events?offset=1&limit=2", headers=_auth(data),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["offset"] == 1
    assert body["limit"] == 2


@pytest.mark.asyncio
async def test_list_events_order(client: AsyncClient):
    """Events returned newest-first by event_date."""
    data = await _register(client)

    from app.core.deps import get_db
    from app.main import app
    from app.schemas.memory import PerformanceEventExtraction
    from app.services.memory import save_performance_events

    db_gen = app.dependency_overrides[get_db]()
    db = await db_gen.__anext__()
    try:
        user_id = uuid.UUID(data["user"]["id"])
        extractions = [
            PerformanceEventExtraction(
                event_type="sparring",
                discipline="boxing",
                event_date=date.today() - timedelta(days=3),
                extraction_confidence=0.8,
            ),
            PerformanceEventExtraction(
                event_type="drill",
                discipline="muay_thai",
                event_date=date.today(),
                extraction_confidence=0.7,
            ),
            PerformanceEventExtraction(
                event_type="competition",
                discipline="mma",
                event_date=date.today() - timedelta(days=1),
                extraction_confidence=0.9,
            ),
        ]
        await save_performance_events(db, user_id, None, extractions)
    finally:
        try:
            await db_gen.__anext__()
        except StopAsyncIteration:
            pass

    resp = await client.get("/api/v1/memory/events", headers=_auth(data))
    assert resp.status_code == 200
    items = resp.json()["items"]
    dates = [item["event_date"] for item in items]
    assert dates == sorted(dates, reverse=True)


# ── GET /memory/state ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_state_null(client: AsyncClient):
    """User with no training state gets null response (200, not 404)."""
    data = await _register(client)
    resp = await client.get("/api/v1/memory/state", headers=_auth(data))

    assert resp.status_code == 200
    assert resp.json() is None


@pytest.mark.asyncio
async def test_get_state_returns_data(client: AsyncClient):
    data = await _register(client)

    from app.core.deps import get_db
    from app.main import app
    from app.schemas.memory import UserTrainingStateExtraction
    from app.services.memory import upsert_training_state

    db_gen = app.dependency_overrides[get_db]()
    db = await db_gen.__anext__()
    try:
        user_id = uuid.UUID(data["user"]["id"])
        state = UserTrainingStateExtraction(
            current_focus=["guard retention", "takedown defense"],
            active_injuries=["sore left knee"],
            short_term_goals=["compete in April"],
        )
        await upsert_training_state(db, user_id, state)
    finally:
        try:
            await db_gen.__anext__()
        except StopAsyncIteration:
            pass

    resp = await client.get("/api/v1/memory/state", headers=_auth(data))
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_focus"] == ["guard retention", "takedown defense"]
    assert body["active_injuries"] == ["sore left knee"]
    assert body["short_term_goals"] == ["compete in April"]
    assert "id" in body
    assert "user_id" in body
    assert "created_at" in body


# ── Auth ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_endpoints_require_auth(client: AsyncClient):
    resp_events = await client.get("/api/v1/memory/events")
    assert resp_events.status_code in (401, 403)

    resp_state = await client.get("/api/v1/memory/state")
    assert resp_state.status_code in (401, 403)
