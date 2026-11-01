# Fresh-clone check

How a clone of this repository behaves without the private corpus, and what was observed.

Procedure: `git clone <this repository> /tmp/<dir>`, check out the branch, then `make setup && make verify` in the clone. No `.env`, no `data/raw`, `data/passages` or `data/index`, no API key.

## Observed result (1 Nov 2026, clone of commit `71c6482`, macOS, Python 3.12.12)

| Command | Observed |
|---|---|
| `make setup` | locked environment installed from `uv.lock` (needs the package index) |
| `make lint` | `All checks passed!` |
| `make test` | `785 passed, 1 skipped, 56 deselected, 5 warnings in 136.94s`. The skip is `tests/web/test_runtime_fixes.py` ("no local passages to compare with"). The 5 warnings are SWIG deprecation notices from a dependency. |
| `make docs-check` | `docs-check: 0 problem(s) in 165 Markdown files` |
| `make rights-scan` | `NOT CHECKED. .../data/passages is absent, so there is no source text to compare against.` Exit 0; with `RIGHTS_FLAGS=--require-corpus` it exits 2. This is not a pass. |
| `make secrets-scan` | no private corpus, PDF or `.env` file tracked; `gitleaks`: `98 commits scanned ... no leaks found` |
| `LABOURLENS_DEMO_ENABLED=false uv run labourlens serve` then `GET /`, `/workbench`, `/deck`, `/static/data/report.json`, `/healthz` | HTTP 200 on each; `/api/status` returned `{"enabled":false,"authenticated":false}` (report-only mode) |

Not checked in the clone: the live workbench (needs the corpus, an API key and server secrets), the 56 corpus-marked tests, the rights scan against source text. Those were run in the author's working tree: `make test-corpus` gave `56 passed` and `labourlens rights-scan` reported 0 hits against the local passages (1 Nov 2026).

The earlier simulation (tracked files copied without `.git`) failed `tests/evaluation/test_integrity.py::test_provenance_fingerprints` because no git HEAD existed; in a real clone it passes.
