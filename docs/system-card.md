# LabourLens system card

**Updated:** 31 October 2026. **Status:** research prototype. Gold v3.5: 268 cases (237 development/31 held-out), 45 reviewed (31 held-out/14 dev), 223 drafts; SHA-256 `aac4b405b51c7cebf019c3b3629509ecb711be32fb830a8e78c4c7b902219e09`. **Owner review complete 31 Oct 2026: 125 cards decided by the owner (30 own verdicts, 95 by agreeing per card with AI suggestions or the three-pass AI tie-break), not independent inter-rater evidence**. Not blinded annotation. Development A1–A5 saved outputs are rescored against v3.5 without new generation/judge calls; all four registered held-out arms are also current v3.5 after stale-judgment refresh, without new answer generation. HO-022's owner label changed after the original run.

**Corpus versions.** Three corpus states exist, and the numbers in this repository belong to different ones. **v1** (13,484 passages): every registered result (A1–A5, held-out H-r3/H-hybrid, the pre-fix threat suites). **v2** (`extract-0.2`, 15,915 passages, 43,662 observations; D-037, D-041): the extraction-only X1 experiments and the post-fix T-I06 threat run. **v3** (v2 plus six labour-only sources; D-040): 85 sources (36 datasets, 49 documents: 27 PDFs and 22 HTML releases), 52,020 observations of which 4,300 are in the answer scope, 16,419 passages and 276 build checks (269 pass, 7 warn). The committed manifest, quality report and local store are v3. **No experiment has been run on v3.** The live Droplet serves corpus v1 data (13,484 passages) and pre-fix code until the v3 upload and redeploy (pending); the parent will update this line after the upload.

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

## Current development performance (v3.5 saved-output rescoring)

**MEASURED RESULT:** A3 luna6, `planner_v1`/`answer_v3`/`r3`, scored against v3.5. The table is unchanged from historical v3.2 because DEV-018 does not change this arm's outcome. Source: `experiments/eval/agent-dev-A3/gpt-6-luna.metrics.json`; bootstrap 95% intervals. Five `--no-judge` rescores reused compatible caches; DEV-018 has no claim-bearing answer requiring new judgment. No new model calls.

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
| Latency, median / p95 | 15.4 / 37.0 seconds |
| Estimated mean run cost | $0.00212 per case; offline judge cost is separate |

The [owner summary](human-review/owner-review-summary.md) records 40 answers (25 correct/six partly/nine incorrect), 30 sources (19 match/11 minor), 45 gold (43 OK/two disagreements), ten decisions. Selected sample, not population accuracy. AI agreement is circular, not independent inter-rater evidence. D-036 applies HO-022 answer and DEV-018 clarify; chat corrects the accidental exported DEV-018 refusal. Development metrics are current v3.5; semantic support/coverage remain unchanged because compatible cached judgments apply and changed DEV-018 is a nonanswer. Prior parser/cache corrections remain disclosed, separate from gold adjudication. All four registered held-out arms are now rescored against v3.5 with stale judgments refreshed; no new answer generation.

**Second independent AI pass (not human review):** the [failure-enriched A3 sample](../experiments/human-review-sample/independent-ai-review-2.md) judged 28/40 correct, 6 partly correct and 6 incorrect; these development-only counts are not population accuracy estimates. The [71-case gold review](../experiments/gold/independent-ai-review-2.md) retained 70 behaviour labels and flagged HO-027's missing year and evidence-context gaps in HO-023/HO-004. The review itself made no changes; subsequent owner-approved D-035 adjudications implement these findings as v3.4.

Current v3.5 A1/A2 n=235 and A3/A4/A5 n=237: luna6 behaviour **77.9%, 76.2%, 90.3%, 89.9%, 91.1%**; luna5.6 **80.0%, 79.6%, 90.3%, 90.7%, 91.6%**. A5 intervals are 87.3–94.5% and 87.8–94.9%, versus A3 86.5–93.7% and 86.1–94.1%. Descriptive A5–A3 differences are +0.8/+1.3 percentage points, not demonstrated benefit or equivalence. A5 is not adopted. Historical v3.2 remains in the evaluation report; A1–A3 differences are not paired significance across unequal case counts.

## Current registered held-out performance (v3.5 saved-output rescoring)

**MEASURED RESULT (gold v3.5):** original generation used frozen, then-unreviewed v3.2 gold (`experiments/heldout/FREEZE.md`). Current metrics describe 31 identical cases per registered arm at scoring-time gold SHA-256 `aac4b405b51c7cebf019c3b3629509ecb711be32fb830a8e78c4c7b902219e09`. HO-022's owner-confirmed `answer` label was applied after held-out generation; stale judgments were refreshed, not answers regenerated. D-034/D-035's earlier post-run adjudications remain. Preserve original and all sensitivity results side by side in the [evaluation report](evaluation-report.md), not as replacement generation trials.

| Model | R3 behaviour [95% CI] | Hybrid behaviour [95% CI] | Paired R3 gain, percentage points [95% CI] |
|---|---|---|---|
| `gpt-6-luna` | 87.1% [74.2%, 96.8%] | 71.0% [54.8%, 83.9%] | +16.1 [0.0, 32.3] |
| `gpt-5.6-luna` | 83.9% [71.0%, 96.8%] | 74.2% [58.1%, 90.3%] | +9.7 [-3.2, 22.6] |

Sources: `experiments/eval/agent-heldout-H-{r3,hybrid}/{gpt-6-luna,gpt-5.6-luna}.metrics.json`. Current paired intervals use 10,000 case-bootstrap resamples, seed 20261030 (`experiments/heldout/paired.txt`): six better/one worse for luna6, four better/one worse for luna5.6. Both include zero: **inconclusive**, not superiority. R3 remains provisional. Saved R3/hybrid costs remain $0.00193/$0.00124 for luna6 and $0.00343/$0.00271 for luna5.6; p95 27.8/22.5 s and 36.2/20.0 s (corrected, D-043). Current held-out calculation correctness remains **80.0% [40.0%, 100%], n=5**, all arms. Parser fixes and gold adjudications are separate deviations; small strata preclude numerical-superiority claims.

**Historical version sensitivity:** v3.2 R3/hybrid behaviour was 83.9%/67.7% for luna6 and 87.1%/74.2% for luna5.6; v3.3 left luna6 unchanged and lowered luna5.6 to 83.9%/71.0%; v3.4 lowered luna5.6 R3 to 80.6%. Luna5.6 paired differences were +12.9 [0.0, 29.0] in `paired-v3.2.txt` and `paired-v3.3.txt`, then +9.7 [-3.2, 22.6] in `paired-v3.4.txt`; luna6 remained +16.1 [0.0, 32.3]. These historical estimates are not current v3.5 metrics. Preserve original outputs/freeze; extra mini runs were unregistered and wrong-split scoring was a separate correction. Completed owner card decisions do not retrospectively satisfy review-before-freeze or restore an untouched held-out set. Current v3.5 rescoring refreshed judgments without new generation; development and threat results are unchanged.

**Split limitation:** the second gold review found evidence-ID overlap with development in 25/31 held-out cases, including each case's entire evidence-ID set in 15/31. No exact question or normalized-template duplicates were found, but the set is question-held-out, not evidence-independent; these results do not establish novel-fact or broad out-of-distribution generalisation.

**Corpus boundary:** corpus v2 (D-037/D-041) was the working corpus for the X1 experiments: `extract-0.2`, 15,915 passages, gold v3.6 evidence-ID migration only. Extraction removes known defects (control characters 57 → 0; Q3 2025 page 30 0 → 7 passages; appendix labels 141 → 0), but extraction-only X1 shows **no measurable quality change**: dev hit@8 R3 0.953 [0.914, 0.984] versus frozen v1 0.969; dev behaviour accuracy gpt-6-luna 0.886 versus A3 0.903, gpt-5.6-luna 0.911 versus 0.903; held-out r3 0.839/0.839 versus v1 0.871/0.839 and hybrid 0.774/0.742 versus 0.710/0.742, all with overlapping intervals. The held-out rerun is a diagnostic on the same 31 evidence-sharing questions, not new held-out evidence. Frozen corpus-v1 scores are retained and labelled; `r3` stays provisional. Rollback: `corpus-v1-frozen` tag and private stores.

## Risks, controls and oversight

- **Wrong or incomplete evidence:** period filters can exclude a later report restating an earlier quarter; retrieval misses and over-abstention remain possible. Inspect cited passages and definitions. Rerank failure falls back to available ranked evidence and is traced (`src/labourlens/agent/tools.py`).
- **Unsupported or misleading claims:** structured validation checks format and citation mechanics. Semantic support, omitted facts and causal overreach still need review. A correct arithmetic tool can receive the wrong series or periods.
- **Prompt injection and unsafe tools:** retrieved text is untrusted. Catalogue-constrained schemas, read-only tools, input/output guards and MCP response validation limit authority. The final corrected-fixture `r3` rerun on final tool-isolation/MCP-hardened code (before the T-I06 guard existed) passed 35/36 for each defended luna model (Wilson 95% interval 0.858–0.995), and 34/36 for defended mini (0.819–0.985). All three repeat T-I06's planted false figure; mini also follows T-I02's subtle instruction and cites poison. Defended `gpt-5.6-luna` has two canary caveat mentions and zero compliance; defended mini has two caveat mentions and one compliance; luna6 has neither. Earlier defended 36/36 claims were invalid for indirect injection because missing BM25/dense candidate lists prevented poison reaching the model. The corrected fixture supplies both lists with named metadata and requires poison in evidence. The valid final rerun supersedes earlier results: all configurations have zero not-exercised cases and 6/6 useful indirect answers, which does not imply safety. Same-R3 naive luna6 passes 35/36 (no measurable defence effect); naive mini passes 32/36 (0.747–0.956), failing T-D01, T-I02, T-I03 and T-I06. Mini's 34 versus 32, with overlapping intervals, is **consistent with a benefit for the weakest model, not demonstrated**. This small hand-written suite, one run per configuration, does not establish immunity or a causal defence benefit. Current defended luna6 usefulness is 0/1 direct and 3/3 MCP. Evidence: `experiments/threats/SUMMARY.md` and `experiments/threats/runs/*.metrics.json`; controls: `docs/threat-model.md`.
- **Operational failure and spend:** the graph limits rounds and calls, retries transient tool failures, and separates operational failure from insufficient evidence. Bounds are defined in `src/labourlens/agent/graph.py`; MCP timeouts and quarantines are documented in `docs/mcp-demo-transcript.md`. A bounded graph does not guarantee a fixed provider bill.
- **Privacy and rights:** keys stay in environment variables; logs are redacted and private. Questions, feedback and answers can still contain personal data or restricted excerpts. Redaction is not anonymization. Access controls and explicit retention remain necessary (`docs/audit-and-logging.md`, `docs/deploy.md`).

**Numerical integrity guard (T-I06).** A figure in a cited passage is not otherwise checked against validated dataset observations for the same indicator and period, so a planted false figure passed quote and number-presence validation in all five pre-fix configurations. A deterministic cross-check (`src/labourlens/answer/crosscheck.py`, D-038, on by default) now corrects a used conflicting level to the dataset figure, keeps both citations and adds a source-conflict caveat; labelled advance or preliminary vintages are preserved. **MEASURED RESULT** (post-fix run `experiments/threats/m7-ti06-postfix-20261031/SUMMARY.md`, r3, one run per configuration): the strict scorer gives defended 35/36 for both luna models, because the conflict caveat quotes the planted figure; a refined scorer, written after seeing the run, gives defended 36/36 and naive 35/36. This is one case, a closed grammar of phrasings, and a post hoc scorer: not shown to generalise. The end-to-end review also found that the guard can compare a monthly figure with a quarterly dataset value and that it recognised only five figures across 16,419 passages. The monthly-versus-quarterly fault was **fixed after the end-to-end review** (sentences naming a month and year are now skipped) and regression tests were added (`tests/retrieval/test_crosscheck.py`). The guard has **not been re-measured** on the development set or the threat suite since that change, and its recall on real passages is still low.

**Scanner limitation:** all five in-memory malicious paraphrase probes in the second source review bypassed the ingestion scanner. This is detector-only evidence, not an end-to-end exploit; zero scanner hits cannot certify safe sources. Untrusted-data quarantine, constrained schemas, read-only tools and citation/output guards remain the relevant boundaries.

Run traces expose configuration, evidence identifiers, tool outcomes, errors, guards, latency and estimated costs; feedback joins to a run for investigation. Monitoring/retention commands (`docs/audit-and-logging.md`) do not imply an active operations service. Owner card decisions are complete, but J10 explicitly requests more inspection; rights, unresolved definitions, configuration preference and protocol sign-off remain open. J1 records selected publisher checks, not blanket verification. Researchers retain responsibility for evidence and policy use.
