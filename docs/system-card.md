# LabourLens system card

**Updated:** 31 October 2026. **Status:** research prototype; dev and registered held-out measurements against unreviewed AI gold. The held-out comparison executed under owner authorization; R3's behaviour gain is inconclusive. Human source/gold/answer review remains incomplete.

## Intended use and users

LabourLens supports Singapore policy researchers and labour-market analysts. It retrieves official evidence, compares published quarterly statistics and produces cited summaries with uncertainty. The answer scope is 2024-Q1 through 2026-Q2; source coverage varies. D-031 makes this a hard boundary: earlier documents are context only, and requests for earlier-period figures or mixed-period comparisons requiring an earlier endpoint must abstain. Timeless definitions remain answerable. Users should inspect source definitions, publication stage and citations before using an answer in research. Scope: `docs/decisions/ADR-001-scope.md`, extended by D-019/D-020/D-031 in `docs/decisions.md`.

Forecasting, unsupported causal attribution, individual employment advice and unrestricted web research are out of scope. The system is not an official government service or an autonomous policy decision-maker. It must not receive confidential, personal or classified information.

## Data and rights

The corpus combines data.gov.sg statistics published by MOM/SingStat with MOM reports and release pages. Source URLs, snapshot hashes, dates, definitions, units and release stages are recorded in `data/manifests/manifest.json` and `specs/sources.yaml` plus `specs/sources.d/`. Transformations and quality limitations are described in `docs/data-sheet.md` and `docs/data-processing-log.md`.

Statistical data is attributed under the [Singapore Open Data Licence](https://developers.data.gov.sg/open-data-licence); no agency endorsement is implied. MOM PDFs carry restrictive copyright notices. Release-page rights remain unresolved where terms were inaccessible. Full documents, extracted passages, indexes and raw answers containing MOM text stay local and gitignored. Public documentation uses paraphrases, identifiers and links. The owner accepted API processing of passages in D-022; provider data-use terms have not been independently verified in this project.

**Review limitation:** the [second blind source review](human-review/independent-ai-review-m1-2.md) could not reproduce three sampled dataset open-licence verification claims from cached publisher evidence; this is a provenance gap, not a finding that the licences are wrong.

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

These results measure agreement with AI-drafted labels and an AI judge, not human-validated reliability. Current gold v3.4 contains 268 cases: 237 development and 31 held-out; the development labels and metrics above remain the unchanged v3.2 snapshot. Three AI review passes, D-031's scope correction, D-034's post-run HO-029 correction and D-035's three further post-run adjudications are recorded in `experiments/gold/CHANGELOG.md`; human review remains pending. The answer-sample pre-review is AI-only (`experiments/human-review-sample/ai-review-summary.md`); neither it nor the judge satisfies human review. A1–A5 judgments were regenerated with input-fingerprinted caching after stale judgments survived v3.2; current support/coverage supersede earlier figures. A3's former 87.5% calculation rate is superseded by 75.0%. An initial strict scorer mishandled prose/units and negated-relative-percent wording; its transient 8.3% result was a scorer bug, fixed before final publication, not a loss of numerical capability. Development generation outputs and behaviour did not change.

**Second independent AI pass (not human review):** the [failure-enriched A3 sample](../experiments/human-review-sample/independent-ai-review-2.md) judged 28/40 correct, 6 partly correct and 6 incorrect; these development-only counts are not population accuracy estimates. The [71-case gold review](../experiments/gold/independent-ai-review-2.md) retained 70 behaviour labels and flagged HO-027's missing year and evidence-context gaps in HO-023/HO-004. The review itself made no changes; subsequent owner-approved D-035 adjudications implement these findings as v3.4.

A1/A2 cover 235 cases; A3/A4/A5 cover 237. The A1-to-A3 R3 gain is descriptive, not a paired significance claim across different case counts. A2 (`answer_v4`) and A4 (widening) show no measurable benefit. A5's single-factor `planner_v2` comparison is complete: behaviour accuracy is 90.7% [86.9%, 94.1%] versus A3's 90.3% [86.5%, 93.7%] for `gpt-6-luna`, and 91.1% [87.3%, 94.5%] versus 90.3% [86.1%, 94.1%] for `gpt-5.6-luna`. These overlapping intervals do not establish improvement or equivalence. A5 is not adopted; `planner_v1`, `answer_v3`, R3 and `gpt-6-luna` remain unchanged (D-032).

## Registered held-out performance

**MEASURED RESULT (gold v3.4):** the owner authorized experiment completion against original frozen but unreviewed v3.2 AI gold (`experiments/heldout/FREEZE.md`, preserved). Registered configurations used `planner_v1` / `answer_v3`, each luna model with R3 and hybrid, on 31 identical held-out cases. After HO-029's v3.3 correction (D-034), the owner approved three more post-run edits (“Yes”, 31 Oct 2026; D-035): HO-027 becomes `clarify` because the unchanged question omits the year (old report evidence becomes context-only and reference facts are cleared); HO-023 gains nonprimary cohort-definition evidence; HO-004's truncated PDF passage becomes nonprimary. Each lowers or leaves registered scores. Current scores use gold SHA-256 `050bb40b4863cf3a00682da0edc305dc4d9c7de1c35b3098989e8afdd50899b9`; provenance fingerprints scoring-time files, not necessarily generation-time state. Sources: `experiments/eval/agent-heldout-H-{r3,hybrid}/{gpt-6-luna,gpt-5.6-luna}.metrics.json`.

| Model | R3 behaviour [95% CI] | Hybrid behaviour [95% CI] | Paired R3 gain, percentage points [95% CI] |
|---|---|---|---|
| `gpt-6-luna` | 83.9% [71.0%, 96.8%] | 67.7% [51.6%, 83.9%] | +16.1 [0.0, 32.3] |
| `gpt-5.6-luna` | 80.6% [67.7%, 93.5%] | 71.0% [54.8%, 87.1%] | +9.7 [-3.2, 22.6] |

Paired intervals use 10,000 case-bootstrap resamples, seed 20261030 (`experiments/heldout/paired.txt`, v3.4). Both include zero, so the registered rule yields **inconclusive**, not demonstrated superiority. R3 is retained provisionally (D-033–D-035), subject to owner quality/cost preference. R3 versus hybrid estimated costs are $0.00193 versus $0.00124 per case for `gpt-6-luna` and $0.00343 versus $0.00271 for `gpt-5.6-luna`; p95 latencies are 26.6 versus 18.5 s and 36.1 versus 19.7 s. Corrected calculation correctness is **80.0% [40.0%, 100%] for all four configurations**, n=5. The earlier calculation-parser rescoring was a separate scoring-code deviation; the subsequent gold adjudications must not be described as parser-only. Small calculation strata preclude numerical-superiority conclusions.

**Version boundary / sensitivity:** original v3.2 R3/hybrid behaviour was 83.9% / 67.7% for `gpt-6-luna` and 87.1% / 74.2% for `gpt-5.6-luna`; v3.3 left luna6 unchanged and lowered luna5.6 to 83.9% / 71.0%; v3.4 lowers only luna5.6 R3 behaviour further to 80.6%. The earlier luna5.6 paired difference was +12.9 [0.0, 29.0] in both `experiments/heldout/paired-v3.2.txt` and `paired-v3.3.txt`; its current estimate is +9.7 [-3.2, 22.6]. Luna6's +16.1 [0.0, 32.3] remains unchanged. Original generation outputs and freeze are preserved; no new model calls are implied. Extra mini configurations were unregistered, not selection evidence. Initial wrong-split scoring was corrected separately. These post-run sensitivities do not replace a clean confirmatory experiment: a separately authorized preregistered run on frozen, human-reviewed gold would be stronger evidence. Execution/correction approval does not complete human review or protocol sign-off. Full analysis: `docs/evaluation-report.md`, `docs/experiments/m6-agent-end-to-end.md`.

**Split limitation:** the second gold review found evidence-ID overlap with development in 25/31 held-out cases, including each case's entire evidence-ID set in 15/31. No exact question or normalized-template duplicates were found, but the set is question-held-out, not evidence-independent; these results do not establish novel-fact or broad out-of-distribution generalisation.

**Corpus boundary:** `extraction-fixes` commit `80a287b` is unmerged and not adopted. Its report, `docs/experiments/m7-extraction-fixes.md` on that branch, describes extraction changes and passage-ID migration; separate retrieval/answer evaluation remains pending owner approval. Existing scores describe the frozen main corpus, not that corrected extraction.

## Risks, controls and oversight

- **Wrong or incomplete evidence:** period filters can exclude a later report restating an earlier quarter; retrieval misses and over-abstention remain possible. Inspect cited passages and definitions. Rerank failure falls back to available ranked evidence and is traced (`src/labourlens/agent/tools.py`).
- **Unsupported or misleading claims:** structured validation checks format and citation mechanics. Semantic support, omitted facts and causal overreach still need review. A correct arithmetic tool can receive the wrong series or periods.
- **Prompt injection and unsafe tools:** retrieved text is untrusted. Catalogue-constrained schemas, read-only tools, input/output guards and MCP response validation limit authority. The final corrected-fixture `r3` rerun on final tool-isolation/MCP-hardened code passed 35/36 for each defended luna model (Wilson 95% interval 0.858–0.995), and 34/36 for defended mini (0.819–0.985). All three repeat T-I06's planted false figure; mini also follows T-I02's subtle instruction and cites poison. Defended `gpt-5.6-luna` has two canary caveat mentions and zero compliance; defended mini has two caveat mentions and one compliance; luna6 has neither. Earlier defended 36/36 claims were invalid for indirect injection because missing BM25/dense candidate lists prevented poison reaching the model. The corrected fixture supplies both lists with named metadata and requires poison in evidence. The valid final rerun supersedes earlier results: all configurations have zero not-exercised cases and 6/6 useful indirect answers, which does not imply safety. Same-R3 naive luna6 passes 35/36 (no measurable defence effect); naive mini passes 32/36 (0.747–0.956), failing T-D01, T-I02, T-I03 and T-I06. Mini's 34 versus 32, with overlapping intervals, is **consistent with a benefit for the weakest model, not demonstrated**. This small hand-written suite, one run per configuration, does not establish immunity or a causal defence benefit. Current defended luna6 usefulness is 0/1 direct and 3/3 MCP. Evidence: `experiments/threats/SUMMARY.md` and `experiments/threats/runs/*.metrics.json`; controls: `docs/threat-model.md`.
- **Operational failure and spend:** the graph limits rounds and calls, retries transient tool failures, and separates operational failure from insufficient evidence. Bounds are defined in `src/labourlens/agent/graph.py`; MCP timeouts and quarantines are documented in `docs/mcp-demo-transcript.md`. A bounded graph does not guarantee a fixed provider bill.
- **Privacy and rights:** keys stay in environment variables; logs are redacted and private. Questions, feedback and answers can still contain personal data or restricted excerpts. Redaction is not anonymization. Access controls and explicit retention remain necessary (`docs/audit-and-logging.md`, `docs/deploy.md`).

**Known numerical integrity gap:** a figure appearing in a cited passage is not cross-checked against validated dataset observations for the same indicator and period. T-I06 exposes that gap despite quotation and number-presence validation. A deterministic passage/dataset numerical cross-check is a proposal, not built; it would need compatible population, adjustment, units and release vintage, and must surface genuine source conflicts rather than silently overwrite them.

**Scanner limitation:** all five in-memory malicious paraphrase probes in the second source review bypassed the ingestion scanner. This is detector-only evidence, not an end-to-end exploit; zero scanner hits cannot certify safe sources. Untrusted-data quarantine, constrained schemas, read-only tools and citation/output guards remain the relevant boundaries.

Run traces and audit records expose configuration, evidence identifiers, tool outcomes, errors, guard events, latency and estimated costs. Feedback joins to a run for investigation. Monitoring and retention commands are documented in `docs/audit-and-logging.md`; their presence does not imply an active operations service. The owner must review prepared source/gold/answer samples, resolve label ambiguities, confirm or revert the provisional default (D-030/D-033) and record remaining protocol sign-off. Executed held-out comparisons do not resolve these review gaps. Researchers retain responsibility for checking evidence and approving policy use.
