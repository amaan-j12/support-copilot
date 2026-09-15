"""Loads the frozen YAML eval set into eval_set_cases. Idempotent: re-running
for a version that's already loaded is a no-op unless the case content
changed (matched by `id` within `scenario_json`).
"""

from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from app.db.models import EvalSetCase

EVAL_SET_DIR = Path(__file__).parent / "eval_set"


def load_eval_set(db: Session, version: str = "v1") -> list[EvalSetCase]:
    version_dir = EVAL_SET_DIR / version
    if not version_dir.exists():
        raise FileNotFoundError(f"No eval set directory at {version_dir}")

    raw_cases = []
    for path in sorted(version_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        raw_cases.extend(data.get("cases", []))

    existing = {
        row.scenario_json["id"]: row
        for row in db.query(EvalSetCase).filter_by(eval_set_version=version).all()
    }

    result: list[EvalSetCase] = []
    for case in raw_cases:
        case_id = case["id"]
        if case_id in existing:
            result.append(existing[case_id])
            continue
        row = EvalSetCase(
            eval_set_version=version,
            scenario_json={
                "id": case_id,
                "customer_id": case["customer_id"],
                "subject": case["subject"],
                "message": case["message"],
            },
            expected_outcome_json=case["expected"],
            expected_tool_calls_json=case["expected"].get("expected_tools", []),
            category=case["category"],
            difficulty=case.get("difficulty", "medium"),
            requires_hitl=case["expected"].get("requires_hitl", False),
        )
        db.add(row)
        result.append(row)
    db.flush()
    return result
