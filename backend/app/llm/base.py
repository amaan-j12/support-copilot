"""Provider-agnostic LLM interface.

Every agent node depends only on this ABC, never on a concrete provider.
Swapping ClaudeCLIAdapter <-> APIAdapter is a single env var
(`LLM_PROVIDER`) with zero changes to agent/graph code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResponse:
    text: str | None
    structured_output: dict[str, Any] | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    model: str = ""
    raw: Any = None


class LLMAdapter(ABC):
    """Provider-agnostic chat completion + embedding interface."""

    name: str = "base"
    model_id: str = "base"

    @abstractmethod
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
        """Run one completion.

        `messages` is a plain list of {"role": "user"|"assistant", "content": str}.
        If `response_schema` (a JSON Schema object) is given, the adapter MUST
        return a value satisfying that schema in `LLMResponse.structured_output`.
        """
        raise NotImplementedError

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        raise NotImplementedError
