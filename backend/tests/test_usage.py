import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import usage as usage_service


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _register(client: AsyncClient, email: str = "usage@example.com") -> dict:
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "securepass123",
        "display_name": "Usage User",
    })
    return resp.json()


def _auth(data: dict) -> dict:
    return {"Authorization": f"Bearer {data['access_token']}"}


# ── Service-level Tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_increment_creates_record(client: AsyncClient, db_session: AsyncSession):
    data = await _register(client, "inc1@example.com")
    user_id = uuid.UUID(data["user"]["id"])

    count_before = await usage_service.get_daily_usage(db_session, user_id)
    assert count_before == 0

    await usage_service.increment_message_count(db_session, user_id)
    await db_session.commit()

    count_after = await usage_service.get_daily_usage(db_session, user_id)
    assert count_after == 1


@pytest.mark.asyncio
async def test_increment_upserts(client: AsyncClient, db_session: AsyncSession):
    data = await _register(client, "inc2@example.com")
    user_id = uuid.UUID(data["user"]["id"])

    await usage_service.increment_message_count(db_session, user_id)
    await db_session.commit()
    await usage_service.increment_message_count(db_session, user_id)
    await db_session.commit()

    count = await usage_service.get_daily_usage(db_session, user_id)
    assert count == 2


@pytest.mark.asyncio
async def test_daily_usage_different_dates(client: AsyncClient, db_session: AsyncSession):
    data = await _register(client, "inc3@example.com")
    user_id = uuid.UUID(data["user"]["id"])

    today = date.today()
    yesterday = date(today.year, today.month, today.day - 1) if today.day > 1 else today

    await usage_service.increment_message_count(db_session, user_id, today)
    await db_session.commit()

    count_today = await usage_service.get_daily_usage(db_session, user_id, today)
    assert count_today == 1

    count_yesterday = await usage_service.get_daily_usage(db_session, user_id, yesterday)
    assert count_yesterday == 0


@pytest.mark.asyncio
async def test_check_quota_pass(client: AsyncClient, db_session: AsyncSession):
    data = await _register(client, "quota_pass@example.com")
    user_id = uuid.UUID(data["user"]["id"])

    within = await usage_service.check_quota(db_session, user_id, daily_limit=50)
    assert within is True


@pytest.mark.asyncio
async def test_check_quota_fail(client: AsyncClient, db_session: AsyncSession):
    data = await _register(client, "quota_fail@example.com")
    user_id = uuid.UUID(data["user"]["id"])

    # Manually set count to the limit
    for _ in range(5):
        await usage_service.increment_message_count(db_session, user_id)
        await db_session.commit()

    within = await usage_service.check_quota(db_session, user_id, daily_limit=5)
    assert within is False


# ── Integration: exhaust quota → 429 ────────────────────────────────────────


@pytest.mark.asyncio
async def test_exhaust_quota_returns_429(client: AsyncClient, db_session: AsyncSession):
    """Exhaust the daily quota via direct DB writes, then verify 429."""
    data = await _register(client, "quota_429@example.com")
    headers = _auth(data)
    user_id = uuid.UUID(data["user"]["id"])

    # Create a conversation
    conv_resp = await client.post(
        "/api/v1/conversations", json={"title": "Quota Test"}, headers=headers,
    )
    conv_id = conv_resp.json()["id"]

    # Set message count to the limit (50) directly
    for _ in range(50):
        await usage_service.increment_message_count(db_session, user_id)
        await db_session.commit()

    # Next message should be 429
    resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "One more please"},
        headers=headers,
    )
    assert resp.status_code == 429
    assert "limit" in resp.json()["detail"].lower()
