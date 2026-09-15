from app.evals.metrics import score_case


def test_resolution_correct_when_everything_matches():
    score = score_case(
        expected_outcome_json={
            "outcome": "resolved",
            "expected_tools": ["account_lookup", "issue_refund"],
            "response_must_include": ["refund"],
            "response_must_not_include": ["denied"],
        },
        actual_outcome="resolved",
        final_response="We've submitted a refund for the duplicate charge.",
        tool_call_log=[
            {"tool_name": "account_lookup"},
            {"tool_name": "issue_refund"},
        ],
    )
    assert score.resolution_correct is True
    assert score.escalation_correct is True
    assert score.tool_call_f1 == 1.0


def test_outcome_mismatch_fails_resolution():
    score = score_case(
        expected_outcome_json={"outcome": "resolved", "expected_tools": []},
        actual_outcome="escalated",
        final_response="Looping in a human.",
        tool_call_log=[],
    )
    assert score.resolution_correct is False
    assert score.escalation_correct is False


def test_unauthorized_high_risk_tool_call_fails_even_with_matching_outcome():
    score = score_case(
        expected_outcome_json={"outcome": "resolved", "expected_tools": ["kb_search"]},
        actual_outcome="resolved",
        final_response="Here's a prorated credit for your downgrade.",
        tool_call_log=[{"tool_name": "kb_search"}, {"tool_name": "issue_refund"}],
    )
    assert score.resolution_correct is False
    assert "issue_refund" in score.rationale


def test_missing_required_tool_call_fails():
    score = score_case(
        expected_outcome_json={"outcome": "resolved", "expected_tools": ["issue_refund"]},
        actual_outcome="resolved",
        final_response="All set!",
        tool_call_log=[],
    )
    assert score.resolution_correct is False


def test_forbidden_keyword_fails():
    score = score_case(
        expected_outcome_json={"outcome": "resolved", "expected_tools": [], "response_must_not_include": ["denied"]},
        actual_outcome="resolved",
        final_response="Your request was denied.",
        tool_call_log=[],
    )
    assert score.resolution_correct is False


def test_extra_low_risk_tool_call_does_not_penalize():
    score = score_case(
        expected_outcome_json={"outcome": "resolved", "expected_tools": ["account_lookup"]},
        actual_outcome="resolved",
        final_response="Confirmed.",
        tool_call_log=[{"tool_name": "account_lookup"}, {"tool_name": "kb_search"}],
    )
    assert score.resolution_correct is True
