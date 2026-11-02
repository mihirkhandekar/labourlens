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

## Final two-run headline and 2 Nov measurements (D-061)

The [FIN2 pre-registration](experiments/fin2-replicate.md) was amended before results to use the mean of two runs. Both single runs remain visible. The commands below document reproduction, not commands executed by this documentation pass. Paid commands require the private corpus and a key. Existing tags below are frozen: substitute a new tag/destination for a new experiment, never use `--force`. The relative-date probes are anchored to 2 Nov 2026; a different date requires a newly declared fixture rather than silently reusing their expected labels.

### Final aggregate (offline, no model calls)

```sh
uv run python scripts/final_mean.py
```

This reads committed FIN/FIN2 scored cases and writes `experiments/eval/final-mean.json`. It asserts identical case membership within each repeated arm, averages each case's two binary outcomes, and computes paired 95% case-bootstrap intervals with 10,000 resamples and seed 20261030. It also saves both run costs, medians and all-case false-answer/over-abstention rates. Mean-of-medians is not pooled p50, and two runs are not a variance estimate. Run only on a disposable reproduction checkout if you need to preserve the existing generated file unchanged.

### Tagged current-corpus retrieval (paid reranking/possible embeddings)

```sh
uv run labourlens retrieval-exp2 --tag V31
```

Historical command, now refuses because V31 exists. Use a new tag for a new run. It writes isolated corpus/model-keyed caches, per-configuration directories `dev-R-<tag>-R*` and a sibling summary directory. Saved [V31 summary](../experiments/runs/dev-R-V31/SUMMARY.md) records 1,847 chunks, gold v3.6 and the actual corpus hash. Do not overwrite or pool the frozen v1 ladder.

### Served research chain (paid generation and judging)

Historical commands, one run per model and arm:

```sh
uv run labourlens served-exp --split dev --gold experiments/served/mixed-sample.jsonl --pairs gpt-6-luna gpt-5.6-luna --tag S65-mcp-on --retrieval r3 --route mcp --web-steps on
uv run labourlens served-exp --split dev --gold experiments/served/mixed-sample.jsonl --pairs gpt-6-luna gpt-5.6-luna --tag S65-direct-on --retrieval r3 --route direct --web-steps on
uv run labourlens served-exp --split dev --gold experiments/served/mixed-sample.jsonl --pairs gpt-6-luna gpt-5.6-luna --tag S65-direct-off --retrieval r3 --route direct --web-steps off
uv run labourlens eval --exp served-dev-S65-mcp-on --split dev --gold experiments/served/mixed-sample.jsonl --labels gpt-6-luna gpt-5.6-luna
uv run labourlens eval --exp served-dev-S65-direct-on --split dev --gold experiments/served/mixed-sample.jsonl --labels gpt-6-luna gpt-5.6-luna
uv run labourlens eval --exp served-dev-S65-direct-off --split dev --gold experiments/served/mixed-sample.jsonl --labels gpt-6-luna gpt-5.6-luna
uv run labourlens paired --gold experiments/served/mixed-sample.jsonl --candidate served-dev-S65-mcp-on --baseline served-dev-S65-direct-on --models gpt-6-luna gpt-5.6-luna --out experiments/served/paired-S65-direct-on.json
uv run labourlens paired --gold experiments/served/mixed-sample.jsonl --candidate served-dev-S65-mcp-on --baseline served-dev-S65-direct-off --models gpt-6-luna gpt-5.6-luna --out experiments/served/paired-S65-direct-off.json
```

Scoring/paired commands need saved raw or scored rows; judging is paid, paired analysis offline. Mixed n=65 comprises 51 stratified reused development gold plus 8 diversion/6 context probes, not 65 new gold cases. The web-on route comparison is the matched-factor comparison; web-off changes route and front steps together. The paired command's generic adoption verdict is not the served protocol's H1/H2 verdict. Exact-case FIN and matched-call numerical-audit commands are in the [served registration](experiments/served-chain-eval.md); those require private raw records for matched-call auditing. Browser HTTP admission, login and rights projection are not evaluated by this harness.

### T-I06 scorer v2 (offline diagnostics versus paid fresh generation)

Historical commands, all destinations already exist. Use new destination ids for any further work:

```sh
uv run labourlens threat-test --rescore --source-experiment . --experiment ti06-v2-original-20261102 --scorer v2
uv run labourlens threat-test --rescore --source-experiment m7-ti06-postfix-20261031 --experiment ti06-v2-postfix-20261102 --scorer v2
uv run labourlens threat-test --rescore --source-experiment m7-e2efix-20261031 --experiment ti06-v2-e2efix-20261102 --scorer v2
uv run labourlens threat-test --models gpt-6-luna gpt-5.6-luna --experiment ti06-v2-fresh-20261102 --scorer v2
uv run labourlens threat-test --models gpt-6-luna gpt-5.6-luna --ablation naive --experiment ti06-v2-fresh-20261102 --scorer v2
```

The first three commands need private saved answers, no model calls; outputs are post-hoc diagnostics. The last two make paid calls on the known 36-case suite and save both scorer verdicts. V1 remains default and all registered historical scores stay unchanged. [Rule declaration](experiments/t-i06-scorer-v2-rule.md), [fresh results](../experiments/threats/ti06-v2-fresh-20261102/SUMMARY.md). A fresh clone can inspect committed metrics/scores, but cannot reproduce raw-answer diagnostics without the private outputs.

## Second-family judge check (D-062)

The [declaration and continuation amendment](experiments/second-judge.md) describe the saved `sonnet55-FIN-s60-b-20261102` experiment. This documentation pass did not run these commands. A clone can read the committed [summary](../experiments/xjudge/sonnet55-FIN-s60-b-20261102/SUMMARY.md) and `summary.json`; a new judging run needs the private saved raw outputs, `ANTHROPIC_API_KEY` and a new experiment ID.

```sh
uv run labourlens judge-xfamily --experiment sonnet55-FIN-s60-b-20261102 --summary
uv run labourlens judge-xfamily --experiment <new-id> --dry-run
```

The summary command reads saved paired and agreement output only. The dry-run makes no API call and prints a token and list-price heuristic, not a bill. A paid execution is deliberately not part of the reproduction path here; if it is needed, use a new immutable ID and an explicit `--max-usd`, never overwrite an existing ID.
