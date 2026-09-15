"""HIGH-risk tool execution, gated by a human approval record.

Phase-1 scope: creates a real Approval + ToolCall(pending_approval) row (so
the audit trail and API/UI are real), then auto-resolves it synchronously
("phase1_auto_stub") so the eval pipeline can run unattended end-to-end.
Phase 2 replaces the auto-resolve with a genuine LangGraph interrupt and a
`POST /approvals/{id}/decision` endpoint that resumes the paused graph.
"""

import uuid
from datetime import UTC, datetime

from app.agent.context import NodeContext
from app.agent.guardrails.cost_cap import apply_cost_cap_updates
from app.agent.state import TicketState
from app.agent.tools.registry import TOOLS
from app.db.models import Approval, ToolCall


def hitl_pause_node(state: TicketState, ctx: NodeContext) -> dict:
    tool_name = state["plan_tool_name"]
    args = state.get("plan_tool_arguments") or {}
    tool_def = TOOLS[tool_name]
    ticket_id = uuid.UUID(state["ticket_id"])

    tool_call = ToolCall(
        ticket_id=ticket_id,
        tool_name=tool_name,
        input_json=args,
        risk_level="high",
        status="pending_approval",
    )
    ctx.db.add(tool_call)
    ctx.db.flush()

    approval = Approval(
        tool_call_id=tool_call.id,
        ticket_id=ticket_id,
        status="pending",
        action_summary=f"{tool_name}({args})",
    )
    ctx.db.add(approval)
    ctx.db.flush()

    # --- Phase-1 auto-stub resolution (see module docstring) ---
    approval.status = "approved"
    approval.reviewer = "phase1_auto_stub"
    approval.reviewed_at = datetime.now(UTC)

    output = tool_def.func(**args)
    tool_call.output_json = output
    tool_call.status = "executed"
    ctx.db.flush()

    new_iteration = state["iteration"] + 1
    updates: dict = {
        "tool_call_log": state["tool_call_log"]
        + [
            {
                "tool_name": tool_name,
                "arguments": args,
                "output": output,
                "risk_level": "high",
                "status": "executed_after_approval",
            }
        ],
        "scratchpad": state["scratchpad"]
        + [f"[REQUIRES HUMAN APPROVAL] Called {tool_name}({args}) -> approved (stub) -> {output}"],
        "iteration": new_iteration,
        "pending_approval_id": str(approval.id),
    }
    apply_cost_cap_updates(state, new_iteration, updates)
    return updates
