# Support Copilot

A self-learning AI customer support agent for **Loopwork**, a fictional
team-collaboration SaaS — built as a portfolio project modeled on production
patterns from Decagon, Intercom Fin, and Sierra: **episodic memory +
reflection-driven playbook promotion + reflective prompt optimization**,
every learned update gated by a frozen eval set before it goes live.

> Business framing and ROI projection: [`CASE_STUDY.md`](CASE_STUDY.md)
> Architecture, data model, agent graph: [`docs/architecture.md`](docs/architecture.md)
> Eval methodology and baseline: [`docs/eval_methodology.md`](docs/eval_methodology.md)

## What "self-learning" means here

Not fine-tuning. Every real production deployment of this pattern (Decagon's
ticket→skill distillation, Glean's Enterprise Memory) works the same way:
memory + retrieval + a feedback loop, not weight updates. Concretely:

1. **Episodic memory** — every resolved ticket is embedded and stored;
   future tickets retrieve similar past outcomes.
2. **Reflection loop** — after every ticket, the agent critiques its own
   resolution and proposes a lesson. Accepted lessons become candidate
   **playbook entries**.
3. **Reflective prompt optimization** — periodically, the agent reflects on
   its own recent *failures* (not successes) and proposes a targeted patch
   to its own system prompt.

Both (2) and (3) are **gated**: a candidate generation is evaluated against
the same frozen eval set the baseline was scored on, and only promoted to
`active` if it doesn't regress. Rejected candidates stay visible in the
database — this is what makes the eval scoreboard's promoted/rejected
badges real evidence, not a claim.

## Architecture at a glance

```
FastAPI + LangGraph  ←→  Postgres + pgvector  ←→  React dashboard
        ↓
  LLMAdapter (provider-agnostic)
   ├── ClaudeCLIAdapter  — shells out to `claude` CLI, $0 marginal cost (dev)
   └── APIAdapter        — litellm, real API call (live deploy)
```

Full diagrams and the data model: [`docs/architecture.md`](docs/architecture.md).

## Results so far

| Generation | Created by | Resolution accuracy | Escalation accuracy |
|---|---|---|---|
| gen0 (baseline) | — | **63.2%** | 94.7% |

(Live-updating table lives in the dashboard's Eval Scoreboard page — this
one row is the "before" number; run `scripts/simulate_traffic.py` +
`scripts/run_learning_cycle.py` / `scripts/run_prompt_optimization.py` to
produce and promote later generations. See
[`docs/eval_methodology.md`](docs/eval_methodology.md) for what each metric
means and why 63% is a real, not-cherry-picked baseline: the eval set
includes adversarial prompt-injection probes and "nothing is actually wrong"
cases specifically designed to catch an agent that over-eagerly issues
refunds.)

## Quickstart (local, $0 cost)

Requires: Python 3.12, Node 20, Postgres 17 with the `pgvector` extension,
and the [Claude Code CLI](https://claude.com/claude-code) authenticated on
your PATH (`claude auth`) — no API key needed for local development.

```bash
# 1. Database
createdb support_copilot
psql -d support_copilot -c "CREATE EXTENSION vector;"

# 2. Backend
cd backend
python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev,local-embeddings]"
cp .env.example .env   # defaults to LLM_PROVIDER=claude_cli — no key needed
.venv/bin/alembic upgrade head
.venv/bin/python scripts/run_baseline.py      # captures the gen0 baseline eval
.venv/bin/uvicorn app.main:app --reload --port 8000

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev   # http://localhost:5173, proxies /api -> localhost:8000
```

Then, to see the learning loop actually promote a new generation:

```bash
cd backend
.venv/bin/python scripts/simulate_traffic.py         # generates reflections
.venv/bin/python scripts/run_learning_cycle.py        # playbook loop -> candidate gen
.venv/bin/python scripts/run_prompt_optimization.py   # prompt loop -> candidate gen
```

Open the dashboard's **Eval Scoreboard** page to watch generations get
promoted or rejected against the frozen eval set.

## Going live

Deploying is meant to be an environment-variable change, not a rewrite —
that's the actual point of the `LLMAdapter` abstraction. See "Deployment" in
[`docs/architecture.md`](docs/architecture.md) for the Docker Compose /
Railway path (`LLM_PROVIDER=api` + a real `ANTHROPIC_API_KEY`).

## Stack

FastAPI · LangGraph · SQLAlchemy + Alembic · Postgres + pgvector · litellm ·
React + TypeScript + Vite + Tailwind + TanStack Query + Recharts · Docker ·
GitHub Actions

## Repo layout

```
backend/app/
  agent/        LangGraph state machine, nodes, tools, guardrails
  learning/     reflection/playbook + prompt-optimization loops (eval-gated)
  memory/       pgvector episodic + playbook retrieval
  llm/          provider-agnostic LLMAdapter (CLI + API implementations)
  evals/        frozen eval set, scoring, runner
  db/           SQLAlchemy models + Alembic migrations
  api/          FastAPI routers
frontend/src/   React dashboard (tickets, approvals, eval scoreboard, playbook)
infra/          Docker Compose, Railway config
docs/           architecture + eval methodology
```

## License

MIT — see [`LICENSE`](LICENSE).
