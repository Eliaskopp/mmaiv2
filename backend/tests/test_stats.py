from datetime import date, timedelta

import pytest
from httpx import AsyncClient


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _register(client: AsyncClient, email: str = "stats@example.com") -> dict:
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "securepass123",
        "display_name": "Stats User",
    })
    return resp.json()


def _auth(data: dict) -> dict:
    return {"Authorization": f"Bearer {data['access_token']}"}


async def _create_session(
    client: AsyncClient, headers: dict, *, session_date: str, rpe: int, duration: int,
) -> dict:
    resp = await client.post("/api/v1/journal/sessions", json={
        "session_type": "muay_thai",
        "session_date": session_date,
        "intensity_rpe": rpe,
        "duration_minutes": duration,
    }, headers=headers)
    assert resp.status_code == 201
    return resp.json()


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_acwr_no_sessions(client: AsyncClient):
    """Empty journal → zero loads, no ratio, insufficient data."""
    data = await _register(client)
    resp = await client.get("/api/v1/stats/acwr", headers=_auth(data))
    assert resp.status_code == 200
    body = resp.json()
    assert body["acute_load"] == 0
    assert body["chronic_load"] == 0
    assert body["acwr_ratio"] is None
    assert body["risk_zone"] == "insufficient_data"
    assert body["is_calibrating"] is True
    assert body["session_count"] == 0


@pytest.mark.asyncio
async def test_acwr_acute_only(client: AsyncClient):
    """Sessions only in last 7 days → chronic == acute, ratio == 4.0 (very high)."""
    data = await _register(client, "stats_acute@example.com")
    headers = _auth(data)
    today = date.today()
    # One session today: RPE 8 × 60 min = 480 load
    await _create_session(client, headers, session_date=str(today), rpe=8, duration=60)

    resp = await client.get("/api/v1/stats/acwr", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["acute_load"] == 480.0
    # Chronic includes acute window, so chronic == 480 too
    assert body["chronic_load"] == 480.0
    # Only 1 session in 1 day — below calibration thresholds, so ratio is suppressed
    assert body["acwr_ratio"] is None
    assert body["risk_zone"] == "insufficient_data"
    assert body["is_calibrating"] is True
    assert body["session_count"] == 1


@pytest.mark.asyncio
async def test_acwr_known_values(client: AsyncClient):
    """Known loads across 28-day window produce expected ratio."""
    data = await _register(client, "stats_known@example.com")
    headers = _auth(data)
    today = date.today()

    # Chronic window (weeks 2–4): 3 sessions of RPE 6 × 50 min = 300 each = 900 total
    for i in [10, 17, 24]:
        d = today - timedelta(days=i)
        await _create_session(client, headers, session_date=str(d), rpe=6, duration=50)

    # Acute window (last 7 days): 2 sessions of RPE 7 × 60 min = 420 each = 840 total
    for i in [1, 3]:
        d = today - timedelta(days=i)
        await _create_session(client, headers, session_date=str(d), rpe=7, duration=60)

    resp = await client.get("/api/v1/stats/acwr", headers=headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["acute_load"] == 840.0
    # Chronic = 840 (acute) + 900 (older) = 1740
    assert body["chronic_load"] == 1740.0
    # ACWR = 840 / (1740 / 4) = 840 / 435 ≈ 1.93
    assert body["acwr_ratio"] == 1.93
    assert body["risk_zone"] == "very_high"
    # 5 sessions spanning 23 days → calibrated
    assert body["is_calibrating"] is False
    assert body["session_count"] == 5


@pytest.mark.asyncio
async def test_acwr_optimal_zone(client: AsyncClient):
    """Balanced training across 28 days lands in optimal zone."""
    data = await _register(client, "stats_optimal@example.com")
    headers = _auth(data)
    today = date.today()

    # Spread 4 sessions evenly: one per week, all RPE 5 × 60 = 300
    for week in range(4):
        d = today - timedelta(days=week * 7 + 1)
        await _create_session(client, headers, session_date=str(d), rpe=5, duration=60)

    resp = await client.get("/api/v1/stats/acwr", headers=headers)
    body = resp.json()

    # Acute = 300 (1 session in last 7 days)
    assert body["acute_load"] == 300.0
    # Chronic = 1200 (all 4)
    assert body["chronic_load"] == 1200.0
    # ACWR = 300 / (1200/4) = 300/300 = 1.0
    assert body["acwr_ratio"] == 1.0
    assert body["risk_zone"] == "optimal"
    # 4 sessions spanning 21 days → calibrated
    assert body["is_calibrating"] is False
    assert body["session_count"] == 4


@pytest.mark.asyncio
async def test_acwr_excludes_soft_deleted(client: AsyncClient):
    """Soft-deleted sessions are excluded from ACWR calculation."""
    data = await _register(client, "stats_del@example.com")
    headers = _auth(data)
    today = date.today()

    # Create a session then delete it
    session = await _create_session(
        client, headers, session_date=str(today), rpe=8, duration=60,
    )
    del_resp = await client.delete(
        f"/api/v1/journal/sessions/{session['id']}", headers=headers,
    )
    assert del_resp.status_code == 200

    resp = await client.get("/api/v1/stats/acwr", headers=headers)
    body = resp.json()
    assert body["acute_load"] == 0
    assert body["chronic_load"] == 0
    assert body["acwr_ratio"] is None


@pytest.mark.asyncio
async def test_acwr_requires_auth(client: AsyncClient):
    """Unauthenticated request is rejected."""
    resp = await client.get("/api/v1/stats/acwr")
    assert resp.status_code in (401, 403)


# ── Calibration Edge-Case Tests ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_acwr_calibrating_count_below_threshold(client: AsyncClient):
    """3 sessions across 20 days → is_calibrating (count < 4)."""
    data = await _register(client, "cal_count@example.com")
    headers = _auth(data)
    today = date.today()

    # 3 sessions on days 0, 10, 20 → span = 20, count = 3
    for offset in [0, 10, 20]:
        d = today - timedelta(days=offset)
        await _create_session(client, headers, session_date=str(d), rpe=6, duration=50)

    resp = await client.get("/api/v1/stats/acwr", headers=headers)
    body = resp.json()
    assert body["is_calibrating"] is True


@pytest.mark.asyncio
async def test_acwr_calibrating_span_below_threshold(client: AsyncClient):
    """5 sessions across 10 days → is_calibrating (span < 14)."""
    data = await _register(client, "cal_span@example.com")
    headers = _auth(data)
    today = date.today()

    # 5 sessions on days 0, 2, 4, 7, 10 → span = 10, count = 5
    for offset in [0, 2, 4, 7, 10]:
        d = today - timedelta(days=offset)
        await _create_session(client, headers, session_date=str(d), rpe=6, duration=50)

    resp = await client.get("/api/v1/stats/acwr", headers=headers)
    body = resp.json()
    assert body["is_calibrating"] is True


@pytest.mark.asyncio
async def test_acwr_calibrating_boundary_exact_thresholds(client: AsyncClient):
    """4 sessions across exactly 14 days → NOT calibrating (both thresholds met exactly)."""
    data = await _register(client, "cal_boundary@example.com")
    headers = _auth(data)
    today = date.today()

    # 4 sessions on days 0, 5, 10, 14 → span = 14, count = 4
    for offset in [0, 5, 10, 14]:
        d = today - timedelta(days=offset)
        await _create_session(client, headers, session_date=str(d), rpe=6, duration=50)

    resp = await client.get("/api/v1/stats/acwr", headers=headers)
    body = resp.json()
    assert body["is_calibrating"] is False


@pytest.mark.asyncio
async def test_acwr_calibrating_soft_delete_flips_flag(client: AsyncClient):
    """Deleting a session drops count below 4 → flips to calibrating."""
    data = await _register(client, "cal_del@example.com")
    headers = _auth(data)
    today = date.today()

    # 4 sessions spanning 14 days → starts calibrated
    sessions = []
    for offset in [0, 5, 10, 14]:
        d = today - timedelta(days=offset)
        s = await _create_session(client, headers, session_date=str(d), rpe=6, duration=50)
        sessions.append(s)

    # Verify calibrated first
    resp = await client.get("/api/v1/stats/acwr", headers=headers)
    assert resp.json()["is_calibrating"] is False

    # Delete one session → count drops to 3
    del_resp = await client.delete(
        f"/api/v1/journal/sessions/{sessions[1]['id']}", headers=headers,
    )
    assert del_resp.status_code == 200

    # Now should be calibrating
    resp = await client.get("/api/v1/stats/acwr", headers=headers)
    body = resp.json()
    assert body["is_calibrating"] is True


# ── Volume Trends Tests ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_volume_no_sessions(client: AsyncClient):
    """No sessions → 30 zero-filled days by default."""
    data = await _register(client, "vol_empty@example.com")
    resp = await client.get("/api/v1/stats/volume", headers=_auth(data))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 30
    assert all(d["total_load"] == 0 and d["total_duration"] == 0 for d in body)


@pytest.mark.asyncio
async def test_volume_zero_fill_7_days(client: AsyncClient):
    """Query 7 days, log 1 session → length 7, 6 days have zeroes."""
    data = await _register(client, "vol_fill@example.com")
    headers = _auth(data)
    today = date.today()

    # Log one session 3 days ago: RPE 7 × 45 min = 315 load
    session_date = str(today - timedelta(days=3))
    await _create_session(client, headers, session_date=session_date, rpe=7, duration=45)

    resp = await client.get("/api/v1/stats/volume?days=7", headers=headers)
    assert resp.status_code == 200
    body = resp.json()

    assert len(body) == 7
    # Sorted oldest to newest
    assert body[0]["date"] < body[-1]["date"]

    non_zero = [d for d in body if d["total_load"] > 0]
    assert len(non_zero) == 1
    assert non_zero[0]["date"] == session_date
    assert non_zero[0]["total_load"] == 315.0
    assert non_zero[0]["total_duration"] == 45

    zero_days = [d for d in body if d["total_load"] == 0]
    assert len(zero_days) == 6


@pytest.mark.asyncio
async def test_volume_aggregates_same_day(client: AsyncClient):
    """Two sessions on the same day are summed together."""
    data = await _register(client, "vol_agg@example.com")
    headers = _auth(data)
    today = date.today()
    today_str = str(today)

    # Session 1: RPE 5 × 30 min = 150
    await _create_session(client, headers, session_date=today_str, rpe=5, duration=30)
    # Session 2: RPE 8 × 60 min = 480
    await _create_session(client, headers, session_date=today_str, rpe=8, duration=60)

    resp = await client.get("/api/v1/stats/volume?days=1", headers=headers)
    assert resp.status_code == 200
    body = resp.json()

    assert len(body) == 1
    assert body[0]["date"] == today_str
    assert body[0]["total_load"] == 630.0  # 150 + 480
    assert body[0]["total_duration"] == 90  # 30 + 60


@pytest.mark.asyncio
async def test_volume_excludes_soft_deleted(client: AsyncClient):
    """Soft-deleted sessions are excluded from volume trends."""
    data = await _register(client, "vol_del@example.com")
    headers = _auth(data)
    today = date.today()

    session = await _create_session(
        client, headers, session_date=str(today), rpe=8, duration=60,
    )
    await client.delete(f"/api/v1/journal/sessions/{session['id']}", headers=headers)

    resp = await client.get("/api/v1/stats/volume?days=7", headers=headers)
    body = resp.json()
    assert all(d["total_load"] == 0 for d in body)


@pytest.mark.asyncio
async def test_volume_requires_auth(client: AsyncClient):
    """Unauthenticated request is rejected."""
    resp = await client.get("/api/v1/stats/volume")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_volume_custom_days(client: AsyncClient):
    """Custom days parameter controls the window size."""
    data = await _register(client, "vol_custom@example.com")
    resp = await client.get("/api/v1/stats/volume?days=14", headers=_auth(data))
    assert resp.status_code == 200
    assert len(resp.json()) == 14
