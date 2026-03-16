import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.note import (
    NoteCreate,
    NoteListResponse,
    NoteResponse,
    NoteUpdate,
)
from app.services import note as note_service

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteResponse, status_code=201)
async def create_note(
    body: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await note_service.create_note(
        db, current_user.id, body.model_dump(exclude_unset=True),
    )
    return NoteResponse.model_validate(note)


@router.get("", response_model=NoteListResponse)
async def list_notes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    type: str | None = Query(None),
    status: str | None = Query(None),
    pinned: bool | None = Query(None),
):
    items, total = await note_service.list_notes(
        db, current_user.id,
        offset=offset, limit=limit,
        type_filter=type, status_filter=status, pinned_filter=pinned,
    )
    return NoteListResponse(
        items=[NoteResponse.model_validate(n) for n in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await note_service.get_note(db, current_user.id, note_id)
    return NoteResponse.model_validate(note)


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: uuid.UUID,
    body: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await note_service.update_note(
        db, current_user.id, note_id, body.model_dump(exclude_unset=True),
    )
    return NoteResponse.model_validate(note)


@router.delete("/{note_id}", response_model=MessageResponse)
async def delete_note(
    note_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await note_service.delete_note(db, current_user.id, note_id)
    return MessageResponse(message="Note deleted")
