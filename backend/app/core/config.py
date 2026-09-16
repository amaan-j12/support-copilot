from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Database ---
    database_url: str = "postgresql+psycopg://localhost/support_copilot"

    # --- LLM provider ---
    # "claude_cli"  -> shells out to the local `claude` CLI, $0 marginal cost, needs `claude` on PATH.
    # "api"         -> real API call via litellm (ANTHROPIC_API_KEY / OPENAI_API_KEY etc).
    llm_provider: Literal["claude_cli", "api"] = "claude_cli"
    llm_model: str = "anthropic/claude-sonnet-5"  # used only when llm_provider == "api" (litellm model id)
    claude_cli_model: str = "sonnet"  # passed to `claude --model`
    claude_cli_timeout_s: int = 120

    local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- Guardrails / cost caps ---
    max_tool_iterations_per_ticket: int = 6
    max_tokens_per_ticket: int = 20_000
    max_cost_usd_per_ticket: float = 0.50

    # --- Observability (Phase 2+) ---
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"

    # --- Eval ---
    active_eval_set_version: str = "v1"

    # --- App ---
    environment: Literal["dev", "prod"] = "dev"
    api_cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
