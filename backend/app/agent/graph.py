r"""The support-agent LangGraph state machine.

intake_validate -> understand_ticket -> retrieve_memory -> plan_and_act
  plan_and_act --(call_tool)--> risk_gate --(low risk)--> tool_execution --> plan_and_act (loop)
                                          \-(high risk)-> hitl_pause      --> plan_and_act (loop)
  plan_and_act --(respond)--> respond_to_customer -> reflect -> record_outcome -> END

Both tool_execution and hitl_pause can force an early escalation via
`force_escalate` (cost-cap breach) which short-circuits straight to
respond_to_customer instead of looping back.
"""

from functools import partial

from langgraph.graph import END, START, StateGraph

from app.agent.context import NodeContext
from app.agent.nodes.hitl import hitl_pause_node
from app.agent.nodes.intake import intake_validate_node
from app.agent.nodes.plan_act import plan_and_act_node
from app.agent.nodes.record_outcome import record_outcome_node
from app.agent.nodes.reflect import reflect_node
from app.agent.nodes.respond import respond_to_customer_node
from app.agent.nodes.retrieve_memory import retrieve_memory_node
from app.agent.nodes.risk_gate import (
    risk_gate_node,
    route_after_plan,
    route_after_risk_gate,
    route_after_tool,
)
from app.agent.nodes.tool_execution import tool_execution_node
from app.agent.nodes.understand import understand_ticket_node
from app.agent.state import TicketState


def build_graph(ctx: NodeContext):
    graph = StateGraph(TicketState)

    graph.add_node("intake_validate", partial(intake_validate_node, ctx=ctx))
    graph.add_node("understand_ticket", partial(understand_ticket_node, ctx=ctx))
    graph.add_node("retrieve_memory", partial(retrieve_memory_node, ctx=ctx))
    graph.add_node("plan_and_act", partial(plan_and_act_node, ctx=ctx))
    graph.add_node("risk_gate", partial(risk_gate_node, ctx=ctx))
    graph.add_node("tool_execution", partial(tool_execution_node, ctx=ctx))
    graph.add_node("hitl_pause", partial(hitl_pause_node, ctx=ctx))
    graph.add_node("respond_to_customer", partial(respond_to_customer_node, ctx=ctx))
    graph.add_node("reflect", partial(reflect_node, ctx=ctx))
    graph.add_node("record_outcome", partial(record_outcome_node, ctx=ctx))

    graph.add_edge(START, "intake_validate")
    graph.add_edge("intake_validate", "understand_ticket")
    graph.add_edge("understand_ticket", "retrieve_memory")
    graph.add_edge("retrieve_memory", "plan_and_act")

    graph.add_conditional_edges(
        "plan_and_act",
        route_after_plan,
        {"risk_gate": "risk_gate", "respond_to_customer": "respond_to_customer"},
    )
    graph.add_conditional_edges(
        "risk_gate",
        route_after_risk_gate,
        {
            "hitl_pause": "hitl_pause",
            "tool_execution": "tool_execution",
            "respond_to_customer": "respond_to_customer",
        },
    )
    graph.add_conditional_edges(
        "tool_execution",
        route_after_tool,
        {"plan_and_act": "plan_and_act", "respond_to_customer": "respond_to_customer"},
    )
    graph.add_conditional_edges(
        "hitl_pause",
        route_after_tool,
        {"plan_and_act": "plan_and_act", "respond_to_customer": "respond_to_customer"},
    )

    graph.add_edge("respond_to_customer", "reflect")
    graph.add_edge("reflect", "record_outcome")
    graph.add_edge("record_outcome", END)

    return graph.compile()
