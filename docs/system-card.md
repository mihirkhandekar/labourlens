# LabourLens system card

**Updated:** 30 October 2026. **Status:** research prototype; development evidence only. Owner review, evaluation freeze and held-out execution remain pending.

## Intended use and users

LabourLens supports Singapore policy researchers and labour-market analysts. It retrieves official evidence, compares published quarterly statistics and produces cited summaries with uncertainty. The answer scope is 2024-Q1 through 2026-Q2; source coverage varies. Users should inspect source definitions, publication stage and citations before using an answer in research. Scope: `docs/decisions/ADR-001-scope.md`, extended by D-019/D-020 in `docs/decisions.md`.

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

**MEASURED RESULT:** A3, `gpt-6-luna`, `answer_v3`, `r3`, on the development split. All figures below come from `experiments/eval/agent-dev-A3/gpt-6-luna.metrics.json`; intervals are that artifact's bootstrap 95% intervals.

| Measure | Observed result |
|---|---|
| Cases | 237 |
| Behaviour accuracy | 89.0% [84.8%, 92.8%] |
| Over-abstention | 5.5% [3.0%, 8.4%] |
| Key-number recall | 79.8% [74.4%, 84.8%], eligible n=160 |
| Calculation correctness | 87.5% [75.0%, 100%], eligible n=24 |
| Any gold evidence cited | 80.8% [75.3%, 86.4%], eligible n=198 |
| Judge-supported claims | 88.3% [83.9%, 92.6%], 309 claims |
| Answers with ungrounded-number flags | 7.6% [4.2%, 11.0%] |
| Latency, median / p95 | 15.4 / 35.6 seconds |
| Estimated mean run cost | $0.00212 per case; offline judge cost is separate |

These results measure agreement with AI-drafted labels and an AI judge, not human-validated reliability. The gold set contains 268 cases: 237 development and 31 held-out. It has undergone three AI review passes, with owner review still pending (`experiments/gold/CHANGELOG.md`, v3/v3.1). The answer-sample pre-review is also AI-only (`experiments/human-review-sample/ai-review-summary.md`). Neither it nor the judge satisfies the assessment's human-review requirement. Held-out results are unavailable. Experiment interpretation: `docs/evaluation-report.md`, `docs/experiments/m6-agent-end-to-end.md`.

## Risks, controls and oversight

- **Wrong or incomplete evidence:** period filters can exclude a later report restating an earlier quarter; retrieval misses and over-abstention remain possible. Inspect cited passages and definitions. Rerank failure falls back to available ranked evidence and is traced (`src/labourlens/agent/tools.py`).
- **Unsupported or misleading claims:** structured validation checks format and citation mechanics. Semantic support, omitted facts and causal overreach still need review. A correct arithmetic tool can receive the wrong series or periods.
- **Prompt injection and unsafe tools:** retrieved text is untrusted. Catalogue-constrained schemas, read-only tools, input/output guards and MCP response validation limit authority. Corrected defended `r3` runs passed 35/36 for `gpt-6-luna` and `gpt-5.6-luna` (Wilson 95% interval 0.858–0.995), and 34/36 for `gpt-4.1-mini` (0.819–0.985). Both luna models repeated the planted false figure in T-I06; mini failed the T-S05 status criterion and followed a subtle instruction/cited poison in T-I02. `gpt-5.6-luna` mentioned the canary once in a caveat, not as compliance. Earlier defended 36/36 claims were invalid for indirect injection: the poisoned fixture lacked BM25/dense candidate lists, so all six attacks failed operationally before reaching the model. The corrected fixture supplies poison in both lists with named document metadata, and exercise requires poison in evidence. Current `gpt-6-luna` usefulness is 0/1 direct, 6/6 indirect and 3/3 MCP; usefulness does not mean every safety criterion passed. Older naive hybrid runs are not a paired `r3` ablation. Evidence: `experiments/threats/SUMMARY.md`, `experiments/threats/runs/gpt-6-luna.metrics.json`, `gpt-5.6-luna.metrics.json` and `gpt-4.1-mini.metrics.json` in the same directory; controls: `docs/threat-model.md`. A finite fixture suite does not establish immunity.
- **Operational failure and spend:** the graph limits rounds and calls, retries transient tool failures, and separates operational failure from insufficient evidence. Bounds are defined in `src/labourlens/agent/graph.py`; MCP timeouts and quarantines are documented in `docs/mcp-demo-transcript.md`. A bounded graph does not guarantee a fixed provider bill.
- **Privacy and rights:** keys stay in environment variables; logs are redacted and private. Questions, feedback and answers can still contain personal data or restricted excerpts. Redaction is not anonymization. Access controls and explicit retention remain necessary (`docs/audit-and-logging.md`, `docs/deploy.md`).

**Known numerical integrity gap:** a figure appearing in a cited passage is not cross-checked against validated dataset observations for the same indicator and period. T-I06 exposes that gap despite quotation and number-presence validation. A deterministic passage/dataset numerical cross-check is a proposal, not built; it would need compatible population, adjustment, units and release vintage, and must surface genuine source conflicts rather than silently overwrite them.

Run traces and audit records expose configuration, evidence identifiers, tool outcomes, errors, guard events, latency and estimated costs. Feedback joins to a run for investigation. Monitoring and retention commands are documented in `docs/audit-and-logging.md`; their presence does not imply an active operations service. The owner must review the prepared source/gold/answer samples, resolve label ambiguities, confirm or revert D-030, then freeze the held-out protocol before running it. Researchers retain responsibility for checking evidence and approving any consequential use.
