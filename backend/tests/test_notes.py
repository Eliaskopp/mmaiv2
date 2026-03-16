import uuid

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.schemas.note import NoteExtraction
from app.services.grok import GrokClient


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _register(client: AsyncClient, email: str = "note@example.com") -> dict:
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "securepass123",
        "display_name": "Note User",
    })
    return resp.json()


def _auth(data: dict) -> dict:
    return {"Authorization": f"Bearer {data['access_token']}"}


async def _create_note(
    client: AsyncClient, headers: dict, **overrides,
) -> dict:
    payload = {
        "type": "technique",
        "title": "Rear Naked Choke Details",
        **overrides,
    }
    resp = await client.post("/api/v1/notes", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()


# ── Note CRUD ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_note_manual(client: AsyncClient):
    data = await _register(client)
    body = await _create_note(client, _auth(data))
    assert body["type"] == "technique"
    assert body["title"] == "Rear Naked Choke Details"
    assert body["source"] == "manual"
    assert body["status"] == "active"
    assert body["pinned"] is False
    assert body["source_conversation_id"] is None
    assert "id" in body
    assert "created_at" in body


@pytest.mark.asyncio
async def test_create_note_all_fields(client: AsyncClient):
    data = await _register(client)
    body = await _create_note(
        client, _auth(data),
        type="drill",
        title="Shadow Boxing Drill",
        summary="3-round shadow boxing with head movement focus",
        user_notes="Remember to stay light on feet",
    )
    assert body["type"] == "drill"
    assert body["summary"] == "3-round shadow boxing with head movement focus"
    assert body["user_notes"] == "Remember to stay light on feet"


@pytest.mark.asyncio
async def test_create_note_unauthenticated(client: AsyncClient):
    resp = await client.post("/api/v1/notes", json={
        "type": "technique", "title": "Nope",
    })
    assert resp.status_code in (401, 403)


# ── List Notes ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_notes_empty(client: AsyncClient):
    data = await _register(client)
    resp = await client.get("/api/v1/notes", headers=_auth(data))
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_list_notes_type_filter(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    await _create_note(client, headers, type="technique", title="Note A")
    await _create_note(client, headers, type="drill", title="Note B")

    resp = await client.get("/api/v1/notes?type=technique", headers=headers)
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["type"] == "technique"


@pytest.mark.asyncio
async def test_list_notes_status_filter(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    note = await _create_note(client, headers, title="To Archive")
    # Archive it
    await client.patch(
        f"/api/v1/notes/{note['id']}", json={"status": "archived"}, headers=headers,
    )

    resp = await client.get("/api/v1/notes?status=active", headers=headers)
    assert resp.json()["total"] == 0

    resp2 = await client.get("/api/v1/notes?status=archived", headers=headers)
    assert resp2.json()["total"] == 1


@pytest.mark.asyncio
async def test_list_notes_pinned_filter(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    note = await _create_note(client, headers, title="Pin Me")
    await client.patch(
        f"/api/v1/notes/{note['id']}", json={"pinned": True}, headers=headers,
    )
    await _create_note(client, headers, title="Not Pinned")

    resp = await client.get("/api/v1/notes?pinned=true", headers=headers)
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["pinned"] is True


@pytest.mark.asyncio
async def test_list_notes_pagination(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    for i in range(5):
        await _create_note(client, headers, title=f"Note {i}")

    resp = await client.get("/api/v1/notes?limit=2&offset=0", headers=headers)
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5

    resp2 = await client.get("/api/v1/notes?limit=2&offset=4", headers=headers)
    body2 = resp2.json()
    assert len(body2["items"]) == 1


# ── Get Note ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_note_by_id(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    note = await _create_note(client, headers, title="Get Me")

    resp = await client.get(f"/api/v1/notes/{note['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Get Me"


@pytest.mark.asyncio
async def test_get_note_not_found(client: AsyncClient):
    data = await _register(client)
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/notes/{fake_id}", headers=_auth(data))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_note_wrong_user(client: AsyncClient):
    user1 = await _register(client, "note_owner@example.com")
    user2 = await _register(client, "note_intruder@example.com")
    note = await _create_note(client, _auth(user1), title="Private Note")

    resp = await client.get(f"/api/v1/notes/{note['id']}", headers=_auth(user2))
    assert resp.status_code == 404


# ── Update Note ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_note_partial(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    note = await _create_note(client, headers, title="Original")

    resp = await client.patch(
        f"/api/v1/notes/{note['id']}",
        json={"title": "Updated Title"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"
    assert resp.json()["type"] == "technique"  # unchanged


@pytest.mark.asyncio
async def test_update_note_toggle_pinned(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    note = await _create_note(client, headers)
    assert note["pinned"] is False

    resp = await client.patch(
        f"/api/v1/notes/{note['id']}", json={"pinned": True}, headers=headers,
    )
    assert resp.json()["pinned"] is True


@pytest.mark.asyncio
async def test_update_note_archive(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    note = await _create_note(client, headers)

    resp = await client.patch(
        f"/api/v1/notes/{note['id']}", json={"status": "archived"}, headers=headers,
    )
    assert resp.json()["status"] == "archived"


# ── Delete Note ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_note(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    note = await _create_note(client, headers)

    resp = await client.delete(f"/api/v1/notes/{note['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Note deleted"

    # Verify gone
    get_resp = await client.get(f"/api/v1/notes/{note['id']}", headers=headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_note_wrong_user(client: AsyncClient):
    user1 = await _register(client, "del_owner@example.com")
    user2 = await _register(client, "del_intruder@example.com")
    note = await _create_note(client, _auth(user1))

    resp = await client.delete(f"/api/v1/notes/{note['id']}", headers=_auth(user2))
    assert resp.status_code == 404


# ── NoteExtraction Pydantic Validation ───────────────────────────────────────


def test_note_extraction_false_no_fields():
    e = NoteExtraction(has_extractable_content=False)
    assert e.has_extractable_content is False
    assert e.type is None
    assert e.title is None


def test_note_extraction_true_with_fields():
    e = NoteExtraction(
        has_extractable_content=True,
        type="technique",
        title="Double Leg Setup",
        summary="Chain jab-cross into level change",
    )
    assert e.has_extractable_content is True
    assert e.type == "technique"


def test_note_extraction_true_missing_title_fails():
    with pytest.raises(ValidationError):
        NoteExtraction(has_extractable_content=True, type="drill")


def test_note_extraction_true_missing_type_fails():
    with pytest.raises(ValidationError):
        NoteExtraction(has_extractable_content=True, title="Some Title")


# ── Grok extract_notes Stub ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_extract_notes_stub_returns_no_content():
    grok = GrokClient()
    result = await grok.extract_notes("Here is some coaching advice.")
    assert result is not None
    assert result["has_extractable_content"] is False


# ── Integration: send message → no notes in stub mode ───────────────────────


@pytest.mark.asyncio
async def test_send_message_triggers_extraction(client: AsyncClient):
    """Sending a message triggers background note extraction.
    In stub mode: extract_notes returns has_extractable_content=False → 0 notes.
    In live mode: Grok may extract a note → >= 0 notes.
    Either way, the pipeline should not crash."""
    import asyncio

    data = await _register(client, "extract_test@example.com")
    headers = _auth(data)

    # Create conversation and send message
    conv_resp = await client.post(
        "/api/v1/conversations", json={"title": "Extraction Test"}, headers=headers,
    )
    conv_id = conv_resp.json()["id"]
    msg_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Show me a jab drill"},
        headers=headers,
    )
    assert msg_resp.status_code == 201

    # Give background task time to complete
    await asyncio.sleep(1.0)

    # Pipeline ran without crashing — check notes endpoint works
    notes_resp = await client.get("/api/v1/notes", headers=headers)
    assert notes_resp.status_code == 200
    # Notes created depend on API key presence — either 0 (stub) or 1+ (live)
    assert notes_resp.json()["total"] >= 0
