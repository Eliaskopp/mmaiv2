import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message, MessageRole
from app.services.grok import GrokClient

_DEFAULT_SYSTEM_PROMPT = "You are MMAi Coach, an AI martial arts coaching assistant."


async def _build_system_prompt(db: AsyncSession, user_id: uuid.UUID) -> str:
    """Build a dynamic system prompt from the user's profile and today's recovery log.

    Falls back to a generic prompt if no profile or recovery data exists.
    """
    from app.services import profile as profile_service
    from app.services import recovery as recovery_service

    parts: list[str] = [
        "You are MMAi Coach, an AI martial arts coaching assistant.",
    ]

    # Fetch profile — catch 404 gracefully
    try:
        profile = await profile_service.get_profile(db, user_id)
        profile_parts: list[str] = []
        if profile.skill_level:
            profile_parts.append(f"Skill level: {profile.skill_level}")
        if profile.martial_arts:
            arts = ", ".join(profile.martial_arts) if isinstance(profile.martial_arts, list) else str(profile.martial_arts)
            profile_parts.append(f"Martial arts: {arts}")
        if profile.goals:
            profile_parts.append(f"Goals: {profile.goals}")
        if profile.injuries:
            injuries = ", ".join(profile.injuries) if isinstance(profile.injuries, list) else str(profile.injuries)
            profile_parts.append(f"Injuries/limitations: {injuries}")
        if profile.training_frequency:
            profile_parts.append(f"Training frequency: {profile.training_frequency}")
        if profile_parts:
            parts.append("User Profile: " + ". ".join(profile_parts) + ".")
    except HTTPException:
        pass

    # Fetch today's recovery log — catch 404 gracefully
    try:
        log = await recovery_service.get_log_by_date(db, user_id, date.today())
        recovery_parts: list[str] = []
        if log.sleep_quality is not None:
            recovery_parts.append(f"Sleep quality: {log.sleep_quality}/5")
        if log.soreness is not None:
            recovery_parts.append(f"Soreness: {log.soreness}/5")
        if log.energy is not None:
            recovery_parts.append(f"Energy: {log.energy}/5")
        if log.notes:
            recovery_parts.append(f"Notes: {log.notes}")
        if recovery_parts:
            parts.append("Today's Recovery: " + ". ".join(recovery_parts) + ".")
    except HTTPException:
        pass

    return " ".join(parts)


async def create_conversation(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str | None = None,
) -> Conversation:
    conversation = Conversation(
        user_id=user_id,
        title=title or "New Conversation",
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def list_conversations(
    db: AsyncSession,
    user_id: uuid.UUID,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Conversation], int]:
    base = select(Conversation).where(
        Conversation.user_id == user_id,
        Conversation.deleted_at.is_(None),
    )

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    rows_q = base.order_by(Conversation.updated_at.desc()).offset(offset).limit(limit)
    rows = (await db.execute(rows_q)).scalars().all()
    return rows, total


async def get_conversation(
    db: AsyncSession,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> Conversation:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
            Conversation.deleted_at.is_(None),
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conversation


async def delete_conversation(
    db: AsyncSession,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> None:
    conversation = await get_conversation(db, user_id, conversation_id)
    conversation.deleted_at = func.now()
    await db.commit()


async def send_message(
    db: AsyncSession,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    content: str,
) -> tuple[Message, Message]:
    # ── 1. DB Reads ──────────────────────────────────────────────────────
    conversation = await get_conversation(db, user_id, conversation_id)

    system_prompt = await _build_system_prompt(db, user_id)

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(20)
    )
    recent = list(reversed(result.scalars().all()))

    # ── 2. Memory Prep ───────────────────────────────────────────────────
    chat_history = [
        {"role": m.role.value if hasattr(m.role, "value") else m.role, "content": m.content}
        for m in recent
    ]
    chat_history.append({"role": "user", "content": content})

    # ── 3. Network I/O (no DB transaction held open) ─────────────────────
    grok = GrokClient()
    assistant_content = await grok.chat(chat_history, system_prompt=system_prompt)

    # ── 4. DB Writes (atomic) ────────────────────────────────────────────
    user_msg = Message(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=content,
    )
    assistant_msg = Message(
        conversation_id=conversation_id,
        role=MessageRole.ASSISTANT,
        content=assistant_content,
    )
    db.add(user_msg)
    db.add(assistant_msg)
    conversation.message_count += 2

    await db.commit()
    await db.refresh(user_msg)
    await db.refresh(assistant_msg)
    return user_msg, assistant_msg


async def list_messages(
    db: AsyncSession,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[Message], int]:
    await get_conversation(db, user_id, conversation_id)

    base = select(Message).where(Message.conversation_id == conversation_id)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    rows_q = base.order_by(Message.created_at.asc()).offset(offset).limit(limit)
    rows = (await db.execute(rows_q)).scalars().all()
    return rows, total
