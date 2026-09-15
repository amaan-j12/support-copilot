import uuid
from datetime import UTC, datetime

from app.agent.context import NodeContext
from app.agent.state import TicketState
from app.db.models import CostLedgerEntry, Reflection, Ticket, TicketMessage
from app.memory.episodic import write_episodic_memory


def record_outcome_node(state: TicketState, ctx: NodeContext) -> dict:
    ticket_id = uuid.UUID(state["ticket_id"])
    ticket = ctx.db.get(Ticket, ticket_id)
    ticket.status = state.get("outcome", "resolved")
    ticket.category = state.get("category")
    ticket.priority = state.get("priority")
    ticket.agent_version_id = (
        uuid.UUID(state["agent_version_id"]) if state.get("agent_version_id") else None
    )
    ticket.resolved_at = datetime.now(UTC)

    ctx.db.add(
        TicketMessage(ticket_id=ticket_id, role="agent", content=state.get("final_response") or "")
    )

    ctx.db.add(
        Reflection(
            ticket_id=ticket_id,
            critique_text=state.get("reflection_critique") or "",
            proposed_lesson=state.get("reflection_lesson"),
            confidence=state.get("reflection_confidence") or 0.5,
            generation_id=(
                uuid.UUID(state["agent_version_id"]) if state.get("agent_version_id") else None
            ),
        )
    )

    summary_text = (
        f"[{state.get('category')}] {state.get('intent_summary')} -> {state.get('final_response')}"
    )
    embedding = ctx.adapter.embed([summary_text])[0]
    write_episodic_memory(
        ctx.db,
        ticket_id=ticket_id,
        summary=summary_text,
        embedding=embedding,
        outcome=ticket.status,
        tags=[state.get("category") or "other"],
    )

    ctx.db.add(
        CostLedgerEntry(
            ticket_id=ticket_id,
            tokens_in=state.get("total_input_tokens", 0),
            tokens_out=state.get("total_output_tokens", 0),
            cost_usd=state.get("total_cost_usd", 0.0),
            provider=ctx.adapter.name,
            model=ctx.adapter.model_id,
        )
    )
    ctx.db.flush()
    return {}
