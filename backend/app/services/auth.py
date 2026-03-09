import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.services import email as email_service

VERIFICATION_TOKEN_EXPIRY_HOURS = 48
PASSWORD_RESET_TOKEN_EXPIRY_MINUTES = 30


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    display_name: str,
) -> tuple[User, str, str]:
    """Register a new user. Returns (user, access_token, refresh_token).

    Raises HTTPException 409 if email already taken.
    """
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    verification_token = secrets.token_urlsafe(32)

    user = User(
        email=email,
        hashed_password=hash_password(password),
        display_name=display_name,
        verification_token=verification_token,
        verification_sent_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await email_service.send_verification_email(email, verification_token)

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return user, access, refresh


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> tuple[User, str, str]:
    """Authenticate a user by email/password. Returns (user, access_token, refresh_token).

    Raises HTTPException 401 on bad credentials.
    """
    bad_creds = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        # Constant-time comparison even when user doesn't exist
        verify_password(password, hash_password("dummy"))
        raise bad_creds

    if not verify_password(password, user.hashed_password):
        raise bad_creds

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return user, access, refresh


async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
) -> str:
    """Validate a refresh token and issue a new access token.

    Raises HTTPException 401 on invalid/expired refresh token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise credentials_exception
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return create_access_token(str(user.id))


async def verify_email(db: AsyncSession, token: str) -> User:
    """Mark a user as verified using their verification token.

    Raises HTTPException 400 on invalid or expired token.
    """
    result = await db.execute(
        select(User).where(User.verification_token == token)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    if user.verification_sent_at is None or datetime.now(timezone.utc) - user.verification_sent_at > timedelta(
        hours=VERIFICATION_TOKEN_EXPIRY_HOURS
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired",
        )

    user.is_verified = True
    user.verification_token = None
    user.verification_sent_at = None
    await db.commit()
    await db.refresh(user)

    await email_service.send_welcome_email(user.email, user.display_name)

    return user


async def request_password_reset(db: AsyncSession, email: str) -> None:
    """Generate a password reset token and send reset email.

    Always returns silently even if email not found — avoids user enumeration.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        return

    reset_token = secrets.token_urlsafe(32)
    user.password_reset_token = reset_token
    user.password_reset_sent_at = datetime.now(timezone.utc)
    await db.commit()

    await email_service.send_password_reset_email(email, reset_token)


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    """Reset a user's password using a valid reset token.

    Raises HTTPException 400 on invalid or expired token.
    """
    result = await db.execute(
        select(User).where(User.password_reset_token == token)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    if user.password_reset_sent_at is None or datetime.now(timezone.utc) - user.password_reset_sent_at > timedelta(
        minutes=PASSWORD_RESET_TOKEN_EXPIRY_MINUTES
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user.hashed_password = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_sent_at = None
    await db.commit()
