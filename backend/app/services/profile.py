import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import TrainingProfile

# Fields that contribute to profile completeness score.
# String fields must be non-null and non-empty; list fields must be non-empty.
_COMPLETENESS_FIELDS = (
    "skill_level",
    "martial_arts",
    "goals",
    "weight_class",
    "training_frequency",
    "primary_domain",
    "game_style",
)


def _calculate_completeness(profile: TrainingProfile) -> int:
    """Count filled completeness fields and return percentage 0–100."""
    filled = 0
    for field in _COMPLETENESS_FIELDS:
        value = getattr(profile, field)
        if value is None:
            continue
        if isinstance(value, (list, dict)) and len(value) == 0:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue
        filled += 1
    return round(filled / len(_COMPLETENESS_FIELDS) * 100)


async def create_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: dict,
) -> TrainingProfile:
    """Create a training profile for a user.

    Raises HTTPException 409 if the user already has a profile.
    """
    result = await db.execute(
        select(TrainingProfile).where(TrainingProfile.user_id == user_id)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists",
        )

    profile = TrainingProfile(user_id=user_id, **data)
    profile.profile_completeness = _calculate_completeness(profile)
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def get_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> TrainingProfile:
    """Return the user's training profile.

    Raises HTTPException 404 if no profile exists.
    """
    result = await db.execute(
        select(TrainingProfile).where(TrainingProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile


async def update_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: dict,
) -> TrainingProfile:
    """Partial-update the user's training profile.

    Only keys present in *data* are written. Raises HTTPException 404
    if no profile exists yet.
    """
    profile = await get_profile(db, user_id)

    for key, value in data.items():
        setattr(profile, key, value)

    profile.profile_completeness = _calculate_completeness(profile)
    await db.commit()
    await db.refresh(profile)
    return profile
