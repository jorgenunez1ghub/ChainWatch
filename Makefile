PYTHON ?= python3
PYTHONPATH := src
SCENARIOS := data/scenarios.json
MANIFEST := results/v0.1-initial.json
RERUN_OUTPUT ?=

.PHONY: test run-baseline check-integrity check-manifest verify

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover -s tests -v

run-baseline:
	@test -n "$(RERUN_OUTPUT)" || { echo 'Set RERUN_OUTPUT to a new replay file; v0.1-initial.json is frozen.' >&2; exit 1; }
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/chainwatch/freeze.py replay --output "$(RERUN_OUTPUT)"

check-integrity:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) src/chainwatch/freeze.py check

check-manifest:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m chainwatch.cli verify --scenarios $(SCENARIOS) --manifest $(MANIFEST)

# Keep integrity first even with make -j: never execute changed frozen source.
verify: check-integrity
	$(MAKE) test
	$(MAKE) check-manifest
