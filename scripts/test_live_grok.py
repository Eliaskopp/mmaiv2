"""
Live E2E test of the AI Coach Engine against localhost:8000.

Usage:
    python scripts/test_live_grok.py

Requires: httpx (pip install httpx)
"""

import os
import sys
import time

import httpx

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
TIMEOUT = 30.0


def main():
    client = httpx.Client(base_url=BASE_URL, timeout=TIMEOUT)
    unique = int(time.time())

    # ── 1. Register ──────────────────────────────────────────────
    print("1) Registering test user...")
    resp = client.post("/api/auth/register", json={
        "email": f"e2e_{unique}@test.com",
        "password": "TestPass123!",
        "display_name": "E2E Tester",
    })
    if resp.status_code != 201:
        print(f"   FAIL ({resp.status_code}): {resp.text}")
        sys.exit(1)
    token = resp.json()["access_token"]
    print(f"   OK — token: {token[:20]}...")

    headers = {"Authorization": f"Bearer {token}"}

    # ── 2. Create Profile ────────────────────────────────────────
    print("2) Creating profile...")
    resp = client.post("/api/profile", json={
        "skill_level": "intermediate",
        "martial_arts": ["Muay Thai"],
        "goals": "Improve cardio",
    }, headers=headers)
    if resp.status_code != 201:
        print(f"   FAIL ({resp.status_code}): {resp.text}")
        sys.exit(1)
    print("   OK — profile created")

    # ── 3. Create Recovery Log ───────────────────────────────────
    print("3) Creating recovery log...")
    resp = client.post("/api/recovery/logs", json={
        "soreness": 5,
        "energy": 1,
        "notes": "Legs are dead from sparring",
    }, headers=headers)
    if resp.status_code not in (200, 201):
        print(f"   FAIL ({resp.status_code}): {resp.text}")
        sys.exit(1)
    print("   OK — recovery log created")

    # ── 4. Create Conversation ───────────────────────────────────
    print("4) Creating conversation...")
    resp = client.post("/api/conversations", json={}, headers=headers)
    if resp.status_code != 201:
        print(f"   FAIL ({resp.status_code}): {resp.text}")
        sys.exit(1)
    conversation_id = resp.json()["id"]
    print(f"   OK — conversation: {conversation_id}")

    # ── 5. Send Message ──────────────────────────────────────────
    print("5) Sending message to coach...")
    resp = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": "Coach, what should I do for training today?"},
        headers=headers,
    )
    if resp.status_code != 201:
        print(f"   FAIL ({resp.status_code}): {resp.text}")
        sys.exit(1)

    messages = resp.json()
    assistant_msg = messages[1]  # [user_msg, assistant_msg]

    # ── 6. Print AI Response ─────────────────────────────────────
    print("\n" + "=" * 60)
    print("AI COACH RESPONSE")
    print("=" * 60)
    print(assistant_msg["content"])
    print("=" * 60)


if __name__ == "__main__":
    main()
