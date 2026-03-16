import uuid

import pytest
from httpx import AsyncClient


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _register(client: AsyncClient, email: str = "chat@example.com") -> dict:
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "securepass123",
        "display_name": "Chat User",
    })
    return resp.json()


def _auth(data: dict) -> dict:
    return {"Authorization": f"Bearer {data['access_token']}"}


async def _create_conversation(
    client: AsyncClient, headers: dict, **overrides,
) -> dict:
    payload = {**overrides}
    resp = await client.post("/api/v1/conversations", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()


async def _send_message(
    client: AsyncClient, headers: dict, conversation_id: str, content: str,
) -> list[dict]:
    resp = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": content},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


# ── Conversation CRUD ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_conversation_with_title(client: AsyncClient):
    data = await _register(client)
    body = await _create_conversation(client, _auth(data), title="Muay Thai Help")
    assert body["title"] == "Muay Thai Help"
    assert body["message_count"] == 0
    assert body["user_id"] == data["user"]["id"]
    assert "id" in body
    assert "created_at" in body


@pytest.mark.asyncio
async def test_create_conversation_default_title(client: AsyncClient):
    data = await _register(client)
    body = await _create_conversation(client, _auth(data))
    assert body["title"] == "New Conversation"


@pytest.mark.asyncio
async def test_list_conversations_empty(client: AsyncClient):
    data = await _register(client)
    resp = await client.get("/api/v1/conversations", headers=_auth(data))
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["offset"] == 0
    assert body["limit"] == 20


@pytest.mark.asyncio
async def test_list_conversations_own_only(client: AsyncClient):
    user1 = await _register(client, "chat_u1@example.com")
    user2 = await _register(client, "chat_u2@example.com")
    await _create_conversation(client, _auth(user1), title="User1 Chat")
    await _create_conversation(client, _auth(user2), title="User2 Chat")

    resp = await client.get("/api/v1/conversations", headers=_auth(user1))
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "User1 Chat"


@pytest.mark.asyncio
async def test_list_conversations_pagination(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    for i in range(5):
        await _create_conversation(client, headers, title=f"Chat {i}")

    resp = await client.get("/api/v1/conversations?limit=2&offset=0", headers=headers)
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5

    resp2 = await client.get("/api/v1/conversations?limit=2&offset=4", headers=headers)
    body2 = resp2.json()
    assert len(body2["items"]) == 1
    assert body2["total"] == 5


@pytest.mark.asyncio
async def test_delete_conversation_soft_delete(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    conv = await _create_conversation(client, headers, title="To Delete")

    resp = await client.delete(f"/api/v1/conversations/{conv['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Conversation deleted"

    # Verify gone from GET
    get_resp = await client.get(f"/api/v1/conversations/{conv['id']}", headers=headers)
    assert get_resp.status_code == 404

    # Verify gone from list
    list_resp = await client.get("/api/v1/conversations", headers=headers)
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_create_conversation_unauthenticated(client: AsyncClient):
    resp = await client.post("/api/v1/conversations", json={"title": "Nope"})
    assert resp.status_code in (401, 403)


# ── Send Message ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_message_returns_pair(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    conv = await _create_conversation(client, headers)

    messages = await _send_message(client, headers, conv["id"], "Hello coach!")
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello coach!"
    assert messages[1]["role"] == "assistant"
    assert len(messages[1]["content"]) > 0


@pytest.mark.asyncio
async def test_send_message_increments_count(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    conv = await _create_conversation(client, headers)
    assert conv["message_count"] == 0

    await _send_message(client, headers, conv["id"], "First message")

    resp = await client.get(f"/api/v1/conversations/{conv['id']}", headers=headers)
    assert resp.json()["message_count"] == 2


@pytest.mark.asyncio
async def test_send_message_assistant_response(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    conv = await _create_conversation(client, headers)

    messages = await _send_message(client, headers, conv["id"], "What should I train?")
    # Works in both stub mode ("stub mode" in response) and live mode (real AI response)
    assert len(messages[1]["content"]) > 0


@pytest.mark.asyncio
async def test_send_message_preserves_order(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    conv = await _create_conversation(client, headers)

    await _send_message(client, headers, conv["id"], "First")
    await _send_message(client, headers, conv["id"], "Second")

    resp = await client.get(
        f"/api/v1/conversations/{conv['id']}/messages", headers=headers,
    )
    items = resp.json()["items"]
    assert len(items) == 4  # 2 pairs
    assert items[0]["role"] == "user"
    assert items[0]["content"] == "First"
    assert items[1]["role"] == "assistant"
    assert items[2]["role"] == "user"
    assert items[2]["content"] == "Second"
    assert items[3]["role"] == "assistant"


@pytest.mark.asyncio
async def test_send_message_nonexistent_conversation(client: AsyncClient):
    data = await _register(client)
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        f"/api/v1/conversations/{fake_id}/messages",
        json={"content": "Hello"},
        headers=_auth(data),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_send_message_other_user_conversation(client: AsyncClient):
    user1 = await _register(client, "msg_owner@example.com")
    user2 = await _register(client, "msg_intruder@example.com")
    conv = await _create_conversation(client, _auth(user1))

    resp = await client.post(
        f"/api/v1/conversations/{conv['id']}/messages",
        json={"content": "Sneaky"},
        headers=_auth(user2),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_send_message_unauthenticated(client: AsyncClient):
    resp = await client.post(
        f"/api/v1/conversations/{uuid.uuid4()}/messages",
        json={"content": "Hello"},
    )
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_send_first_message_generates_title(client: AsyncClient):
    data = await _register(client, "title_gen@example.com")
    headers = _auth(data)
    conv = await _create_conversation(client, headers)
    assert conv["title"] == "New Conversation"

    await _send_message(client, headers, conv["id"], "How do I improve my jab?")

    resp = await client.get(f"/api/v1/conversations/{conv['id']}", headers=headers)
    body = resp.json()
    # Title should have been auto-generated (no longer the default)
    assert body["title"] != "New Conversation"
    assert len(body["title"]) > 0


@pytest.mark.asyncio
async def test_second_message_does_not_change_title(client: AsyncClient):
    data = await _register(client, "title_keep@example.com")
    headers = _auth(data)
    conv = await _create_conversation(client, headers)

    await _send_message(client, headers, conv["id"], "First message")

    resp = await client.get(f"/api/v1/conversations/{conv['id']}", headers=headers)
    title_after_first = resp.json()["title"]

    await _send_message(client, headers, conv["id"], "Second message")

    resp2 = await client.get(f"/api/v1/conversations/{conv['id']}", headers=headers)
    assert resp2.json()["title"] == title_after_first


# ── Get Conversation Detail ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_conversation_with_messages(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    conv = await _create_conversation(client, headers, title="Detail Test")
    await _send_message(client, headers, conv["id"], "Hi there")

    resp = await client.get(f"/api/v1/conversations/{conv['id']}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    # Title is auto-generated on first message, so it won't be "Detail Test" anymore
    assert body["title"] != "New Conversation"
    assert body["message_count"] == 2
    assert len(body["messages"]) == 2


@pytest.mark.asyncio
async def test_get_conversation_not_found(client: AsyncClient):
    data = await _register(client)
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/conversations/{fake_id}", headers=_auth(data))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_conversation_other_user(client: AsyncClient):
    user1 = await _register(client, "conv_owner@example.com")
    user2 = await _register(client, "conv_intruder@example.com")
    conv = await _create_conversation(client, _auth(user1))

    resp = await client.get(
        f"/api/v1/conversations/{conv['id']}", headers=_auth(user2),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_conversation_soft_deleted(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    conv = await _create_conversation(client, headers)
    await client.delete(f"/api/v1/conversations/{conv['id']}", headers=headers)

    resp = await client.get(f"/api/v1/conversations/{conv['id']}", headers=headers)
    assert resp.status_code == 404


# ── List Messages ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_messages_chronological(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    conv = await _create_conversation(client, headers)
    await _send_message(client, headers, conv["id"], "Msg A")
    await _send_message(client, headers, conv["id"], "Msg B")

    resp = await client.get(
        f"/api/v1/conversations/{conv['id']}/messages", headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 4
    # First message is oldest
    assert body["items"][0]["content"] == "Msg A"
    assert body["items"][2]["content"] == "Msg B"


@pytest.mark.asyncio
async def test_list_messages_pagination(client: AsyncClient):
    data = await _register(client)
    headers = _auth(data)
    conv = await _create_conversation(client, headers)
    await _send_message(client, headers, conv["id"], "Msg 1")
    await _send_message(client, headers, conv["id"], "Msg 2")

    resp = await client.get(
        f"/api/v1/conversations/{conv['id']}/messages?limit=2&offset=0",
        headers=headers,
    )
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["total"] == 4


@pytest.mark.asyncio
async def test_list_messages_other_user(client: AsyncClient):
    user1 = await _register(client, "list_owner@example.com")
    user2 = await _register(client, "list_intruder@example.com")
    conv = await _create_conversation(client, _auth(user1))

    resp = await client.get(
        f"/api/v1/conversations/{conv['id']}/messages", headers=_auth(user2),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_messages_unauthenticated(client: AsyncClient):
    resp = await client.get(f"/api/v1/conversations/{uuid.uuid4()}/messages")
    assert resp.status_code in (401, 403)
