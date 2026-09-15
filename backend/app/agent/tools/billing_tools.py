from app.synthetic_data import store


def invoice_lookup(customer_id: str, invoice_id: str | None = None) -> dict:
    acct = store.get_account(customer_id)
    if acct is None:
        return {"found": False, "invoices": []}
    invoices = acct.invoices
    if invoice_id:
        invoices = [i for i in invoices if i.id == invoice_id]
    return {
        "found": True,
        "invoices": [
            {
                "id": i.id,
                "amount_usd": i.amount_usd,
                "status": i.status,
                "date": i.date,
                "description": i.description,
            }
            for i in invoices
        ],
    }


def issue_refund(customer_id: str, invoice_id: str, reason: str) -> dict:
    """HIGH RISK: only executed after the HITL approval gate signs off."""
    acct = store.get_account(customer_id)
    if acct is None:
        return {"success": False, "error": "account_not_found"}
    for inv in acct.invoices:
        if inv.id == invoice_id:
            if inv.status == "refunded":
                return {"success": False, "error": "already_refunded"}
            inv.status = "refunded"
            return {"success": True, "invoice_id": invoice_id, "amount_usd": inv.amount_usd, "reason": reason}
    return {"success": False, "error": "invoice_not_found"}


def cancel_subscription(customer_id: str, reason: str) -> dict:
    """HIGH RISK: only executed after the HITL approval gate signs off."""
    acct = store.get_account(customer_id)
    if acct is None:
        return {"success": False, "error": "account_not_found"}
    acct.status = "canceled"
    return {"success": True, "customer_id": customer_id, "reason": reason}
