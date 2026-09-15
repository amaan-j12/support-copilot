import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import AgentVersion, EvalResult, EvalRun, EvalSetCase
from app.db.session import get_db

router = APIRouter(prefix="/eval-runs", tags=["evals"])


@router.get("")
def list_eval_runs(db: Session = Depends(get_db)):
    runs = db.query(EvalRun).order_by(EvalRun.started_at.asc()).all()
    out = []
    for r in runs:
        results = db.query(EvalResult).filter_by(eval_run_id=r.id).all()
        n = len(results)
        agent_version = db.get(AgentVersion, r.agent_version_id)
        out.append(
            {
                "id": str(r.id),
                "agent_version_generation": agent_version.generation_number if agent_version else None,
                "agent_version_status": agent_version.status if agent_version else None,
                "eval_set_version": r.eval_set_version,
                "status": r.status,
                "triggered_by": r.triggered_by,
                "started_at": r.started_at.isoformat(),
                "n_cases": n,
                "resolution_accuracy": (sum(x.resolution_correct for x in results) / n) if n else None,
                "escalation_accuracy": (sum(x.escalation_correct for x in results) / n) if n else None,
                "avg_tool_call_f1": (sum(x.tool_call_f1 for x in results) / n) if n else None,
                "total_cost_usd": sum(x.cost_usd for x in results),
            }
        )
    return out


@router.get("/{eval_run_id}/results")
def get_eval_results(eval_run_id: str, db: Session = Depends(get_db)):
    run = db.get(EvalRun, uuid.UUID(eval_run_id))
    if run is None:
        raise HTTPException(404, "not found")
    results = db.query(EvalResult).filter_by(eval_run_id=run.id).all()
    out = []
    for r in results:
        case = db.get(EvalSetCase, r.case_id)
        out.append(
            {
                "case_id": case.scenario_json["id"] if case else str(r.case_id),
                "category": case.category if case else None,
                "resolution_correct": r.resolution_correct,
                "escalation_correct": r.escalation_correct,
                "tool_call_f1": r.tool_call_f1,
                "hallucination_score": r.hallucination_score,
                "latency_ms": r.latency_ms,
                "cost_usd": r.cost_usd,
                "rationale": r.judge_rationale,
            }
        )
    return out
