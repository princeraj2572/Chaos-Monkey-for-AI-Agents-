PYTHON ?= python

.PHONY: test
test:
	$(PYTHON) -m unittest discover -s tests -t .

.PHONY: demo
demo:
	$(PYTHON) -m chaos_monkey compare --seed 1 --out out
	@echo "Report: out/report.html"
