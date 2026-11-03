# Reproducing the artefacts

Exact commands from a fresh clone. Each step says what it needs. Costs are from the saved metrics files, not estimates for your account; model prices are in `specs/prices.yaml`.

**Reruns are not bit-reproducible.** Requests set no temperature, top_p or seed. Agent/served raw generation provenance records `sampling`; eval publishes this as `generation_sampling` in metrics. Threat-test metrics use `sampling`. Unset values are recorded as `provider-default`, not an invented temperature or seed.

Ids inside commands (for example `agent-dev-A3`, `S65`, `FIN`) are internal experiment names that must stay as they are; each is explained beside its command and in the [glossary](glossary.md). Tags starting `MY-` are placeholders for names you choose.

## Quick start — report and MCP, zero spend

Prerequisites: Git, uv, CPython 3.12 (uv can provision it) and make for make targets. No Node/npm, Docker, provider key or private corpus is needed. Clone the supplied repository URL and enter its root, then run:

```bash
make setup
make verify && uv run labourlens mcp-demo && uv run python scripts/final_mean.py
LABOURLENS_DEMO_ENABLED=false make serve
```

Open `http://127.0.0.1:8000/`, `/deck` and `/workbench`. Without make, install with `uv sync --frozen`; the direct app command is `LABOURLENS_DEMO_ENABLED=false uv run labourlens serve --host 127.0.0.1 --port 8000`.

`make verify` needs no key or paid call. In a public clone the rights scan prints `NOT CHECKED` (not a pass); history scanning is conditional on installed gitleaks. The clean-clone audit of `d8a0b0e` on 2 Nov 2026 recorded 1,100 passed, 1 skipped, 57 deselected; counts and durations are not acceptance targets. The detailed fresh-clone working record is kept locally, not in the repository. The documentation checker validates tracked relative links and anchors, not external URL availability, CLI flags or prose accuracy.

## What each artefact needs

| Artefact | Command | Needs | Expected result | Cost |
|---|---|---|---|---|
| Offline test suite | `make test` | checkout only | offline tests pass; `corpus`-marked tests are deselected | none |
| Corpus tests | `make test-corpus` | complete private corpus | corpus-marked tests pass | none |
| Report data for the site | `make report` (`uv run labourlens build-report`) | checkout only | rewrites `web/static/data/report.json` from committed artefacts; the file in git is the output of this command | none |
| Report and deck, static chapters | `make serve`, open `http://127.0.0.1:8000/` | checkout only | the ten report chapters and the deck; the live workbench needs the corpus and an API key | none |
| Docs link check | `make docs-check` | checkout only | `0 problem(s)` | none |
| Statistical store, EDA, export | `uv run labourlens fetch && uv run labourlens build && uv run labourlens eda && uv run labourlens export` | network; rewrites generated files | manifest, snapshots, `data/processed/`, figures. Do not run on a checkout whose `data/` you want to keep. | none |
| Documents and passages | `uv run labourlens fetch --kind documents`, then `uv run labourlens build` | network, time; the MOM and MTI files are not redistributed | local `data/raw/`, `data/passages/` (gitignored); corpus v4 has 106 document files including the 57 added by D-080 (`specs/sources.d/documents-2020-2022.yaml`) | none |
| MCP protocol demo | `uv run labourlens mcp-demo` | committed statistical store, manifest and snapshots; no private MOM/MTI corpus | writes gitignored `data/runs/mcp-demo-transcript.md`; leave committed transcript unchanged | none |
| MCP-backed agent run | `uv run labourlens mcp-agent-demo` | corpus, `OPENAI_API_KEY` | rewrites `artifacts/mcp-agent-demo.md`; recorded run cost about $0.001 | paid, small |
| Re-score saved raw answers, no judge (`agent-dev-A3` is the filter-then-rerank run, one of the five first-build development runs) | `uv run labourlens eval --exp agent-dev-A3 --no-judge --gold experiments/gold/archive/gold-v3.5.jsonl --force` | scratch checkout only, original private `data/runs/` records; deliberately replaces scratch evaluation output | deterministic rescoring, not restoration of judge metrics | none |
| A new development experiment (`MY-SMOKE` is a tag you choose) | `uv run labourlens agent-exp --split dev --tag MY-SMOKE --pairs gpt-6-luna`, then `eval --exp agent-dev-MY-SMOKE` | corpus, `OPENAI_API_KEY`; new unused tag | new files; refuses an existing id | paid; for scale, the saved regression check cost $0.00285/$0.00463 per case for generation, plus judge $0.243/$0.2689 per 237 cases |
| Threat suite | `uv run labourlens threat-test --experiment MY-THREATS-20261102 --models gpt-6-luna gpt-5.6-luna` | complete corpus, `OPENAI_API_KEY`; choose a new unused identifier | per-case results under `experiments/threats/` | paid requests |
| Final aggregation and paired comparisons | `uv run python scripts/final_mean.py`; full `paired` command below | committed scored rows, no private corpus/key | the two-run mean headline of the final evaluation, or separate paired diagnostics | none |
| Saved second-family summary (the second-judge check: `FIN` is the first run of the final evaluation, whose answers were judged; `s60` is 60 cases per generator) | `uv run labourlens judge-xfamily --experiment sonnet55-FIN-s60-b-20261102 --summary` | checkout only | saved summary, no calls or writes | none |
| New second-family dry-run | `uv run labourlens judge-xfamily --experiment MY-JUDGE-20261102 --dry-run` | private raw outputs of the first run of the final evaluation, to construct the paired sample | token/list-price heuristic, not a bill; unavailable in public clone | none |
| Embedding-cache preparation | `uv run labourlens dense-exp --force` | scratch checkout only, complete corpus, `OPENAI_API_KEY`; replaces fixed-name scratch experiment outputs | cached vectors needed before live serving | paid embeddings |
| Embedding the missing v4 chunks (D-080) | `uv run labourlens embed-corpus` (dry run, lists the missing chunks, free), then `OPENAI_API_KEY=... uv run labourlens embed-corpus --yes` | complete v4 corpus, `OPENAI_API_KEY` for `--yes` only | fills `data/index/embeddings/text-embedding-3-large/cache.npz` for the 1,285 chunks that had no vector; about 288,000 tokens, about $0.04 at list price (an estimate); the live container never embeds at startup | paid embeddings, small |
| Human review ingestion (`v2-approve` is the approval step for the 65 fresh questions) | review-ingest and v2-approve commands | original owner exports and associated private review inputs | original signed records remain the evidence; never fabricate missing inputs | none |

Published numbers come from saved outputs. Re-running a model gives different outputs; that is expected and does not change the published results. Do not use `--force` on a registered experiment: it overwrites frozen evidence.

`retrieval-exp` and `dense-exp` refuse existing metrics, cases and summaries; `eval` refuses existing judgements, cases, metrics and reports; `paired --out` refuses an existing destination. Their `--force` flag deliberately allows replacement, not exemption from gold-hash checks. Only use it in a disposable reproduction checkout, never against the authoritative submission. For new generation choose unused tags; for paired statistics choose a new `--out` path (the example below deliberately omits `--force`). Historical command blocks below remain history and now refuse existing outputs.

## Verifying hashes

Frozen gold files and their hashes are listed in [`experiments/gold/CHANGELOG.md`](../experiments/gold/CHANGELOG.md) and [`experiments/heldout-v2/FREEZE.md`](../experiments/heldout-v2/FREEZE.md).

```bash
shasum -a 256 experiments/gold/gold_v3.7.jsonl experiments/gold/heldout_v2_v1.jsonl experiments/gold/draft_cases.jsonl
shasum -a 256 data/processed/observations.parquet specs/prices.yaml
```

Gold and observations hashes can be compared directly with the frozen records. `specs/prices.yaml` has since gained second-family judge prices; its current hash is `6c61e81b4fca213be3b9db467443ce294148be7f6e16697e13f105ac2d75d224`. Verify historical price hashes against the price file at the recorded run commit; do not edit a signed freeze to match the present file. `eval` and `paired` reject mismatched gold hashes unless `--allow-gold-mismatch` is passed. With the corpus, `make test-corpus` re-hashes raw files against the manifest.

## What a clone cannot reproduce

- Anything that reads MOM or MTI text (passages, retrieval indexes, live answers about report content): the documents are not redistributed. The statistical datasets, manifests, saved scores and reports are in git.
- Three datasets whose raw CSVs are gitignored (licence not verified); their derived rows are in `observations.parquet`, so a rebuild from a clone stops at those files (`docs/data-sheet.md`, section 9).
- Raw model outputs (`data/runs/`) are not in git; committed experiment files hold scores, metrics and short judge notes.
- The live site needs the corpus, an API key and the server secrets (`docs/deploy.md`).

A fresh fetch acquires current publisher bytes, not necessarily the historical corpus. Preserve the frozen manifest before `fetch`; compare all retrieval statuses and raw hashes before `build`. A successful download is not proof of snapshot identity. Local private files are needed for a complete rebuild.

In `experiments/triage/*/raw.jsonl` and `experiments/context/*/raw.jsonl`, `raw.jsonl` holds routing results, not transcripts.

## Final two-run headline and 2 Nov measurements

The [pre-registration of the second run](experiments/fin2-replicate.md) of the final evaluation was amended before results to use the mean of the two runs. Both single runs remain visible. The commands below document reproduction, not commands executed by this documentation pass. Paid commands require the private corpus and a key. Existing tags below are frozen: substitute a new tag/destination for a new experiment, never use `--force`. The relative-date probes are anchored to 2 Nov 2026; a different date requires a newly declared fixture rather than silently reusing their expected labels.

### Final aggregate (offline, no model calls)

```sh
# the two-run mean of the first and second runs of the final evaluation (folders FIN and FIN2)
uv run python scripts/final_mean.py
```

This reads the committed scored cases of the first and second runs and writes `experiments/eval/final-mean.json`. It asserts identical case membership within each repeated arm, averages each case's two binary outcomes, and computes paired 95% case-bootstrap intervals with 10,000 resamples and seed 20261030. It also saves both run costs, medians and all-case false-answer/over-abstention rates. Mean-of-medians is not pooled p50, and two runs are not a variance estimate. Run only on a disposable reproduction checkout if you need to preserve the existing generated file unchanged.

For the final headline use `scripts/final_mean.py`, which selects each declared question set. Stored generic paired files for the second run, on the 237 development questions and the original 31 test questions, used combined gold and have incomplete-membership diagnostics; their generic adoption verdicts are not valid split-specific headline tests. Keep those historical files unchanged.
Regenerating those generic second-run files needs explicit split selection while preserving the parent gold hash, not manual deletion of missing cases.

To recompute a separate complete comparison on the 65 fresh questions from committed scores, choose an unused output path:

```sh
uv run labourlens paired --gold experiments/gold/heldout_v2_v1.jsonl --candidate agent-heldout-V2-r3 --baseline agent-heldout-V2-hybrid --models gpt-6-luna gpt-5.6-luna --out /tmp/labourlens-paired-v2-new.json
```

`web/static/data/report.json` is generated output: rebuilding changes its timestamp and commit provenance, so byte identity is not expected. `final_mean.py` reads saved scores, not new model answers.

### Tagged corpus v3.1 retrieval (paid reranking/possible embeddings)

```sh
# tag V31 = the corpus v3.1 retrieval re-run (128 development report questions, build v3.1)
uv run labourlens retrieval-exp2 --tag V31
```

Historical command (`V31` tags the corpus v3.1 retrieval re-run); it now refuses because that tag exists. Use a new tag for a new run. It writes isolated corpus/model-keyed caches, per-configuration directories `dev-R-<tag>-R*` and a sibling summary directory. Saved [v3.1 retrieval summary](../experiments/runs/dev-R-V31/SUMMARY.md) records 1,847 chunks, gold v3.6 and the actual corpus hash. Do not overwrite or pool the frozen v1 ladder.

### Served research chain (paid generation and judging)

Historical commands, one run per model and arm:

```sh
# S65 = the served-chain check (65 cases); mcp-on / direct-on / direct-off = which route and whether the web-only steps were used
uv run labourlens served-exp --split dev --gold experiments/served/mixed-sample.jsonl --pairs gpt-6-luna gpt-5.6-luna --tag S65-mcp-on --retrieval r3 --route mcp --web-steps on
uv run labourlens served-exp --split dev --gold experiments/served/mixed-sample.jsonl --pairs gpt-6-luna gpt-5.6-luna --tag S65-direct-on --retrieval r3 --route direct --web-steps on
uv run labourlens served-exp --split dev --gold experiments/served/mixed-sample.jsonl --pairs gpt-6-luna gpt-5.6-luna --tag S65-direct-off --retrieval r3 --route direct --web-steps off
uv run labourlens eval --exp served-dev-S65-mcp-on --split dev --gold experiments/served/mixed-sample.jsonl --labels gpt-6-luna gpt-5.6-luna
uv run labourlens eval --exp served-dev-S65-direct-on --split dev --gold experiments/served/mixed-sample.jsonl --labels gpt-6-luna gpt-5.6-luna
uv run labourlens eval --exp served-dev-S65-direct-off --split dev --gold experiments/served/mixed-sample.jsonl --labels gpt-6-luna gpt-5.6-luna
uv run labourlens paired --gold experiments/served/mixed-sample.jsonl --candidate served-dev-S65-mcp-on --baseline served-dev-S65-direct-on --models gpt-6-luna gpt-5.6-luna --out experiments/served/paired-S65-direct-on.json
uv run labourlens paired --gold experiments/served/mixed-sample.jsonl --candidate served-dev-S65-mcp-on --baseline served-dev-S65-direct-off --models gpt-6-luna gpt-5.6-luna --out experiments/served/paired-S65-direct-off.json
```

Scoring/paired commands need saved raw or scored rows; judging is paid, paired analysis offline. Mixed n=65 comprises 51 stratified reused development gold plus 8 diversion/6 context probes, not 65 new gold cases. The web-on route comparison is the matched-factor comparison; web-off changes route and front steps together. The paired command's generic adoption verdict is not the served-chain check's own verdict (within three points on the same 51 questions; matched numerical records). The exact-case comparison and matched-call numerical-audit commands are in the [served registration](experiments/served-chain-eval.md); those require private raw records for matched-call auditing. Browser HTTP admission, login and rights projection are not evaluated by this harness.

### Second scorer for the planted-false-figure attack (offline diagnostics versus paid fresh generation)

Historical commands, all destinations already exist. Use new destination ids for any further work:

```sh
# ti06 = the planted-false-figure attack (case T-I06); v2 = the second scorer; the date suffix is the run date
# 1-3: rescore saved answers of the original attack run, the 31 Oct post-fix attack run (m7-ti06-postfix-...) and the 31 Oct fixed-system attack run (m7-e2efix-...)
uv run labourlens threat-test --rescore --source-experiment . --experiment ti06-v2-original-20261102 --scorer v2
uv run labourlens threat-test --rescore --source-experiment m7-ti06-postfix-20261031 --experiment ti06-v2-postfix-20261102 --scorer v2
uv run labourlens threat-test --rescore --source-experiment m7-e2efix-20261031 --experiment ti06-v2-e2efix-20261102 --scorer v2
# 4-5: the fresh 2 Nov attack rerun (defended, then with the defences switched off)
uv run labourlens threat-test --models gpt-6-luna gpt-5.6-luna --experiment ti06-v2-fresh-20261102 --scorer v2
uv run labourlens threat-test --models gpt-6-luna gpt-5.6-luna --ablation naive --experiment ti06-v2-fresh-20261102 --scorer v2
```

The first three commands need private saved answers, no model calls; outputs are post-hoc diagnostics. The last two make paid calls on the known 36-case suite and save both scorer verdicts. V1 remains default and all registered historical scores stay unchanged. [Rule declaration](experiments/t-i06-scorer-v2-rule.md), [fresh results](../experiments/threats/ti06-v2-fresh-20261102/SUMMARY.md). A fresh clone can inspect committed metrics/scores, but cannot reproduce raw-answer diagnostics without the private outputs.

## Second-family judge check

The [declaration and continuation amendment](experiments/second-judge.md) describe the saved second-judge check, experiment `sonnet55-FIN-s60-b-20261102` (FIN is the first run of the final evaluation, whose answers it judged). This documentation pass did not run these commands. A clone can read the committed [summary](../experiments/xjudge/sonnet55-FIN-s60-b-20261102/SUMMARY.md) and `summary.json`; a new judging run needs the private saved raw outputs, `ANTHROPIC_API_KEY` and a new experiment ID.

```sh
# the second-judge check: FIN = the first run of the final evaluation (the answers judged), s60 = 60 cases per generator
uv run labourlens judge-xfamily --experiment sonnet55-FIN-s60-b-20261102 --summary
```

A new dry-run needs private raw outputs of the first run of the final evaluation; it is not checkout-only:

```sh
uv run labourlens judge-xfamily --experiment MY-JUDGE-20261102 --dry-run
```

The summary command reads saved paired and agreement output only. A new dry-run makes no API call but still requires private raw outputs of the first run of the final evaluation to construct its sample; it does not work from this public clone. Paid execution additionally needs `ANTHROPIC_API_KEY`, a new immutable ID and an explicit `--max-usd`.

## Deploy — your registry, domain and private corpus

Follow [deploy.md](deploy.md). Deployment needs Docker Engine and Compose, SSH/scp/rsync, openssl, curl, a domain/DNS and reachable ports 80/443; the bootstrap installs server tooling. The gh CLI is not required: Actions secrets can be configured in the web UI. Set `LABOURLENS_IMAGE=ghcr.io/<your-github-owner>/<your-repository>` in the private server `.env`; publish that image before selecting its commit with `IMAGE_TAG`. Compose has no build stanza. Report-only mode does not need restricted passages; live mode requires all files in `deploy/runtime-data.txt`, including the complete embedding cache. Deployment commands are operational instructions, not evidence that a fork or remote deployment was executed in this pass.

## Packaging

Hand over by GitHub URL, a fresh clone or `git archive HEAD`, never zip or copy the working folder: ignored secrets, private corpus and assessment material share that folder.

## Updating the innovation page

Edit [`innovation-page.json`](innovation-page.json). The source contains `title`, a short `scope`, `abstract`, a bulleted `approach` list, six `sections`, `limitations`, `components` and `references`. Each section has `id`, `title`, `summary`, `paragraphs` with reference IDs, optional `tables` (`retrieval`, `answers` or `cost`) and `proposals`. Every proposal has `title`, `gap`, `measure`, `threshold` and `status`, which must be `proposal`; these become a plain disclosure and definition list. References identify repository `docs/` paths and appear as superscript evidence links. The builder rejects unknown references, missing fields and non-proposal statuses. Keep the approach and six section headings consistent with the short assessment. Changing a proposal to implemented requires a reviewed implementation and a deliberate schema change.

Run `uv run labourlens build-report` to project this editorial source into `web/static/data/report.json`, then `uv run pytest -q tests/web/test_innovation.py`. Open `/innovation` on the local report server. Commit the JSON source and regenerated report together. The page reads only this build output; it does not fetch Markdown or private experiment files in the browser. Measurements are selected from the existing committed-artifact report projection, never copied from roadmap prose. Editorial copy uses the working-tree JSON during the build so it can be previewed before commit; its source hash is recorded separately from the measurement evidence commit. The separate short submission remains [`innovation.md`](innovation.md).

The document layout uses one reading column and a plain contents list. Browser printing uses the A4 stylesheet in `web/static/css/innovation.css`, including expanded proposal definitions; it is not constrained to the short deliverable's two-page limit. Keep [`innovation.md`](innovation.md) within two A4 pages when printed separately, and record the type size and margins used for that measurement.
