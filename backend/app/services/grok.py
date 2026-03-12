import httpx

from app.core.config import settings

_DEFAULT_SYSTEM_PROMPT = "You are MMAi Coach, an AI martial arts coaching assistant."

_STUB_RESPONSE = (
    "I'm MMAi Coach (stub mode). "
    "Grok integration is pending configuration."
)


class GrokClient:
    """Wrapper around the xAI Grok API (OpenAI-compatible)."""

    def __init__(self) -> None:
        self.api_key = settings.grok_api_key
        self.base_url = settings.grok_base_url

    async def chat(
        self,
        messages: list[dict],
        system_prompt: str = _DEFAULT_SYSTEM_PROMPT,
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
