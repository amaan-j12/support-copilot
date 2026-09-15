"""Reflective prompt optimization, in the spirit of DSPy's GEPA optimizer:
rather than policy-gradient updates, an LLM reflects on textual traces of
recent eval failures and proposes a natural-language patch to the
plan_and_act system prompt (see app/agent/nodes/plan_act.py's
`_prompt_optimizer_patch`). The patch is versioned as a new candidate
AgentVersion and must clear the same eval gate as the reflection/playbook
loop before going live — same anti-regression discipline, different lever
(prompt text instead of playbook facts).

Note: this does not depend on the `dspy` package. DSPy's optimizers assume
programmatic token-level API access; this codebase's default LLM adapter
shells out to the `claude` CLI, so we reimplement the same reflective-rewrite
idea directly rather than overclaiming a library integration that wouldn't
actually fit that adapter.
"""

import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import AgentVersion, EvalResult, EvalSetCase, PromptVersion
from app.evals.runner import run_eval
from app.learning.eval_gate import latest_completed_eval_run, resolution_accuracy
from app.llm.base import LLMAdapter

MAX_FAILURES_CONSIDERED = 8

OPTIMIZE_SCHEMA = {
    "type": "object",
    "properties": {
        "analysis": {"type": "string"},
        "prompt_patch": {"type": "string"},
    },
    "required": ["analysis", "prompt_patch"],
}

SYSTEM_PROMPT = (
    "You are optimizing a support agent's system prompt. You will see several tickets it handled "
    "incorrectly and why. Propose a short, concrete ADDITIONAL instruction paragraph (not a full "
    "rewrite of the prompt) to append that would have prevented these specific failures, without "
    "contradicting the agent's existing instructions. Be specific and actionable, not generic."
)


def _collect_failures(db: Session, eval_run_id, limit: int = MAX_FAILURES_CONSIDERED) -> list[dict]:
    results = (
        db.query(EvalResult).filter_by(eval_run_id=eval_run_id, resolution_correct=False).limit(limit).all()
    )
    failures = []
    for r in results:
        case = db.get(EvalSetCase, r.case_id)
        if case is None:
            continue
        failures.append(
            {
                "subject": case.scenario_json.get("subject"),
                "message": case.scenario_json.get("message"),
                "expected": case.expected_outcome_json,
                "why_it_failed": r.judge_rationale,
            }
        )
    return failures


def run_prompt_optimization_cycle(
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
            f"Active version gen{base_version.generation_number} has no completed eval run to learn from."
        )

    failures = _collect_failures(db, base_run.id)
    if not failures:
        print("No failing cases on the current active version — nothing to optimize.")
        return None
    base_accuracy = resolution_accuracy(db, base_run)

    prompt = "Here are tickets the agent got wrong:\n\n" + "\n\n".join(
        f"- Subject: {f['subject']}\n"
        f"  Message: {f['message']}\n"
        f"  Expected: {json.dumps(f['expected'])}\n"
        f"  Why it failed: {f['why_it_failed']}"
        for f in failures
    )
    resp = adapter.complete(
        [{"role": "user", "content": prompt}],
        system=SYSTEM_PROMPT,
        response_schema=OPTIMIZE_SCHEMA,
        max_tokens=600,
        node_name="prompt_optimizer",
    )
    out = resp.structured_output or {}
    patch = out.get("prompt_patch")
    if not patch:
        print("Optimizer produced no usable patch this cycle.")
        return None

    latest_gen = db.query(AgentVersion).order_by(AgentVersion.generation_number.desc()).first()
    next_gen_number = latest_gen.generation_number + 1

    candidate_version = AgentVersion(
        generation_number=next_gen_number,
        parent_version_id=base_version.id,
        status="candidate",
        created_by="prompt_optimizer",
        notes=out.get("analysis"),
    )
    db.add(candidate_version)
    db.flush()

    db.add(
        PromptVersion(
            agent_version_id=candidate_version.id,
            node_name="plan_and_act",
            prompt_text=patch,
            diff_from_parent=patch,
        )
    )
    db.flush()

    print(
        f"Evaluating prompt-optimized candidate gen{next_gen_number} against base "
        f"gen{base_version.generation_number}..."
    )
    candidate_run = run_eval(
        db,
        adapter,
        agent_version=candidate_version,
        eval_set_version=eval_set_version,
        triggered_by="prompt_optimizer",
        is_candidate_eval=True,
    )
    candidate_accuracy = resolution_accuracy(db, candidate_run)
    print(
        f"\nBase gen{base_version.generation_number}: {base_accuracy:.1%}  ->  "
        f"Candidate gen{next_gen_number}: {candidate_accuracy:.1%}"
    )

    now = datetime.now(UTC)
    if candidate_accuracy >= base_accuracy:
        candidate_version.status = "active"
        candidate_version.activated_at = now
        base_version.status = "retired"
        base_version.retired_at = now
        db.commit()
        print(f"PROMOTED gen{next_gen_number} (prompt patch).")
        return candidate_version
    else:
        candidate_version.status = "rejected"
        db.commit()
        print(f"REJECTED gen{next_gen_number} (regressed vs base).")
        return None
