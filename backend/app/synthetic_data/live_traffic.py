"""Synthetic 'live' ticket traffic — distinct wording/scenarios from
eval_set/v1 — used to generate organic Reflection rows that seed the
reflection/playbook learning loop. Kept separate from the frozen eval set so
promotion is judged on held-out cases, not the traffic the agent learned from.
"""

LIVE_TICKETS = [
    {
        "customer_id": "cust_1001",
        "subject": "Two charges on my card",
        "message": (
            "Hey, weird one — my card statement shows Loopwork billed me twice this cycle, "
            "same amount both times. Can you take a look?"
        ),
    },
    {
        "customer_id": "cust_1003",
        "subject": "Invoice went up after adding people",
        "message": (
            "I added a few teammates mid-month and now my invoice is higher than usual. "
            "Is that expected or did something go wrong?"
        ),
    },
    {
        "customer_id": "cust_1006",
        "subject": "Can I get last month's invoice?",
        "message": "Could you send over the invoice from last month? I need it for our books.",
    },
    {
        "customer_id": "cust_1002",
        "subject": "What happens if I go from Team to Business mid-month",
        "message": (
            "Thinking about upgrading us from Team to Business plan in the middle of the "
            "billing cycle — how does the pricing work for that?"
        ),
    },
    {
        "customer_id": "cust_1009",
        "subject": "Please cancel",
        "message": "We've decided to move on from Loopwork. Please cancel our subscription.",
    },
    {
        "customer_id": "cust_1007",
        "subject": "Seat count question",
        "message": (
            "I dropped a couple of seats last week but my most recent invoice looks the "
            "same as before — is that a mistake?"
        ),
    },
    {
        "customer_id": "cust_1005",
        "subject": "trial ending?",
        "message": "hey when does my trial run out and what do I need to do before then",
    },
    {
        "customer_id": "cust_1008",
        "subject": "Double billed",
        "message": (
            "Looking at my bank activity and I see Loopwork charged me twice on the same "
            "day for what should be one payment. Please help."
        ),
    },
    {
        "customer_id": "cust_1004",
        "subject": "past due — what's going on",
        "message": (
            "I got a notice that my account is past due and I'm confused why, my card should "
            "be valid. Can someone explain what happened and how to fix it?"
        ),
    },
    {
        "customer_id": "cust_1002",
        "subject": "This is absolutely unacceptable, considering legal options",
        "message": (
            "I've been billed for months for a plan I never signed up for and nobody has "
            "explained why. I'm speaking with an attorney about this if it's not resolved today."
        ),
    },
]
