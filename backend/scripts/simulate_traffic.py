"""Runs the synthetic 'live traffic' batch through the current active agent
version. Each ticket produces a Reflection row; running this before
scripts/run_learning_cycle.py is what gives the reflection loop something
to learn from.
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent.runner import run_ticket
from app.db.models import AgentVersion, Ticket
from app.db.session import SessionLocal
from app.llm.factory import get_llm_adapter
from app.synthetic_data.live_traffic import LIVE_TICKETS


def main() -> None:
    db = SessionLocal()
    adapter = get_llm_adapter()

    active = db.query(AgentVersion).filter_by(status="active").order_by(AgentVersion.generation_number.desc()).first()
    if active is None:
        raise SystemExit("No active agent version. Run scripts/run_baseline.py first.")

    print(f"Simulating {len(LIVE_TICKETS)} live tickets against gen{active.generation_number}...")
    for i, item in enumerate(LIVE_TICKETS, start=1):
        ticket = Ticket(
            id=uuid.uuid4(),
            customer_id=item["customer_id"],
            subject=item["subject"],
            channel="email",
            status="open",
        )
        db.add(ticket)
        db.flush()
        try:
            final_state = run_ticket(
                db, adapter, ticket=ticket, customer_message=item["message"], agent_version_id=str(active.id)
            )
            db.commit()
            print(f"  [{i}/{len(LIVE_TICKETS)}] {item['subject']!r:45s} -> {final_state.get('outcome')}")
        except Exception as e:  # noqa: BLE001
            db.rollback()
            print(f"  [{i}/{len(LIVE_TICKETS)}] {item['subject']!r:45s} -> ERROR: {e}")


if __name__ == "__main__":
    main()
