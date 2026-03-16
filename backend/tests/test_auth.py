import pytest
from httpx import AsyncClient

from tests.conftest import db_execute, db_fetchval


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _register(client: AsyncClient, email: str = "test@example.com") -> dict:
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "securepass123",
        "display_name": "Test User",
    })
    return resp.json()


# ── Registration ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "securepass123",
        "display_name": "Test User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["display_name"] == "Test User"
    assert data["user"]["is_verified"] is False
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "email": "dupe@example.com",
        "password": "securepass123",
        "display_name": "First User",
    }
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json={**payload, "display_name": "Second User"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "short@example.com",
        "password": "123",
        "display_name": "Short Pass",
    })
    assert resp.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await _register(client, "login@example.com")
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "securepass123",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await _register(client, "wrong@example.com")
    resp = await client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "securepass123",
    })
    assert resp.status_code == 401


# ── Me ────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient):
    data = await _register(client, "me@example.com")
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_me_no_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


# ── Refresh ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    data = await _register(client, "refresh@example.com")
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(client: AsyncClient):
    data = await _register(client, "badrefresh@example.com")
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": data["access_token"]})
    assert resp.status_code == 401


# ── Logout ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out successfully"


# ── Verify Email ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verify_email_invalid_token(client: AsyncClient):
    resp = await client.post("/api/v1/auth/verify-email", json={"token": "invalid-token"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_verify_email_valid_token(client: AsyncClient):
    await _register(client, "verify@example.com")
    token = await db_fetchval(
        "SELECT verification_token FROM users WHERE email = $1", "verify@example.com"
    )
    resp = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Email verified successfully"
    is_verified = await db_fetchval(
        "SELECT is_verified FROM users WHERE email = $1", "verify@example.com"
    )
    assert is_verified is True


@pytest.mark.asyncio
async def test_verify_email_expired_token(client: AsyncClient):
    await _register(client, "expired@example.com")
    await db_execute(
        "UPDATE users SET verification_sent_at = NOW() - INTERVAL '49 hours' WHERE email = $1",
        "expired@example.com",
    )
    token = await db_fetchval(
        "SELECT verification_token FROM users WHERE email = $1", "expired@example.com"
    )
    resp = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


# ── Forgot / Reset Password ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_forgot_password_existing_email(client: AsyncClient):
    await _register(client, "forgot@example.com")
    resp = await client.post("/api/v1/auth/forgot-password", json={"email": "forgot@example.com"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_forgot_password_unknown_email(client: AsyncClient):
    # Must return 200 even for unknown email — no user enumeration
    resp = await client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    resp = await client.post("/api/v1/auth/reset-password", json={
        "token": "invalid-token",
        "password": "newpassword123",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_success(client: AsyncClient):
    await _register(client, "reset@example.com")
    await client.post("/api/v1/auth/forgot-password", json={"email": "reset@example.com"})

    token = await db_fetchval(
        "SELECT password_reset_token FROM users WHERE email = $1", "reset@example.com"
    )
    resp = await client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "password": "newpassword999",
    })
    assert resp.status_code == 200

    login = await client.post("/api/v1/auth/login", json={
        "email": "reset@example.com",
        "password": "newpassword999",
    })
    assert login.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_expired_token(client: AsyncClient):
    await _register(client, "resetexp@example.com")
    await client.post("/api/v1/auth/forgot-password", json={"email": "resetexp@example.com"})

    await db_execute(
        "UPDATE users SET password_reset_sent_at = NOW() - INTERVAL '31 minutes' WHERE email = $1",
        "resetexp@example.com",
    )
    token = await db_fetchval(
        "SELECT password_reset_token FROM users WHERE email = $1", "resetexp@example.com"
    )
    resp = await client.post("/api/v1/auth/reset-password", json={
        "token": token,
        "password": "newpassword999",
    })
    assert resp.status_code == 400
