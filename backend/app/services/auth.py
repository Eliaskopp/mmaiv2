import secrets
import uuid
from datetime import datetime, timezone

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

    # TODO: send verification email (logged to console for now)
    print(f"[AUTH] Verification token for {email}: {verification_token}")

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

    Raises HTTPException 400 on invalid token.
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

    user.is_verified = True
    user.verification_token = None
    user.verification_sent_at = None
    await db.commit()
    await db.refresh(user)
    return user
