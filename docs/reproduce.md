# Reproducing the artefacts

Exact commands from a fresh clone. Each step says what it needs. Costs are from the saved metrics files, not estimates for your account; model prices are in `specs/prices.yaml`.

**Reruns are not bit-reproducible.** The model requests set no temperature, top_p or seed, so a rerun can differ from a saved run. Historic runs did not record sampling values; new `agent-exp` and `threat-test` runs write a `sampling` block (model, prompt files and SHA-256, max tokens, `provider-default` where unset, no seed, timestamp) into their metrics files.

```bash
git clone <repository-url> labourlens && cd labourlens
make setup        # uv sync --frozen: Python 3.12 and the locked dependencies (needs the package index once)
make verify       # lint, offline tests, docs links, rights scan, secrets scan
```

`make verify` needs no API key, no private data and no paid call. On a clone, `rights-scan` prints `NOT CHECKED` (there is no source text to compare with), and `secrets-scan` runs gitleaks only if it is installed. A fresh-clone run is recorded in [`fresh-clone-check.md`](fresh-clone-check.md).

## What each artefact needs

| Artefact | Command | Needs | Expected result | Cost |
|---|---|---|---|---|
| Offline test suite | `make test` | checkout only | 1027 passed, 57 deselected (1 Nov 2026, `uv run pytest -q -m 'not corpus'`) | none |
| Corpus tests | `make test-corpus` | private corpus | 56 tests pass | none |
| Report data for the site | `make report` (`uv run labourlens build-report`) | checkout only | rewrites `web/static/data/report.json` from committed artefacts; the file in git is the output of this command | none |
| Report and deck, static chapters | `make serve`, open `http://127.0.0.1:8000/` | checkout only | the ten report chapters and the deck; the live workbench needs the corpus and an API key | none |
| Docs link check | `make docs-check` | checkout only | `0 problem(s)` | none |
| Statistical store, EDA, export | `uv run labourlens fetch && uv run labourlens build && uv run labourlens eda && uv run labourlens export` | network; rewrites generated files | manifest, snapshots, `data/processed/`, figures. Do not run on a checkout whose `data/` you want to keep. | none |
| Documents and passages | `uv run labourlens fetch --kind documents`, then `build` | network, time; the MOM and MTI files are not redistributed | local `data/raw/`, `data/passages/` (gitignored) | none |
| MCP protocol demo | `uv run labourlens mcp-demo` | the statistics store | writes `data/runs/mcp-demo-transcript.md` (gitignored; `--out docs/mcp-demo-transcript.md` overwrites the committed record) | none |
| MCP-backed agent run | `uv run labourlens mcp-agent-demo` | corpus, `OPENAI_API_KEY` | rewrites `artifacts/mcp-agent-demo.md`; recorded run cost about $0.001 | paid, small |
| Re-score a frozen run, no judge | `uv run labourlens eval --exp agent-dev-A3 --no-judge --gold experiments/gold/archive/gold-v3.5.jsonl` | `data/runs/` (raw outputs, not in git) | metrics identical to the committed ones | none |
| A new dev experiment | `uv run labourlens agent-exp --split dev --tag SMOKE --pairs gpt-6-luna`, then `eval --exp agent-dev-SMOKE` | corpus, `OPENAI_API_KEY` | new files; refuses an existing id | paid. For scale: saved X2 metrics show $0.00285 per case for `gpt-6-luna` and $0.00463 for `gpt-5.6-luna`, plus judge cost $0.243 and $0.2689 for the 237 cases |
| Threat suite | `uv run labourlens threat-test` | corpus, `OPENAI_API_KEY` | per-case results under `experiments/threats/` | paid |
| Held-out v2 paired comparison | `uv run labourlens paired ...` (see `docs/experiments/m7-heldout-v2-result.md`) | saved scores | `experiments/heldout-v2/paired.json` | none |

Published numbers come from saved outputs. Re-running a model gives different outputs; that is expected and does not change the published results. Do not use `--force` on a registered experiment: it overwrites frozen evidence.

## Verifying hashes

Frozen gold files and their hashes are listed in [`experiments/gold/CHANGELOG.md`](../experiments/gold/CHANGELOG.md) and [`experiments/heldout-v2/FREEZE.md`](../experiments/heldout-v2/FREEZE.md).

```bash
shasum -a 256 experiments/gold/gold_v3.7.jsonl experiments/gold/heldout_v2_v1.jsonl experiments/gold/draft_cases.jsonl
shasum -a 256 data/processed/observations.parquet specs/prices.yaml
```

Compare the output with those two files. `eval` and `paired` refuse a gold file whose SHA-256 differs from the one recorded with the run unless `--allow-gold-mismatch` is passed. With the corpus, `make test-corpus` re-hashes every raw file against `data/manifests/manifest.json`.

## What a clone cannot reproduce

- Anything that reads MOM or MTI text (passages, retrieval indexes, live answers about report content): the documents are not redistributed. The statistical datasets, manifests, saved scores and reports are in git.
- Three datasets whose raw CSVs are gitignored (licence not verified); their derived rows are in `observations.parquet`, so a rebuild from a clone stops at those files (`docs/data-sheet.md`, section 9).
- Raw model outputs (`data/runs/`) are not in git; committed experiment files hold scores, metrics and short judge notes.
- The live site needs the corpus, an API key and the server secrets (`docs/deploy.md`).
