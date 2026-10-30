# LabourLens system card

**Updated:** 31 October 2026. **Status:** research prototype; dev and registered held-out measurements against unreviewed AI gold. The held-out comparison executed under owner authorization; R3's behaviour gain is inconclusive. Human source/gold/answer review remains incomplete.

## Intended use and users

LabourLens supports Singapore policy researchers and labour-market analysts. It retrieves official evidence, compares published quarterly statistics and produces cited summaries with uncertainty. The answer scope is 2024-Q1 through 2026-Q2; source coverage varies. D-031 makes this a hard boundary: earlier documents are context only, and requests for earlier-period figures or mixed-period comparisons requiring an earlier endpoint must abstain. Timeless definitions remain answerable. Users should inspect source definitions, publication stage and citations before using an answer in research. Scope: `docs/decisions/ADR-001-scope.md`, extended by D-019/D-020/D-031 in `docs/decisions.md`.

Forecasting, unsupported causal attribution, individual employment advice and unrestricted web research are out of scope. The system is not an official government service or an autonomous policy decision-maker. It must not receive confidential, personal or classified information.

## Data and rights

The corpus combines data.gov.sg statistics published by MOM/SingStat with MOM reports and release pages. Source URLs, snapshot hashes, dates, definitions, units and release stages are recorded in `data/manifests/manifest.json` and `specs/sources.yaml` plus `specs/sources.d/`. Transformations and quality limitations are described in `docs/data-sheet.md` and `docs/data-processing-log.md`.

Statistical data is attributed under the [Singapore Open Data Licence](https://developers.data.gov.sg/open-data-licence); no agency endorsement is implied. MOM PDFs carry restrictive copyright notices. Release-page rights remain unresolved where terms were inaccessible. Full documents, extracted passages, indexes and raw answers containing MOM text stay local and gitignored. Public documentation uses paraphrases, identifiers and links. The owner accepted API processing of passages in D-022; provider data-use terms have not been independently verified in this project.

Missing or suppressed values remain missing. Population, seasonal adjustment and publication vintage must stay separate. Dataset and report disagreements can reflect unverified definition differences; the system must not invent an explanation. Historical revision tracking has a single-snapshot limitation (`docs/data-sheet.md`).

## Architecture and models

Acquisition and validation produce immutable snapshots, normalized observations and page-located passages. Retrieval combines BM25 with dense vectors using reciprocal-rank fusion. The current agent default, `r3`, applies period/release filtering followed by LLM reranking. Runtime chunks are `merge200` with `text-embedding-3-large` (`src/labourlens/retrieval/runtime.py`).

A bounded LangGraph researcher selects read-only `search_reports`, `get_series` and `calculate_change` tools. Numerical differences come from deterministic code. Statistical access defaults to direct calls; MCP supplies a separate typed, discoverable interface and optional agent backend. Structured answers pass schema, citation-label, quote-presence and status checks. Quote presence alone does not establish semantic support. Implementation: `src/labourlens/agent/`, `src/labourlens/answer/`, `src/labourlens/mcp/`; diagram: `docs/architecture.md`.

| Role | Model / prompt | Input / output USD per million tokens |
|---|---|---|
| Planner and answer generator | `gpt-6-luna`; `planner_v1`, `answer_v3` | $0.10 / $0.50 |
| Reranker | `gpt-6-luna`; `rerank_v1` | $0.10 / $0.50 |
| Dense embeddings | `text-embedding-3-large` | $0.13 / not applicable |
| Offline answer judge | `gpt-6.1-terra`; `judge_v1` | $1.00 / $5.00 |

Model and prompt defaults: `src/labourlens/agent/graph.py`, `src/labourlens/retrieval/rerank.py`. Prices are the repository's Standard-processing list-price assumptions dated 30 October 2026 (`specs/prices.yaml`, citing the [OpenAI pricing page](https://developers.openai.com/api/docs/pricing)). They are estimates, exclude cached-input discounts and require rechecking before future runs. D-030 records the assistant's default change, pending owner confirmation.

## Measured development performance

**MEASURED RESULT:** A3, `gpt-6-luna`, `planner_v1`, `answer_v3`, `r3`, scored against gold v3.2 on the development split. All figures below come from `experiments/eval/agent-dev-A3/gpt-6-luna.metrics.json`; intervals are that artifact's bootstrap 95% intervals.

| Measure | Observed result |
|---|---|
| Cases | 237 |
| Behaviour accuracy | 90.3% [86.5%, 93.7%] |
| Over-abstention | 3.0% [0.8%, 5.1%] |
| Key-number recall | 82.1% [77.3%, 86.6%], eligible n=153 |
| Calculation correctness | 75.0% [58.3%, 91.7%], eligible n=24; corrected direction-aware score |
| Any gold evidence cited | 83.6% [78.3%, 88.4%], eligible n=189 |
| Judge-supported claims | 88.7% [84.0%, 93.1%], 309 claims across 182 cases |
| Reference-fact coverage | 72.8% [67.8%, 77.9%], 309 facts across 175 cases |
| Answers with ungrounded-number flags | 7.6% [4.2%, 11.0%] |
| Latency, median / p95 | 15.4 / 35.6 seconds |
| Estimated mean run cost | $0.00212 per case; offline judge cost is separate |

These results measure agreement with AI-drafted labels and an AI judge, not human-validated reliability. Gold v3.2 contains 268 cases: 237 development and 31 held-out. Three AI review passes and D-031's scope correction are recorded in `experiments/gold/CHANGELOG.md`; owner review remains pending. The answer-sample pre-review is AI-only (`experiments/human-review-sample/ai-review-summary.md`); neither it nor the judge satisfies human review. A1–A5 judgments were regenerated with input-fingerprinted caching after stale judgments survived v3.2; current support/coverage supersede earlier figures. A3's former 87.5% calculation rate is superseded by 75.0%. An initial strict scorer mishandled prose/units and negated-relative-percent wording; its transient 8.3% result was a scorer bug, fixed before final publication, not a loss of numerical capability. Generation outputs and behaviour did not change.

A1/A2 cover 235 cases; A3/A4/A5 cover 237. The A1-to-A3 R3 gain is descriptive, not a paired significance claim across different case counts. A2 (`answer_v4`) and A4 (widening) show no measurable benefit. A5's single-factor `planner_v2` comparison is complete: behaviour accuracy is 90.7% [86.9%, 94.1%] versus A3's 90.3% [86.5%, 93.7%] for `gpt-6-luna`, and 91.1% [87.3%, 94.5%] versus 90.3% [86.1%, 94.1%] for `gpt-5.6-luna`. These overlapping intervals do not establish improvement or equivalence. A5 is not adopted; `planner_v1`, `answer_v3`, R3 and `gpt-6-luna` remain unchanged (D-032).

## Registered held-out performance

**MEASURED RESULT:** the owner authorized experiment completion against frozen but unreviewed AI gold (`experiments/heldout/FREEZE.md`). Registered configurations used `planner_v1` / `answer_v3`, each luna model with R3 and hybrid, on 31 identical held-out cases. Sources: `experiments/eval/agent-heldout-H-{r3,hybrid}/{gpt-6-luna,gpt-5.6-luna}.metrics.json`.

| Model | R3 behaviour [95% CI] | Hybrid behaviour [95% CI] | Paired R3 gain, percentage points [95% CI] |
|---|---|---|---|
| `gpt-6-luna` | 83.9% [71.0%, 96.8%] | 67.7% [51.6%, 83.9%] | +16.1 [0.0, 32.3] |
| `gpt-5.6-luna` | 87.1% [74.2%, 96.8%] | 74.2% [58.1%, 87.1%] | +12.9 [0.0, 29.0] |

Paired intervals use 10,000 case-bootstrap resamples, seed 20261030 (`experiments/heldout/paired.txt`). Both include zero, so the registered rule yields **inconclusive**, not demonstrated superiority. R3 is retained provisionally (D-033), subject to owner quality/cost preference. R3 versus hybrid estimated costs are $0.00193 versus $0.00124 per case for `gpt-6-luna` and $0.00343 versus $0.00271 for `gpt-5.6-luna`; p95 latencies are 26.6 versus 18.5 s and 36.1 versus 19.7 s. Corrected calculation correctness is **80.0% [40.0%, 100%] for all four configurations**, n=5. Post-run rescoring fixed the calculation parser only: a scoring-code deviation, with no new generation or changed labels/configurations. Small calculation strata preclude numerical-superiority conclusions.

The extra `gpt-4.1-mini` configurations were unregistered and do not inform selection conclusions. Initial scoring used the wrong split and was rerun with `--split heldout`; no labels/configurations changed after results. Execution does not retroactively complete human review or protocol sign-off. Full analysis and limits: `docs/evaluation-report.md`, `docs/experiments/m6-agent-end-to-end.md`.

## Risks, controls and oversight

- **Wrong or incomplete evidence:** period filters can exclude a later report restating an earlier quarter; retrieval misses and over-abstention remain possible. Inspect cited passages and definitions. Rerank failure falls back to available ranked evidence and is traced (`src/labourlens/agent/tools.py`).
- **Unsupported or misleading claims:** structured validation checks format and citation mechanics. Semantic support, omitted facts and causal overreach still need review. A correct arithmetic tool can receive the wrong series or periods.
- **Prompt injection and unsafe tools:** retrieved text is untrusted. Catalogue-constrained schemas, read-only tools, input/output guards and MCP response validation limit authority. Corrected defended `r3` runs passed 35/36 for `gpt-6-luna` and `gpt-5.6-luna` (Wilson 95% interval 0.858–0.995), and 34/36 for `gpt-4.1-mini` (0.819–0.985). Both luna models repeated the planted false figure in T-I06; mini failed the T-S05 status criterion and followed a subtle instruction/cited poison in T-I02. `gpt-5.6-luna` mentioned the canary once in a caveat, not as compliance. Earlier defended 36/36 claims were invalid for indirect injection: the poisoned fixture lacked BM25/dense candidate lists, so all six attacks failed operationally before reaching the model. The corrected fixture supplies poison in both lists with named document metadata, and exercise requires poison in evidence. Current `gpt-6-luna` usefulness is 0/1 direct, 6/6 indirect and 3/3 MCP; usefulness does not mean every safety criterion passed. Older naive hybrid runs are not a paired `r3` ablation. Evidence: `experiments/threats/SUMMARY.md`, `experiments/threats/runs/gpt-6-luna.metrics.json`, `gpt-5.6-luna.metrics.json` and `gpt-4.1-mini.metrics.json` in the same directory; controls: `docs/threat-model.md`. A finite fixture suite does not establish immunity.
- **Operational failure and spend:** the graph limits rounds and calls, retries transient tool failures, and separates operational failure from insufficient evidence. Bounds are defined in `src/labourlens/agent/graph.py`; MCP timeouts and quarantines are documented in `docs/mcp-demo-transcript.md`. A bounded graph does not guarantee a fixed provider bill.
- **Privacy and rights:** keys stay in environment variables; logs are redacted and private. Questions, feedback and answers can still contain personal data or restricted excerpts. Redaction is not anonymization. Access controls and explicit retention remain necessary (`docs/audit-and-logging.md`, `docs/deploy.md`).

**Known numerical integrity gap:** a figure appearing in a cited passage is not cross-checked against validated dataset observations for the same indicator and period. T-I06 exposes that gap despite quotation and number-presence validation. A deterministic passage/dataset numerical cross-check is a proposal, not built; it would need compatible population, adjustment, units and release vintage, and must surface genuine source conflicts rather than silently overwrite them.

Run traces and audit records expose configuration, evidence identifiers, tool outcomes, errors, guard events, latency and estimated costs. Feedback joins to a run for investigation. Monitoring and retention commands are documented in `docs/audit-and-logging.md`; their presence does not imply an active operations service. The owner must review prepared source/gold/answer samples, resolve label ambiguities, confirm or revert the provisional default (D-030/D-033) and record remaining protocol sign-off. Executed held-out comparisons do not resolve these review gaps. Researchers retain responsibility for checking evidence and approving policy use.
