"""LLMAdapter backed by a real API call via litellm.

Used for the eventual live deploy (Railway) once the user is ready to spend a
small API budget; provider is whatever `LLM_MODEL` (a litellm model id, e.g.
"anthropic/claude-sonnet-4-5" or "gpt-4.1") resolves to. Selecting this
adapter over ClaudeCLIAdapter is a single `LLM_PROVIDER=api` env var change.
"""

import json
import time
from typing import Any

from app.core.config import get_settings
from app.llm.base import LLMAdapter, LLMResponse


class APIAdapter(LLMAdapter):
    name = "api"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_id = self.settings.llm_model

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        system: str | None = None,
        response_schema: dict[str, Any] | None = None,
        max_tokens: int = 1024,
        node_name: str = "",
        ticket_id: str | None = None,
    ) -> LLMResponse:
        import litellm

        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        kwargs: dict[str, Any] = {
            "model": self.settings.llm_model,
            "messages": full_messages,
            "max_tokens": max_tokens,
        }
        if response_schema:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": response_schema, "strict": True},
            }

        start = time.monotonic()
        resp = litellm.completion(**kwargs)
        latency_ms = int((time.monotonic() - start) * 1000)

        content = resp.choices[0].message.content or ""
        structured_output = None
        if response_schema:
            try:
                structured_output = json.loads(content)
            except json.JSONDecodeError:
                structured_output = None

        cost_usd = 0.0
        try:
            cost_usd = litellm.completion_cost(completion_response=resp)
        except Exception:  # noqa: BLE001, S110 — cost lookup is best-effort; litellm raises
            pass  # for unrecognized models, which shouldn't fail the actual completion.

        usage = getattr(resp, "usage", None)

        return LLMResponse(
            text=content,
            structured_output=structured_output,
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            model=self.settings.llm_model,
            raw=resp,
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        import litellm

        resp = litellm.embedding(model="text-embedding-3-small", input=texts)
        return [item["embedding"] for item in resp.data]

    def count_tokens(self, text: str) -> int:
        import litellm

        return litellm.token_counter(model=self.settings.llm_model, text=text)
