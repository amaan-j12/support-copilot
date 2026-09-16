"""Eval-gated promotion: reflections become candidate playbook entries, a new
AgentVersion generation is evaluated with them against the frozen eval set,
and only promoted to "active" if it doesn't regress versus the current
active version's latest run. Rejected candidates stay in the DB — visible on
the dashboard as a rejected generation — rather than being deleted, so the
gate is demonstrably real and not just always-promote.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import AgentVersion
from app.evals.runner import run_eval
from app.learning.eval_gate import compute_metrics, latest_completed_eval_run, passes_gate
from app.learning.reflection import build_candidate_playbook_entries
from app.llm.base import LLMAdapter


def run_reflection_learning_cycle(
    db: Session, adapter: LLMAdapter, *, eval_set_version: str = "v1"
) -> AgentVersion | None:
    base_version = (
        db.query(AgentVersion).filter_by(status="active").order_by(AgentVersion.generation_number.desc()).first()
    )
    if base_version is None:
        raise RuntimeError("No active agent version. Run scripts/run_baseline.py first.")

    base_run = latest_completed_eval_run(db, base_version.id, eval_set_version)
    if base_run is None:
        raise RuntimeError(
            f"Active version gen{base_version.generation_number} has no completed eval run to compare against."
        )
    base_metrics = compute_metrics(db, base_run)

    latest_gen = db.query(AgentVersion).order_by(AgentVersion.generation_number.desc()).first()
    next_gen_number = latest_gen.generation_number + 1

    candidate_version = AgentVersion(
        generation_number=next_gen_number,
        parent_version_id=base_version.id,
        status="candidate",
        created_by="reflection_loop",
    )
    db.add(candidate_version)
    db.flush()

    new_entries = build_candidate_playbook_entries(db, adapter, agent_version_id=candidate_version.id)
    if not new_entries:
        db.delete(candidate_version)
        db.commit()
        print("No new (unincorporated) reflections to learn from — skipping this cycle.")
        return None

    print(
        f"Evaluating candidate gen{next_gen_number} with {len(new_entries)} new playbook "
        f"entr{'y' if len(new_entries) == 1 else 'ies'} against base gen{base_version.generation_number}..."
    )
    candidate_run = run_eval(
        db,
        adapter,
        agent_version=candidate_version,
        eval_set_version=eval_set_version,
        triggered_by="reflection_loop",
        is_candidate_eval=True,
    )
    candidate_metrics = compute_metrics(db, candidate_run)
    ok, reason = passes_gate(candidate_metrics, base_metrics)

    print(
        f"\nBase gen{base_version.generation_number}: "
        f"resolution={base_metrics.resolution_accuracy:.1%} "
        f"escalation={base_metrics.escalation_accuracy:.1%} "
        f"tool_f1={base_metrics.avg_tool_call_f1:.2f}\n"
        f"Candidate gen{next_gen_number}: "
        f"resolution={candidate_metrics.resolution_accuracy:.1%} "
        f"escalation={candidate_metrics.escalation_accuracy:.1%} "
        f"tool_f1={candidate_metrics.avg_tool_call_f1:.2f}"
    )

    now = datetime.now(UTC)
    if ok:
        candidate_version.status = "active"
        candidate_version.activated_at = now
        base_version.status = "retired"
        base_version.retired_at = now
        for entry in new_entries:
            entry.status = "active"
            entry.promoted_at = now
            entry.promoted_by_eval_run_id = candidate_run.id
        db.commit()
        print(f"PROMOTED gen{next_gen_number}.")
        return candidate_version
    else:
        candidate_version.status = "rejected"
        candidate_version.notes = f"Rejected by eval gate: {reason}"
        for entry in new_entries:
            entry.status = "retired"
        db.commit()
        print(f"REJECTED gen{next_gen_number}: {reason}")
        return None
