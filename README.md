# LabourLens

LabourLens is an evidence-grounded Singapore labour-market research assistant for policy researchers and analysts. It combines official statistics with MOM reports, retrieves source passages, and produces structured answers with citations, deterministic calculations and visible tool activity.

The supported answer period is **2024-Q1 through 2026-Q2** ([scope](docs/decisions/ADR-001-scope.md), [D-031](docs/decisions.md#d-031--supported-analysis-period-is-a-hard-scope-decision-owner-30-oct-2026)). Earlier documents are context only: requests for pre-2024 analysis, including mixed-period comparisons requiring an earlier endpoint, must abstain. Forecasts, individual employment advice and unsupported causal conclusions are outside scope.

## Current state

The repository includes ingestion, BM25/dense/hybrid retrieval, a bounded LangGraph research agent, an MCP server and client, an evaluation harness, a threat suite, and a report with an authenticated live research workspace. Deployment configuration exists; a real Droplet deployment has not been verified. See [progress](docs/progress.md), [architecture](docs/architecture.md) and the [requirement-to-evidence matrix](docs/requirements-matrix.md).

**Evaluation remains provisional.** Gold v3.5 has **268 cases: 237 development/31 held-out; 45 reviewed (31 held-out/14 dev), 223 drafts**; SHA-256 `aac4b405b51c7cebf019c3b3629509ecb711be32fb830a8e78c4c7b902219e09` ([history](experiments/gold/CHANGELOG.md), D-036). **Owner review complete 31 Oct 2026: 125 cards decided by the owner (30 own verdicts, 95 by agreeing per card with AI suggestions or the three-pass AI tie-break), not independent inter-rater evidence**. Not blinded annotation or blanket verification. Cards: 45 gold, 40 answers, 30 sources, ten decisions. Chat confirms HO-022 `clarify` → `answer` after held-out execution and DEV-018 `refuse` → `clarify`; the exported DEV-018 refusal was accidental, and the private original remains unedited. **Development A1–A5 and all four registered held-out arms are now rescored against v3.5 saved outputs. Development reused compatible caches without model calls; held-out refreshed stale judgments, with no new answer generation.** Preserve original v3.2 [freeze](experiments/heldout/FREEZE.md) and v3.2–v3.4 sensitivities alongside current scores; post-run review does not restore blind confirmation.

The live agent currently defaults to **A3-style R3 retrieval, `planner_v1`, `answer_v3` and `gpt-6-luna`** ([configuration](src/labourlens/agent/graph.py)). This is an implementation default pending owner confirmation, not a frozen final selection. The `agent-exp` CLI still defaults to `hybrid`; pass `--retrieval r3` to reproduce the candidate configuration.

### Corpus and evidence

| Item | Recorded evidence |
|---|---|
| Statistical sources | 33 datasets in the [source manifest](data/manifests/manifest.json) |
| Document sources | 46 documents: 24 PDFs and 22 HTML releases in the [source manifest](data/manifests/manifest.json) |
| Extracted passages | 15,915 on corpus v2 (`extract-0.2`), rebuilt offline; old evaluation results remain **frozen corpus v1** ([migration/runbook](docs/experiments/m7-corpus-v2-runbook.md)) |
| Structured observations | 43,662 total; 3,790 in scope ([corpus expansion log](docs/progress.md), [runtime data inventory](docs/deploy.md#6-runtime-data)) |
| Data-quality checks | 248 passes and 7 warnings in the saved [quality report](artifacts/data-quality/quality-report.md); these are build checks, not a current test-suite result |
| EDA | Findings and figures in [EDA findings](artifacts/data-quality/eda-findings.md) |
| Human checks | 125 per-card owner decisions recorded in [review summary](docs/human-review/owner-review-summary.md); not blinded annotation or independent inter-rater evidence; unresolved rights/protocol checks remain |

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

**Current development results (gold v3.5).** [Saved metrics](experiments/eval/) use gold SHA-256 `aac4b405b51c7cebf019c3b3629509ecb711be32fb830a8e78c4c7b902219e09`; [evaluation report](docs/evaluation-report.md) preserves historical versions side by side. A1/A2 n=235; A3/A4/A5 n=237. Luna6 A1–A5 behaviour is **77.9%, 76.2%, 90.3%, 89.9%, 91.1%**; luna5.6 **80.0%, 79.6%, 90.3%, 90.7%, 91.6%**. A3 luna6 remains **90.3% [86.5%, 93.7%]**, over-abstention 3.0% versus A1 15.7%. A3's gain is descriptive, not paired significance across differing populations; A2/A4/A5 do not establish benefit. Five `--no-judge` rescoring commands reused compatible cached judgments; changed DEV-018 outputs were nonanswers without claims. No model calls. Raw answers/judge payloads stay local because they can contain report excerpts.

**Scoring correction history:** input-fingerprinted judging replaced stale v3.2 caches. Direction-aware calculation corrected A3 luna6 to **75.0% [58.3%, 91.7%], n=24**, superseding 87.5%; transient 8.3% was a prose/units/negation parser bug. A3 support **88.7% [84.0%, 93.1%]** and coverage **72.8% [67.8%, 77.9%]** remain unchanged in current v3.5 dev rescoring. Held-out calculation correctness remains **80.0% [40.0%, 100%], n=5**, all four registered arms, in current v3.5 metrics. Scoring-code corrections and gold adjudications are separate; neither involved new answer generation.

**Current held-out result (gold v3.5; saved-output rescoring):** on 31 identical cases, R3/hybrid behaviour accuracy is **87.1% [74.2%, 96.8%] / 71.0% [54.8%, 83.9%]** for `gpt-6-luna`, and **83.9% [71.0%, 96.8%] / 74.2% [58.1%, 90.3%]** for `gpt-5.6-luna` ([metrics](experiments/eval/)). Scoring-time gold SHA-256 is the v3.5 hash above. [Paired gains](experiments/heldout/paired.txt) remain **+16.1 percentage points [0.0, 32.3]** and **+9.7 [-3.2, 22.6]**, both **inconclusive** (10,000 paired case-bootstrap resamples, seed 20261030). HO-022's owner label changed after original generation; refreshing judgments is not a new generation trial or blind confirmation. **History:** luna6 R3/hybrid was 83.9%/67.7% in v3.2–v3.4; luna5.6 was 87.1%/74.2% (v3.2), 83.9%/71.0% (v3.3), 80.6%/71.0% (v3.4). Preserve [v3.2](experiments/heldout/paired-v3.2.txt), [v3.3](experiments/heldout/paired-v3.3.txt), [v3.4](experiments/heldout/paired-v3.4.txt), original outputs and freeze side by side with current scores in the [evaluation report](docs/evaluation-report.md). R3 remains provisional. Extra mini runs were unregistered and excluded from selection conclusions.

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
| [Human review](docs/human-review/) | Completed 125-card owner decisions with explicit AI-agreement provenance, separately labelled AI reviews and unresolved inspection items. |
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

- Gold was AI-drafted; 45 cards now have owner review and 223 remain drafts. AI-assisted per-card decisions are not blinded annotation or independent inter-rater evidence. Development and registered held-out scores are current v3.5; held-out labels changed after generation, and paired uncertainty still includes zero.
- A [second independent AI pass](experiments/human-review-sample/independent-ai-review-2.md), not human review, rated a failure-enriched 40-case A3 development sample 28 correct / 6 partly correct / 6 incorrect; these are not population accuracy estimates. Its [gold audit](experiments/gold/independent-ai-review-2.md) found development evidence-ID overlap in 25/31 held-out cases (the entire evidence set in 15/31): question-held-out is not evidence-independent, despite no exact question/normalized-template duplicates.
- Citation existence and quote matching do not establish semantic support. Development reports expose omissions, behavioral errors and numerical-grounding failures.
- PDF tables can extract poorly. Arithmetic tools use validated observation records; report-only figures are not generally available as deterministic calculation inputs.
- Extraction corrections on unmerged `extraction-fixes` (`80a287b`; `docs/experiments/m7-extraction-fixes.md` on that branch) are not adopted or reflected in frozen scores; separate retrieval/answer evaluation awaits owner approval.
- Dataset/report employment totals can differ in definition or vintage. The corpus does not establish every cause of a discrepancy.
- Coverage varies by series. Missing and suppressed values stay missing; the answer window does not guarantee every series covers it fully.
- Prompt-injection detection is heuristic. Corrected threat runs expose planted-figure acceptance and subtle instruction-following; useful answers and passing bounded safety checks do not establish resistance to adaptive attacks. Deterministic passage-to-dataset figure cross-checking is not built.
- The [second source review](docs/human-review/independent-ai-review-m1-2.md) found all five malicious paraphrases bypassed the ingestion scanner (not an end-to-end exploit), and three sampled dataset licence-verification claims could not be reproduced from cached publisher evidence. Zero scan hits are not safety assurance; quarantine, schema/citation/output guards and source-specific rights review remain necessary.
- Live research depends on provider availability and paid calls. The application is a single-process prototype with local state, not a production multi-user government system.
- The Droplet runbook and deployment files do not establish a completed remote deployment. Owner rehearsal, deployment checks and final submission checks remain necessary.
