"""Shared by both learning loops (reflection/playbook and prompt
optimization): compute a version's resolution accuracy and find its latest
completed eval run, so a candidate generation can be compared against the
current active version's own results.
"""

import uuid

from sqlalchemy.orm import Session

from app.db.models import EvalResult, EvalRun


def resolution_accuracy(db: Session, eval_run: EvalRun) -> float:
    results = db.query(EvalResult).filter_by(eval_run_id=eval_run.id).all()
    if not results:
        return 0.0
    return sum(r.resolution_correct for r in results) / len(results)


def latest_completed_eval_run(
    db: Session, agent_version_id: uuid.UUID, eval_set_version: str
) -> EvalRun | None:
    return (
        db.query(EvalRun)
        .filter_by(agent_version_id=agent_version_id, eval_set_version=eval_set_version, status="completed")
        .order_by(EvalRun.started_at.desc())
        .first()
    )
