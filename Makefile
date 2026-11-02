# One entry point for setup, checks and common tasks. `make verify` runs everything that works offline from a fresh clone.
# The private corpus (data/raw, data/passages, data/index) is not in git: targets that need it say so and are marked below.

UV ?= uv
RIGHTS_FLAGS ?=

.PHONY: help setup lint format test test-corpus notebooks rights-scan secrets-scan docs-check report serve verify clean

help:
	@echo "setup         install the locked dependencies (uv sync --frozen)"
	@echo "lint          ruff, correctness rules only (pyflakes and syntax errors)"
	@echo "format        apply ruff's safe automatic fixes for those rules; no code formatter is enforced"
	@echo "test          pytest without the corpus-marked tests (offline, no API key)"
	@echo "test-corpus   the corpus-marked tests; needs the private local corpus"
	@echo "notebooks     execute and save offline walkthroughs using optional Jupyter packages (no API key or private corpus)"
	@echo "rights-scan   quote check against local MOM/MTI text; prints NOT CHECKED without it (RIGHTS_FLAGS=--require-corpus to fail instead)"
	@echo "secrets-scan  tracked-file leak guard, plus gitleaks over history when installed"
	@echo "docs-check    relative links and heading anchors in the tracked Markdown files"
	@echo "report        rebuild web/static/data/report.json from the committed artefacts"
	@echo "serve         serve the report and workbench on 127.0.0.1:8000"
	@echo "verify        lint, test, docs-check, rights-scan, secrets-scan"
	@echo "clean         remove caches"

setup:
	$(UV) sync --frozen

lint:
	$(UV) run ruff check src tests scripts

format:
	$(UV) run ruff check --fix src tests scripts

test:
	$(UV) run pytest -q -p no:cacheprovider -m 'not corpus'

test-corpus:
	$(UV) run pytest -q -p no:cacheprovider -m corpus

notebooks:
	$(UV) run --with jupyter --with nbconvert jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=180 notebooks/01_data_and_eda.ipynb notebooks/02_evaluation_walkthrough.ipynb

rights-scan:
	$(UV) run labourlens rights-scan $(RIGHTS_FLAGS)

secrets-scan:
	@leaked="$$(git ls-files 'data/raw' 'data/passages' 'data/index' 'data/runs' 'data/feedback' 'data/audit' '*.pdf' '.env' '.env.*' | grep -v -x -e '.env.example' -e 'deploy/.env.example' || true)"; \
	if [ -n "$$leaked" ]; then echo "tracked files that must stay out of git:"; echo "$$leaked"; exit 1; fi; \
	echo "secrets-scan: no private corpus, PDF or .env file is tracked"
	@if command -v gitleaks >/dev/null 2>&1; then gitleaks git --redact --no-banner -c .gitleaks.toml; \
	else echo "secrets-scan: gitleaks is not installed; history was NOT scanned (https://github.com/gitleaks/gitleaks)"; fi

docs-check:
	$(UV) run python scripts/check_docs.py

report:
	$(UV) run labourlens build-report

serve:
	$(UV) run labourlens serve

verify: lint test docs-check rights-scan secrets-scan

clean:
	rm -rf .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -not -path './.venv/*' -prune -exec rm -rf {} +
