# make run   -> install (first time only), download (first time only), start all cameras
# make test  -> run the unit tests
# Extra options for the service:  make run ARGS="--duration 300"

PYTHON = .venv/bin/python

.PHONY: run download test

run: .venv download
	$(PYTHON) -m app.main $(ARGS)

download:
	bash scripts/download.sh

test: .venv
	$(PYTHON) tests/test_line_counter.py
	$(PYTHON) tests/test_zones_alerts.py

# Re-created only when requirements.txt changes
.venv: requirements.txt
	python3.11 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	touch .venv
