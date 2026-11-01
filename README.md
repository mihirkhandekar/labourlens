# LabourLens

LabourLens is an evidence-grounded research assistant for Singapore policy researchers and labour-market analysts. It combines official statistics (data.gov.sg datasets from MOM and SingStat) with MOM labour-market reports. It retrieves source passages and returns structured answers with citations, deterministic calculations, an honest abstention when evidence is thin, and a visible tool-activity trace.

**Scope.** Supported answer period: **2024-Q1 to 2026-Q2** ([ADR-001](docs/decisions/ADR-001-scope.md), [D-031](docs/decisions.md#d-031--supported-analysis-period-is-a-hard-scope-decision-owner-30-oct-2026)). Earlier documents are context only; requests that need a pre-2024 figure must abstain. Out of scope: forecasts, individual employment advice, unsupported causal claims, unrestricted web research.

**Live site:** <https://labourlens.navig.me> (report and workbench). It runs on one DigitalOcean Droplet, deployed by the GitHub Actions workflow in [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). Live research is switched on and needs an access code, which is shared privately and is not in this repository. Live answers make paid model calls; a provider-side spend cap has **not** been verified, only the application's own budget limit ([deployment](docs/deploy.md)).

## Headline results

All numbers are saved outputs, each with its source file. Behaviour accuracy means the answer's status and content agree with a gold label. The labels were drafted by AI first; the owner then reviewed all 268 cases card by card (one reviewer, after the saved runs were scored). These are agreement figures, not validated accuracy. Wilson 95% intervals in brackets.

| Question | Result | Source |
|---|---|---|
| Does filter plus rerank (A3) beat plain hybrid retrieval (A1) with `gpt-6-luna`? | Development behaviour 0.903 [0.865, 0.937] (n=237) versus 0.779 [0.728, 0.830] (n=235); over-abstention 3.0% versus 15.7%. Descriptive, not a paired test. | [`experiments/eval/`](experiments/eval/) |
| Does it hold on the 31 held-out cases? | r3 0.871 [0.742, 0.968] versus hybrid 0.710 [0.548, 0.839]. Paired gain +16.1 points [0.0, 32.3]: **not demonstrated**. | [`experiments/heldout/paired.txt`](experiments/heldout/paired.txt) |
| Does it hold on the 65-case held-out v2 set (corpus v3, sources no earlier case cites)? | `gpt-6-luna`: r3 0.754 versus hybrid 0.708, paired +0.046 (3 better, 0 worse), 90% case interval [0.015, 0.092], McNemar exact p = 0.25. The pre-registered rule is met for the primary model; the effect is three cases; I would not call it a confirmed gain; the second model shows none (`gpt-5.6-luna` 0.723 versus 0.723). Absolute accuracy is low (`numerical_comparison` 0.214), mostly from a tool coverage gap, not retrieval. A separate, additional set; not pooled with the row above. | [result](docs/experiments/m7-heldout-v2-result.md), [`experiments/heldout-v2/paired.json`](experiments/heldout-v2/paired.json) |
| Do the extraction fixes (corpus v2) help? | No measurable change (dev 0.886 [0.844, 0.924] versus 0.903). | [evaluation report](docs/evaluation-report.md) |
| Does the served system (corpus v3, end-to-end review fixes, cross-check on) hold up on the development set? | **MEASURED** regression check, not an ablation: several factors changed together. Behaviour `gpt-6-luna` 0.903 [0.865, 0.941], `gpt-5.6-luna` 0.916 [0.878, 0.949], both overlapping A3. Cases with an ungrounded number rose for `gpt-5.6-luna` to 0.165 [0.118, 0.215] from 0.051 [0.025, 0.080] in A3 (no overlap), and the check itself was widened in the same change. | [X2 report](experiments/eval/agent-dev-X2-REPORT.md), [evaluation report](docs/evaluation-report.md) |
| Does an extra tool for arithmetic on report figures help (tool set v2, D-046 and D-048)? | **MEASURED, not adopted.** Dev X3 against X2 (n=237, one run per model): behaviour `gpt-6-luna` 0.903 to 0.895, `gpt-5.6-luna` 0.916 to 0.899, no gain; the criteria declared before the run **failed for both models** (false-answer cases 7 against 6, and ungrounded numbers in cases that used the new tool). On the held-out v2 questions, re-run as a **post-freeze diagnostic (not held-out, optimistic by construction, not a replacement of the held-out v2 result)**, `numerical_comparison` rose from 3 to 12 of 14 for `gpt-6-luna`. The default tool set is unchanged and the threat suite was not run under v2. | [tool-fix report](docs/experiments/m7-tool-fix.md) |
| Threat suite, 36 hand-written cases | Pre-guard (corpus v1): defended 35/36 [0.858, 0.995] for both luna models, 34/36 for mini; the shared failure was a planted false figure (T-I06). Final-code run `m7-e2efix-20261031` (corpus v3, cross-check on, one run per configuration): `gpt-6-luna` defended 36/36 strict, `gpt-5.6-luna` 35/36 (T-I06 fails strict and the post-hoc refined scorer), naive baselines 35/36 on both. T-I06 is **not shown stable** across runs, the scorer is brittle (exact-string checks) and was not changed, and the suite shows no defence effect. | [`experiments/threats/m7-e2efix-20261031/SUMMARY.md`](experiments/threats/m7-e2efix-20261031/SUMMARY.md), [`experiments/threats/SUMMARY.md`](experiments/threats/SUMMARY.md) |
| Human review | The owner decided all 403 labelling items (268 gold cases, 65 held-out v2 cases, 40 saved answers, 30 source checks) by own click. Labels were AI-drafted first and the review came after the saved runs were scored. One reviewer, so not inter-rater evidence. Gold v3.7 records this and changes no label or score; saved evaluations were not rescored on it. | [final owner review summary](docs/human-review/owner-review-final-summary.md) |

Caveats that matter for reading the table: the original held-out set shares evidence with development; its labels changed after the run (HO-022, v3.5), and the full version history is in the [evaluation report](docs/evaluation-report.md). Held-out v2 uses sources no earlier case cites but the same system, prompts and tools, with an AI-drafted gold that the owner approved unchanged. Each configuration was run once.

The live agent defaults to retrieval `r3`, `planner_v1`, `answer_v3` and `gpt-6-luna` ([`agent/graph.py`](src/labourlens/agent/graph.py)). That is an implementation default pending owner confirmation, not a final selection ([D-030](docs/decisions.md), D-033).

## Corpus versions

Three corpus states exist, and different parts of this repository belong to different ones.

| Corpus | Contents | Used for |
|---|---|---|
| **v1** | 13,484 passages | All registered experiments: A1–A5, held-out H-r3/H-hybrid, pre-guard threat suites |
| **v2** (`extract-0.2`) | 15,915 passages, 43,662 observations | Extraction-only X1 experiments and the earlier post-fix T-I06 run (`m7-ti06-postfix-20261031`) |
| **v3** (v2 plus six labour-only sources, D-040) | 85 sources (36 datasets, 49 documents: 27 PDFs and 22 HTML), 52,020 observations (4,300 in the answer scope), 16,419 passages, 1,847 chunks, 276 build checks (269 pass, 7 warn) | The committed [manifest](data/manifests/manifest.json) and [quality report](artifacts/data-quality/quality-report.md), the local store, the X2 development regression check, the `m7-e2efix-20261031` threat run and held-out v2 |

**Corpus v3 has three measured evaluations, all on 31 Oct 2026: the X2 development regression check, the `m7-e2efix-20261031` threat run and held-out v2, the first evidence-disjoint-source evaluation** (D-045; only partly independent: same system, prompts and tools, one run per arm). Frozen v1 and v2 results are retained unchanged. **Owner-supplied, not checkable from the repository:** the Droplet serves corpus v3 and the post-fix code (commit `c297146`; `/healthz` fingerprint `d402120f6f8f`, 16,419 passages, 1,847 chunks), so the served system is the one X2 and the threat run measured. Details: [data sheet](docs/data-sheet.md), [evaluation report](docs/evaluation-report.md).

## Quick start

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). Run from the repository root.

```bash
uv sync --frozen
uv run labourlens --help
uv run pytest -q -m 'not corpus'
uv run labourlens build-report
LABOURLENS_DEMO_ENABLED=false uv run labourlens serve --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000> for the report and <http://127.0.0.1:8000/workbench> for the workbench page. This offline path needs no API key and no local corpus. `build-report` reads curated artefacts from the current Git commit and runs no experiments.

### What you can and cannot run without the corpus

| Needs nothing but the checkout | Needs the local corpus (`data/raw`, `data/passages`, `data/runs`; gitignored for rights reasons) | Needs an API key and spends money |
|---|---|---|
| `uv sync`, CLI help, `pytest -m 'not corpus'`, `build-report`, report-only `serve` | `fetch`, `build`, `eda`, `export`, `scan-sources`, `trace`, `pytest -m corpus`, `mcp-demo` (needs the statistics store) | live answers, `answer-exp`, `agent-exp`, reranked retrieval, model-judged `eval`, the threat suite |

`uv run pytest -q -m 'not corpus'` is the supported command on a fresh clone. Corpus-marked tests skip cleanly when `data/` is absent, so plain `uv run pytest -q` also runs, but they only check anything with the local corpus. Metrics cannot be regenerated without the corpus and a key, so they are read from committed JSON under [`experiments/`](experiments/). MOM reports are not redistributed: acquire them yourself with `labourlens fetch`, which depends on publisher access.

### Rebuild the corpus (needs network and time)

```bash
uv run labourlens fetch
uv run labourlens build
uv run labourlens eda
uv run labourlens export
```

`fetch --kind datasets|documents` and `--only <source_id>` narrow acquisition. Immutable hashes and provenance are recorded in `data/manifests/`. Do not run these on a checkout whose `data/` you want to keep as is: they rewrite generated files.

### Enable the live workspace locally

Set `OPENAI_API_KEY` (environment or a private `.env`), plus `LABOURLENS_ACCESS_CODES`, `LABOURLENS_SESSION_SECRET` and `LABOURLENS_DEMO_ENABLED=true` ([configuration guide](docs/deploy.md#4-server-configuration-srvlabourlensenv)). The live workspace needs the processed observations, passages, manifest and embedding cache listed in [`deploy/runtime-data.txt`](deploy/runtime-data.txt). It makes paid calls: use a restricted provider project and a provider-side budget. Feedback is operational evidence, not a gold label.

### Sample questions

- What was the seasonally adjusted resident unemployment rate in Q2 2026?
- How did the vacancy-to-unemployed ratio change from Q1 to Q2 2026?
- What do the statistics and the Q2 2026 final report say about retrenchments?
- How do the Q2 2026 advance and final employment estimates differ?
- What was the unemployment rate? (Should ask which population and adjustment.)
- What is the verified reason for the employment dataset and report discrepancy? (The corpus may not establish one.)

## Experiments

Commands that call a model or the embeddings API cost money. The registered dev and held-out raw runs are not re-run by these commands, and re-running them is not needed to reproduce the published numbers. `labourlens agent-exp` refuses to overwrite an existing experiment id (`--force` overrides it and destroys frozen evidence). To exercise the pipeline, use a throwaway tag (paid API calls; needs `OPENAI_API_KEY`):

```bash
uv run labourlens retrieval-exp --split dev          # BM25, no model calls
uv run labourlens retrieval-exp2 --split dev --no-rerank
uv run labourlens agent-exp --split dev --tag SMOKE --pairs gpt-6-luna
uv run labourlens eval --exp agent-dev-SMOKE
```

To re-score a frozen run offline, pass the gold file it was scored on:

```bash
uv run labourlens eval --exp agent-dev-A3 --no-judge --gold experiments/gold/archive/gold-v3.5.jsonl
```

`eval` and `paired` refuse a gold file whose SHA-256 differs from the one recorded for the run unless `--allow-gold-mismatch` is given. The current gold file is v3.6 (`6169a9de…`); the published A1–A5 and held-out metrics were scored on v3.5 (`aac4b405…`), archived at `experiments/gold/archive/gold-v3.5.jsonl`. The registered held-out comparison already ran once and must not be rerun to pick a winner.

Results and their history: [evaluation report](docs/evaluation-report.md). Prompts are in [`prompts/`](prompts/).

## MCP and audit

```bash
uv run python -m labourlens.mcp.server   # stdio MCP server
uv run labourlens mcp-demo               # scripted protocol demo
uv run labourlens audit-report
```

The MCP server exposes read-only statistics, discovery, comparison, revision and provenance tools, plus source-catalogue resources. The [MCP transcript](docs/mcp-demo-transcript.md) records discovery, validated calls, failures, hostile output and a direct-integration comparison. The live web app calls the statistics tools directly, not through MCP; an MCP-backed agent answer is recorded separately in the demo script. Audit records hold bounded task states and outcomes, never model reasoning ([audit and logging](docs/audit-and-logging.md)).

## Repository structure

| Path | Purpose |
|---|---|
| `src/labourlens/` | Ingestion, retrieval, answers, agent, MCP, evaluation, security, audit, web serving |
| `tests/` | Data, retrieval, agent, MCP, audit and web tests |
| `prompts/`, `specs/` | Versioned prompts; source catalogues, schemas and price assumptions |
| `data/manifests/`, `data/snapshots/` | Provenance and immutable statistical snapshots |
| `data/raw/`, `data/passages/`, `data/runs/` | Local only, gitignored (rights and sensitivity) |
| `experiments/`, `artifacts/` | Gold set, saved metrics, threat results, quality reports, figures |
| `web/`, `deploy/`, `scripts/`, `.github/` | Report and workbench front end; deployment |
| `docs/` | Submission documents |

## Submission documents

| Document | What it is |
|---|---|
| [Architecture](docs/architecture.md) | Data flow, agent graph, guardrails, trust boundaries |
| [Data sheet](docs/data-sheet.md) | Sources, licences, schema, checks, EDA findings |
| [Evaluation report](docs/evaluation-report.md) | Design, results, error analysis, review rubric, limits |
| [System card](docs/system-card.md) | Intended use, risks, controls |
| [Threat model](docs/threat-model.md) | Attacks tested, controls, residual risk |
| [Innovation assessment](docs/innovation.md) | Forward plan (about two pages) |
| [Demo script](docs/demo-script.md) | 20-minute live demonstration plan |
| [Requirements matrix](docs/requirements-matrix.md) | Assessment requirement to evidence, with honest status |
| [Deployment](docs/deploy.md) | Droplet runbook and verified state |
| [Decisions](docs/decisions.md), [progress](docs/progress.md) | Dated decisions; working log |
| [MCP transcript](docs/mcp-demo-transcript.md) | Protocol demonstration |

Planning documents under `docs/0*.md` and `docs/presentation-plan.md` record earlier proposals; they are not evidence that anything ran.

## Rights and responsible use

Statistical data comes from data.gov.sg datasets published by MOM and SingStat under the [Singapore Open Data Licence v1.0](https://developers.data.gov.sg/open-data-licence); keep attribution and non-endorsement notices. LabourLens is not endorsed by any agency. MOM PDFs carry restrictive copyright notices and HTML release rights are unresolved, so reports, extracted passages, raw answers and judge payloads stay local and are not in the repository, image or static report. The repository publishes provenance, identifiers, locators, links and short permitted quotations.

Treat user input, retrieved passages and MCP content as untrusted data. Do not submit confidential, personal or classified information. Inspect citations and definitions before using an answer in policy work.

## Main limitations

- Gold labels were AI-drafted first. The owner then decided every case by own click, but that is one reviewer working after the saved runs were scored, so it is not independent inter-rater evidence. Gold v3.7 changes only provenance fields; the saved evaluations are still scored on v3.5, v3.6 and the signed held-out v2 gold. The threat suite and the automatic judge checks are not human review.
- The original held-out set shares evidence with development; its gain over hybrid retrieval is not demonstrated. The separate held-out v2 set meets its pre-registered rule for the primary model on three cases, with no gain on the second model and a lower bound of 0.0 when one question group is removed; I would not call it a confirmed gain.
- Both arms of held-out v2 score about 0.71 to 0.75, and numerical comparisons about 0.21, mostly because the tools cannot do arithmetic on figures printed in reports. A tool set v2 that adds that arithmetic was built and tested (D-046). On dev it did not pass its pre-declared criteria and was **not adopted** (D-048); the large gain on the v2 questions is a post-freeze diagnostic on cases whose errors motivated the fix, so it is optimistic by construction. Adoption would need a fresh dev pass and a threat run under v2.
- The planted-figure guard is a closed grammar and had known faults found by the end-to-end review (see the [threat model](docs/threat-model.md)). T-I06 is one case: the post-fix runs gave 36/36 refined once and 35/36 once for `gpt-5.6-luna`, and its scorer requires exact strings, so it is brittle and was not changed after the failure was seen.
- The X2 regression check changed several factors at once; it does not isolate any one of them. Its rise in ungrounded-number cases mixes a wider check with possible behaviour change.
- The ingestion scanner missed all five paraphrased attack probes; citation checks confirm a quote exists, not that it supports the claim.
- PDF tables can extract poorly; report-only figures are not deterministic calculation inputs.
- Dataset and report employment totals can differ in definition or vintage; the corpus does not explain every gap.
- A single-process prototype with local state, not a multi-user government system; provider-side spend cap unverified.
