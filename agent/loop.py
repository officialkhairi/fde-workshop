"""
The agent loop. You do not need to change this file.

It reads your system prompt, offers your tool the message, and asks the model to
answer. That is all an agent is.
"""
from pathlib import Path

from . import brain, tools

PROMPT_PATH = Path(__file__).parent / "prompt.md"


def answer(user_msg: str, sender_phone: str = None) -> str:
    """sender_phone is set when the message came in over WhatsApp."""
    system_prompt = PROMPT_PATH.read_text()
    tool_result, tool_error = None, None

    order_id = tools.find_order_id(user_msg)
    try:
        if order_id:
            tool_result = tools.get_shipment_status(order_id)
        elif sender_phone:
            tool_result = tools.find_order_by_phone(sender_phone)
    except Exception as exc:                          # noqa: BLE001 - teams decide
        tool_error = f"{type(exc).__name__}: {exc}"

    return brain.think(system_prompt, user_msg, tool_result, tool_error)
