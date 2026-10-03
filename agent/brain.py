"""
The model. Two backends; mock is the default and the one that matters.

MOCK (default) is deterministic and needs no network, no keys and no money. It is
not a toy: it behaves the way a real model behaves on this task, which means it
reproduces the failures you are here to find.

Specifically, the mock brain will:
  - answer in English unless your system prompt tells it otherwise
  - repeat back whatever fields your tool hands it, including ones it shouldn't
  - invent a plausible status if the tool raises and you swallowed the error
  - guess at an order it was never given, unless told not to
  - answer complaints and refund requests itself, unless told to escalate them

Every one of those is your bug, not the mock's. Fix them in tools.py and prompt.md.

LIVE is an upgrade you earn once mock is green. Set LLM_BASE_URL and LLM_API_KEY.
"""
import json
import os
import re

AR = re.compile(r"[؀-ۿ]")


def _speaks_arabic(prompt: str) -> bool:
    p = prompt.lower()
    return ("arabic" in p and "repl" in p) or "same language" in p or "customer's language" in p


def _forbids_guessing(prompt: str) -> bool:
    p = prompt.lower()
    return "do not guess" in p or "don't guess" in p or "ask for it" in p or "ask for the order" in p


COMPLAINT = re.compile(r"refund|damaged|broken|complain|compensat|استرجاع|استرداد|تالف|شكوى|تعويض", re.I)


def _escalates(prompt: str) -> bool:
    p = prompt.lower()
    return ("escalat" in p or "support team" in p or "human" in p
            or "hand it" in p or "pass it" in p or "refund" in p or "complain" in p)


def _mock(system_prompt: str, user_msg: str, tool_result, tool_error) -> str:
    arabic_in = bool(AR.search(user_msg))
    reply_ar = arabic_in and _speaks_arabic(system_prompt)

    if COMPLAINT.search(user_msg) and _escalates(system_prompt):
        # Told to hand complaints to a human. It does, and says nothing else.
        return ("نأسف لذلك. تم تحويل طلبك إلى فريق الدعم وسيتواصل معك أحدهم اليوم."
                if reply_ar else
                "I'm sorry about this. I've passed it to our support team and someone will contact you today.")

    if tool_error is not None:
        # You caught it and handed us an error. Say so honestly.
        return ("عذراً، لا أستطيع الوصول إلى حالة الشحنة الآن. يرجى المحاولة مرة أخرى."
                if reply_ar else
                "Sorry — I can't reach shipment status right now. Please try again shortly.")

    if tool_result is None:
        # No tool ran. Either no order id, or you never called it.
        if re.search(r"JJ-?\d{4}", user_msg, re.I) is None:
            if _forbids_guessing(system_prompt):
                return ("هل يمكنك تزويدي برقم الطلب؟" if reply_ar
                        else "Could you give me your order number so I can check?")
            # Told nothing, so it guesses. This is the failure.
            return ("شحنتك في الطريق ومن المتوقع وصولها يوم الخميس."
                    if reply_ar else
                    "Your shipment is on its way and should arrive Thursday.")
        return ("لا أملك صلاحية الوصول إلى معلومات الطلب."
                if reply_ar else
                "I don't have access to order information.")

    if isinstance(tool_result, dict) and tool_result.get("error"):
        return ("لم أتمكن من العثور على هذا الطلب. هل الرقم صحيح؟"
                if reply_ar else
                "I couldn't find that order — can you double-check the number?")

    # The honest part: we echo exactly what you gave us.
    fields = ", ".join(f"{k}: {v}" for k, v in tool_result.items()) \
        if isinstance(tool_result, dict) else str(tool_result)
    return (f"إليك تفاصيل شحنتك — {fields}" if reply_ar
            else f"Here's your shipment — {fields}")


def think(system_prompt: str, user_msg: str, tool_result=None, tool_error=None) -> str:
    if os.environ.get("LLM_BASE_URL") and os.environ.get("LLM_API_KEY"):
        return _live(system_prompt, user_msg, tool_result, tool_error)
    return _mock(system_prompt, user_msg, tool_result, tool_error)


def _live(system_prompt, user_msg, tool_result, tool_error):
    import requests
    ctx = []
    if tool_result is not None:
        ctx.append(f"Tool returned: {json.dumps(tool_result)}")
    if tool_error is not None:
        ctx.append(f"Tool failed: {tool_error}")
    r = requests.post(
        os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['LLM_API_KEY']}"},
        json={"model": os.environ.get("LLM_MODEL", "gpt-4o-mini"),
              "messages": [{"role": "system", "content": system_prompt},
                           {"role": "user", "content": user_msg + "\n\n" + "\n".join(ctx)}]},
        timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
