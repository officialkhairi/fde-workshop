"""
Guided branch — a working tool, so a stuck team can keep moving.

    make guided     swaps this in, keeping your version as tools.py.mine

Read it rather than just running it. The three decisions are commented.
"""
import os
import re

import requests

ORDERS_API = os.environ.get("ORDERS_API", "http://127.0.0.1:8081")
ORDERS_KEY = os.environ.get("ORDERS_KEY", "")

# Decision 3, made explicit: the customer sees these and nothing else.
SAFE_FIELDS = ("status", "eta", "destination")


def find_order_id(message: str):
    m = re.search(r"JJ-?\s?(\d{4})", message, re.I)
    return f"JJ-{m.group(1)}" if m else None


def get_shipment_status(order_id: str) -> dict:
    try:
        # Decision 2a: a timeout. The API can hang for 45s; the customer will not wait.
        resp = requests.get(f"{ORDERS_API}/orders/{order_id}",
                            headers={"x-api-key": ORDERS_KEY},
                            timeout=3)
    except requests.Timeout as exc:
        # Raised, not swallowed. The loop turns this into an honest "try again".
        raise RuntimeError("orders api timed out") from exc

    # Decision 2b: a missing order is an answer, not an exception.
    if resp.status_code == 404:
        return {"error": "order not found"}
    resp.raise_for_status()

    data = resp.json()
    # Decision 3: allow-list, not deny-list. New fields stay private by default.
    return {k: data[k] for k in SAFE_FIELDS if k in data}


def find_order_by_phone(phone: str):
    # Decision 4: the support lead told us agents find customers by phone number,
    # through an endpoint the API docs never mention. Same allow-list as above.
    try:
        resp = requests.get(f"{ORDERS_API}/orders", params={"phone": phone},
                            headers={"x-api-key": ORDERS_KEY}, timeout=3)
    except requests.Timeout as exc:
        raise RuntimeError("orders api timed out") from exc
    resp.raise_for_status()
    orders = resp.json().get("orders", [])
    if not orders:
        return None
    return {k: orders[0][k] for k in SAFE_FIELDS if k in orders[0]}
