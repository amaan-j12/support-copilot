"""Lightweight PII redaction applied at intake, before anything is persisted
or embedded. Phase-1 regex-based scope: emails, phone numbers, and credit
card-like digit sequences. Deepened with more coverage in Phase 2.
"""

import re

_PATTERNS: dict[str, re.Pattern] = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "phone": re.compile(r"\b(?:\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"),
    "card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
}


def redact(text: str) -> tuple[str, dict[str, int]]:
    """Return (redacted_text, counts_by_type)."""
    counts: dict[str, int] = {}
    redacted = text
    for label, pattern in _PATTERNS.items():
        redacted, n = pattern.subn(f"[REDACTED_{label.upper()}]", redacted)
        if n:
            counts[label] = n
    return redacted, counts
