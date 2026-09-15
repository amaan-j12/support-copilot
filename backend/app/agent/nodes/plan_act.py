import json
import uuid

from app.agent.context import NodeContext
from app.agent.guardrails.injection_defense import wrap_untrusted
from app.agent.state import TicketState
from app.agent.tools.registry import tool_catalog_text
from app.db.models import PromptVersion

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "thought": {"type": "string"},
        "action": {"type": "string", "enum": ["call_tool", "respond", "escalate"]},
        "tool_name": {"type": "string"},
        "tool_arguments": {"type": "object"},
        "response_message": {"type": "string"},
    },
    "required": ["thought", "action"],
}


def _prompt_optimizer_patch(state: TicketState, ctx: NodeContext) -> str | None:
    """A prompt patch proposed by the prompt-optimization learning loop for
    this specific agent generation, if one was promoted (or is the candidate
    currently being evaluated). See app/learning/prompt_optimizer.py.
    """
    if not ctx.agent_version_id:
        return None
    row = (
        ctx.db.query(PromptVersion)
        .filter_by(agent_version_id=uuid.UUID(ctx.agent_version_id), node_name="plan_and_act")
        .first()
    )
    return row.prompt_text if row else None


def _system_prompt(state: TicketState, ctx: NodeContext) -> str:
    playbook = state.get("retrieved_playbook") or []
    playbook_text = (
        "\n".join(f"- {p['title']}: {p['content']}" for p in playbook)
        if playbook
        else "(none yet — this agent generation has no learned playbook entries)"
    )
    patch = _prompt_optimizer_patch(state, ctx)
    patch_section = f"\n\nAdditional guidance learned from past mistakes:\n{patch}" if patch else ""
    return (
        "You are Loopwork's AI billing support agent. Resolve the customer's ticket using the "
        "available tools, then respond directly to the customer in `response_message`. Be concise "
        "and follow Loopwork's stated refund policy exactly — check kb_articles for it, don't guess. "
        "Never promise a refund or cancellation has already happened: issue_refund and "
        "cancel_subscription are gated by human approval, so if you call one of them, tell the "
        "customer the action is pending approval rather than confirmed. On each turn, do exactly "
        "one of: call a tool (action=call_tool), send the final reply (action=respond), or hand off "
        "to a human teammate (action=escalate) — never combine these.\n\n"
        "Escalate (action=escalate) instead of resolving yourself when: the customer threatens legal "
        "action or alleges fraud, the request is ambiguous enough that guessing could cause real harm, "
        "it combines multiple unrelated issues, or it falls outside your documented tools/policy. When "
        "escalating, still set response_message to a short, reassuring note the customer will see "
        "(e.g. 'I'm looping in a specialist on our team who can help with this.').\n\n"
        f"Available tools:\n{tool_catalog_text()}\n\n"
        f"Learned playbook (lessons distilled from past tickets — trust these over your own "
        f"assumptions when they apply):\n{playbook_text}"
        f"{patch_section}\n\n"
        "Respond ONLY with the requested JSON structure."
    )


def plan_and_act_node(state: TicketState, ctx: NodeContext) -> dict:
    parts = [
        f"Subject: {state['subject']}",
        (
            f"Verified customer_id (from the authenticated support session, already confirmed — "
            f"use this exact value for any tool call that needs customer_id, never invent one): "
            f"{state['customer_id']}"
        ),
        wrap_untrusted("customer_message", state["sanitized_message"]),
        f"Detected category: {state.get('category')}, priority: {state.get('priority')}",
    ]
    if state.get("retrieved_memories"):
        parts.append(wrap_untrusted("past_similar_tickets", json.dumps(state["retrieved_memories"])))
    if state.get("retrieved_kb"):
        parts.append(wrap_untrusted("kb_articles", json.dumps(state["retrieved_kb"])))
    if state.get("scratchpad"):
        parts.append("Tool results so far this turn:\n" + "\n".join(state["scratchpad"]))
    prompt = "\n\n".join(parts)

    resp = ctx.adapter.complete(
        [{"role": "user", "content": prompt}],
        system=_system_prompt(state, ctx),
        response_schema=PLAN_SCHEMA,
        max_tokens=600,
        node_name="plan_and_act",
        ticket_id=state["ticket_id"],
    )
    out = resp.structured_output or {}
    action = out.get("action", "respond")
    updates = {
        "plan_thought": out.get("thought"),
        "plan_action": action,
        "plan_tool_name": out.get("tool_name"),
        "plan_tool_arguments": out.get("tool_arguments") or {},
        "plan_response_message": out.get("response_message"),
        "total_input_tokens": state["total_input_tokens"] + resp.input_tokens,
        "total_output_tokens": state["total_output_tokens"] + resp.output_tokens,
        "total_cost_usd": state["total_cost_usd"] + resp.cost_usd,
    }
    if action == "escalate":
        updates["outcome"] = "escalated"
    return updates
