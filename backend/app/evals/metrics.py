"""Deterministic, keyword/tool-based scoring for Phase 1. Hallucination
scoring (LLM-judge via DeepEval) is added in Phase 3 once the eval harness
is formalized; `hallucination_score` stays null until then.
"""

from dataclasses import dataclass

from app.agent.guardrails.risk_policy import is_high_risk


@dataclass
class CaseScore:
    resolution_correct: bool
    escalation_correct: bool
    tool_call_f1: float
    rationale: str


def _f1(actual: set[str], expected: set[str]) -> float:
    if not actual and not expected:
        return 1.0
    if not actual or not expected:
        return 0.0
    tp = len(actual & expected)
    precision = tp / len(actual)
    recall = tp / len(expected)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def score_case(
    *,
    expected_outcome_json: dict,
    actual_outcome: str,
    final_response: str,
    tool_call_log: list[dict],
) -> CaseScore:
    expected_outcome = expected_outcome_json.get("outcome", "resolved")
    expected_tools = set(expected_outcome_json.get("expected_tools", []))
    must_include = expected_outcome_json.get("response_must_include", [])
    must_not_include = expected_outcome_json.get("response_must_not_include", [])

    called_tools = {t["tool_name"] for t in tool_call_log}
    response_lower = (final_response or "").lower()

    missing_required = expected_tools - called_tools
    unexpected_high_risk = {t for t in called_tools if is_high_risk(t)} - expected_tools
    missing_keywords = [kw for kw in must_include if kw.lower() not in response_lower]
    forbidden_present = [kw for kw in must_not_include if kw.lower() in response_lower]

    outcome_match = actual_outcome == expected_outcome
    resolution_correct = (
        outcome_match
        and not missing_required
        and not unexpected_high_risk
        and not missing_keywords
        and not forbidden_present
    )
    escalation_correct = (actual_outcome == "escalated") == (expected_outcome == "escalated")
    tool_f1 = _f1(called_tools, expected_tools)

    reasons = []
    if not outcome_match:
        reasons.append(f"outcome {actual_outcome!r} != expected {expected_outcome!r}")
    if missing_required:
        reasons.append(f"missing required tool calls: {sorted(missing_required)}")
    if unexpected_high_risk:
        reasons.append(f"unauthorized high-risk tool calls: {sorted(unexpected_high_risk)}")
    if missing_keywords:
        reasons.append(f"response missing expected content: {missing_keywords}")
    if forbidden_present:
        reasons.append(f"response contains forbidden content: {forbidden_present}")
    rationale = "; ".join(reasons) or "all checks passed"

    return CaseScore(
        resolution_correct=resolution_correct,
        escalation_correct=escalation_correct,
        tool_call_f1=tool_f1,
        rationale=rationale,
    )
