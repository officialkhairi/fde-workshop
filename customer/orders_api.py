"""
Jaldi Jaldi Express — Orders API.

This is the CUSTOMER'S system. You do not own it, you cannot change it, and it was
written fifteen years ago by someone who has left. It fronts an on-prem SQL Server.

Run it:      make api          (or python3 customer/orders_api.py)
Health:      GET  /health
Lookup:      GET  /orders/{order_id}      header: x-api-key

Fault injection for the curveball is controlled by the facilitator:
    ORDERS_API_FAULT=timeout   one call in three crawls to 8s
"""
import json
import os
import random
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PORT = int(os.environ.get("ORDERS_API_PORT", "8081"))
VALID_KEYS = {"njm_live_7f3a9c", "njm_team_key"}
DATA = json.loads((Path(__file__).parent / "data" / "orders.json").read_text())


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # quiet; the workshop has enough noise

    def _send(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"ok": True})

        if self.path.startswith("/orders?"):
            return self._by_phone()

        if not self.path.startswith("/orders/"):
            return self._send(404, {"error": "not found"})

        if self.headers.get("x-api-key") not in VALID_KEYS:
            return self._send(401, {"error": "missing or invalid x-api-key"})

        # The curveball. One call in three crawls.
        # 8s is chosen deliberately: long enough that a caller with no timeout
        # visibly stalls, short enough that a 20-ticket run still finishes inside
        # the block. A team with a 3s timeout degrades in milliseconds instead.
        if os.environ.get("ORDERS_API_FAULT") == "timeout" and random.random() < 0.34:
            time.sleep(8)

        order_id = self.path.split("/orders/", 1)[1].strip().upper()

        # One record is locked by the nightly reconciliation job. Reads on it
        # block until the lock clears. Nobody has fixed this in years.
        if order_id == "JJ-4480":
            time.sleep(8)

        order = DATA.get(order_id)
        if not order:
            return self._send(404, {"error": "order not found", "order_id": order_id})

        # Note what comes back. All of it. Every time.
        return self._send(200, {"order_id": order_id, **order})

    def _by_phone(self):
        # Not in the docs above. The support team uses it through the old desktop
        # tool, which is how they find customers who have no order number. You
        # find out it exists by asking them, or by reading this file.
        #   GET /orders?phone=+966-56-904-4475     header: x-api-key
        if self.headers.get("x-api-key") not in VALID_KEYS:
            return self._send(401, {"error": "missing or invalid x-api-key"})
        from urllib.parse import parse_qs, urlparse
        phone = parse_qs(urlparse(self.path).query).get("phone", [""])[0]
        digits = "".join(ch for ch in phone if ch.isdigit())
        found = [{"order_id": oid, **o} for oid, o in DATA.items()
                 if "".join(ch for ch in o["customer_phone"] if ch.isdigit()) == digits]
        return self._send(200, {"orders": found})


if __name__ == "__main__":
    fault = os.environ.get("ORDERS_API_FAULT")
    print(f"Jaldi Jaldi Orders API on :{PORT}" + (f"  [FAULT: {fault}]" if fault else ""))
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
