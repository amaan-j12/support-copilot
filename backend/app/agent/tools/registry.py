"""Tool registry the agent's plan_and_act/tool_execution nodes read from.
Risk level is looked up from the guardrails risk policy, not duplicated here.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.agent.guardrails.risk_policy import RISK_LEVELS
from app.agent.tools.account_tools import account_lookup
from app.agent.tools.billing_tools import cancel_subscription, invoice_lookup, issue_refund
from app.agent.tools.kb_search import kb_search


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema for the tool's arguments
    func: Callable[..., dict[str, Any]]
    risk_level: str
    needs_adapter: bool = False  # kb_search needs the LLM adapter for embeddings


TOOLS: dict[str, ToolDef] = {
    "kb_search": ToolDef(
        name="kb_search",
        description="Search Loopwork's help-center articles for policy/how-to information.",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        func=kb_search,
        risk_level=RISK_LEVELS["kb_search"],
        needs_adapter=True,
    ),
    "account_lookup": ToolDef(
        name="account_lookup",
        description="Look up a customer's Loopwork account (plan, seats, status, trial info).",
        parameters={
            "type": "object",
            "properties": {"customer_id": {"type": "string"}},
            "required": ["customer_id"],
        },
        func=account_lookup,
        risk_level=RISK_LEVELS["account_lookup"],
    ),
    "invoice_lookup": ToolDef(
        name="invoice_lookup",
        description="Look up a customer's invoices, optionally filtered to one invoice_id.",
        parameters={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "invoice_id": {"type": ["string", "null"]},
            },
            "required": ["customer_id"],
        },
        func=invoice_lookup,
        risk_level=RISK_LEVELS["invoice_lookup"],
    ),
    "issue_refund": ToolDef(
        name="issue_refund",
        description=(
            "Issue a refund for a specific invoice. HIGH RISK: always routed through human "
            "approval before it actually executes."
        ),
        parameters={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "invoice_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["customer_id", "invoice_id", "reason"],
        },
        func=issue_refund,
        risk_level=RISK_LEVELS["issue_refund"],
    ),
    "cancel_subscription": ToolDef(
        name="cancel_subscription",
        description=(
            "Cancel a customer's subscription. HIGH RISK: always routed through human approval "
            "before it actually executes."
        ),
        parameters={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["customer_id", "reason"],
        },
        func=cancel_subscription,
        risk_level=RISK_LEVELS["cancel_subscription"],
    ),
}


def tool_catalog_text() -> str:
    """Human-readable tool catalog injected into the plan_and_act prompt."""
    lines = []
    for t in TOOLS.values():
        lines.append(f"- {t.name} ({t.risk_level} risk): {t.description}\n  args schema: {t.parameters}")
    return "\n".join(lines)
