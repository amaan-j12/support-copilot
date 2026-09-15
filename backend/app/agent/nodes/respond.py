from app.agent.context import NodeContext
from app.agent.state import TicketState

DEFAULT_MESSAGE = "Thanks for reaching out — we'll follow up shortly."


def respond_to_customer_node(state: TicketState, ctx: NodeContext) -> dict:
    message = state.get("final_response") or state.get("plan_response_message") or DEFAULT_MESSAGE
    outcome = state.get("outcome") or "resolved"
    return {"final_response": message, "outcome": outcome}
