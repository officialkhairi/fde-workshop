"""
Your tool. This is the only code file you need to change.

Four TODOs. Each one maps to something that will bite you later if you skip it.
"""
import os
import re

import requests

ORDERS_API = os.environ.get("ORDERS_API", "http://127.0.0.1:8081")
ORDERS_KEY = os.environ.get("ORDERS_KEY", "")


def find_order_id(message: str):
    """Pull an order reference out of a customer message. Returns None if absent."""
    m = re.search(r"JJ-?\s?(\d{4})", message, re.I)
    return f"JJ-{m.group(1)}" if m else None


def get_shipment_status(order_id: str) -> dict:
    """
    Look up one order in the customer's Orders API.

    TODO 1 — Call it.
        GET {ORDERS_API}/orders/{order_id}
        Header: x-api-key: {ORDERS_KEY}
        The URL and key are in your .env (make login).

    TODO 2 — Handle failure.
        This API fronts a fifteen-year-old SQL Server. It is slow, it is sometimes
        down, and it is about to get worse. Decide what a timeout means, and what
        your caller should see when the order genuinely does not exist.

    TODO 3 — Decide what to return.
        Look at the full response before you pass it on. The agent will repeat back
        whatever you hand it. Every field. To the customer.
    """
    resp = requests.get(f"{ORDERS_API}/orders/{order_id}",
                        headers={"x-api-key": ORDERS_KEY})
    return resp.json()


def find_order_by_phone(phone: str):
    """
    Some customers write in on WhatsApp. Their message has no order number, but
    you have the number they wrote from.

    TODO 4 — Find their order without an order number.
        How do Jaldi Jaldi's support agents do this today? Ask them.
        Return the order (same rules as TODO 3), or None if you can't.
    """
    return None
