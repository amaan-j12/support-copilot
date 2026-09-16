"""Exports the active agent version's latest eval scores to
backend/baseline_scores.json, the committed "known good" numbers that
.github/workflows/eval-gate.yml checks new code against. Re-run and commit
the updated file whenever a promotion legitimately raises the bar.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.models import AgentVersion
from app.db.session import SessionLocal
from app.learning.eval_gate import compute_metrics, latest_completed_eval_run

OUT_PATH = Path(__file__).resolve().parent.parent / "baseline_scores.json"


def main() -> None:
    db = SessionLocal()
    active = db.query(AgentVersion).filter_by(status="active").order_by(AgentVersion.generation_number.desc()).first()
    if active is None:
        raise SystemExit("No active agent version.")
    eval_run = latest_completed_eval_run(db, active.id, "v1")
    if eval_run is None:
        raise SystemExit("Active version has no completed eval run.")

    metrics = compute_metrics(db, eval_run)
    payload = {
        "generation_number": active.generation_number,
        "eval_set_version": "v1",
        "resolution_accuracy": round(metrics.resolution_accuracy, 4),
        "escalation_accuracy": round(metrics.escalation_accuracy, 4),
        "avg_tool_call_f1": round(metrics.avg_tool_call_f1, 4),
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {OUT_PATH}: {payload}")


if __name__ == "__main__":
    main()
