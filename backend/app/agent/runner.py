from sqlalchemy.orm import Session

from app.agent.context import NodeContext
from app.agent.graph import build_graph
from app.agent.state import TicketState
from app.db.models import Ticket
from app.llm.base import LLMAdapter


def run_ticket(
    db: Session,
    adapter: LLMAdapter,
    *,
    ticket: Ticket,
    customer_message: str,
    agent_version_id: str | None,
    is_candidate_eval: bool = False,
) -> TicketState:
    """Run one ticket through the full graph, synchronously, to completion.

    (The Phase-1 HITL stub auto-resolves approvals inline, so there is no
    mid-run pause to resume yet — see app/agent/nodes/hitl.py.)
    """
    ctx = NodeContext(
        db=db, adapter=adapter, agent_version_id=agent_version_id, is_candidate_eval=is_candidate_eval
    )
    graph = build_graph(ctx)

    initial_state: TicketState = {
        "ticket_id": str(ticket.id),
        "customer_id": ticket.customer_id,
        "subject": ticket.subject,
        "raw_message": customer_message,
        "agent_version_id": agent_version_id,
    }
    return graph.invoke(initial_state, config={"recursion_limit": 60})
