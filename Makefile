# Requires an xAI API key in a .env file (XAI_API_KEY=...) for `run` and `cli`.

VENV ?= invoice_agent_env
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
ALEMBIC := $(VENV)/bin/alembic
INVOICE ?= data/invoices/invoice_1013.pdf

.PHONY: help setup venv install seed run cli test clean

help:
	@echo "PayPilot — make targets:"
	@echo "  make setup    First-time setup: create venv, install deps, seed the database"
	@echo "  make install  Install Python dependencies into the venv"
	@echo "  make seed     Delete the database, recreate the schema, then load inventory + merchants"
	@echo "  make run      Launch the Streamlit app"
	@echo "  make cli      Process one invoice (INVOICE=data/invoices/<file>)"
	@echo "  make test     Run the unit tests"
	@echo "  make clean    Delete the local database"

setup: venv install seed
	@echo "Setup complete. Add your XAI_API_KEY to a .env file, then run 'make run'."

venv:
	python3.11 -m venv $(VENV)

install:
	$(PIP) install -r requirements.txt

seed:
	rm -f data/acme.db
	$(ALEMBIC) upgrade head
	$(PY) migrations/seed.py

run:
	$(PY) -m streamlit run app.py

cli:
	$(PY) main.py --invoice_path=$(INVOICE)

test:
	$(PY) -m pytest -q

clean:
	rm -f data/acme.db
