"""Live ACWR endpoint smoke test against localhost:8000."""

import json
from datetime import date, timedelta

import httpx

BASE = "http://localhost:8000/api"


def main():
    client = httpx.Client(base_url=BASE, timeout=10)

    # 1. Register
    email = "acwr_test_live@test.com"
    r = client.post("/auth/register", json={
        "email": email,
        "password": "testpass123",
        "display_name": "ACWR Tester",
    })
    r.raise_for_status()
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Registered {email}")

    today = date.today()

    # 2. Acute window — 3 sessions in last 7 days
    acute_sessions = [
        (today - timedelta(days=1), 10, 50),   # 500
        (today - timedelta(days=3), 10, 60),   # 600
        (today - timedelta(days=5), 10, 70),   # 700
    ]
    for d, rpe, dur in acute_sessions:
        r = client.post("/journal/sessions", json={
            "session_type": "muay_thai",
            "session_date": str(d),
            "intensity_rpe": rpe,
            "duration_minutes": dur,
        }, headers=headers)
        r.raise_for_status()
        load = r.json()["exertion_load"]
        print(f"  Acute  | {d} | RPE {rpe} x {dur}min = {load}")

    # 3. Chronic window — 4 sessions between 8-28 days ago
    chronic_sessions = [
        (today - timedelta(days=10), 6, 45),   # 270
        (today - timedelta(days=14), 7, 50),   # 350
        (today - timedelta(days=20), 5, 60),   # 300
        (today - timedelta(days=26), 6, 40),   # 240
    ]
    for d, rpe, dur in chronic_sessions:
        r = client.post("/journal/sessions", json={
            "session_type": "bjj_gi",
            "session_date": str(d),
            "intensity_rpe": rpe,
            "duration_minutes": dur,
        }, headers=headers)
        r.raise_for_status()
        load = r.json()["exertion_load"]
        print(f"  Chronic| {d} | RPE {rpe} x {dur}min = {load}")

    # 4. Fetch ACWR
    r = client.get("/stats/acwr", headers=headers)
    r.raise_for_status()

    # 5. Pretty print
    print("\n── ACWR Response ──────────────────────────")
    print(json.dumps(r.json(), indent=2))


if __name__ == "__main__":
    main()
