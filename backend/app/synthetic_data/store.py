"""Mutable, resettable handle onto the fixture accounts, so tools can read
and (for refunds/cancellations) write state, while eval runs stay
deterministic by resetting before each run.
"""

from app.synthetic_data.loopwork_fixtures import Account, build_fixture_accounts

_accounts: dict[str, Account] = build_fixture_accounts()


def reset() -> None:
    global _accounts
    _accounts = build_fixture_accounts()


def get_account(customer_id: str) -> Account | None:
    return _accounts.get(customer_id)


def all_accounts() -> dict[str, Account]:
    return _accounts
