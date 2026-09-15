# Case study: a self-learning support agent for Loopwork

*A product case study written from the perspective of deploying this system
at a real company — "Loopwork" is a fictional SaaS product used as the
synthetic domain, but the architecture, guardrails, and eval methodology are
directly applicable to a real support queue.*

## The problem

Support teams at fast-growing SaaS companies face the same shape of problem
regardless of product: ticket volume scales faster than headcount, a large
fraction of tickets are variations on a small number of billing/account
patterns, and the cost of a wrong answer (an unauthorized refund, a
cancellation nobody approved) is high enough that full autonomy is
uncomfortable — but requiring a human to touch every single ticket doesn't
scale either.

Industry data backs this up: MIT-cited research puts the failure rate of
generative-AI pilots that never show ROI at roughly 95%, and a
CB-Insights-sourced survey found many enterprise AI-agent deployments hit
reliability and integration walls. The gap isn't the model — it's that most
deployments skip the boring parts: memory that's actually gated, evaluation
that's actually run, and guardrails that are actually enforced rather than
prompted-for.

## The solution

Support Copilot resolves routine billing/account tickets autonomously,
routes genuinely high-risk actions (refunds, cancellations) through a human
approval gate, and — the differentiating piece — **measurably improves over
time** through two gated learning loops rather than staying static after
launch:

- **Reflection → playbook**: every ticket produces a self-critique; accepted
  critiques become candidate "playbook" entries (distilled lessons), which
  only go live if they don't regress the agent's score on a frozen,
  held-out eval set.
- **Reflective prompt optimization**: periodically, the agent's own failure
  traces are fed back into an optimization pass that proposes a targeted
  prompt patch — same eval gate, same promote/reject discipline.

This mirrors how Decagon, Glean, and Salesforce Agentforce describe their
own "agent memory" in public engineering writeups: retrieval and feedback
loops over a frozen model, not continuous fine-tuning.

## What it would take to point this at a real company

The domain layer (`app/synthetic_data/`, `app/agent/tools/`) is the only
part that's Loopwork-specific. Standing this up for a real support queue
means:

1. Replace the mock account/invoice fixtures with real API calls (Stripe,
   Zendesk, an internal billing service) behind the same `ToolDef` interface.
2. Replace the synthetic KB articles with a real help-center corpus (the
   embedding-based retrieval code doesn't change).
3. Rebuild the eval set from real historical tickets with known-correct
   resolutions (the harness, scoring, and promotion gate don't change).
4. Swap `LLM_PROVIDER=claude_cli` for `LLM_PROVIDER=api` with a production
   API key (one environment variable — see `docs/architecture.md`).
5. Wire the HITL approval gate to a real notification channel (Slack, an
   internal queue) instead of the Phase-1 auto-resolve stub.

## Projected impact (illustrative, not measured on real traffic)

Using the gen0 baseline as a stand-in for "agent handles what it can handle
confidently, escalates the rest":

- **63% of routine billing tickets resolved without human involvement**,
  with a 95% escalation-accuracy rate on the ambiguous/high-risk cases
  meant to catch it — i.e., it escalates the right ~5% it's actually unsure
  about rather than guessing.
- If a support team currently spends ~8 minutes of agent time per routine
  billing ticket, autonomously resolving even 60% of a 10,000-ticket/month
  queue is ~800 agent-hours/month redirected to the harder tickets that
  actually need a human — the kind of number a company would validate
  against its own historical average-handle-time data before committing to,
  which is exactly what re-running the eval harness against real historical
  tickets (step 3 above) is for.
- The self-learning loop means this number is a floor, not a ceiling: every
  promoted generation is evaluated against the *same* held-out set, so
  "gen12 resolves 78% instead of gen0's 63%" is a verifiable claim, not a
  vendor promise.

## Where human oversight stays necessary — stated plainly

This is deliberately not pitched as full autonomy, and the architecture
reflects that:

- **Every refund and cancellation requires approval**, full stop — this is
  enforced by a static risk policy the agent cannot talk itself out of
  (`app/agent/guardrails/risk_policy.py`), not by asking the model nicely.
- **The agent escalates on legal threats, fraud allegations, and ambiguity**
  by design — the eval set specifically tests for this, and gen0 already
  scores 94.7% on it.
- **The eval set is 19 cases, not thousands.** It's enough to produce a
  real, varied signal and a genuine promote/reject gate, but a production
  deployment should grow it from real historical tickets before trusting
  the numbers at face value.
- **The HITL approval gate auto-resolves synchronously in this build**
  (documented in `docs/architecture.md`) so the eval harness and traffic
  simulation can run unattended for this portfolio project. A real
  deployment needs the already-scaffolded resume-on-human-decision path
  actually wired to a human, not a stub.
- **Hallucination isn't scored yet** — the eval harness checks
  outcome/tool-call correctness deterministically but doesn't yet run an
  LLM-judge faithfulness check, the natural next addition.

Being specific about these limits is the point: a system that claims full
autonomy and hides where it actually needs a human is a worse product than
one that's honest about the boundary — and a support team evaluating this
for their own queue should be able to see exactly where that boundary is
before trusting it with a customer's money.
