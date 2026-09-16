# Eval methodology

## Why this exists

Most "AI agent" portfolio projects skip evaluation entirely — a live demo
that works once on a happy path isn't evidence the agent is any good, and
it's definitely not evidence a *later change* to the agent didn't break it.
Industry surveys cited in this project's design research put the gap at
roughly **89% of teams with production agents have tracing, but only ~52%
have evals** — so a real eval harness with a committed baseline and a
regression gate is a deliberate differentiator here, not boilerplate.

## The eval set

`backend/app/evals/eval_set/v1/*.yaml` — 19 synthetic Loopwork billing
tickets, frozen once the baseline was captured (see `baseline_scores.json`).
Five categories:

| Category | Count | Tests |
|---|---|---|
| `routine` | 5 | Correct lookups/answers with **no** refund/cancel — includes several "nothing is actually wrong" cases against over-eager refunding |
| `must_approve` | 4 | A refund/cancellation genuinely IS warranted and gets routed through the HITL-gated tool |
| `must_escalate` | 4 | Legal threats, multi-issue tickets, extreme ambiguity, out-of-policy asks — correct behavior is `action=escalate`, not guessing |
| `ambiguous` | 3 | Plausible-sounding refund requests that fail Loopwork's actual policy on close reading |
| `adversarial` | 3 | Prompt-injection / social-engineering attempts embedded in the customer message |

Each case specifies `expected.outcome`, `expected.requires_hitl`,
`expected.expected_tools`, and optional `response_must_include` /
`response_must_not_include` keyword checks.

## Scoring (`app/evals/metrics.py`)

Deterministic, not an LLM judge (Phase-1 scope — see "Known limitations" in
`docs/architecture.md`):

- **resolution_correct** — outcome matches expected, every required tool was
  called, **no unauthorized high-risk tool was called** (this is the
  precise check that catches over-eager refunding even when the outcome
  happens to look right), and required/forbidden response keywords hold.
- **escalation_correct** — did the agent escalate exactly when it should
  have (independent of whether the rest of the resolution was perfect).
- **tool_call_f1** — precision/recall over actual vs. expected tool calls,
  reported per-case for diagnosis even when it isn't what gates promotion.

## Baseline

Generation 0 (`created_by="baseline"`, empty playbook, no reflections) run
against eval_set v1:

```
resolution_accuracy: 63.2%
escalation_accuracy: 94.7%
avg_tool_call_f1:    0.76
```

Committed to `backend/baseline_scores.json` via
`scripts/export_baseline_scores.py`; this is the "before" number the
CASE_STUDY.md and README reference, and what `eval-gate.yml` checks new code
against.

## Promotion gate

Both learning loops (`app/learning/playbook_promote.py`,
`app/learning/prompt_optimizer.py`) run the *same* frozen eval set against a
candidate generation and only flip it to `active` if none of
**resolution_accuracy, escalation_accuracy, avg_tool_call_f1** regress by
more than a 5-point tolerance (`app/learning/eval_gate.py::passes_gate`).
Regressions are rejected and the candidate stays in the database as a
visible `rejected` generation rather than being deleted — this is what
makes the eval-scoreboard chart's promoted/rejected badges meaningful
instead of decorative.

**This gate was strengthened after a real finding, not preemptively.** The
first promotion cycle (gen0 → gen1) originally checked resolution_accuracy
alone. gen1 tied gen0 on resolution_accuracy (63.2%) and got promoted — but
escalation_accuracy quietly dropped 94.7% → 89.5% and avg_tool_call_f1
dropped 0.76 → 0.63. A resolution-only gate is blind to a candidate that
trades escalation judgment for a tied headline number. The gate now checks
all three (see `tests/unit/test_eval_gate.py::test_the_gen0_to_gen1_regression_this_project_actually_hit`,
a regression test built directly from this incident); later generations are
held to the stronger bar. gen1 itself was left promoted rather than
retroactively reverted — the honest record is that it shipped under the
weaker gate, which is exactly why the gate changed.

**The strengthened gate proved itself immediately.** The very next cycle
(gen1 → gen2, via prompt optimization) produced a candidate that improved
resolution_accuracy to 68.4% — a genuine 5-point gain — but dropped
escalation_accuracy to 78.9%, an 11-point regression beyond tolerance. Under
the *original* gate this would have promoted (resolution went up). Under the
strengthened gate it was correctly **rejected**, and gen1 stayed active.
This is the clearest evidence in this project that the eval-gated promotion
mechanism isn't decorative: it caught a regression that a naive "did the
headline number go up?" check would have missed, one cycle after that exact
blind spot was found and fixed.

## Running it

```bash
python scripts/run_baseline.py            # captures/refreshes gen0
python scripts/simulate_traffic.py        # generates reflections from live-style tickets
python scripts/run_learning_cycle.py      # reflection/playbook loop -> candidate gen
python scripts/run_prompt_optimization.py # prompt-optimization loop -> candidate gen
python scripts/export_baseline_scores.py  # re-pin baseline_scores.json after a real improvement
```
