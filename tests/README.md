# Tests

Run from the repository root.

| Command | What it runs | Needs |
|---|---|---|
| `make test` (`uv run pytest -q -m 'not corpus'`) | The supported suite for a fresh clone (the current count is in `docs/progress.md`) | Nothing beyond `make setup`. No API key, no network, no private data. |
| `make test-corpus` (`uv run pytest -q -m corpus`) | 56 tests that read the private local corpus (`data/raw`, `data/passages`, `data/index`, or built artefacts) | The corpus, which is gitignored for rights reasons. |

## Markers

`corpus` is the only marker (registered in `pyproject.toml`). Mark a test with `@pytest.mark.corpus`, or set `pytestmark` at module level, when it reads any file that is not tracked in git. `tests/conftest.py` also marks a short list of tests by name; prefer the explicit marker for new tests.

## What is skipped without the private data

- The 56 corpus-marked tests are deselected by `-m 'not corpus'`. In a clone without `data/`, a plain `uv run pytest -q` runs them too, and they skip or have nothing to check, so only the `not corpus` run is meaningful there.
- `tests/web/test_runtime_fixes.py` has one inline skip ("no local passages to compare with") that still shows up in a clone.
- `labourlens rights-scan` compares tracked files with the local MOM/MTI passages. Without them it prints `NOT CHECKED`; its own tests use synthetic passages and do run.

## What the suite does and does not show

- It checks code behaviour: parsing and validation, retrieval and scoring functions, the agent graph with scripted models, MCP client and server protocol behaviour, guards against prompt injection and secret leakage, deterministic calculations, the web app's routes and limits, and the integrity of frozen artefacts (hash checks between gold files and saved runs).
- It makes no paid model call. Saved experiment results are inputs to some tests; they are not regenerated.
- Passing tests do not validate model quality. Quality evidence is in `docs/evaluation-report.md`.
- Some tests pin frozen counts (for example 268 gold cases). They exist to catch an accidental change to a frozen artefact; a deliberate new gold version needs a deliberate test update.

Lint: `make lint` runs ruff with correctness rules only (`F`, `E9`).
