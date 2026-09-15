"""Static risk policy: which tools are irreversible/costly enough to require
human approval before executing. The `risk_gate` graph node reads this
directly rather than trusting the model's own judgment about risk.
"""

RISK_LEVELS: dict[str, str] = {
    "kb_search": "low",
    "account_lookup": "low",
    "invoice_lookup": "low",
    "issue_refund": "high",
    "cancel_subscription": "high",
}


def is_high_risk(tool_name: str) -> bool:
    return RISK_LEVELS.get(tool_name, "high") == "high"  # unknown tools default to high-risk
