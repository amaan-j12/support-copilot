"""Phase-1 deliverable: run the eval_set v1 against the generation-0 (no
memory, no playbook, no reflections yet) baseline agent, and persist the
"before" score that every later generation is measured against.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.models import AgentVersion
from app.db.session import SessionLocal
from app.evals.runner import run_eval
from app.llm.factory import get_llm_adapter


def main() -> None:
    db = SessionLocal()
    adapter = get_llm_adapter()

    baseline = db.query(AgentVersion).filter_by(generation_number=0).first()
    if baseline is None:
        baseline = AgentVersion(
            generation_number=0,
            status="active",
            created_by="baseline",
            notes="Phase 1 baseline: empty playbook, no reflections applied yet.",
        )
        db.add(baseline)
        db.commit()

    run_eval(db, adapter, agent_version=baseline, eval_set_version="v1", triggered_by="manual")


if __name__ == "__main__":
    main()
