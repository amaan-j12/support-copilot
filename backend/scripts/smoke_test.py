"""One-ticket end-to-end smoke test: creates a baseline AgentVersion + a
ticket, runs it through the full graph against the live LLM adapter, and
prints what happened. Run from backend/ with the venv active.
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent.runner import run_ticket
from app.db.models import AgentVersion, Ticket
from app.db.session import SessionLocal
from app.llm.factory import get_llm_adapter


def main() -> None:
    db = SessionLocal()
    adapter = get_llm_adapter()

    baseline = db.query(AgentVersion).filter_by(generation_number=0).first()
    if baseline is None:
        baseline = AgentVersion(generation_number=0, status="active", created_by="baseline")
        db.add(baseline)
        db.flush()

    ticket = Ticket(
        id=uuid.uuid4(),
        customer_id="cust_1001",
        subject="Charged twice this month",
        channel="email",
        status="open",
    )
    db.add(ticket)
    db.flush()

    message = (
        "Hi, I just looked at my card statement and I was charged $288 TWICE this month "
        "for my Loopwork Business plan. Can you check and refund the duplicate?"
    )

    print(f"Running ticket {ticket.id} ...")
    final_state = run_ticket(
        db, adapter, ticket=ticket, customer_message=message, agent_version_id=str(baseline.id)
    )
    db.commit()

    print("\n--- Final state ---")
    for key in [
        "category",
        "priority",
        "intent_summary",
        "outcome",
        "final_response",
        "tool_call_log",
        "reflection_lesson",
        "total_input_tokens",
        "total_output_tokens",
        "total_cost_usd",
    ]:
        print(f"{key}: {final_state.get(key)}")


if __name__ == "__main__":
    main()
