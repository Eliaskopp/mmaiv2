import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageCreate,
    MessageListResponse,
    MessageResponse as MsgResponse,
)
from app.services import conversation as conversation_service

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await conversation_service.create_conversation(
        db, current_user.id, body.title,
    )
    return ConversationResponse.model_validate(conv)


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    items, total = await conversation_service.list_conversations(
        db, current_user.id, offset=offset, limit=limit,
    )
    return ConversationListResponse(
        items=[ConversationResponse.model_validate(c) for c in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await conversation_service.get_conversation(
        db, current_user.id, conversation_id,
    )
    messages, _ = await conversation_service.list_messages(
        db, current_user.id, conversation_id, offset=0, limit=1000,
    )
    return ConversationDetailResponse(
        **ConversationResponse.model_validate(conv).model_dump(),
        messages=[MsgResponse.model_validate(m) for m in messages],
    )


@router.delete("/{conversation_id}", response_model=MessageResponse)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await conversation_service.delete_conversation(
        db, current_user.id, conversation_id,
    )
    return MessageResponse(message="Conversation deleted")


@router.post(
    "/{conversation_id}/messages",
    response_model=list[MsgResponse],
    status_code=201,
)
async def send_message(
    conversation_id: uuid.UUID,
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_msg, assistant_msg = await conversation_service.send_message(
        db, current_user.id, conversation_id, body.content,
    )
    return [
        MsgResponse.model_validate(user_msg),
        MsgResponse.model_validate(assistant_msg),
    ]


@router.get(
    "/{conversation_id}/messages",
    response_model=MessageListResponse,
)
async def list_messages(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    items, total = await conversation_service.list_messages(
        db, current_user.id, conversation_id, offset=offset, limit=limit,
    )
    return MessageListResponse(
        items=[MsgResponse.model_validate(m) for m in items],
        total=total,
        offset=offset,
        limit=limit,
    )
