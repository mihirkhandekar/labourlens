# LabourLens

LabourLens is an evidence-grounded research assistant for Singapore policy researchers and labour-market analysts. It combines official statistics (data.gov.sg datasets from MOM and SingStat) with MOM labour-market reports. It retrieves source passages and returns structured answers with citations, deterministic calculations, an honest abstention when evidence is thin, and a visible tool-activity trace.

**Scope.** Supported answer period: **2024-Q1 to 2026-Q2** ([ADR-001](docs/decisions/ADR-001-scope.md), [D-031](docs/decisions.md#d-031--supported-analysis-period-is-a-hard-scope-decision-owner-30-oct-2026)). Earlier documents are context only; requests that need a pre-2024 figure must abstain. Out of scope: forecasts, individual employment advice, unsupported causal claims, unrestricted web research.

**Live site:** <https://labourlens.navig.me> (report and workbench). It runs on one DigitalOcean Droplet, deployed by the GitHub Actions workflow in [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). Live research is switched on and needs an access code, which is shared privately and is not in this repository. Live answers make paid model calls; a provider-side spend cap has **not** been verified, only the application's own budget limit ([deployment](docs/deploy.md)).

**At a glance**

- **What it does:** answers analytical questions about the Singapore labour market from official statistics and MOM reports, with passage-level citations, deterministic arithmetic and abstention. One bounded LangGraph agent, a read-only MCP statistics server, and an evaluation harness.
- **Results:** on 237 development questions the default configuration agrees with the gold label on 0.903 of cases (`gpt-6-luna`); on the separate 65-case held-out v2 set rerank-plus-filter retrieval beats plain hybrid by 3 cases for one model and not at all for the other, which I do not call a confirmed gain; numerical comparisons are weak (0.214) because of a tool gap; a tool set built to fix that failed its own criteria and was not adopted.
- **What the final results are on:** document build v3 (85 sources, 16,419 passages; the current build v3.1 differs only in how 40 passages of one article are labelled, and no result was re-run), retrieval `r3` (period and stage filter, then rerank), `gpt-6-luna` as the primary model (`gpt-5.6-luna` compared), `gpt-6.1-terra` as judge, and the base tool set. Do not compare numbers across document builds.
- **Caveats:** the gold labels were AI-drafted and reviewed by one person after the runs were scored, so these are agreement figures, not validated accuracy; each configuration was run once; a clone cannot run anything that needs the private MOM and MTI text.

Reviewer entry points: [`SUBMISSION.md`](SUBMISSION.md) (what to read first and how to run it), [`docs/README.md`](docs/README.md) (documentation index), [`docs/agent-logs.md`](docs/agent-logs.md) (how AI agents were used, with the approval record).

## Served versus evaluated

**The live web app is not exactly the system the experiments measured.** In front of the agent the web runner adds (1) a **small-talk fast path** (D-050): a closed list of whole-message greetings, thanks and similar answered with no model call; and (2) a **model scope check** (D-051): one `gpt-6-luna` call that can answer or decline off-topic, small-talk and unsafe messages without running the agent, and otherwise adds its tokens, cost and latency (about 1.6 s median, 2.4 s p95, $0.000124 mean per call, 409 calls) to the question. It fails open to the agent on any error. Together with the runtime changes of D-043 (web citation projection, soft ungrounded-number notice, 80 s run deadline with retry, rights-window hardening, MCP withheld-row reporting, login and feedback limits) and (3) D-053, the served app routes `get_series` through the local MCP stdio server while every accuracy evaluation called statistics directly, these are the full list of differences. `run_agent`, `agent-exp`, `threat-test` and every gold, held-out and threat result use none of the first two, and call statistics directly. Triage was measured on its own, not end to end: **0 of 333** gold and held-out v2 questions diverted as out of scope, **1 of 36** threat cases diverted (T-D05), **30 of 30** hand-written off-topic or unsafe or small-talk messages caught, 10 of 10 borderline in-scope kept ([`metrics.json`](experiments/triage/triage-v1-luna/metrics.json), one run, my own 40 off-topic cases). No end-to-end accuracy, cost or latency run exists with triage switched on; the 1-in-36 threat diversion and the borderline cases show it can misroute on judgement calls.

## Headline results

All numbers are saved outputs, each with its source file. Behaviour accuracy means the answer's status matches the gold label (answer, abstain, clarify or refuse); it does not check content, which other metrics cover (key-number recall, claim support, fact coverage). Behaviour status, key-number recall, calculation correctness, false-answer and over-abstention are deterministic code. Claim support and fact coverage come from an AI judge (`gpt-6.1-terra`). Gold labels were drafted by AI. I then went through them in the review interface and signed off on every case, answer verdict and source check (four separate streams, 403 items in total: 268 gold questions, 65 held-out v2 questions, 40 saved system answers and 30 source checks; only the first two are questions). It is one reviewer, working after AI pre-review (three separate AI review passes, one model family) and after the saved runs were scored, so it is not independent inter-rater evidence. These are agreement figures, not validated accuracy. Intervals are 95% case-bootstrap intervals (Wilson only for the threat suite).

| Question | Result | Source |
|---|---|---|
| Does filter plus rerank (A3) beat plain hybrid retrieval (A1) with `gpt-6-luna`? | Development behaviour 0.903 [0.865, 0.937] (n=237) versus 0.779 [0.728, 0.830] (n=235); over-abstention 0.030 [0.008, 0.051] versus 0.157 [0.111, 0.204]. Descriptive, not a paired test. | [`experiments/eval/`](experiments/eval/) |
| Does it hold on the 31 held-out cases? | r3 0.871 [0.742, 0.968] versus hybrid 0.710 [0.548, 0.839]. Paired gain +16.1 points [0.0, 32.3]: **not demonstrated**. | [`experiments/heldout/paired.txt`](experiments/heldout/paired.txt) |
| Does it hold on the 65-case held-out v2 set (corpus v3, sources no earlier case cites)? | `gpt-6-luna`: r3 0.754 versus hybrid 0.708, paired +0.046 (3 better, 0 worse), 90% case interval [0.015, 0.092], McNemar exact p = 0.25. The pre-registered rule is met for the primary model; the effect is three cases; I would not call it a confirmed gain; the second model shows none (`gpt-5.6-luna` 0.723 versus 0.723). Absolute accuracy is low (`numerical_comparison` 0.214), mostly from a tool coverage gap, not retrieval. A separate, additional set; not pooled with the row above. | [result](docs/experiments/m7-heldout-v2-result.md), [`experiments/heldout-v2/paired.json`](experiments/heldout-v2/paired.json) |
| Do the extraction fixes (corpus v2) help? | No measurable change (dev 0.886 [0.844, 0.924] versus 0.903). | [evaluation report](docs/evaluation-report.md) |
| Which model should generate answers? | Early exploratory screen, 30 development questions, six models (`gpt-4.1-mini`, `gpt-5.4-mini`, `gpt-5.6-luna`, `gpt-6-luna`, `gpt-6-sol`, `gpt-6.1-terra`), with retrieved and with oracle evidence. Price did not track quality; models differ more in caution than in skill; single runs cannot rank neighbours. `gpt-6.1-terra` was a generator candidate here and later became the judge. The later two-model comparison (A3, 237 questions) shows no model winner. | [m3 answer generation](docs/experiments/m3-answer-generation.md) |
| Does the served system (corpus v3, end-to-end review fixes, cross-check on) hold up on the development set? | **MEASURED** regression check, not an ablation: several factors changed together. Behaviour `gpt-6-luna` 0.903 [0.865, 0.941], `gpt-5.6-luna` 0.916 [0.878, 0.949], both overlapping A3. Cases with an ungrounded number rose for `gpt-5.6-luna` to 0.165 [0.118, 0.215] from 0.051 [0.025, 0.080] in A3 (no overlap), and the check itself was widened in the same change. | [X2 report](experiments/eval/agent-dev-X2-REPORT.md), [evaluation report](docs/evaluation-report.md) |
| Does an extra tool for arithmetic on report figures help (tool set v2, D-046 and D-048)? | **MEASURED, not adopted.** Dev X3 against X2 (n=237, one run per model): behaviour `gpt-6-luna` 0.903 to 0.895, `gpt-5.6-luna` 0.916 to 0.899, no gain; the criteria declared before the run **failed for both models** (false-answer cases 7 against 6, and ungrounded numbers in cases that used the new tool). On the held-out v2 questions, re-run as a **post-freeze diagnostic (not held-out, optimistic by construction, not a replacement of the held-out v2 result)**, `numerical_comparison` rose from 3 to 12 of 14 for `gpt-6-luna`. The default tool set is unchanged and the threat suite was not run under v2. | [tool-fix report](docs/experiments/m7-tool-fix.md) |
| Threat suite, 36 hand-written cases | Pre-guard (corpus v1): defended 35/36 [0.858, 0.995] for both luna models, 34/36 for mini; the shared failure was a planted false figure (T-I06). Final-code run `m7-e2efix-20261031` (corpus v3, cross-check on, one run per configuration): `gpt-6-luna` defended 36/36 strict, `gpt-5.6-luna` 35/36 (T-I06 fails strict and the post-hoc refined scorer), naive baselines 35/36 on both. T-I06 is **not shown stable** across runs, the scorer is brittle (exact-string checks) and was not changed, and the suite shows no defence effect. | [`experiments/threats/m7-e2efix-20261031/SUMMARY.md`](experiments/threats/m7-e2efix-20261031/SUMMARY.md), [`experiments/threats/SUMMARY.md`](experiments/threats/SUMMARY.md) |
| Human review | Gold labels were drafted by AI. The owner then went through them in the review interface and signed off on every case, answer verdict and source check (four separate streams, 403 items in total: 268 gold questions, 65 held-out v2 questions, 40 saved system answers and 30 source checks; only the first two are questions). The strongest human evidence is the first pack (17 answer verdicts, J1 to J10, 3 gold cards), the four change-clicks, J10 and the owner's written policy decisions (D-031, D-034, D-035, D-036, D-047). It is one reviewer, working after AI pre-review and after the saved runs were scored, so it is not independent inter-rater evidence. Gold v3.7 records this and changes no label or score; saved evaluations were not rescored on it. | [final owner review summary](docs/human-review/owner-review-final-summary.md), [numbers audit](docs/human-review/numbers-audit.md) |

The question sets are separate and not additive. The 268 reference questions are 237 development questions (used while building the system) plus 31 original held-out questions. The original 31 share evidence with development (25 of 31 cite at least one development evidence id, 15 of 31 have their whole evidence set in it), so they are held out by question, not by evidence. The 65 held-out v2 questions are a later set written on six sources no earlier case cites, signed before their run and used once. The post-freeze tool-set diagnostic re-ran those same 65, so it is not a fresh test. The 40 saved answers (a failure-enriched sample from one run) and the 30 source checks are review items, not question sets. Five original held-out cases changed after the v3.2 freeze (HO-029 in v3.3; HO-027, HO-023 and HO-004 in v3.4; HO-022 in v3.5); the full version history is in the [evaluation report](docs/evaluation-report.md). Held-out v2 uses the same system, prompts and tools, with an AI-drafted gold that I approved unchanged. Each configuration was run once.

The live agent defaults to retrieval `r3`, `planner_v1`, `answer_v3` and `gpt-6-luna` ([`agent/graph.py`](src/labourlens/agent/graph.py)). That is an implementation default pending owner confirmation, not a final selection ([D-030](docs/decisions.md), D-033).

## Corpus versions

The system and the live site use the current document build (v3.1: 85 sources, 16,419 passages). Every measured result, including the final held-out test, was run on v3, which differs from v3.1 only in how 40 passages of the MTI article are labelled (D-052); none was re-run. Two earlier builds are kept only so older results can be reproduced: v1 is the first experiments and the original held-out test (results frozen), v2 is the extraction fixes tested alone (no measurable change), and v3 adds six untouched sources so the 65-question held-out set shares no evidence with development. Development accuracy 0.903 appears on both the earlier build (A3, v1) and the current build (X2, v3); held-out v2 0.754 is on the current build. Do not compare numbers across builds. The table gives the detail.

| Corpus | Contents | Used for |
|---|---|---|
| **v1** | 13,484 passages | All registered experiments: A1–A5, held-out H-r3/H-hybrid, pre-guard threat suites |
| **v2** (`extract-0.2`) | 15,915 passages, 43,662 observations | Extraction-only X1 experiments and the earlier post-fix T-I06 run (`m7-ti06-postfix-20261031`) |
| **v3** (`extract-0.2`; v2 plus six labour-only sources, D-040) | 85 sources (36 datasets, 49 documents: 27 PDFs and 22 HTML), 52,020 observations (4,300 in the answer scope), 16,419 passages, 1,847 chunks, 276 build checks (269 pass, 7 warn) | The committed [manifest](data/manifests/manifest.json) and [quality report](artifacts/data-quality/quality-report.md), the local store, the X2 development regression check, the `m7-e2efix-20261031` threat run and held-out v2 |
| **v3.1, current build** (`extract-0.3`, D-052) | Same 85 sources, 52,020 observations, 16,419 passages and 1,847 chunks. The refined garbled-text rule relabels 40 passages of the MTI feature article (16 `garbled` to `ok`, 24 `garbled` to `table_unreliable`) and 4 `ok` to `table_unreliable`; quality flags 9,052 `ok`, 7,121 `table_unreliable`, 246 `garbled`; 10 chunk texts and 4 chunk ids change, 10 new vectors are needed. 276 build checks (269 pass, 7 warn). Snapshot: [`v3.1.json`](experiments/corpus-snapshots/v3.1.json), diff [`v3.1-diff.json`](experiments/corpus-snapshots/v3.1-diff.json) | The local store and, after the re-embed and upload, the live site. **No measured evaluation exists on v3.1** |

**Corpus v3 has four measured evaluations (31 Oct and 1 Nov 2026): the X2 development regression check, the `m7-e2efix-20261031` threat run, held-out v2 (the first evidence-disjoint-source evaluation, D-045; only partly independent: same system, prompts and tools, one run per arm) and the post-freeze tool-set diagnostic (X3 and the re-run of the 65 held-out v2 questions, D-048, not adopted).** Frozen v1 and v2 results are retained unchanged. **Owner-supplied, not checkable from the repository:** the Droplet serves corpus v3 (`/healthz` fingerprint `d402120f6f8f`, 16,419 passages, 1,847 chunks), so the served corpus is the one these runs measured. Details: [data sheet](docs/data-sheet.md), [evaluation report](docs/evaluation-report.md).

## Quick start

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). Run from the repository root.

```bash
make setup     # uv sync --frozen
make verify    # lint, offline tests, docs links, rights scan (NOT CHECKED without the private corpus), secret scan
make serve     # report and workbench page on http://127.0.0.1:8000
```

`make help` lists every target. The underlying commands, for reference:

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

`eval` and `paired` refuse a gold file whose SHA-256 differs from the one recorded for the run unless `--allow-gold-mismatch` is given. Scoring still reads `experiments/gold/draft_cases.jsonl` (v3.6, `6169a9de…`); `gold_v3.7.jsonl` is the review-provenance file. In `draft_cases.jsonl` 3 records are `owner_manual`, 42 `agreed_with_ai_suggestion` and 223 `draft`; only `gold_v3.7.jsonl` carries 268 `owner_manual`. The published A1–A5 and held-out metrics were scored on v3.5 (`aac4b405…`), archived at `experiments/gold/archive/gold-v3.5.jsonl`. The registered held-out comparison already ran once and must not be rerun to pick a winner.

Results and their history: [evaluation report](docs/evaluation-report.md). Prompts are in [`prompts/`](prompts/).

## MCP and audit

```bash
uv run python -m labourlens.mcp.server   # stdio MCP server
uv run labourlens mcp-demo               # scripted protocol demo
uv run labourlens audit-report
```

The MCP server exposes read-only statistics, discovery, comparison, revision and provenance tools, plus source-catalogue resources. The [MCP transcript](docs/mcp-demo-transcript.md) records discovery, validated calls, failures, hostile output and a direct-integration comparison. The live web app routes the agent's `get_series` lookups through this server over stdio (D-053; `LABOURLENS_MCP=false` returns to direct calls), and each such call shows `transport: mcp` in the trace. Only `get_statistic` is used by the agent; the other eight tools are not given to it. `search_reports` and `calculate_change` stay in-process. Every frozen accuracy evaluation and the threat runs, except the 10 `mcp_server_failure` cases, called statistics directly, so their results do not describe the MCP route; no end-to-end accuracy run with MCP on the live path has been measured. Measured cost: median 22.7 ms per call against 4.4 ms direct, plus about 1.9 s once at startup. The scripted MCP agent answer is a recorded single run in the demo script. Audit records hold bounded task states and outcomes, never model reasoning ([audit and logging](docs/audit-and-logging.md)).

## Repository structure

| Path | Purpose |
|---|---|
| `src/labourlens/` | Ingestion, retrieval, answers, agent, MCP, evaluation, security, audit, web serving |
| `tests/` | Data, retrieval, agent, MCP, audit and web tests ([`tests/README.md`](tests/README.md)) |
| `prompts/`, `specs/` | Versioned prompts; source catalogues, schemas and price assumptions |
| `data/manifests/`, `data/snapshots/` | Provenance and immutable statistical snapshots |
| `data/raw/`, `data/passages/`, `data/runs/` | Local only, gitignored (rights and sensitivity) |
| `experiments/`, `artifacts/` | Gold set, saved metrics, threat results, quality reports, figures |
| `web/`, `deploy/`, `scripts/`, `.github/` | Report and workbench front end; deployment |
| `docs/` | Documentation ([index](docs/README.md)); `docs/archive/` holds superseded planning drafts and the early progress log; `docs/process/` holds the initial plan and prompt |
| `Makefile`, `.pre-commit-config.yaml`, `.gitleaks.toml`, `.github/workflows/ci.yml` | One entry point and the checks CI runs |

## Documents

| Document | What it is |
|---|---|
| [Architecture](docs/architecture.md) | Data flow, agent graph, guardrails, trust boundaries; [rendered diagram](docs/img/architecture.svg) |
| [Data sheet](docs/data-sheet.md) | Sources, licences, schema, checks, EDA findings |
| [Evaluation report](docs/evaluation-report.md) | Design, results, error analysis, review rubric, limits |
| [System card](docs/system-card.md) | Intended use, risks, controls |
| [Threat model](docs/threat-model.md) | Attacks tested, controls, residual risk |
| [Innovation assessment](docs/innovation.md) | Forward plan (about two pages) |
| [Demo script](docs/demo-script.md) | 20-minute live demonstration plan |
| [Requirements matrix](docs/requirements-matrix.md) | Assessment requirement to evidence, with honest status |
| [Deployment](docs/deploy.md) | Droplet runbook and verified state |
| [Decisions](docs/decisions.md), [progress](docs/progress.md) | Dated decisions (54 entries, D-000 to D-053); current state and recent log |
| [Agent logs](docs/agent-logs.md) | How AI agents were used: contract, approval gates, controls, mistakes caught |
| [Reproduce](docs/reproduce.md), [fresh-clone check](docs/fresh-clone-check.md) | Commands to each artefact, what needs the private corpus or an API key, expected output |
| [Review records](docs/human-review/README.md) | Owner review and AI reviews, kept separate |
| [Security policy](SECURITY.md) | Secrets, untrusted text, rights |
| [MCP transcript](docs/mcp-demo-transcript.md) | Protocol demonstration |

Planning drafts in `docs/archive/planning/` record earlier proposals; they are not evidence that anything ran.

## Rights and responsible use

Statistical data comes from data.gov.sg datasets published by MOM and SingStat under the [Singapore Open Data Licence v1.0](https://developers.data.gov.sg/open-data-licence); keep attribution and non-endorsement notices. LabourLens is not endorsed by any agency. MOM PDFs carry restrictive copyright notices and HTML release rights are unresolved, so reports, extracted passages, raw answers and judge payloads stay local and are not in the repository, image or static report. The repository publishes provenance, identifiers, locators, links and short permitted quotations.

Treat user input, retrieved passages and MCP content as untrusted data. Do not submit confidential, personal or classified information. Inspect citations and definitions before using an answer in policy work.

## Main limitations

- Gold labels were AI-drafted first and the judge is an AI. The owner went through them in the review interface and signed off on every case, answer verdict and source check (four separate streams, 403 items in total: 268 gold questions, 65 held-out v2 questions, 40 saved system answers and 30 source checks; only the first two are questions). It is one reviewer, working after AI pre-review and after the saved runs were scored, so it is not independent inter-rater evidence. Gold v3.7 changes only provenance fields; the saved evaluations are still scored on v3.5, v3.6 and the signed held-out v2 gold. The four D-047 change-clicks are recorded but not applied. The threat suite and the automatic judge checks are not human review.
- The original held-out set shares evidence with development; its gain over hybrid retrieval is not demonstrated. The separate held-out v2 set meets its pre-registered rule for the primary model on three cases, with no gain on the second model and a lower bound of 0.0 when one question group is removed; I would not call it a confirmed gain.
- Both arms of held-out v2 score about 0.71 to 0.75, and numerical comparisons about 0.21, mostly because the tools cannot do arithmetic on figures printed in reports. A tool set v2 that adds that arithmetic was built and tested (D-046). On dev it did not pass its pre-declared criteria and was **not adopted** (D-048); the large gain on the v2 questions is a post-freeze diagnostic on cases whose errors motivated the fix, so it is optimistic by construction. Adoption would need a fresh dev pass and a threat run under v2.
- The planted-figure guard is a closed grammar and had known faults found by the end-to-end review (see the [threat model](docs/threat-model.md)). T-I06 is one case: the post-fix runs gave 36/36 refined once and 35/36 once for `gpt-5.6-luna`, and its scorer requires exact strings, so it is brittle and was not changed after the failure was seen.
- The X2 regression check changed several factors at once; it does not isolate any one of them. Its rise in ungrounded-number cases mixes a wider check with possible behaviour change.
- The ingestion scanner missed all five paraphrased attack probes; citation checks confirm a quote exists, not that it supports the claim.
- PDF tables can extract poorly; report-only figures are not deterministic calculation inputs.
- Dataset and report employment totals can differ in definition or vintage; the corpus does not explain every gap.
- A single-process prototype with local state, not a multi-user government system; provider-side spend cap unverified.

## Licence and attribution

The code and documents are all rights reserved and shared for review ([`LICENSE`](LICENSE)). Statistical data: contains information from data.gov.sg datasets of the Ministry of Manpower and the Singapore Department of Statistics, under the [Singapore Open Data Licence v1.0](https://developers.data.gov.sg/open-data-licence); not endorsed by the publishers. Three datasets are recorded as licence assumed, not verified (see [data sheet, section 9](docs/data-sheet.md#9-open-licence-items-and-what-the-rights-scan-covers)). MOM and MTI reports are the Ministries' copyright and are not in this repository. Fonts are SIL OFL 1.1 ([`web/static/fonts/LICENSES.md`](web/static/fonts/LICENSES.md)).
