import uuid

from app.agent.context import NodeContext
from app.agent.guardrails.cost_cap import apply_cost_cap_updates
from app.agent.state import TicketState
from app.agent.tools.registry import TOOLS
from app.db.models import ToolCall


def tool_execution_node(state: TicketState, ctx: NodeContext) -> dict:
    """Executes LOW-risk tools directly. High-risk tools never reach this node
    (risk_gate routes them to hitl_pause instead).
    """
    tool_name = state["plan_tool_name"]
    args = state.get("plan_tool_arguments") or {}
    tool_def = TOOLS[tool_name]

    output = tool_def.func(**args, adapter=ctx.adapter) if tool_def.needs_adapter else tool_def.func(**args)

    tool_call = ToolCall(
        ticket_id=uuid.UUID(state["ticket_id"]),
        tool_name=tool_name,
        input_json=args,
        output_json=output,
        risk_level="low",
        status="executed",
    )
    ctx.db.add(tool_call)
    ctx.db.flush()

    new_iteration = state["iteration"] + 1
    updates: dict = {
        "tool_call_log": state["tool_call_log"]
        + [{"tool_name": tool_name, "arguments": args, "output": output, "risk_level": "low", "status": "executed"}],
        "scratchpad": state["scratchpad"] + [f"Called {tool_name}({args}) -> {output}"],
        "iteration": new_iteration,
    }
    apply_cost_cap_updates(state, new_iteration, updates)
    return updates
