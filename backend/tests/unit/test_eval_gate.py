from app.learning.eval_gate import RunMetrics, passes_gate


def test_passes_when_candidate_strictly_better():
    base = RunMetrics(0.60, 0.90, 0.70, 19)
    candidate = RunMetrics(0.70, 0.95, 0.80, 19)
    ok, reason = passes_gate(candidate, base)
    assert ok is True
    assert reason == ""


def test_passes_on_exact_tie():
    base = RunMetrics(0.632, 0.947, 0.76, 19)
    candidate = RunMetrics(0.632, 0.947, 0.76, 19)
    ok, _ = passes_gate(candidate, base)
    assert ok is True


def test_fails_when_resolution_regresses_beyond_tolerance():
    base = RunMetrics(0.70, 0.90, 0.80, 19)
    candidate = RunMetrics(0.60, 0.90, 0.80, 19)
    ok, reason = passes_gate(candidate, base)
    assert ok is False
    assert "resolution_accuracy" in reason


def test_the_gen0_to_gen1_regression_this_project_actually_hit():
    """Regression test for the real trade-off the first promotion cycle
    produced: resolution_accuracy tied, but escalation_accuracy and
    avg_tool_call_f1 both dropped. The original (resolution-only) gate let
    this through; the fixed gate must not.
    """
    base = RunMetrics(resolution_accuracy=0.632, escalation_accuracy=0.947, avg_tool_call_f1=0.76, n_cases=19)
    candidate = RunMetrics(resolution_accuracy=0.632, escalation_accuracy=0.895, avg_tool_call_f1=0.63, n_cases=19)
    ok, reason = passes_gate(candidate, base)
    assert ok is False
    assert "escalation_accuracy" in reason
    assert "avg_tool_call_f1" in reason


def test_small_regression_within_tolerance_still_passes():
    base = RunMetrics(0.70, 0.90, 0.80, 19)
    candidate = RunMetrics(0.68, 0.88, 0.78, 19)  # within default 5% tolerance
    ok, _ = passes_gate(candidate, base)
    assert ok is True
