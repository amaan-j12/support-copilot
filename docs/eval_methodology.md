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
candidate generation and only flip it to `active` if
`candidate.resolution_accuracy >= base.resolution_accuracy` — ties promote
(the candidate is at least as good and may still generalize better outside
the eval set), regressions are rejected and the candidate stays in the
database as a visible `rejected` generation rather than being deleted. This
is what makes the eval-scoreboard chart's promoted/rejected badges
meaningful instead of decorative.

## Running it

```bash
python scripts/run_baseline.py            # captures/refreshes gen0
python scripts/simulate_traffic.py        # generates reflections from live-style tickets
python scripts/run_learning_cycle.py      # reflection/playbook loop -> candidate gen
python scripts/run_prompt_optimization.py # prompt-optimization loop -> candidate gen
python scripts/export_baseline_scores.py  # re-pin baseline_scores.json after a real improvement
```
