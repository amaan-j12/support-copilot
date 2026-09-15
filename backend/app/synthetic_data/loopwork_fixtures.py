"""In-memory mock backend for 'Loopwork', a fictional team-collaboration SaaS.

Standing in for the real systems a support agent would call (billing
provider, account DB). Deliberately not a database table: this is fixture
data the agent's tools query, reset on process restart, seeded fresh for
every eval run so eval cases are deterministic and reproducible.
"""

from dataclasses import dataclass, field

PLANS = {
    "free": {"name": "Free", "price_per_seat": 0},
    "team": {"name": "Team", "price_per_seat": 12},
    "business": {"name": "Business", "price_per_seat": 24},
    "enterprise": {"name": "Enterprise", "price_per_seat": None},
}


@dataclass
class Invoice:
    id: str
    customer_id: str
    amount_usd: float
    status: str  # paid / failed / refunded / duplicate
    date: str
    description: str
    duplicate_of: str | None = None


@dataclass
class Account:
    customer_id: str
    name: str
    email: str
    plan: str
    seats: int
    status: str  # active / past_due / canceled
    trial_ends: str | None = None
    invoices: list[Invoice] = field(default_factory=list)


KB_ARTICLES = [
    {
        "id": "kb-001",
        "title": "Understanding proration when changing plans",
        "body": (
            "When you upgrade or downgrade your Loopwork plan mid-cycle, we prorate the "
            "difference. Upgrades are charged immediately for the remaining days in the "
            "billing period; downgrades are credited toward your next invoice, not refunded "
            "as cash."
        ),
    },
    {
        "id": "kb-002",
        "title": "Duplicate charges from a card retry",
        "body": (
            "If a card is declined and then a payment retry succeeds, some banks briefly "
            "show two pending authorizations. Only one actually settles. If two SEPARATE "
            "invoices in the Loopwork billing history both show status=paid for the same "
            "billing period, that is a genuine duplicate charge and should be refunded."
        ),
    },
    {
        "id": "kb-003",
        "title": "Refund policy",
        "body": (
            "Loopwork issues full refunds for: (1) confirmed duplicate charges, (2) accidental "
            "charges within 48 hours of a plan change the customer did not intend, (3) failed "
            "service outages lasting >24h. Refunds require agent approval before issuing. "
            "We do not refund for partial-month cancellations outside these cases; those get "
            "prorated credit instead."
        ),
    },
    {
        "id": "kb-004",
        "title": "Seat count and billing mismatches",
        "body": (
            "Your invoice charges for the seat count at the start of the billing cycle. "
            "Removing a seat mid-cycle does not reduce the current invoice; it reduces seats "
            "billed starting next cycle."
        ),
    },
    {
        "id": "kb-005",
        "title": "Canceling your subscription",
        "body": (
            "Canceling stops future billing at the end of the current paid period; you keep "
            "access until then. Cancellation does not retroactively refund the current period "
            "unless it falls under the refund policy (see kb-003)."
        ),
    },
    {
        "id": "kb-006",
        "title": "Trial to paid conversion",
        "body": (
            "Free trials convert automatically to the Team plan unless canceled before the "
            "trial end date. Customers are emailed 3 days before conversion."
        ),
    },
]


def _acct(customer_id, name, email, plan, seats, status, invoices, trial_ends=None) -> Account:
    return Account(
        customer_id=customer_id,
        name=name,
        email=email,
        plan=plan,
        seats=seats,
        status=status,
        trial_ends=trial_ends,
        invoices=invoices,
    )


def build_fixture_accounts() -> dict[str, Account]:
    """Fresh fixture data — call once per eval run / process start for determinism."""
    accounts = {
        "cust_1001": _acct(
            "cust_1001", "Priya Nair", "priya@northwind.io", "business", 12, "active",
            [
                Invoice("inv_1001a", "cust_1001", 288.00, "paid", "2026-08-01", "Business plan, 12 seats"),
                Invoice("inv_1001b", "cust_1001", 288.00, "paid", "2026-08-01", "Business plan, 12 seats"),
            ],
        ),
        "cust_1002": _acct(
            "cust_1002", "Marcus Cole", "marcus@fieldstone.co", "team", 5, "active",
            [Invoice("inv_1002a", "cust_1002", 60.00, "paid", "2026-08-03", "Team plan, 5 seats")],
        ),
        "cust_1003": _acct(
            "cust_1003", "Elena Fischer", "elena@brightloop.dev", "team", 8, "active",
            [
                Invoice("inv_1003a", "cust_1003", 60.00, "paid", "2026-07-05", "Team plan, 5 seats"),
                Invoice("inv_1003b", "cust_1003", 96.00, "paid", "2026-08-05", "Team plan, 8 seats (upgraded mid-cycle)"),
            ],
        ),
        "cust_1004": _acct(
            "cust_1004", "Sam Okafor", "sam@driftworks.app", "business", 20, "past_due",
            [Invoice("inv_1004a", "cust_1004", 480.00, "failed", "2026-08-10", "Business plan, 20 seats")],
        ),
        "cust_1005": _acct(
            "cust_1005", "Julia Novak", "julia@parktech.io", "free", 1, "active",
            [], trial_ends="2026-09-20",
        ),
        "cust_1006": _acct(
            "cust_1006", "Devon Reyes", "devon@lumecraft.com", "team", 6, "active",
            [Invoice("inv_1006a", "cust_1006", 72.00, "paid", "2026-08-02", "Team plan, 6 seats")],
        ),
        "cust_1007": _acct(
            "cust_1007", "Aiko Tanaka", "aiko@ridgeline.jp", "business", 15, "active",
            [Invoice("inv_1007a", "cust_1007", 360.00, "paid", "2026-08-04", "Business plan, 15 seats")],
        ),
        "cust_1008": _acct(
            "cust_1008", "Ben Okwuosa", "ben@harborline.co", "team", 4, "active",
            [
                Invoice("inv_1008a", "cust_1008", 48.00, "paid", "2026-08-06", "Team plan, 4 seats"),
                Invoice("inv_1008b", "cust_1008", 48.00, "paid", "2026-08-06", "Team plan, 4 seats"),
            ],
        ),
        "cust_1009": _acct(
            "cust_1009", "Lina Moreau", "lina@westgate.fr", "business", 10, "active",
            [Invoice("inv_1009a", "cust_1009", 240.00, "paid", "2026-08-07", "Business plan, 10 seats")],
        ),
    }
    return accounts
