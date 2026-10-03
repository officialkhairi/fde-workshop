# Jaldi Jaldi Express — FDE Skills Lab

You are the forward deployed engineer. Jaldi Jaldi Express wants an AI agent for customer
support, live in thirty days.

There is already an agent. It demos well and gets 12 of Jaldi Jaldi's 20 real tickets wrong.
Fixing it is your job. Some of what you need is in this repo. Some of it is only in the
heads of the people who answer Jaldi Jaldi's support messages every day — go and ask them.

---

## Setup — two minutes

```bash
make setup                    # installs one dependency
make api                      # terminal 1: the customer's system. leave it running
make login TEAM=falcon        # terminal 2: writes your .env
make run                      # talk to your agent
```

**Everything runs offline.** No keys, no network calls to anyone, no spend. Mock mode is
the starting state, not a fallback — get it green here before anyone thinks about a live
model.

---

## What you change

Two files. That's all.

| File | Your job |
|---|---|
| `agent/tools.py` | Four TODOs. Call the customer's API, handle it failing, decide what comes back, find customers who have no order number |
| `agent/prompt.md` | How the agent should answer. Shorter than you think |

Everything else — `agent/loop.py`, `agent/brain.py`, `customer/` — is not yours to change.
`customer/` in particular is the customer's system. You do not own it, you cannot change
it, and that is the entire point.

---

## The loop

```bash
make run      # try it by hand. does it work for one message?
make eval     # twenty real tickets. does it work for twenty?
```

`make eval` is the one that matters. It sends twenty messages from Jaldi Jaldi's actual queue —
English and Arabic, some with no order number, two from WhatsApp, some fishing for things
a customer should never see — and tells you what broke.

**Read the failures before you fix anything.** They come out grouped. The group with the
most failures is rarely the one that would hurt Jaldi Jaldi most.

---

## If you get stuck

```bash
make guided   # swaps in a working tool. yours is kept safe
make mine     # puts yours back
```

No prize for suffering. Take the guided branch, read why it makes the four decisions it
makes, then carry on. A team stuck for forty minutes learns less than a team that read a
good answer in four.

---

## Things worth knowing

**The agent repeats whatever your tool hands it.** Every field, to the customer. Look at a
full API response before you decide what to return.

**The Orders API fronts a fifteen-year-old SQL Server.** It is slow, it is sometimes down,
and it may get worse during the session. Decide now what a timeout should mean.

If the customer tells you their order system is playing up, you can reproduce it:

```bash
make api FAULT=timeout      # one call in three crawls
```

Run your tickets again with that on. What your agent says to a customer when it cannot
check is a decision, not an accident.

**Some tickets can't be fixed from the code alone.** If you're stuck at 18/20 and the
failures say "came in on WhatsApp", the answer isn't in this repo's docs. Ask how Jaldi Jaldi's
support agents handle it today.

**Mock mode is not a toy.** It reproduces the failures a real model makes on this task. If
the eval says the agent invented a shipment status, it invented one, and that is your bug
rather than the mock's.

---

## Round 2

At 20/20? Run `make eval2`. Eight messages from yesterday's queue that the first twenty
didn't cover. Same rules: you change `agent/tools.py` and `agent/prompt.md`, nothing else.
Read the failures before you fix anything.

---

## Afterwards

This repo keeps working. The customer's API, the ticket set and the eval harness all run
on your laptop with no account and no key, for as long as you want them.

Try: what did those twenty tickets *not* test?
