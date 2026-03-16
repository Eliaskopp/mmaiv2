import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _register(client: AsyncClient, email: str = "streak@example.com") -> dict:
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "securepass123",
        "display_name": "Streak User",
    })
    return resp.json()


def _auth(data: dict) -> dict:
    return {"Authorization": f"Bearer {data['access_token']}"}


async def _create_profile(client: AsyncClient, headers: dict) -> dict:
    resp = await client.post("/api/v1/profile", json={}, headers=headers)
    assert resp.status_code == 201
    return resp.json()


async def _create_session(
    client: AsyncClient, headers: dict, session_date: str | None = None, **overrides,
) -> dict:
    payload = {"session_type": "muay_thai", "duration_minutes": 60, **overrides}
    if session_date is not None:
        payload["session_date"] = session_date
    resp = await client.post("/api/v1/journal/sessions", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()


async def _get_streak(client: AsyncClient, headers: dict) -> dict:
    resp = await client.get("/api/v1/profile", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    return {
        "current_streak": body["current_streak"],
        "longest_streak": body["longest_streak"],
        "last_active_date": body["last_active_date"],
    }


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_first_session_starts_streak(client: AsyncClient):
    data = await _register(client, "streak_first@example.com")
    headers = _auth(data)
    await _create_profile(client, headers)

    today = date.today().isoformat()
    await _create_session(client, headers, session_date=today)

    streak = await _get_streak(client, headers)
    assert streak["current_streak"] == 1
    assert streak["longest_streak"] == 1
    assert streak["last_active_date"] == today


@pytest.mark.asyncio
async def test_consecutive_days_increment_streak(client: AsyncClient):
    data = await _register(client, "streak_consec@example.com")
    headers = _auth(data)
    await _create_profile(client, headers)

    base = date.today() - timedelta(days=2)
    for i in range(3):
        d = (base + timedelta(days=i)).isoformat()
        await _create_session(client, headers, session_date=d)

    streak = await _get_streak(client, headers)
    assert streak["current_streak"] == 3
    assert streak["longest_streak"] == 3


@pytest.mark.asyncio
async def test_same_day_no_double_count(client: AsyncClient):
    data = await _register(client, "streak_sameday@example.com")
    headers = _auth(data)
    await _create_profile(client, headers)

    today = date.today().isoformat()
    await _create_session(client, headers, session_date=today)
    await _create_session(client, headers, session_date=today)

    streak = await _get_streak(client, headers)
    assert streak["current_streak"] == 1


@pytest.mark.asyncio
async def test_one_grace_day_continues_streak(client: AsyncClient):
    data = await _register(client, "streak_grace@example.com")
    headers = _auth(data)
    await _create_profile(client, headers)

    day1 = date.today() - timedelta(days=2)
    day3 = day1 + timedelta(days=2)  # gap=2, 1 day skipped

    await _create_session(client, headers, session_date=day1.isoformat())
    await _create_session(client, headers, session_date=day3.isoformat())

    streak = await _get_streak(client, headers)
    assert streak["current_streak"] == 2


@pytest.mark.asyncio
async def test_two_missed_days_resets_streak(client: AsyncClient):
    data = await _register(client, "streak_reset@example.com")
    headers = _auth(data)
    await _create_profile(client, headers)

    day1 = date.today() - timedelta(days=5)
    day4 = day1 + timedelta(days=3)  # gap=3, 2 days skipped

    await _create_session(client, headers, session_date=day1.isoformat())
    await _create_session(client, headers, session_date=day4.isoformat())

    streak = await _get_streak(client, headers)
    assert streak["current_streak"] == 1


@pytest.mark.asyncio
async def test_longest_streak_preserved_after_reset(client: AsyncClient):
    data = await _register(client, "streak_longest@example.com")
    headers = _auth(data)
    await _create_profile(client, headers)

    base = date.today() - timedelta(days=10)
    # Build streak of 3
    for i in range(3):
        await _create_session(client, headers, session_date=(base + timedelta(days=i)).isoformat())

    # Break it (gap=3)
    await _create_session(client, headers, session_date=(base + timedelta(days=6)).isoformat())

    streak = await _get_streak(client, headers)
    assert streak["current_streak"] == 1
    assert streak["longest_streak"] == 3


@pytest.mark.asyncio
async def test_longest_streak_updates_when_exceeded(client: AsyncClient):
    data = await _register(client, "streak_exceed@example.com")
    headers = _auth(data)
    await _create_profile(client, headers)

    base = date.today() - timedelta(days=15)
    # Build streak of 2
    for i in range(2):
        await _create_session(client, headers, session_date=(base + timedelta(days=i)).isoformat())

    # Break it (gap=3)
    await _create_session(client, headers, session_date=(base + timedelta(days=5)).isoformat())

    # Build streak of 4
    for i in range(1, 4):
        await _create_session(client, headers, session_date=(base + timedelta(days=5 + i)).isoformat())

    streak = await _get_streak(client, headers)
    assert streak["current_streak"] == 4
    assert streak["longest_streak"] == 4


@pytest.mark.asyncio
async def test_no_profile_skips_silently(client: AsyncClient):
    data = await _register(client, "streak_noprof@example.com")
    headers = _auth(data)
    # No profile created — session should still succeed
    resp = await client.post("/api/v1/journal/sessions", json={
        "session_type": "muay_thai",
        "duration_minutes": 60,
        "session_date": date.today().isoformat(),
    }, headers=headers)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_explicit_session_date(client: AsyncClient):
    data = await _register(client, "streak_explicit@example.com")
    headers = _auth(data)
    await _create_profile(client, headers)

    past = (date.today() - timedelta(days=5)).isoformat()
    await _create_session(client, headers, session_date=past)

    streak = await _get_streak(client, headers)
    assert streak["last_active_date"] == past
    assert streak["current_streak"] == 1


@pytest.mark.asyncio
async def test_backfill_past_date_no_streak_change(client: AsyncClient):
    data = await _register(client, "streak_backfill@example.com")
    headers = _auth(data)
    await _create_profile(client, headers)

    base = date.today() - timedelta(days=5)
    # Log day 1, day 2, day 3 — streak=3
    for i in range(3):
        await _create_session(client, headers, session_date=(base + timedelta(days=i)).isoformat())

    streak_before = await _get_streak(client, headers)
    assert streak_before["current_streak"] == 3

    # Backfill day 1 again (past date before last_active) — no change
    await _create_session(client, headers, session_date=base.isoformat())

    streak_after = await _get_streak(client, headers)
    assert streak_after["current_streak"] == 3
    assert streak_after["longest_streak"] == 3


@pytest.mark.asyncio
async def test_grace_then_consecutive(client: AsyncClient):
    data = await _register(client, "streak_gracethen@example.com")
    headers = _auth(data)
    await _create_profile(client, headers)

    base = date.today() - timedelta(days=5)
    day1 = base
    day3 = base + timedelta(days=2)  # grace day
    day4 = base + timedelta(days=3)  # consecutive

    await _create_session(client, headers, session_date=day1.isoformat())
    await _create_session(client, headers, session_date=day3.isoformat())
    await _create_session(client, headers, session_date=day4.isoformat())

    streak = await _get_streak(client, headers)
    assert streak["current_streak"] == 3


@pytest.mark.asyncio
async def test_large_gap_resets(client: AsyncClient):
    data = await _register(client, "streak_largegap@example.com")
    headers = _auth(data)
    await _create_profile(client, headers)

    day1 = (date.today() - timedelta(days=30)).isoformat()
    day30 = date.today().isoformat()

    await _create_session(client, headers, session_date=day1)
    await _create_session(client, headers, session_date=day30)

    streak = await _get_streak(client, headers)
    assert streak["current_streak"] == 1
    assert streak["longest_streak"] == 1
