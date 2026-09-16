"""Shared by both learning loops (reflection/playbook and prompt
optimization): compute a version's eval metrics and find its latest
completed eval run, so a candidate generation can be compared against the
current active version's own results before promotion.

The gate originally checked resolution_accuracy alone. The project's first
real promotion cycle (gen0 -> gen1) showed why that's not enough: gen1 tied
gen0 on resolution_accuracy (63.2%) but escalation_accuracy dropped
94.7% -> 89.5% and avg_tool_call_f1 dropped 0.76 -> 0.63 — a real regression
the original gate let through. `passes_gate` now requires all three not to
regress beyond `tolerance`.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models import EvalResult, EvalRun

DEFAULT_TOLERANCE = 0.05


@dataclass
class RunMetrics:
    resolution_accuracy: float
    escalation_accuracy: float
    avg_tool_call_f1: float
    n_cases: int


def resolution_accuracy(db: Session, eval_run: EvalRun) -> float:
    return compute_metrics(db, eval_run).resolution_accuracy


def compute_metrics(db: Session, eval_run: EvalRun) -> RunMetrics:
    results = db.query(EvalResult).filter_by(eval_run_id=eval_run.id).all()
    n = len(results)
    if n == 0:
        return RunMetrics(0.0, 0.0, 0.0, 0)
    return RunMetrics(
        resolution_accuracy=sum(r.resolution_correct for r in results) / n,
        escalation_accuracy=sum(r.escalation_correct for r in results) / n,
        avg_tool_call_f1=sum(r.tool_call_f1 for r in results) / n,
        n_cases=n,
    )


def passes_gate(candidate: RunMetrics, base: RunMetrics, tolerance: float = DEFAULT_TOLERANCE) -> tuple[bool, str]:
    """Returns (passes, reason) — reason explains a failure, or is empty on pass."""
    checks = [
        ("resolution_accuracy", candidate.resolution_accuracy, base.resolution_accuracy),
        ("escalation_accuracy", candidate.escalation_accuracy, base.escalation_accuracy),
        ("avg_tool_call_f1", candidate.avg_tool_call_f1, base.avg_tool_call_f1),
    ]
    failures = [
        f"{name} regressed ({cand_val:.1%} < {base_val:.1%} - {tolerance:.0%} tolerance)"
        for name, cand_val, base_val in checks
        if cand_val < base_val - tolerance
    ]
    return (not failures, "; ".join(failures))


def latest_completed_eval_run(
    db: Session, agent_version_id: uuid.UUID, eval_set_version: str
) -> EvalRun | None:
    return (
        db.query(EvalRun)
        .filter_by(agent_version_id=agent_version_id, eval_set_version=eval_set_version, status="completed")
        .order_by(EvalRun.started_at.desc())
        .first()
    )
