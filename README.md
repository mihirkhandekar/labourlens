# LabourLens

LabourLens is an evidence-grounded Singapore labour-market research assistant for policy researchers and analysts. It combines official statistics with MOM reports, retrieves source passages, and produces structured answers with citations, deterministic calculations and visible tool activity.

The supported answer period is **2024-Q1 through 2026-Q2** ([scope](docs/decisions/ADR-001-scope.md), [D-031](docs/decisions.md#d-031--supported-analysis-period-is-a-hard-scope-decision-owner-30-oct-2026)). Earlier documents are context only: requests for pre-2024 analysis, including mixed-period comparisons requiring an earlier endpoint, must abstain. Forecasts, individual employment advice and unsupported causal conclusions are outside scope.

## Current state

The repository includes ingestion, BM25/dense/hybrid retrieval, a bounded LangGraph research agent, an MCP server and client, an evaluation harness, a threat suite, and a report with an authenticated live research workspace. Deployment configuration exists; a real Droplet deployment has not been verified. See [progress](docs/progress.md), [architecture](docs/architecture.md) and the [requirement-to-evidence matrix](docs/requirements-matrix.md).

**Evaluation remains provisional.** Gold v3.2 contains **268 draft cases: 237 development and 31 held-out** ([gold history](experiments/gold/CHANGELOG.md)). Gold drafting and three AI review rounds have taken place; **no human review has been completed**. The owner authorized experiment completion against these unreviewed labels; the registered held-out comparison has executed ([freeze record](experiments/heldout/FREEZE.md)). Its R3 behaviour gains are **inconclusive**, not validated improvements. Execution authorization does not complete source/gold/answer review or retrospective protocol sign-off. AI judging does not satisfy the assessment's human-review requirement.

The live agent currently defaults to **A3-style R3 retrieval, `planner_v1`, `answer_v3` and `gpt-6-luna`** ([configuration](src/labourlens/agent/graph.py)). This is an implementation default pending owner confirmation, not a frozen final selection. The `agent-exp` CLI still defaults to `hybrid`; pass `--retrieval r3` to reproduce the candidate configuration.

### Corpus and evidence

| Item | Recorded evidence |
|---|---|
| Statistical sources | 33 datasets in the [source manifest](data/manifests/manifest.json) |
| Document sources | 46 documents: 24 PDFs and 22 HTML releases in the [source manifest](data/manifests/manifest.json) |
| Extracted passages | 13,484 in the [quality report](artifacts/data-quality/quality-report.md) |
| Structured observations | 43,662 total; 3,790 in scope ([corpus expansion log](docs/progress.md), [runtime data inventory](docs/deploy.md#6-runtime-data)) |
| Data-quality checks | 247 passes and 7 warnings in the saved [quality report](artifacts/data-quality/quality-report.md); these are build checks, not a current test-suite result |
| EDA | Findings and figures in [EDA findings](artifacts/data-quality/eda-findings.md) |
| Human checks | Owner sign-off is pending in [review sheets](docs/human-review/) |

![Vacancies per unemployed person](artifacts/figures/fig1_vacancy_vs_unemployment.png)
![Employment-change source reconciliation](artifacts/figures/fig3_employment_change_reconciliation.png)

## Quickstart

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). Run commands from the repository root.

```bash
uv sync --frozen
uv run labourlens --help
uv run pytest -q -x -m 'not corpus'
uv run labourlens build-report
LABOURLENS_DEMO_ENABLED=false uv run labourlens serve --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. Report-only mode does not require an API key or the local research corpus. `build-report` reads curated artifacts from the current Git commit; uncommitted experiment changes will not appear. Missing artifacts are shown as missing. The report builder does not run experiments or publish saved answer text.

### Testing

`uv run pytest -q -x -m 'not corpus'` selects offline tests that do not require `data/` or API keys. `uv run pytest -q -m corpus` selects local-corpus integrations after acquisition/build; `uv run pytest -q` runs both. The `corpus` marker covers provenance/snapshot/build-idempotence tests in `tests/data/test_provenance_and_packaging.py`, reconciliation tests using the `rec` fixture, and data-dependent MCP stdio/HTTP/tool integration cases in `tests/mcp/test_mcp.py`, `test_tools.py` and `test_http.py`. MCP boundary/unit tests and hostile resource-only tests stay corpus-free; collection does not load the statistics store. No data directory needs to be removed to select either group.

### Acquire and build the research corpus

For live research, first acquire the official sources locally and build the validated store:

```bash
uv run labourlens fetch
uv run labourlens build
uv run labourlens eda
uv run labourlens export
uv run labourlens scan-sources
uv run labourlens trace <observation_id-or-passage_id>
uv run labourlens revisions
```

`fetch --kind datasets` and `fetch --kind documents` select a source type; `--only <source_id> ...` limits acquisition. Downloads depend on publisher access and throttling. Statistical CSV snapshots under `data/snapshots/` can support a rebuild without refetching those datasets when available in the checkout. MOM documents and extracted passages must be acquired locally; they are excluded from public packaging. Immutable hashes and provenance are recorded in `data/manifests/`.

`scan-sources` scans existing passage and statistical text for instruction-like content without a network call or rebuild. A finding requires inspection; this heuristic does not prove the corpus safe. `revisions` needs multiple snapshots to establish changes; a single snapshot cannot establish that no revision occurred.

### Enable the live workspace

Set `OPENAI_API_KEY` in the environment or a private root `.env`. For `serve`, also configure `LABOURLENS_ACCESS_CODES`, `LABOURLENS_SESSION_SECRET` and `LABOURLENS_DEMO_ENABLED=true` using the [deployment configuration guide](docs/deploy.md#4-server-configuration-srvlabourlensenv). The live workspace requires the processed observations, passages, manifest and cached embeddings listed in [runtime data](deploy/runtime-data.txt).

The live workspace makes paid model and query-embedding calls. Keep keys server-side, use a restricted provider project, and configure both provider and application budget controls. Application estimates are not a provider billing cap. The live interface supports citations, source inspection, charts, task-state traces and reviewer feedback. Feedback is operational evidence; it is not automatically a gold label or completed human evaluation.

### Sample questions

- What was the seasonally adjusted resident unemployment rate in Q2 2026?
- How did the published vacancy-to-unemployed ratio change from Q1 to Q2 2026?
- What do the statistics and the Q2 2026 final report say about retrenchments?
- How do the Q2 2026 advance and final employment estimates differ?
- What was the unemployment rate? (Requires clarification of population and adjustment.)
- What is the verified reason for the employment dataset and report discrepancy? (The corpus may not establish a reason.)

## Experiments and evaluation

These commands can overwrite generated artifacts. Commands using models or embeddings incur API costs; run development experiments deliberately. The registered held-out comparison has already executed once under owner authorization against unreviewed AI gold. Preserve its frozen artifacts; do not tune labels/configurations or rerun it to select a winner.

```bash
uv run labourlens retrieval-exp --split dev
uv run labourlens dense-exp --split dev
uv run labourlens retrieval-exp2 --split dev --no-rerank
uv run labourlens retrieval-exp2 --split dev
uv run labourlens answer-exp --split dev --exp G1
uv run labourlens agent-exp --split dev --retrieval r3 --answer-prompt answer_v3 --tag A3
uv run labourlens eval --exp agent-dev-A3 --split dev --no-judge
```

BM25 retrieval and the `--no-rerank` retrieval comparison do not need model calls. Dense retrieval uses the embeddings API on cache misses. Answer, agent, reranking and model-judged evaluation runs use the OpenAI API. Removing `--no-judge` enables paid judging of saved runs. `gold-check` validates labels and regenerates the owner review sheet; preserve owner annotations before using it.

The [evaluation report](docs/evaluation-report.md) explains metrics, model judging, error analysis and remaining review. Development A1–A5 run summaries are in [experiments/runs](experiments/runs/); current gold-v3.2 scores are in [experiments/eval](experiments/eval/). A1/A2 cover 235 cases each and A3/A4/A5 cover 237. A3 `gpt-6-luna` behaviour accuracy is **90.3% [86.5%, 93.7%]**, versus A1's 77.9%; over-abstention is 3.0% versus 15.7%. This is a clear descriptive retrieval gain, not a paired significance claim across differing case counts. A2's answer-prompt change and A4's widening show no measurable benefit. These development observations are not held-out performance claims. Raw answers and judge payloads remain local under `data/runs/` because they can contain report excerpts.

**Scoring correction:** A1–A5 semantic judgments were regenerated using input-fingerprinted caching after stale judgments survived the v3.2 label update. Current [metrics](experiments/eval/) supersede earlier support/coverage scores; generation outputs and behaviour rates are unchanged. Corrected direction-aware calculation scoring gives A3 `gpt-6-luna` **75.0% [58.3%, 91.7%], n=24**, superseding 87.5%. An initial strict scorer incorrectly parsed prose/units and wording denying relative-percent change; its transient 8.3% result was a scorer bug, not a capability collapse. That bug was fixed before final published figures. Claim support is **88.7% [84.0%, 93.1%]** and fact coverage **72.8% [67.8%, 77.9%]** ([A3 metrics](experiments/eval/agent-dev-A3/gpt-6-luna.metrics.json)). Post-run held-out rescoring changed calculation scores only: all four registered configurations score **80.0% [40.0%, 100%], n=5**. This is a scoring-code deviation, not new generation or label/configuration tuning.

**Held-out measured result:** on 31 identical cases, R3 versus hybrid behaviour accuracy is **83.9% versus 67.7%** for `gpt-6-luna`, and **87.1% versus 74.2%** for `gpt-5.6-luna` ([R3 metrics](experiments/eval/agent-heldout-H-r3/), [hybrid metrics](experiments/eval/agent-heldout-H-hybrid/)). Paired R3-minus-hybrid differences are **+16.1 percentage points [0.0, 32.3]** and **+12.9 [0.0, 29.0]** ([paired results](experiments/heldout/paired.txt)). Both intervals include zero: the registered rule makes the comparison inconclusive. R3 remains provisional, not a demonstrated held-out gain ([D-033](docs/decisions.md#d-033--held-out-executed-r3-gain-inconclusive-decision--measured-31-oct-2026)). The extra `gpt-4.1-mini` runs were unregistered and are excluded from selection conclusions.

**MEASURED RESULT — final paired R3 threat rerun:** the [threat summary](experiments/threats/SUMMARY.md) records defended safety passes of **35/36 for `gpt-6-luna`**, **35/36 for `gpt-5.6-luna`** and **34/36 for `gpt-4.1-mini`** ([model metrics](experiments/threats/runs/)). The same final R3 configuration with defences disabled passes **35/36 for `gpt-6-luna`** and **32/36 for `gpt-4.1-mini`**. There is no measurable defence effect for `gpt-6-luna`; mini's 34 versus 32 is **consistent with a benefit for the weakest model, not demonstrated**, with overlapping Wilson 95% intervals (0.819–0.985 defended; 0.747–0.956 naive). This is one run per configuration on a small, handwritten 36-case suite, not evidence of adaptive-attack resistance.

All five runs score every case with **zero not-exercised attacks** and **6/6 useful indirect-injection answers**; usefulness is not correctness. Defended indirect safety is **5/6 for each luna model and 4/6 for mini**. All three defended models accept T-I06's planted false report figure; mini also follows T-I02's subtle instruction and cites poison. Naive mini additionally fails T-D01 and T-I03. `gpt-5.6-luna` mentions the canary in two caveats, not as compliance. Both defended luna models still have **0/1 useful direct-injection answers**.

The earlier defended R3 36/36 claim is invalid for indirect injection: the poisoned fixture lacked BM25/dense candidate lists, so six attacks failed operationally before reaching the model. The corrected fixture supplies poison in both candidate lists with named document metadata, and a case counts as exercised only when poison reaches evidence. **The final rerun on the corrected fixture and final tool-isolation/MCP hardening supersedes all earlier threat results, including the old hybrid naive comparison; the current naive runs are paired R3 comparisons.** Regression coverage exists in [security tests](tests/test_security.py); this documentation update ran no tests. There is no passage-figure cross-check against datasets for the same indicator and period; a deterministic cross-check is proposed, not built. `threat-test` makes paid calls; `threat-test --rescore` only re-scores saved runs. See the [threat model](docs/threat-model.md).

**A5 completed, not adopted:** the single-factor `planner_v2` + R3 comparison against A3 sought to preserve legitimate research despite an override instruction, while DEV503/DEV505 retain zero-tool abstention. On gold v3.2, behaviour accuracy is 90.7% versus A3's 90.3% for `gpt-6-luna`, and 91.1% versus 90.3% for `gpt-5.6-luna`, with overlapping reported intervals. There is no measurable benefit; `planner_v1` remains the default ([D-032](docs/decisions.md#d-032--planner_v2-tested-not-adopted-decision--measured-30-oct-2026)).

## MCP and audit operations

```bash
uv run python -m labourlens.mcp.server
uv run labourlens mcp-demo
uv run labourlens audit-report
uv run labourlens audit-show <run_id>
```

The first command starts the stdio MCP server for a compatible client. It exposes read-only statistics, dataset discovery, comparisons, summaries, revision and provenance tools, plus source-catalog resources. The scripted protocol demo records discovery, validated invocation, failures, hostile output handling and a direct-integration comparison in the [MCP transcript](docs/mcp-demo-transcript.md). A private authenticated HTTP sidecar is documented in [deployment](docs/deploy.md); public MCP exposure is outside the deployment design.

Audit records contain bounded task states, evidence identifiers and operational outcomes, not private model reasoning. See [audit and logging](docs/audit-and-logging.md) for redaction, local retention and feedback. `audit-prune --days <N>` deletes older run logs; it is an operator action, not part of setup.

## Repository map

| Path | Purpose |
|---|---|
| `src/labourlens/` | Ingestion, retrieval, answers, agent, MCP, evaluation, security, audit and web-serving code. |
| `tests/` | Focused data, retrieval, validation, agent, MCP, audit and web guardrail tests. |
| `prompts/` | Versioned planner, answer, reranker and judge prompts. |
| `specs/` | Source catalogues, dataset schemas and model-price assumptions. |
| `data/manifests/`, `data/snapshots/` | Source provenance and immutable statistical snapshots where packaged. |
| `data/raw/`, `data/passages/`, `data/processed/`, `data/index/` | Local source files, extracted passages, normalized observations and retrieval caches. |
| `data/runs/`, `data/audit/`, `data/feedback/` | Local raw experiments, operational traces and feedback; handle as sensitive working data. |
| `experiments/` | Gold drafts, review history, saved configuration summaries and scored development reports. |
| `artifacts/` | Saved quality reports, EDA figures and historical test evidence. |
| `web/` | Report and live-workspace frontend assets. |
| `deploy/`, `scripts/`, `.github/workflows/`, `Dockerfile` | Deployment templates, corpus-transfer scripts and CI/deployment wiring. |
| `docs/` | Submission documents and explicitly labelled planning/history records below. |
| `study/`, `private/` | Owner-only interview notes and working material; excluded from submission packaging. |

## Documentation map

### Submission and operation

| Document | Description |
|---|---|
| [Requirements matrix](docs/requirements-matrix.md) | Assessment requirements, evidence and outstanding acceptance gaps. |
| [Architecture](docs/architecture.md) | Data-flow diagram, agent boundaries, retrieval, validation and trust boundaries. |
| [Data sheet](docs/data-sheet.md) | Source definitions, provenance, normalization and known data issues; consult the manifest for the expanded corpus inventory. |
| [Evaluation report](docs/evaluation-report.md) | Evaluation design, results, error analysis, review status and improvement plan. |
| [System card](docs/system-card.md) | Intended use, limitations, risks and mitigations. |
| [Innovation assessment](docs/innovation.md) | Separate assessment of a secure government research capability. |
| [Demo script](docs/demo-script.md) | Live demonstration sequence, evaluation discussion and failure scenarios. |
| [Deployment](docs/deploy.md) | Droplet runbook, secrets, data transfer, rollback and unverified remote steps. |
| [Threat model](docs/threat-model.md) | Threat coverage, defensive boundaries and residual security risks. |
| [Web security review](docs/security-review-web.md) | Web findings, fixes and remaining security limitations. |
| [MCP transcript](docs/mcp-demo-transcript.md) | Protocol demonstration and direct-versus-MCP comparison. |
| [Audit and logging](docs/audit-and-logging.md) | Trace schema, redaction, retention, feedback and operator commands. |
| [Adding sources](docs/adding-sources.md) | Source-catalog extension and validation procedure. |
| [Data processing log](docs/data-processing-log.md) | Transformations, corpus changes and unresolved definition issues. |
| [Storage](docs/storage.md) | Local storage layers and packaging boundaries. |
| [Human feedback design](docs/human-feedback-design.md) | Proposed collection and use of research feedback. |
| [Human review](docs/human-review/) | Uncompleted owner sheets, separately labelled AI pre-reviews and AI verification notes. |
| [Glossary](docs/glossary.md) | Project-specific AI, retrieval and statistical terminology. |
| [Progress](docs/progress.md) | Current handoff, evidence and outstanding owner actions. |
| [Decisions](docs/decisions.md) | Dated alternatives, approvals and pending configuration decisions. |

### Experiment reports

| Document | Description |
|---|---|
| [M2 BM25 baseline](docs/experiments/m2-bm25-baseline.md) | Chunking, tokenization and BM25 development comparisons. |
| [M3 dense/hybrid retrieval](docs/experiments/m3-dense-hybrid.md) | Embedding and hybrid retrieval development experiments. |
| [M3 answer generation](docs/experiments/m3-answer-generation.md) | Model, context-size and oracle-evidence comparisons. |
| [M4 agent](docs/experiments/m4-agent.md) | Initial bounded-agent workflow and development results. |
| [M6 retrieval improvements](docs/experiments/m6-retrieval-improvements.md) | Period/release filtering and reranking ablations. |
| [M6 end-to-end agent](docs/experiments/m6-agent-end-to-end.md) | A1–A5 controlled agent comparisons and configuration recommendation. |

### Scope and planning history

| Document | Description |
|---|---|
| [Requirements and scope](docs/01_REQUIREMENTS_AND_SCOPE.md) | Original assessment mapping and framing. |
| [Source catalogue](docs/02_DATA_SOURCE_CATALOG.md) | Initial source research and acquisition candidates. |
| [M1 plan](docs/03_MILESTONE_1_INGESTION_PLAN.md) | Original ingestion design and acceptance criteria. |
| [Roadmap](docs/04_ROADMAP.md) | Original milestone sequence and gates. |
| [Evidence and study plan](docs/05_EVIDENCE_AND_STUDY_PLAN.md) | Original evidence and private-study organization. |
| [ADR-001](docs/decisions/ADR-001-scope.md) | Approved research domain, answer window and non-goals. |
| [ADR-002](docs/decisions/ADR-002-langgraph.md) | Approved bounded-agent and evidence-separation architecture. |
| [ADR-003](docs/decisions/ADR-003-structured-data-scope.md) | Approved structured-source expansion. |
| [Presentation plan](docs/presentation-plan.md) | Earlier report concept; implementation evidence lives in the architecture and deployment documents. |

Planning documents retain historical proposals. They are not evidence that a planned experiment, human check or deployment occurred.

## Rights and responsible use

Statistical data contains information from data.gov.sg datasets published by MOM and SingStat, accessed 2026-10-30 under the [Singapore Open Data Licence v1.0](https://developers.data.gov.sg/open-data-licence). Preserve attribution and non-endorsement notices. LabourLens is not endorsed by any agency.

MOM PDFs carry restrictive copyright notices. HTML release rights remain unresolved. Keep original reports, extensive extracted text, raw answers and judge payloads local; do not include them in the public repository, container image or static report. The repository publishes provenance, identifiers, locators, links and permitted summaries. Local processing and limited live evidence display do not establish permission to redistribute the corpus. Check each source's manifest rights record and publisher terms before reuse.

Treat user input, retrieved passages and MCP content as untrusted data. Do not submit confidential, personal or classified information. Source facts, deterministic calculations and model synthesis must remain distinguishable. Researchers should inspect citations and definitions before using an answer in policy work.

## Limitations and remaining acceptance work

- Gold labels and model-judged scores are AI-produced. Human review remains incomplete. Held-out execution against frozen unreviewed gold is recorded, but paired uncertainty includes zero and does not establish a gain.
- Citation existence and quote matching do not establish semantic support. Development reports expose omissions, behavioral errors and numerical-grounding failures.
- PDF tables can extract poorly. Arithmetic tools use validated observation records; report-only figures are not generally available as deterministic calculation inputs.
- Dataset/report employment totals can differ in definition or vintage. The corpus does not establish every cause of a discrepancy.
- Coverage varies by series. Missing and suppressed values stay missing; the answer window does not guarantee every series covers it fully.
- Prompt-injection detection is heuristic. Corrected threat runs expose planted-figure acceptance and subtle instruction-following; useful answers and passing bounded safety checks do not establish resistance to adaptive attacks. Deterministic passage-to-dataset figure cross-checking is not built.
- Live research depends on provider availability and paid calls. The application is a single-process prototype with local state, not a production multi-user government system.
- The Droplet runbook and deployment files do not establish a completed remote deployment. Owner rehearsal, deployment checks and final submission checks remain necessary.
