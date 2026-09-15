"""LLMAdapter backed by the local `claude` CLI (Claude Code), for $0-marginal-cost
development against an existing Claude subscription instead of API billing.

Uses `-p --output-format json` for a single non-interactive turn, `--tools ""`
to disable all of Claude Code's own file/bash tools (we only want raw
completions), and `--json-schema` for structured output when a
`response_schema` is requested. Session persistence and project settings are
disabled so every call is isolated and reproducible.
"""

import json
import shutil
import subprocess
import time
from typing import Any

from app.core.config import get_settings
from app.llm.base import LLMAdapter, LLMResponse
from app.llm.embeddings import embed_local

_CLAUDE_BIN = shutil.which("claude")
_MAX_ATTEMPTS = 3
_RETRY_BACKOFF_S = 1.5


class ClaudeCLIError(RuntimeError):
    pass


def _render_transcript(messages: list[dict[str, str]]) -> str:
    """Collapse a chat history into one prompt string for `claude -p`.

    The common case in this codebase is a single user message carrying the
    full rendered context, in which case this is a no-op passthrough.
    """
    if len(messages) == 1 and messages[0]["role"] == "user":
        return messages[0]["content"]
    parts = []
    for m in messages:
        parts.append(f"[{m['role'].upper()}]\n{m['content']}")
    return "\n\n".join(parts)


class ClaudeCLIAdapter(LLMAdapter):
    name = "claude_cli"

    def __init__(self) -> None:
        if _CLAUDE_BIN is None:
            raise ClaudeCLIError(
                "The `claude` CLI was not found on PATH. Install Claude Code or "
                "set LLM_PROVIDER=api in .env."
            )
        self.settings = get_settings()
        self.model_id = self.settings.claude_cli_model

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
        prompt = _render_transcript(messages)

        cmd = [
            _CLAUDE_BIN,
            "-p",
            prompt,
            "--output-format",
            "json",
            "--tools",
            "",
            "--no-session-persistence",
            "--setting-sources",
            "",
            "--strict-mcp-config",
            "--model",
            self.settings.claude_cli_model,
        ]
        if system:
            cmd += ["--system-prompt", system]
        if response_schema:
            cmd += ["--json-schema", json.dumps(response_schema)]

        last_error: Exception | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            start = time.monotonic()
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.settings.claude_cli_timeout_s,
                    check=False,  # non-zero exit handled explicitly below (with retry)
                )
            except subprocess.TimeoutExpired as e:
                last_error = ClaudeCLIError(
                    f"claude CLI timed out after {self.settings.claude_cli_timeout_s}s "
                    f"(node={node_name}, ticket={ticket_id}, attempt={attempt})"
                )
                last_error.__cause__ = e
                time.sleep(_RETRY_BACKOFF_S * attempt)
                continue
            latency_ms = int((time.monotonic() - start) * 1000)

            if proc.returncode != 0:
                # Observed under rapid sequential invocation (e.g. eval-harness runs):
                # the CLI occasionally exits 1 with empty stderr, transiently. Retrying
                # resolves it; a real config/auth error will fail on every attempt.
                last_error = ClaudeCLIError(
                    f"claude CLI exited {proc.returncode} (node={node_name}, attempt={attempt}): "
                    f"{proc.stderr[:2000]}"
                )
                time.sleep(_RETRY_BACKOFF_S * attempt)
                continue

            try:
                payload = json.loads(proc.stdout)
            except json.JSONDecodeError as e:
                last_error = ClaudeCLIError(
                    f"claude CLI returned non-JSON stdout (attempt={attempt}): {proc.stdout[:500]}"
                )
                last_error.__cause__ = e
                time.sleep(_RETRY_BACKOFF_S * attempt)
                continue

            if payload.get("is_error"):
                last_error = ClaudeCLIError(f"claude CLI reported an error (attempt={attempt}): {payload}")
                time.sleep(_RETRY_BACKOFF_S * attempt)
                continue

            last_error = None
            break

        if last_error is not None:
            raise last_error

        usage = payload.get("usage", {})
        input_tokens = (
            usage.get("input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0)
        )

        return LLMResponse(
            text=payload.get("result"),
            structured_output=payload.get("structured_output"),
            input_tokens=input_tokens,
            output_tokens=usage.get("output_tokens", 0),
            # Actual out-of-pocket cost is $0 under a Claude subscription; we still
            # capture the CLI's own metered estimate (`total_cost_usd`, priced off
            # standard API rates) so eval-run cost/ticket stays comparable to the
            # APIAdapter's real spend once this swaps for a live deploy.
            cost_usd=payload.get("total_cost_usd", 0.0),
            latency_ms=latency_ms,
            model=self.settings.claude_cli_model,
            raw=payload,
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        # The CLI has no embeddings endpoint; fall back to a local model so
        # memory retrieval works with zero API spend during development.
        return embed_local(texts)

    def count_tokens(self, text: str) -> int:
        # Rough heuristic (no local tokenizer access); good enough for the
        # pre-call cost/iteration guardrails, not for billing.
        return max(1, len(text) // 4)
