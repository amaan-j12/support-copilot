import uuid

from app.agent.context import NodeContext
from app.agent.guardrails.injection_defense import flag_injection
from app.agent.guardrails.pii import redact
from app.agent.state import TicketState
from app.db.models import TicketMessage


def intake_validate_node(state: TicketState, ctx: NodeContext) -> dict:
    raw = state["raw_message"]
    redacted, counts = redact(raw)

    ctx.db.add(
        TicketMessage(
            ticket_id=uuid.UUID(state["ticket_id"]),
            role="customer",
            content=redacted,
            redaction_meta=counts,
        )
    )
    ctx.db.flush()

    return {
        "sanitized_message": redacted,
        "pii_redaction_counts": counts,
        "injection_flag": flag_injection(raw),
        "scratchpad": [],
        "tool_call_log": [],
        "iteration": 0,
        "force_escalate": False,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cost_usd": 0.0,
    }
