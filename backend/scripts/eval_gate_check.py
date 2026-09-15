"""CI eval-regression gate: runs the frozen eval set against the code as it
stands in this checkout (a fresh AgentVersion in a throwaway CI database) and
fails if resolution_accuracy drops more than TOLERANCE below the committed
backend/baseline_scores.json. Requires LLM_PROVIDER=api + a real API key
(the claude_cli adapter has no authenticated session available in CI).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.models import AgentVersion, EvalResult
from app.db.session import SessionLocal
from app.evals.runner import run_eval
from app.llm.factory import get_llm_adapter

BASELINE_PATH = Path(__file__).resolve().parent.parent / "baseline_scores.json"
TOLERANCE = 0.05


def main() -> None:
    committed = json.loads(BASELINE_PATH.read_text())

    db = SessionLocal()
    adapter = get_llm_adapter()

    latest = db.query(AgentVersion).order_by(AgentVersion.generation_number.desc()).first()
    next_gen = (latest.generation_number + 1) if latest else 0
    version = AgentVersion(generation_number=next_gen, status="active", created_by="ci_gate")
    db.add(version)
    db.commit()

    eval_run = run_eval(
        db, adapter, agent_version=version, eval_set_version=committed["eval_set_version"], triggered_by="gate"
    )
    results = db.query(EvalResult).filter_by(eval_run_id=eval_run.id).all()
    if not results:
        print("No eval results produced — failing.")
        sys.exit(1)

    accuracy = sum(r.resolution_correct for r in results) / len(results)
    baseline_accuracy = committed["resolution_accuracy"]
    print(f"Current resolution_accuracy: {accuracy:.1%}  |  committed baseline: {baseline_accuracy:.1%}")

    if accuracy < baseline_accuracy - TOLERANCE:
        print(f"REGRESSION: dropped more than {TOLERANCE:.0%} below the committed baseline — failing CI gate.")
        sys.exit(1)
    print("OK — no regression beyond tolerance.")


if __name__ == "__main__":
    main()
