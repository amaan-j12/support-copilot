from app.agent.context import NodeContext
from app.agent.state import TicketState
from app.agent.tools.registry import TOOLS


def risk_gate_node(state: TicketState, ctx: NodeContext) -> dict:
    tool_name = state.get("plan_tool_name")
    if not tool_name or tool_name not in TOOLS:
        return {
            "plan_tool_risk_level": "unknown",
            "force_escalate": True,
            "outcome": "escalated",
            "final_response": "I'm looping in a human teammate to make sure this is handled correctly.",
            "error": f"model requested an unknown tool: {tool_name!r}",
        }
    return {"plan_tool_risk_level": TOOLS[tool_name].risk_level}


def route_after_plan(state: TicketState) -> str:
    return "risk_gate" if state.get("plan_action") == "call_tool" else "respond_to_customer"


def route_after_risk_gate(state: TicketState) -> str:
    if state.get("force_escalate"):
        return "respond_to_customer"
    return "hitl_pause" if state.get("plan_tool_risk_level") == "high" else "tool_execution"


def route_after_tool(state: TicketState) -> str:
    return "respond_to_customer" if state.get("force_escalate") else "plan_and_act"
