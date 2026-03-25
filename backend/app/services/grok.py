import json
import logging

import httpx

from app.core.config import settings
from app.prompts.coach import COACH_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_STUB_RESPONSE = (
    "I'm MMAi Coach (stub mode). "
    "Grok integration is pending configuration."
)

_TITLE_SYSTEM_PROMPT = (
    "You are a title generator. Summarize the user's message into a concise "
    "3 to 5 word title. Return ONLY the title text, no quotes, no punctuation."
)

_STUB_TITLE = "Stub Training Chat"


class GrokClient:
    """Wrapper around the xAI Grok API (OpenAI-compatible)."""

    def __init__(self) -> None:
        self.api_key = settings.grok_api_key
        self.base_url = settings.grok_base_url

    async def chat(
        self,
        messages: list[dict],
        system_prompt: str = COACH_SYSTEM_PROMPT,
        model: str = "grok-3-mini",
    ) -> str:
        """Send messages to Grok and return the assistant response.

        If GROK_API_KEY is empty, returns a canned stub response.
        """
        if not self.api_key:
            return _STUB_RESPONSE

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages,
            ],
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def chat_with_search(
        self,
        messages: list[dict],
        system_prompt: str = COACH_SYSTEM_PROMPT,
        model: str | None = None,
    ) -> str:
        """Send messages with web search enabled for MMA domain knowledge.

        Falls back to regular chat() in stub mode.
        """
        if not self.api_key:
            return _STUB_RESPONSE

        model = model or settings.grok_search_model

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            "search_mode": "auto",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def generate_title(self, user_message: str, model: str = "grok-3-mini") -> str:
        """Generate a short conversation title from the first user message.

        Returns a stub title when no API key is configured.
        """
        if not self.api_key:
            return _STUB_TITLE

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": _TITLE_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    async def extract_notes(self, assistant_content: str) -> dict | None:
        """Analyze an assistant response for actionable training content.

        Returns a dict matching NoteExtraction schema, or None on failure.
        In stub mode, returns has_extractable_content=False.
        """
        if not self.api_key:
            return {"has_extractable_content": False}

        system = (
            "You are a note extraction engine. Analyze the coaching response and determine "
            "if it contains actionable training content worth saving as a note. "
            "Return JSON with these fields:\n"
            '- has_extractable_content: bool\n'
            '- type: one of "technique", "drill", "goal", "gear", "gym", "insight" (only if extractable)\n'
            '- title: concise title, max 200 chars (only if extractable)\n'
            '- summary: brief summary of the actionable content (only if extractable)\n'
            "Return ONLY valid JSON, no markdown fences."
        )

        payload = {
            "model": "grok-3-mini",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": assistant_content},
            ],
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )
                resp.raise_for_status()
                data = resp.json()
                raw = data["choices"][0]["message"]["content"].strip()
                return json.loads(raw)
        except Exception:
            logger.exception("extract_notes failed")
            return None

    async def extract_memory(
        self,
        messages: list[dict],
        model: str = "grok-3-mini",
    ) -> dict | None:
        """Extract structured performance data from conversation messages.

        Returns a dict with 'performance_events' and 'training_state' keys,
        or None on failure. Pydantic validation happens in the service layer.
        """
        if not self.api_key:
            return {"performance_events": [], "training_state": None}

        from app.prompts.memory_extraction import MEMORY_EXTRACTION_PROMPT

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": MEMORY_EXTRACTION_PROMPT},
                *messages,
            ],
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )
                resp.raise_for_status()
                data = resp.json()
                raw = data["choices"][0]["message"]["content"].strip()
                return json.loads(raw)
        except Exception:
            logger.exception("extract_memory failed")
            return None

    async def health_check(self) -> dict:
        """Lightweight Grok API ping. Returns status and latency."""
        import time

        if not self.api_key:
            return {"status": "unconfigured", "latency_ms": 0}

        start = time.monotonic()
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": "grok-3-mini",
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 1,
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )
                resp.raise_for_status()
                latency = round((time.monotonic() - start) * 1000)
                return {"status": "connected", "latency_ms": latency}
        except Exception:
            latency = round((time.monotonic() - start) * 1000)
            return {"status": "disconnected", "latency_ms": latency}
