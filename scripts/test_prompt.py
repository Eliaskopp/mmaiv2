"""
Prompt evaluation script — sends test scenarios to Grok via the MMAi Coach
system prompt and prints responses for manual review.

Usage:
    python scripts/test_prompt.py          # Interactive menu
    python scripts/test_prompt.py --all    # Run all scenarios
    python scripts/test_prompt.py --pick 1 # Run scenario 1 only

Requires: httpx, python-dotenv
"""

import argparse
import os
import sys
import time
from pathlib import Path

import httpx

# ── Load env & prompt ─────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
ENV_PATH = BACKEND_DIR / ".env"

# Parse .env manually (no extra dep if dotenv missing)
def _load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env

_env = _load_env(ENV_PATH)
API_KEY = _env.get("GROK_API_KEY", "")
BASE_URL = "https://api.x.ai/v1"

if not API_KEY:
    print("\033[91mERROR: GROK_API_KEY not found in backend/.env\033[0m")
    sys.exit(1)

# Import system prompt
sys.path.insert(0, str(BACKEND_DIR))
from app.prompts.coach import COACH_SYSTEM_PROMPT

# ── Mock athlete context ──────────────────────────────────────────────
MOCK_ATHLETE_CONTEXT = (
    "User Profile: Skill level: intermediate. Martial arts: Muay Thai, BJJ. "
    "Goals: Compete in amateur MMA within 12 months. "
    "Injuries/limitations: Previous ACL reconstruction (left knee, 18 months ago). "
    "Training frequency: 4x/week.\n"
    "Today's Recovery: Sleep quality: 3/5. Soreness: 4/5. Energy: 2/5."
)

SYSTEM_PROMPT = COACH_SYSTEM_PROMPT.replace("{athlete_context}", MOCK_ATHLETE_CONTEXT)

# ── ANSI colors ───────────────────────────────────────────────────────
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_DIM = "\033[2m"
C_RED = "\033[91m"

# ── Scenarios ─────────────────────────────────────────────────────────
SCENARIOS: list[dict] = [
    {
        "name": "Technique Question (multi-turn)",
        "messages": [
            "How do I improve my jab? It feels slow and telegraphed.",
            "What about when I'm fighting southpaw?",
        ],
        "eval": [
            "4-part structure (Tactical Observation → Breakdown → Reframe → Next Steps)",
            "Biomechanics depth (force vectors, kinetic chain, physics language)",
            "Actionable drills with reps/cues",
            "Southpaw follow-up references stance asymmetry",
        ],
    },
    {
        "name": "Psychological / Mindset",
        "messages": [
            "I keep getting anxious before sparring and my performance drops.",
        ],
        "eval": [
            "D'Amato Standard application (fear as fuel, not weakness)",
            "Reframes anxiety as a performance signal",
            "No generic motivational fluff",
            "Concrete arousal-regulation drills",
        ],
    },
    {
        "name": "Accountability",
        "messages": [
            "I've only trained once this week. I keep finding excuses.",
        ],
        "eval": [
            "No-excuses callout — names the avoidance pattern",
            "Big Heart (Popovich Standard) — closes with genuine belief",
            "Constructive bridge (specific next action)",
            "Balanced: not cruel, not enabling",
        ],
    },
    {
        "name": "Edge: Greeting",
        "messages": [
            "Hey coach, what's up?",
        ],
        "eval": [
            "Brief, natural response (no forced 4-part structure)",
            "Stays in character as the coach",
        ],
    },
    {
        "name": "Edge: Off-topic",
        "messages": [
            "Can you help me with my JavaScript code?",
        ],
        "eval": [
            "Declines or redirects to MMA coaching",
            "Stays in character, no lecture",
        ],
    },
    {
        "name": "Edge: Medical (ACL history)",
        "messages": [
            "My knee is swollen and hurts when I kick. Should I keep training?",
        ],
        "eval": [
            "References ACL reconstruction from athlete context",
            "Does NOT recommend pushing through",
            "Directs to medical professional",
            "Injury-aware — recognizes the left knee history",
        ],
    },
    {
        "name": "Edge: Vague",
        "messages": [
            "I want to get better",
        ],
        "eval": [
            "Asks a clarification question (genuinely ambiguous intent)",
            "OR uses profile context to provide targeted advice",
            "Does not give generic motivational content",
        ],
    },
    {
        "name": "Extended Session (8 turns)",
        "messages": [
            # Turn 1 — casual opener
            "Hey coach, had a rough week. Just got back from BJJ and I'm cooked.",
            # Turn 2 — technique question
            "We drilled arm bars from guard today and I keep losing the finish. They just posture out every time.",
            # Turn 3 — short follow-up referencing earlier answer
            "That makes sense. What if they're way bigger than me though? Like 20kg heavier.",
            # Turn 4 — topic shift to sparring anxiety
            "Yeah. Honestly rolling with the big guys scares me a bit. I tense up and gas out in the first minute.",
            # Turn 5 — emotional / vulnerable moment
            "Sometimes I wonder if I'm even cut out for this. Everyone at the gym seems to be improving faster than me.",
            # Turn 6 — recovery / injury check-in
            "My knee has been a bit stiff after rolling too. Not swollen, just tight. Should I be worried?",
            # Turn 7 — planning / goal-oriented
            "Alright. So realistically, what should my next 4 weeks look like if I want to be ready to compete?",
            # Turn 8 — closing gratitude
            "Thanks coach. Needed that. See you next session.",
        ],
        "eval": [
            "Persona consistency — stays in character across all 8 turns",
            "Tone flexibility — casual for turns 1/8, technical for 2/3, empathetic for 4/5",
            "Context memory — references earlier turns (arm bar, big guys, knee) in later answers",
            "No repetition — doesn't recycle the same phrases/structures every turn",
            "Vulnerability handling — turn 5 gets D'Amato/Popovich, not dismissive or generic",
            "Injury awareness — turn 6 references ACL history without being asked",
            "Planning depth — turn 7 gives a structured block, not vague encouragement",
            "Natural close — turn 8 gets a brief sign-off, not a forced 4-part response",
            "Overall feel — would a real athlete want to come back for another session?",
        ],
    },
]

# ── Grok API call ─────────────────────────────────────────────────────
def send_message(history: list[dict], user_msg: str) -> tuple[str, float]:
    """Send a message to Grok with search enabled. Returns (response, latency_s)."""
    history.append({"role": "user", "content": user_msg})

    payload = {
        "model": "grok-3-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
        ],
        "search_mode": "auto",
    }

    start = time.monotonic()
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            f"{BASE_URL}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()

    elapsed = time.monotonic() - start
    content = resp.json()["choices"][0]["message"]["content"]
    history.append({"role": "assistant", "content": content})
    return content, elapsed


# ── Display helpers ───────────────────────────────────────────────────
def print_header(text: str) -> None:
    width = 70
    print(f"\n{C_CYAN}{'═' * width}")
    print(f"  {text}")
    print(f"{'═' * width}{C_RESET}")


def print_user(msg: str) -> None:
    print(f"\n{C_YELLOW}  ATHLETE:{C_RESET} {msg}")


def print_coach(msg: str, latency: float) -> None:
    print(f"\n{C_GREEN}  COACH{C_DIM} ({latency:.1f}s){C_RESET}{C_GREEN}:{C_RESET}")
    for line in msg.split("\n"):
        print(f"  {line}")


def print_eval_criteria(criteria: list[str]) -> None:
    print(f"\n{C_DIM}  ── Evaluation criteria ──{C_RESET}")
    for c in criteria:
        print(f"  {C_DIM}  • {c}{C_RESET}")


# ── Run a single scenario ────────────────────────────────────────────
def run_scenario(idx: int, scenario: dict) -> None:
    print_header(f"Scenario {idx + 1}: {scenario['name']}")

    history: list[dict] = []
    for msg in scenario["messages"]:
        print_user(msg)
        try:
            response, latency = send_message(history, msg)
            print_coach(response, latency)
        except httpx.HTTPStatusError as e:
            print(f"\n{C_RED}  API ERROR: {e.response.status_code} — {e.response.text[:200]}{C_RESET}")
            return

    print_eval_criteria(scenario["eval"])


# ── Interactive menu ──────────────────────────────────────────────────
def interactive_menu() -> None:
    print(f"\n{C_BOLD}MMAi Coach — Prompt Evaluation Script{C_RESET}")
    print(f"{C_DIM}Model: grok-3-mini | Search: auto | Mock athlete injected{C_RESET}\n")

    for i, s in enumerate(SCENARIOS):
        turns = len(s["messages"])
        turn_label = f"{turns} turn{'s' if turns > 1 else ''}"
        print(f"  {C_BOLD}{i + 1}{C_RESET}. {s['name']} ({turn_label})")

    print(f"  {C_BOLD}A{C_RESET}. Run all scenarios")
    print(f"  {C_BOLD}Q{C_RESET}. Quit\n")

    choice = input(f"{C_CYAN}Pick scenario(s) (e.g. 1,3 or A): {C_RESET}").strip().lower()

    if choice == "q":
        return
    elif choice == "a":
        run_all()
    else:
        for part in choice.split(","):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(SCENARIOS):
                    run_scenario(idx, SCENARIOS[idx])
                else:
                    print(f"{C_RED}Invalid scenario number: {part}{C_RESET}")
            else:
                print(f"{C_RED}Invalid input: {part}{C_RESET}")


def run_all() -> None:
    total_start = time.monotonic()
    for i, scenario in enumerate(SCENARIOS):
        run_scenario(i, scenario)

    elapsed = time.monotonic() - total_start
    print(f"\n{C_BOLD}{'─' * 70}")
    print(f"  All {len(SCENARIOS)} scenarios complete in {elapsed:.1f}s")
    print(f"{'─' * 70}{C_RESET}\n")


# ── Entrypoint ────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="MMAi Coach prompt evaluator")
    parser.add_argument("--all", action="store_true", help="Run all scenarios")
    parser.add_argument("--pick", type=str, help="Comma-separated scenario numbers (e.g. 1,3)")
    args = parser.parse_args()

    if args.all:
        run_all()
    elif args.pick:
        for part in args.pick.split(","):
            idx = int(part.strip()) - 1
            if 0 <= idx < len(SCENARIOS):
                run_scenario(idx, SCENARIOS[idx])
            else:
                print(f"{C_RED}Invalid scenario: {part}{C_RESET}")
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
