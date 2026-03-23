import hashlib
import secrets
from datetime import datetime, timedelta, timezone

OTP_EXPIRY_MINUTES = 10


def generate_otp() -> tuple[str, str]:
    """Generate a 6-digit OTP. Returns (plaintext_code, hashed_code)."""
    code = str(secrets.randbelow(900_000) + 100_000)
    hashed = hashlib.sha256(code.encode()).hexdigest()
    return code, hashed


def verify_otp(code: str, hashed: str) -> bool:
    """Verify a plaintext OTP against its SHA-256 hash."""
    return hashlib.sha256(code.encode()).hexdigest() == hashed


def is_otp_expired(sent_at: datetime | None) -> bool:
    """Check if the OTP has exceeded the expiry window."""
    if sent_at is None:
        return True
    return datetime.now(timezone.utc) - sent_at > timedelta(minutes=OTP_EXPIRY_MINUTES)
