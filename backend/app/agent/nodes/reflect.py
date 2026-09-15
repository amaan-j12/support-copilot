from app.agent.context import NodeContext
from app.agent.state import TicketState

REFLECT_SCHEMA = {
    "type": "object",
    "properties": {
        "critique": {"type": "string"},
        "lesson": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": ["critique", "lesson", "confidence"],
}

SYSTEM_PROMPT = (
    "You are a QA reviewer for a support agent. Be specific and concise. If the resolution was "
    "already correct and there is nothing generalizable to learn, say so plainly rather than "
    "inventing a lesson."
)


def reflect_node(state: TicketState, ctx: NodeContext) -> dict:
    trace = "\n".join(state.get("scratchpad", []))
    prompt = (
        f"Ticket subject: {state['subject']}\n"
        f"Category: {state.get('category')}\n"
        f"Tool calls made:\n{trace or '(none)'}\n"
        f"Final response sent to customer: {state.get('final_response')}\n\n"
        "Critique this resolution: was it correct, complete, and policy-compliant? Propose one "
        "concise, generalizable lesson for handling similar tickets better next time."
    )
    resp = ctx.adapter.complete(
        [{"role": "user", "content": prompt}],
        system=SYSTEM_PROMPT,
        response_schema=REFLECT_SCHEMA,
        max_tokens=400,
        node_name="reflect",
        ticket_id=state["ticket_id"],
    )
    out = resp.structured_output or {}
    return {
        "reflection_critique": out.get("critique"),
        "reflection_lesson": out.get("lesson"),
        "reflection_confidence": out.get("confidence"),
        "total_input_tokens": state["total_input_tokens"] + resp.input_tokens,
        "total_output_tokens": state["total_output_tokens"] + resp.output_tokens,
        "total_cost_usd": state["total_cost_usd"] + resp.cost_usd,
    }
