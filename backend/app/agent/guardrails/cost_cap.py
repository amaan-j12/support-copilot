"""Per-ticket cost/iteration guardrail. A breach routes the ticket to
escalation rather than truncating silently mid-response.
"""

from app.core.config import get_settings


class CostCapExceeded(Exception):
    pass


def check_within_budget(*, tokens_used: int, cost_usd: float, iteration: int) -> None:
    settings = get_settings()
    if iteration > settings.max_tool_iterations_per_ticket:
        raise CostCapExceeded(f"Exceeded max_tool_iterations_per_ticket={settings.max_tool_iterations_per_ticket}")
    if tokens_used > settings.max_tokens_per_ticket:
        raise CostCapExceeded(f"Exceeded max_tokens_per_ticket={settings.max_tokens_per_ticket}")
    if cost_usd > settings.max_cost_usd_per_ticket:
        raise CostCapExceeded(f"Exceeded max_cost_usd_per_ticket={settings.max_cost_usd_per_ticket}")


ESCALATION_MESSAGE = "I'm looping in a human teammate to make sure this gets resolved correctly."


def apply_cost_cap_updates(state: dict, new_iteration: int, updates: dict) -> None:
    """Shared by tool_execution and hitl_pause: if this call pushed the ticket
    over budget, force the graph to escalate instead of looping further.
    """
    try:
        check_within_budget(
            tokens_used=state["total_input_tokens"] + state["total_output_tokens"],
            cost_usd=state["total_cost_usd"],
            iteration=new_iteration,
        )
    except CostCapExceeded as e:
        updates.update(
            {
                "force_escalate": True,
                "outcome": "escalated",
                "final_response": ESCALATION_MESSAGE,
                "error": str(e),
            }
        )
