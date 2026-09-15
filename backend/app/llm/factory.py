from functools import lru_cache

from app.core.config import get_settings
from app.llm.base import LLMAdapter


@lru_cache
def get_llm_adapter() -> LLMAdapter:
    provider = get_settings().llm_provider
    if provider == "claude_cli":
        from app.llm.claude_cli_adapter import ClaudeCLIAdapter

        return ClaudeCLIAdapter()
    if provider == "api":
        from app.llm.api_adapter import APIAdapter

        return APIAdapter()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
