# Testing

The code tests run without paid model calls. They check implementation behaviour and frozen artefacts, not the quality of a new model answer. Model-quality evidence comes from saved experiments and has a different scope.

## Test layers

Counts below come from `uv run pytest --collect-only -q`, run on 4 November 2026: **1,640 tests collected**, exit 0. Directory counts include parametrised cases, optional browser checks and corpus tests; they are not pass counts. The owner supplied the latest `make verify` result for this documentation update: **1,521 passed, 60 skipped, 59 corpus-marked tests deselected**. That full run was not repeated here. Counts describe this checkout and will change with the code.

| Layer | What it checks | Count | How to run from the repository root | Needs keys? | Last observed result and evidence |
|---|---|---|---|---|---|
| Unit and integration | Parsing, typed outputs, calculations, scripted agent runs, web routes, access controls, audit records and frozen artefact integrity | 1,640 collected overall; includes every pytest row below, not an additional layer | `make test`; `make verify` adds lint, documentation, rights and secrets checks | No | `make verify` on 3 Nov 2026: 1,521 passed, 60 skipped, 59 deselected (corpus-marked tests that need the local report corpus). |
| Data contracts and provenance | Schema and normalisation, units and periods, lineage, immutable snapshots, release reconciliation, extraction and rights handling | 118 in `tests/data/` | `uv run pytest -q -m 'not corpus' tests/data`; `make test-corpus` selects corpus tests across all directories | No; corpus selection needs private files | 4 Nov 2026: 118 collected; layer not separately executed in this update. [Reproduction guide](reproduce.md#verifying-hashes) describes corpus hash checks. |
| Retrieval and agent regression | Chunking, filtering, ranking, evidence budgets, deterministic tools, bounded execution, timeouts and scripted planner behaviour | 304 in `tests/retrieval/` | `uv run pytest -q -m 'not corpus' tests/retrieval` | No; corpus-marked cases require private files | 4 Nov 2026: 304 collected; layer not separately executed here. The [saved retrieval comparison](../experiments/runs/dev-R-V31/SUMMARY.md), described in the [2 Nov method record](reproduce.md#final-two-run-headline-and-2-nov-measurements), covers 128 development text questions: chunk hit@8 .969 for filter then rerank against .539 for hybrid. It is not a current-corpus regression run. |
| MCP protocol | Client/server negotiation, typed arguments and responses, tools, resources, HTTP transport, hostile replies and annual-average contracts | 143 in `tests/mcp/` | `uv run pytest -q tests/mcp`; `uv run labourlens mcp-demo` for the actual client/protocol demonstration | No; demo uses committed statistical files | 4 Nov 2026: 143 collected; protocol tests and demo not separately executed here. [Committed protocol transcript](mcp-demo-transcript.md) records the earlier demonstration. |
| Adversarial code tests | Injection scanner, input/output guards, scorer rules, custom suite loading and unsafe-request fixtures; hostile MCP checks also sit in the MCP layer | 58 across `tests/test_security.py`, `tests/test_scanner_eval.py`, `tests/test_threat_v2.py` and `tests/test_threat_scorer_v2.py`; not the entire security-related test set | `uv run pytest -q tests/test_security.py tests/test_scanner_eval.py tests/test_threat_v2.py tests/test_threat_scorer_v2.py` | No | 4 Nov 2026: 58 collected; not separately executed here. These are code checks, not fresh attacks against a model. |
| Model threat suites | Direct and passage injection, false figures, exfiltration, sensitive-data requests, unsafe tools, citation failures, overreach, cost abuse and benign lookalikes | Earlier suite: 36 cases. V2: 62 cases, 54 attacks and 8 benign, three repeats per arm | `uv run labourlens threat-test --cases experiments/threats/cases-v2.jsonl --experiment MY-THREATS-NEW --models gpt-6-luna --repeats 3 --scorer v1` | Yes: `OPENAI_API_KEY`, private corpus and paid calls; use an unused experiment ID | 3 Nov 2026 saved [paired analysis](../experiments/threats/threat-v2-analysis.json): majority pass 50/54 guarded versus 42/54 naive; both fail 3/8 benign cases. [Guarded repeat results](../experiments/threats/threat-v2-guarded-20261103/SUMMARY.md). Not rerun here. |
| Web routes and browser checks | 617 web tests in total, including HTTP/API contracts and optional Playwright checks for layout, controls, access links, streaming, conversation context and deck navigation | 617 in `tests/web/`; 21 collected in the focused workbench-controls module | Install Chromium: `uv run --with playwright playwright install chromium`. Run: `uv run --with playwright pytest -q tests/web` | No; synthetic API responses or local fixture servers, not a live provider | 4 Nov 2026: collection only. Playwright execution was not part of this update. Missing optional Playwright skips browser cases, so a green default run is not browser verification. The controls module tests both themes at 1920, 1440, 1024 and 390 pixels; screenshots go to `/tmp/labourlens-workbench-review`. |
| Evaluation harness | Scoring, serialisation, reference/hash checks, paired analysis and experiment-specific accounting; separate paid runs measure answer status, citations, content, cost and latency | 228 in `tests/evaluation/`. Main saved comparison: 237 development, 31 original-test and 65 fresh questions, two runs per configuration | Code: `uv run pytest -q tests/evaluation`. New model runs: use the generation and scoring commands in [Reproduce](reproduce.md#what-each-artefact-needs), with new tags | Code tests: no. Generation/judging: provider key, corpus and private raw outputs as specified | 4 Nov 2026: 228 collected, not separately executed here. [2 Nov saved aggregate](../experiments/eval/final-mean.json): primary-model development status score .897 versus .827; no demonstrated end-to-end gain on the test sets. [Evaluation report](evaluation-report.md) defines denominators and limitations. |
| Latency and load | Per-run wall time, token usage and list-price cost; historical route comparisons, not a concurrent-load benchmark | Earlier served-chain sample: 65 questions; no measured load-test count | Inspect [saved operational measures](../experiments/eval/final-mean.json) and [served-chain reproduction commands](reproduce.md#served-research-chain-paid-generation-and-judging) | Reading saved results: no. New runs: key, corpus and paid calls | Earlier 2 Nov served-chain run: primary-model p50 12.4 s, p95 34.7 s, excluding one-off startup; [system card](system-card.md#served-versus-evaluated). Not rerun here. [Deployment guide](deploy.md) records memory under load as unverified. |

`corpus` and `offline` are registered pytest markers in [pyproject.toml](../pyproject.toml). `make test` explicitly excludes `corpus`; `make test-corpus` selects it. The `offline` marker is not the Makefile's default selection rule. [Makefile](../Makefile) is the command source of truth. Optional notebook and browser dependencies can produce skips, which must not be counted as passes.

## Commands

```bash
uv run pytest --collect-only -q
make verify
make test-corpus
```

The exact pytest commands behind the make targets are:

```bash
uv run pytest -q -p no:cacheprovider -m 'not corpus'
uv run pytest -q -p no:cacheprovider -m corpus
```

`make verify` runs `uv run ruff check src tests scripts`, the non-corpus pytest command, `make docs-check`, `make rights-scan` and `make secrets-scan`. A public clone cannot check restricted report quotations without the local passage files: rights-scan reports `NOT CHECKED`, not a pass. Gitleaks history scanning is conditional on it being installed. The documentation checker checks tracked relative links and anchors, not external URLs or the truth of prose.

## What the tests do not cover

- **The current served system has not had a new quality evaluation.** The saved headline runs use corpus v3.1, earlier prompts and structured-output planning. Corpus v4, 2020 to 2023 answers, native function calling, newer prompts and the annual-average tool are unevaluated. Scripted tests do not close that gap.
- **No per-layer defence ablation.** The guarded-versus-naive threat comparison changes guards and the answer prompt together. It cannot isolate the contribution of each defence. Separate retrieval and statistics-removal experiments do not answer that question.
- **The scanner is heuristic.** It misses attacks and is a warning layer, not a security boundary. The suites do not establish resistance to arbitrary prompt injection.
- **Citation checks are not semantic proof.** A valid evidence ID and matching quotation do not establish that the passage supports every claim. Report-only figures cannot enter deterministic calculations, and poorly extracted PDF tables remain a limitation.
- **Live deployment smoke is manual.** The [deployment checklist](deploy.md#9-verify-a-deployment) calls for an operator to submit a paid live question and inspect answer, evidence, chart, trace and feedback. Offline browser fixtures do not test production authentication, proxy streaming or provider behaviour end to end.
- **No demonstrated concurrent-load capacity.** Saved latency describes specific historical runs. It does not establish throughput, memory under load, an availability target or provider-side spend enforcement.
- **Evaluation is not independent ground truth.** AI drafted references, the sole owner reviewed them after scoring, some question sets share evidence and the main judge is from the generator family. Two runs do not estimate run-to-run variance; second-family review did not reproduce every gain.
- **A public clone cannot reproduce all experiments.** Restricted report passages and raw model answers are local-only. Inspecting saved scores is not a fresh generation, retrieval or human-review run.

## Checks run for this documentation update

4 November 2026, from the repository root:

| Command | Observed result |
|---|---|
| `uv run pytest --collect-only -q` | 1,640 tests collected; exit 0 |
| `make docs-check` | 0 problems in 259 Markdown files |
| `uv run labourlens rights-scan` | 0 hits; 24 allowlisted globs |
| `uv run ruff check src tests scripts` | All checks passed |
| `uv run pytest -q -p no:cacheprovider tests/web/test_deck.py::test_process_slide_is_graphic_first_and_commands_come_from_the_docs` | 1 passed |

The new guide was registered with `git add -N docs/testing.md` so the tracked-file documentation checker included it. No model calls, full pytest execution, browser execution or live deployment smoke were performed in this update.
