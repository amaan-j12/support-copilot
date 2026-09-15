from typing import Any, TypedDict


class ToolCallLogEntry(TypedDict):
    tool_name: str
    arguments: dict[str, Any]
    output: dict[str, Any]
    risk_level: str
    status: str  # executed / pending_approval


class TicketState(TypedDict, total=False):
    ticket_id: str
    customer_id: str
    subject: str
    raw_message: str
    sanitized_message: str
    injection_flag: bool
    pii_redaction_counts: dict[str, int]

    category: str | None
    priority: str | None
    intent_summary: str | None

    retrieved_memories: list[dict[str, Any]]
    retrieved_playbook: list[dict[str, Any]]
    retrieved_kb: list[dict[str, Any]]

    tool_call_log: list[ToolCallLogEntry]
    scratchpad: list[str]  # human-readable trace of tool results fed back into plan_and_act
    iteration: int

    plan_thought: str | None
    plan_action: str | None  # "call_tool" | "respond"
    plan_tool_name: str | None
    plan_tool_arguments: dict[str, Any] | None
    plan_tool_risk_level: str | None
    plan_response_message: str | None

    pending_approval_id: str | None
    force_escalate: bool

    final_response: str | None
    outcome: str | None  # resolved / escalated / pending_approval

    reflection_critique: str | None
    reflection_lesson: str | None
    reflection_confidence: float | None

    agent_version_id: str | None

    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float

    error: str | None
