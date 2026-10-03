.DEFAULT_GOAL := help
SHELL  := /bin/bash
SYS_PY ?= python3
VENV   := .venv
PY     := $(VENV)/bin/python
PORT   ?= 8081
KEY    := njm_team_key

# Use uv if it's installed (faster), otherwise plain python3 -m venv + pip.
HAS_UV := $(shell command -v uv 2> /dev/null)

help:
	@echo ""
	@echo "  make setup    create .venv, install the one dependency"
	@echo "  make login    TEAM=falcon   write your team's .env"
	@echo "  make api      start the customer's Orders API (leave running)"
	@echo "  make run      chat with your agent by hand"
	@echo "  make eval     run the customer's 20 tickets"
	@echo "  make eval2    round 2: yesterday's tickets (once you're at 20/20)"
	@echo "  make eval3    round 3: edge cases (angry, ownership, PII, format)"
	@echo "  make guided   swap in a working tool if you are stuck"
	@echo "  make mine     put your own tool back"
	@echo ""
	@echo "  Everything runs offline. No keys to find, no network, no spend."
	@echo ""

setup:
ifdef HAS_UV
	@echo "using uv"
	@uv venv -q --allow-existing $(VENV)
	@uv pip install -q --python $(PY) -r requirements.txt && echo "ready"
else
	@echo "uv not found, using python3 -m venv"
	@test -x $(PY) || $(SYS_PY) -m venv $(VENV) || { echo ""; \
		echo "  Could not create .venv. On Ubuntu/Debian run: sudo apt install python3-venv"; \
		echo ""; exit 1; }
	@$(PY) -m pip install -q --disable-pip-version-check -r requirements.txt && echo "ready"
endif

login:
	@test -n "$(TEAM)" || { echo "usage: make login TEAM=falcon"; exit 1; }
	@printf 'TEAM=%s\nORDERS_API=http://127.0.0.1:%s\nORDERS_KEY=%s\n' \
		"$(TEAM)" "$(PORT)" "$(KEY)" > .env
	@echo "team $(TEAM) — wrote .env"
	@echo "the Orders API URL and key are in there."

api: _check_venv
	@ORDERS_API_FAULT=$(FAULT) ORDERS_API_PORT=$(PORT) $(PY) customer/orders_api.py

run: _check_venv _check_env _check_api
	@set -a && source .env && set +a && $(PY) -m chat

eval: _check_venv _check_env _check_api
	@set -a && source .env && set +a && $(PY) evals/run.py

eval2: _check_venv _check_env _check_api
	@set -a && source .env && set +a && $(PY) evals/run.py evals/tickets2.json

eval3: _check_venv _check_env _check_api
	@set -a && source .env && set +a && $(PY) evals/run.py evals/tickets3.json

guided:
	@test -f agent/tools.py.mine || cp agent/tools.py agent/tools.py.mine
	@cp .guided/tools.py agent/tools.py
	@echo "guided tool swapped in. yours is safe at agent/tools.py.mine"
	@echo "read it: the four decisions are commented."
	@echo "not at 20/20 after this? the rest is in agent/prompt.md."

mine:
	@test -f agent/tools.py.mine && mv agent/tools.py.mine agent/tools.py && echo "your tool is back" || echo "nothing to restore"

_check_venv:
	@test -x $(PY) || { echo ""; echo "  No .venv yet. Run:  make setup"; echo ""; exit 1; }

_check_env:
	@test -f .env || { echo ""; echo "  No .env yet. Run:  make login TEAM=yourteam"; echo ""; exit 1; }

_check_api:
	@curl -s --max-time 2 http://127.0.0.1:$(PORT)/health > /dev/null \
		|| { echo ""; echo "  The customer's Orders API is not running."; \
		     echo "  Open another terminal and run:  make api"; echo ""; exit 1; }

.PHONY: help setup login api run eval eval2 eval3 guided mine _check_venv _check_env _check_api
