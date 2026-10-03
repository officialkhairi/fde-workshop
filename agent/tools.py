"""
Your tool. This is the only code file you need to change.

Four decisions, each commented where it is made.
"""
import os
import re

import requests

ORDERS_API = os.environ.get("ORDERS_API", "http://127.0.0.1:8081")
ORDERS_KEY = os.environ.get("ORDERS_KEY", "")

# The API fronts a slow SQL Server that can hang for seconds. Customers will not wait.
TIMEOUT = 3

# The customer sees these fields and nothing else. Allow-list, not deny-list:
# any new field the API grows (notes, phone numbers, names) stays private by default.
SAFE_FIELDS = ("status", "eta", "destination")

# Arabic-Indic (٠-٩) and Extended Arabic-Indic (۰-۹) digits -> ASCII.
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def find_order_id(message: str):
    """Pull an order reference out of a customer message. Returns None if absent."""
    text = message.translate(_DIGITS)
    m = re.search(r"JJ-?\s?(\d{4})", text, re.I)
    if not m:
        # Customers often drop the prefix: "where's order 4474?". Accept a lone
        # four-digit number, but not one embedded in a phone number or longer run.
        m = re.search(r"(?<![\d-])(\d{4})(?![\d-])", text)
    return f"JJ-{m.group(1)}" if m else None


def _get(path: str, **params):
    try:
        return requests.get(f"{ORDERS_API}{path}", params=params or None,
                            headers={"x-api-key": ORDERS_KEY}, timeout=TIMEOUT)
    except requests.RequestException as exc:
        # Raised, not swallowed. The loop turns this into an honest "try again"
        # instead of letting the model invent a status.
        raise RuntimeError("orders api unavailable") from exc


def _safe(order: dict) -> dict:
    return {k: order[k] for k in SAFE_FIELDS if k in order}


def get_shipment_status(order_id: str) -> dict:
    """Look up one order in the customer's Orders API."""
    resp = _get(f"/orders/{order_id}")
    # A missing order is an answer, not an outage.
    if resp.status_code == 404:
        return {"error": "order not found"}
    resp.raise_for_status()
    return _safe(resp.json())


def find_order_by_phone(phone: str):
    """
    WhatsApp customers have no order number, but we have the number they wrote
    from. Support finds them through GET /orders?phone=..., which the API docs
    never mention. Returns the order(s) with the same allow-list, or None.
    """
    resp = _get("/orders", phone=phone)
    resp.raise_for_status()
    orders = resp.json().get("orders", [])
    if not orders:
        return None
    if len(orders) == 1:
        return _safe(orders[0])
    # One phone, several orders: the customer hears about all of them.
    return {o["order_id"]: ", ".join(f"{k} {v}" for k, v in _safe(o).items())
            for o in orders}
