"""Runs the full frozen eval set against a given agent version, scores every
case, and persists an EvalRun + EvalResult rows so results are versioned and
comparable across generations (the data the EvalScoreboard chart reads).
"""

import time
import uuid

from sqlalchemy.orm import Session

from app.agent.runner import run_ticket
from app.db.models import AgentVersion, EvalResult, EvalRun, EvalSetCase, Ticket
from app.evals.loader import load_eval_set
from app.evals.metrics import score_case
from app.llm.base import LLMAdapter
from app.synthetic_data import store as fixture_store


def run_eval(
    db: Session,
    adapter: LLMAdapter,
    *,
    agent_version: AgentVersion,
    eval_set_version: str = "v1",
    triggered_by: str = "manual",
    is_candidate_eval: bool = False,
) -> EvalRun:
    cases: list[EvalSetCase] = load_eval_set(db, eval_set_version)
    db.commit()

    eval_run = EvalRun(
        agent_version_id=agent_version.id,
        eval_set_version=eval_set_version,
        triggered_by=triggered_by,
        status="running",
    )
    db.add(eval_run)
    db.commit()

    print(f"Eval run {eval_run.id} — {len(cases)} cases, agent_version=gen{agent_version.generation_number}")

    for i, case in enumerate(cases, start=1):
        # Deterministic per-case fixture state: nothing a prior case's refund/
        # cancellation did should leak into the next case's ground truth.
        fixture_store.reset()

        scenario = case.scenario_json
        ticket = Ticket(
            id=uuid.uuid4(),
            customer_id=scenario["customer_id"],
            subject=scenario["subject"],
            channel="email",
            status="open",
            eval_case_id=case.id,
        )
        db.add(ticket)
        db.flush()

        start = time.monotonic()
        try:
            final_state = run_ticket(
                db,
                adapter,
                ticket=ticket,
                customer_message=scenario["message"],
                agent_version_id=str(agent_version.id),
                is_candidate_eval=is_candidate_eval,
            )
            error = None
        except Exception as e:  # noqa: BLE001 — a failed ticket is a scored failure, not a crash
            final_state = {
                "outcome": "escalated",
                "final_response": "",
                "tool_call_log": [],
                "total_cost_usd": 0.0,
            }
            error = str(e)
        latency_ms = int((time.monotonic() - start) * 1000)

        score = score_case(
            expected_outcome_json=case.expected_outcome_json,
            actual_outcome=final_state.get("outcome", "escalated"),
            final_response=final_state.get("final_response", ""),
            tool_call_log=final_state.get("tool_call_log", []),
        )

        db.add(
            EvalResult(
                eval_run_id=eval_run.id,
                case_id=case.id,
                resolution_correct=score.resolution_correct,
                escalation_correct=score.escalation_correct,
                tool_call_f1=score.tool_call_f1,
                hallucination_score=None,
                latency_ms=latency_ms,
                cost_usd=final_state.get("total_cost_usd", 0.0),
                judge_rationale=(error or score.rationale),
            )
        )
        db.commit()

        status_icon = "PASS" if score.resolution_correct else "FAIL"
        print(
            f"  [{i}/{len(cases)}] {scenario['id']:16s} {status_icon:4s} "
            f"tool_f1={score.tool_call_f1:.2f}  {score.rationale}"
        )

    eval_run.status = "completed"
    from datetime import UTC, datetime

    eval_run.finished_at = datetime.now(UTC)
    db.commit()

    _print_summary(db, eval_run)
    return eval_run


def _print_summary(db: Session, eval_run: EvalRun) -> None:
    results = db.query(EvalResult).filter_by(eval_run_id=eval_run.id).all()
    n = len(results)
    if n == 0:
        print("No results.")
        return
    resolution_acc = sum(r.resolution_correct for r in results) / n
    escalation_acc = sum(r.escalation_correct for r in results) / n
    avg_f1 = sum(r.tool_call_f1 for r in results) / n
    total_cost = sum(r.cost_usd for r in results)
    avg_latency = sum(r.latency_ms or 0 for r in results) / n
    print("\n=== Eval summary ===")
    print(f"cases:              {n}")
    print(f"resolution_accuracy: {resolution_acc:.1%}")
    print(f"escalation_accuracy: {escalation_acc:.1%}")
    print(f"avg_tool_call_f1:    {avg_f1:.2f}")
    print(f"avg_latency_ms:      {avg_latency:.0f}")
    print(f"total_cost_usd:      {total_cost:.4f}  (reported/metered; $0 actual spend on claude_cli)")
