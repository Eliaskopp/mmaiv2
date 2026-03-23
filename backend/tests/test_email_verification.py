import hashlib

import pytest
from httpx import AsyncClient

from tests.conftest import db_execute, db_fetchval


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _register(client: AsyncClient, email: str = "otp@example.com") -> dict:
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "securepass123",
        "display_name": "OTP User",
    })
    return resp.json()


async def _get_plaintext_otp_from_hash(email: str) -> str | None:
    """We can't reverse the hash, so tests that need the plaintext OTP
    must intercept it before it's hashed. This helper is only used for
    negative tests where we verify the DB stores a hash, not plaintext."""
    return None  # Placeholder — positive tests use a different strategy


# ── OTP Unit Tests ───────────────────────────────────────────────────────────

def test_otp_is_six_digits():
    from app.core.otp import generate_otp
    for _ in range(100):
        code, _ = generate_otp()
        assert len(code) == 6
        assert code.isdigit()
        assert 100_000 <= int(code) <= 999_999


def test_otp_hash_verification():
    from app.core.otp import generate_otp, verify_otp
    code, hashed = generate_otp()
    assert verify_otp(code, hashed) is True
    assert verify_otp("000000", hashed) is False


def test_otp_hash_is_sha256():
    from app.core.otp import generate_otp
    code, hashed = generate_otp()
    expected = hashlib.sha256(code.encode()).hexdigest()
    assert hashed == expected
    assert len(hashed) == 64  # SHA-256 hex digest length


def test_otp_expiry_check():
    from datetime import datetime, timedelta, timezone
    from app.core.otp import is_otp_expired

    now = datetime.now(timezone.utc)
    assert is_otp_expired(None) is True
    assert is_otp_expired(now - timedelta(minutes=11)) is True
    assert is_otp_expired(now - timedelta(minutes=9)) is False
    assert is_otp_expired(now - timedelta(seconds=30)) is False


# ── Register Stores Hashed OTP ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_stores_hashed_otp(client: AsyncClient):
    """verification_token in DB must be a SHA-256 hex digest (64 chars), not a 6-digit code."""
    await _register(client, "hashcheck@example.com")
    token = await db_fetchval(
        "SELECT verification_token FROM users WHERE email = $1", "hashcheck@example.com"
    )
    assert token is not None
    assert len(token) == 64  # SHA-256 hex digest
    assert not token.isdigit()  # Not the plaintext 6-digit code


@pytest.mark.asyncio
async def test_register_returns_unverified(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "unreg@example.com",
        "password": "securepass123",
        "display_name": "Unverified User",
    })
    assert resp.status_code == 201
    assert resp.json()["user"]["is_verified"] is False


# ── Verify Email (OTP) ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_verify_email_correct_code(client: AsyncClient, monkeypatch):
    """Intercept OTP generation to capture the plaintext code, then verify it."""
    captured = {}

    from app.core.otp import generate_otp as _original
    from app.services import auth as auth_svc

    def patched_generate():
        code, hashed = _original()
        captured["code"] = code
        return code, hashed

    monkeypatch.setattr(auth_svc, "generate_otp", patched_generate)

    await _register(client, "verify-otp@example.com")
    assert "code" in captured

    resp = await client.post("/api/v1/auth/verify-email", json={
        "email": "verify-otp@example.com",
        "code": captured["code"],
    })
    assert resp.status_code == 200
    assert resp.json()["message"] == "Email verified successfully"

    # Verify DB state
    is_verified = await db_fetchval(
        "SELECT is_verified FROM users WHERE email = $1", "verify-otp@example.com"
    )
    assert is_verified is True

    # Token should be nullified
    token = await db_fetchval(
        "SELECT verification_token FROM users WHERE email = $1", "verify-otp@example.com"
    )
    assert token is None


@pytest.mark.asyncio
async def test_verify_email_wrong_code(client: AsyncClient):
    await _register(client, "wrongcode@example.com")
    resp = await client.post("/api/v1/auth/verify-email", json={
        "email": "wrongcode@example.com",
        "code": "000000",
    })
    assert resp.status_code == 400
    assert "invalid" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_verify_email_expired_code(client: AsyncClient, monkeypatch):
    captured = {}
    from app.core.otp import generate_otp as _original
    from app.services import auth as auth_svc

    def patched_generate():
        code, hashed = _original()
        captured["code"] = code
        return code, hashed

    monkeypatch.setattr(auth_svc, "generate_otp", patched_generate)

    await _register(client, "expiredotp@example.com")

    # Push verification_sent_at back 11 minutes
    await db_execute(
        "UPDATE users SET verification_sent_at = NOW() - INTERVAL '11 minutes' WHERE email = $1",
        "expiredotp@example.com",
    )

    resp = await client.post("/api/v1/auth/verify-email", json={
        "email": "expiredotp@example.com",
        "code": captured["code"],
    })
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_verify_email_unknown_email(client: AsyncClient):
    resp = await client.post("/api/v1/auth/verify-email", json={
        "email": "ghost@example.com",
        "code": "123456",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_verify_email_already_verified(client: AsyncClient, monkeypatch):
    """Verifying an already-verified user (token is None) should fail."""
    captured = {}
    from app.core.otp import generate_otp as _original
    from app.services import auth as auth_svc

    def patched_generate():
        code, hashed = _original()
        captured["code"] = code
        return code, hashed

    monkeypatch.setattr(auth_svc, "generate_otp", patched_generate)

    await _register(client, "alreadyverified@example.com")

    # Manually mark as verified and clear token
    await db_execute(
        "UPDATE users SET is_verified = true, verification_token = NULL WHERE email = $1",
        "alreadyverified@example.com",
    )

    resp = await client.post("/api/v1/auth/verify-email", json={
        "email": "alreadyverified@example.com",
        "code": captured["code"],
    })
    assert resp.status_code == 400


# ── Resend Verification ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resend_generates_new_otp(client: AsyncClient):
    await _register(client, "resend@example.com")

    old_token = await db_fetchval(
        "SELECT verification_token FROM users WHERE email = $1", "resend@example.com"
    )

    resp = await client.post("/api/v1/auth/resend-verification", json={
        "email": "resend@example.com",
    })
    assert resp.status_code == 200

    new_token = await db_fetchval(
        "SELECT verification_token FROM users WHERE email = $1", "resend@example.com"
    )
    assert new_token is not None
    assert new_token != old_token  # New OTP was generated
    assert len(new_token) == 64  # Still a SHA-256 hash


@pytest.mark.asyncio
async def test_resend_unknown_email_returns_200(client: AsyncClient):
    """Silent 200 to prevent user enumeration."""
    resp = await client.post("/api/v1/auth/resend-verification", json={
        "email": "nobody@example.com",
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_resend_already_verified_returns_400(client: AsyncClient):
    await _register(client, "resendverified@example.com")
    await db_execute(
        "UPDATE users SET is_verified = true, verification_token = NULL WHERE email = $1",
        "resendverified@example.com",
    )
    resp = await client.post("/api/v1/auth/resend-verification", json={
        "email": "resendverified@example.com",
    })
    assert resp.status_code == 400
    assert "already verified" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_resend_then_verify_with_new_code(client: AsyncClient, monkeypatch):
    """After resend, only the NEW code should work."""
    codes = []
    from app.core.otp import generate_otp as _original
    from app.services import auth as auth_svc

    def patched_generate():
        code, hashed = _original()
        codes.append(code)
        return code, hashed

    monkeypatch.setattr(auth_svc, "generate_otp", patched_generate)

    await _register(client, "resendnew@example.com")
    old_code = codes[-1]

    await client.post("/api/v1/auth/resend-verification", json={
        "email": "resendnew@example.com",
    })
    new_code = codes[-1]
    assert old_code != new_code  # CSPRNG should produce different codes (astronomically unlikely to collide)

    # Old code should NOT work
    resp = await client.post("/api/v1/auth/verify-email", json={
        "email": "resendnew@example.com",
        "code": old_code,
    })
    assert resp.status_code == 400

    # New code SHOULD work
    resp = await client.post("/api/v1/auth/verify-email", json={
        "email": "resendnew@example.com",
        "code": new_code,
    })
    assert resp.status_code == 200
