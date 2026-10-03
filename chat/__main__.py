"""Talk to your agent. Ctrl-C to stop.

To send a message as if it came in on WhatsApp, start the line with the sender's
number and a colon:   +973-39-455-4477: متى توصل شحنتي؟
"""
import re

from agent import loop

BOLD, DIM, OFF = "\033[1m", "\033[2m", "\033[0m"
WHATSAPP = re.compile(r"^\s*(\+[\d\- ]{7,}):\s*(.+)$")

print(f"\n{BOLD}Jaldi Jaldi Express support agent{OFF}  {DIM}(ctrl-c to quit){OFF}")
print(f"{DIM}try: Where is my shipment? Order JJ-4471{OFF}")
print(f"{DIM}try: وين شحنتي؟ رقم الطلب JJ-4471{OFF}")
print(f"{DIM}WhatsApp: +966-56-904-4475: is my delivery coming today?{OFF}\n")

try:
    while True:
        msg = input(f"{BOLD}you  {OFF}").strip()
        if not msg:
            continue
        m = WHATSAPP.match(msg)
        sender, text = (m.group(1).strip(), m.group(2)) if m else (None, msg)
        print(f"{BOLD}bot  {OFF}{loop.answer(text, sender)}\n")
except (KeyboardInterrupt, EOFError):
    print("\n")
