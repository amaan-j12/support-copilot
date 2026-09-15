from app.synthetic_data import store


def account_lookup(customer_id: str) -> dict:
    acct = store.get_account(customer_id)
    if acct is None:
        return {"found": False}
    return {
        "found": True,
        "customer_id": acct.customer_id,
        "name": acct.name,
        "email": acct.email,
        "plan": acct.plan,
        "seats": acct.seats,
        "status": acct.status,
        "trial_ends": acct.trial_ends,
    }
