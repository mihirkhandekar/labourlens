# M7 — Evidence-disjoint held-out v2 design

**31 October 2026. Status: source audit and blind-authored draft complete; full confirmatory design A BLOCKED by lack of verified untouched substantive documents. No system evaluation was run.**

## Requirement, scope and decision boundary

**REQUIREMENT:** fix the evidence-overlap limitation, preserve existing results, author new cases blind to system outputs, preregister before any generation, compare only retrieval (`r3` versus `hybrid`) with the same two models and harness. No corpus changes by this worker. **DECISION already approved by owner:** investigate/fix overlap, not manufacture a new evidence-holdout claim from old evidence.

**VERIFIED FACT:** ExtractionMerge confirmed the offline extract-0.2 rebuild complete before this worker read passages: 15,915 passages, 43,662 observations, same 46 document sources. Passage identity remains source + physical block/section + text hash. Its gold v3.6 migration changes identifiers only. This authoring uses observations, whose IDs are stable, and no passage IDs. No questions were submitted to the system and no outputs exist for these new IDs.

**PROPOSAL / recommendation:** A below is the correct confirmatory study. Do not silently substitute the available 60-case structured-only draft for unseen-document R3 validation. The draft is useful as a **separately labelled reserved-dataset diagnostic**, conditional on owner acceptance of its narrower evidence claim. `experiments/heldout-v2/FREEZE.md` records the draft/hash and blocks generation until that choice and pre-run human review. It does not claim an approved completed confirmatory freeze.

## 1. Exact overlap audit

Input is original v3.5 gold SHA-256 `aac4b405b51c7cebf019c3b3629509ecb711be32fb830a8e78c4c7b902219e09`, preserved at `private/corpus-v1-frozen/gold-v3.5.jsonl`; current v3.6 ID migration has the same overlap counts. There are 237 dev and 31 original held-out cases. The acceptable-evidence union is `evidence_text[].passage_ids` plus `evidence_data[].observation_ids`; duplicate IDs within a case count once. Partial/context-only evidence is inventoried separately, not scored as an acceptable alternative.

**MEASURED RESULT:** **25/31** have at least one acceptable evidence ID in dev; **14/31** have their entire nonempty acceptable evidence union in dev. The previously supplied 15/31 entire-set figure is **not reproduced** against current v3.5/v3.6; retain this correction, not a forced match. HO-025/HO-030 have empty unions and are not counted as fully shared. New passage identifiers do not turn old source content into unseen evidence.

The machine-readable `experiments/heldout-v2/evidence-audit.json` lists **every held-out passage/observation ID and its sharing dev case IDs**, **all 46 documents** and **all 3,914 dataset-period groups**, including historical periods and explicit in-scope flags. It also lists partial/context-only evidence and 31 inspected prior development-run files. No raw answers or MOM text are included.

| Held-out | Passage / observation IDs | IDs shared with dev | Sharing dev cases | Entire nonempty union shared |
|---|---:|---:|---|---|
| HO-001 | 2 / 0 | 1 | DEV-614 | no |
| HO-002 | 16 / 0 | 0 | none | no |
| HO-003 | 5 / 0 | 0 | none | no |
| HO-004 | 2 / 0 | 2 | DEV-010, DEV-328, DEV-329 | yes |
| HO-005 | 11 / 0 | 0 | none | no |
| HO-006 | 0 / 2 | 2 | DEV-008, DEV-013, DEV-016, DEV-313, DEV-323, DEV-429, DEV-433 | yes |
| HO-007 | 0 / 2 | 2 | DEV-008, DEV-013, DEV-016, DEV-313, DEV-326, DEV-429, DEV-512 | yes |
| HO-008 | 0 / 2 | 2 | DEV-314, DEV-508, DEV-509 | yes |
| HO-009 | 0 / 2 | 1 | DEV-432 | no |
| HO-010 | 0 / 2 | 2 | DEV-434 | yes |
| HO-011 | 0 / 2 | 2 | DEV-116, DEV-430, DEV-435 | yes |
| HO-012 | 3 / 0 | 2 | DEV-003, DEV-224, DEV-311, DEV-333 | no |
| HO-013 | 2 / 4 | 4 | DEV-007, DEV-021, DEV-029, DEV-030, DEV-321, DEV-524, DEV-525 | no |
| HO-014 | 1 / 4 | 5 | DEV-001, DEV-006, DEV-116, DEV-316, DEV-430, DEV-435 | yes |
| HO-015 | 1 / 6 | 7 | DEV-004, DEV-008, DEV-009, DEV-014, DEV-017, DEV-026, DEV-101, DEV-123, DEV-306, DEV-310, DEV-319, DEV-320, DEV-322, DEV-429, DEV-431, DEV-432, DEV-433 | yes |
| HO-016 | 1 / 0 | 1 | DEV-011, DEV-313 | yes |
| HO-017 | 2 / 0 | 1 | DEV-003, DEV-311, DEV-333 | no |
| HO-018 | 2 / 0 | 1 | DEV-023, DEV-312, DEV-335 | no |
| HO-019 | 3 / 1 | 2 | DEV-004, DEV-008, DEV-009, DEV-014, DEV-017, DEV-026, DEV-310, DEV-319, DEV-320, DEV-429, DEV-431, DEV-433 | no |
| HO-020 | 3 / 1 | 2 | DEV-011, DEV-313 | no |
| HO-021 | 2 / 2 | 4 | DEV-008, DEV-013, DEV-016, DEV-026, DEV-306, DEV-313, DEV-322, DEV-323, DEV-324, DEV-429, DEV-433 | yes |
| HO-022 | 2 / 2 | 2 | DEV-008, DEV-013, DEV-016, DEV-313, DEV-323, DEV-429 | no |
| HO-023 | 2 / 4 | 5 | DEV-004, DEV-008, DEV-009, DEV-014, DEV-017, DEV-026, DEV-101, DEV-128, DEV-306, DEV-310, DEV-319, DEV-320, DEV-322, DEV-429, DEV-431, DEV-433 | no |
| HO-024 | 3 / 1 | 2 | DEV-023, DEV-312, DEV-335 | no |
| HO-025 | 0 / 0 | 0 | none | no |
| HO-026 | 0 / 2 | 2 | DEV-116, DEV-430, DEV-435 | yes |
| HO-027 | 0 / 1 | 1 | DEV-001, DEV-006, DEV-316, DEV-430 | yes |
| HO-028 | 2 / 0 | 2 | DEV-012, DEV-331, DEV-334 | yes |
| HO-029 | 2 / 0 | 2 | DEV-023, DEV-026, DEV-306, DEV-312, DEV-322, DEV-324, DEV-335 | yes |
| HO-030 | 0 / 0 | 0 | none | no |
| HO-031 | 1 / 0 | 0 | none | no |

### Document coverage

Counts are case count / distinct acceptable passage IDs, using pre-migration gold for historical provenance. Passage counts show original / fixed corpus. Full per-source IDs are in the JSON inventory.

| Document source | Corpus passages original / fixed | Dev cases / IDs | Held-out cases / IDs | Observed prior dev-run exposure |
|---|---:|---:|---:|---|
| `mom-2023-q1-final` | 766 / 822 | 1 / 1 | 1 / 1 | yes |
| `mom-2023-q2-final` | 767 / 827 | 1 / 1 | 1 / 1 | yes |
| `mom-2023-q3-final` | 745 / 798 | 1 / 1 | 1 / 1 | yes |
| `mom-2023-q4-final` | 927 / 1074 | 1 / 1 | 2 / 2 | yes |
| `mom-2024-q1-advance` | 21 / 21 | 1 / 1 | 0 / 0 | yes |
| `mom-2024-q1-final` | 720 / 842 | 3 / 3 | 2 / 2 | yes |
| `mom-2024-q1-final-release` | 31 / 35 | 5 / 5 | 0 / 0 | yes |
| `mom-2024-q2-advance` | 24 / 24 | 1 / 1 | 0 / 0 | yes |
| `mom-2024-q2-final` | 887 / 1009 | 1 / 1 | 2 / 2 | yes |
| `mom-2024-q2-final-release` | 37 / 37 | 7 / 5 | 0 / 0 | yes |
| `mom-2024-q3-advance` | 22 / 22 | 2 / 2 | 0 / 0 | yes |
| `mom-2024-q3-final` | 845 / 985 | 1 / 1 | 3 / 3 | yes |
| `mom-2024-q3-final-release` | 26 / 26 | 7 / 5 | 0 / 0 | yes |
| `mom-2024-q4-advance` | 29 / 29 | 2 / 2 | 0 / 0 | yes |
| `mom-2024-q4-final` | 990 / 1120 | 1 / 1 | 2 / 2 | yes |
| `mom-2024-q4-final-release` | 32 / 29 | 9 / 5 | 0 / 0 | yes |
| `mom-2025-q1-advance` | 24 / 24 | 1 / 1 | 0 / 0 | yes |
| `mom-2025-q1-final` | 800 / 958 | 2 / 2 | 2 / 2 | yes |
| `mom-2025-q1-final-release` | 23 / 19 | 6 / 5 | 0 / 0 | yes |
| `mom-2025-q2-advance` | 26 / 22 | 2 / 2 | 0 / 0 | yes |
| `mom-2025-q2-final` | 867 / 1069 | 2 / 2 | 3 / 3 | yes |
| `mom-2025-q2-final-release` | 25 / 22 | 5 / 2 | 0 / 0 | yes |
| `mom-2025-q3-advance` | 25 / 21 | 3 / 3 | 2 / 3 | yes |
| `mom-2025-q3-final` | 889 / 1111 | 4 / 3 | 3 / 3 | yes |
| `mom-2025-q3-final-release` | 18 / 18 | 11 / 6 | 3 / 2 | yes |
| `mom-2025-q4-advance` | 23 / 23 | 7 / 4 | 1 / 1 | yes |
| `mom-2025-q4-final` | 1063 / 1283 | 6 / 6 | 3 / 3 | yes |
| `mom-2025-q4-final-release` | 20 / 17 | 8 / 4 | 3 / 3 | yes |
| `mom-2026-q1-advance` | 19 / 22 | 3 / 3 | 2 / 1 | yes |
| `mom-2026-q1-final` | 868 / 1068 | 3 / 5 | 4 / 4 | yes |
| `mom-2026-q1-final-release` | 8 / 16 | 7 / 3 | 4 / 2 | yes |
| `mom-2026-q2-advance` | 18 / 19 | 4 / 4 | 2 / 2 | yes |
| `mom-2026-q2-final` | 906 / 1080 | 4 / 4 | 7 / 6 | yes |
| `mom-2026-q2-final-release` | 12 / 16 | 17 / 4 | 8 / 4 | yes |
| `mom-jv2025` | 121 / 440 | 1 / 1 | 0 / 0 | yes |
| `mom-jv2025-release` | 38 / 35 | 9 / 6 | 0 / 0 | yes |
| `mom-lf2024-copyright` | 11 / 11 | 0 / 0 | 0 / 0 | not observed |
| `mom-lf2024-coverage-methodology` | 115 / 115 | 1 / 1 | 1 / 1 | yes |
| `mom-lf2024-survey-findings` | 161 / 210 | 0 / 0 | 0 / 0 | yes |
| `mom-lf2024-survey-highlights` | 4 / 4 | 2 / 1 | 0 / 0 | yes |
| `mom-lf2025-copyright` | 4 / 4 | 0 / 0 | 0 / 0 | not observed |
| `mom-lf2025-coverage-methodology` | 115 / 115 | 7 / 7 | 3 / 3 | yes |
| `mom-lf2025-survey-findings` | 198 / 250 | 21 / 15 | 1 / 1 | yes |
| `mom-lf2025-survey-highlights` | 1 / 1 | 5 / 1 | 0 / 0 | yes |
| `mom-wage-practices2024` | 187 / 196 | 4 / 4 | 0 / 0 | yes |
| `mom-wage-practices2024-release` | 26 / 26 | 2 / 2 | 0 / 0 | yes |

### Dataset-period coverage and possible reserve

The inventory contains all corpus dataset-period rows with dev/held-out case and observation IDs, not just cited groups. Within 2024-Q1–2026-Q2 there are 326 source-period groups. Existing gold cites 107 in-scope groups. Before excluding observed development-run evidence there are 219 uncited groups / 2,949 observations. Excluding all groups observed in prior saved dev evidence leaves **162 groups / 2,319 observations** (2,001 nonmissing), across 27 datasets. These are **candidate reserves**, not a certificate that developers never inspected them or rerank candidate pools never contained them. The 60-case draft uses 56 of these groups / 60 distinct observations; all are absent from both old gold evidence and observed prior dev evidence.

| Candidate reserved dataset | Reserved periods | Observations incl. missing |
|---|---|---:|
| `citizen_unemployment_rate` | 2024-Q1, 2024-Q2, 2024-Q3, 2025-Q2, 2025-Q3, 2025-Q4 | 12 |
| `job_vacancies_by_industry` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2026-Q2 | 210 |
| `job_vacancies_by_occupation` | 2024-Q1, 2024-Q2, 2024-Q4, 2026-Q1 | 20 |
| `job_vacancy_count` | 2024-Q1 | 1 |
| `job_vacancy_rate` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2025-Q1, 2025-Q2 | 6 |
| `job_vacancy_rate_by_industry` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2025-Q1, 2025-Q2, 2025-Q3, 2025-Q4, 2026-Q2 | 378 |
| `job_vacancy_rate_by_occupation` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2026-Q2 | 25 |
| `overall_unemployment_rate` | 2024-Q2, 2024-Q3, 2025-Q2, 2025-Q3 | 8 |
| `recruitment_rate_by_industry` | 2024-Q1, 2024-Q2, 2025-Q1, 2025-Q2, 2025-Q3, 2025-Q4, 2026-Q1, 2026-Q2 | 336 |
| `recruitment_rate_by_occupation` | 2024-Q1, 2025-Q3, 2025-Q4, 2026-Q1, 2026-Q2 | 15 |
| `reentry_12m` | 2024-Q1, 2025-Q3, 2025-Q4 | 3 |
| `resignation_rate` | 2024-Q1, 2024-Q2, 2024-Q4, 2025-Q1 | 4 |
| `resignation_rate_by_industry` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2026-Q2 | 210 |
| `resignation_rate_by_occupation` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2025-Q1, 2025-Q2, 2025-Q3, 2026-Q2 | 24 |
| `retrenched_by_industry` | 2024-Q1, 2024-Q2, 2024-Q3 | 126 |
| `retrenched_by_occupation` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2025-Q1, 2025-Q2, 2025-Q3, 2025-Q4 | 24 |
| `retrenched_permanent` | 2024-Q1, 2025-Q3, 2025-Q4 | 3 |
| `retrenched_permanent_by_industry` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2025-Q1, 2025-Q2, 2025-Q3, 2025-Q4, 2026-Q2 | 378 |
| `retrenched_permanent_by_occupation` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2025-Q1, 2025-Q2, 2025-Q3, 2026-Q2 | 24 |
| `retrenched_term_contract` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2025-Q1, 2025-Q2, 2025-Q3, 2025-Q4 | 8 |
| `retrenched_term_contract_by_industry` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2025-Q1, 2025-Q2, 2025-Q3, 2026-Q2 | 336 |
| `retrenched_term_contract_by_occupation` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2025-Q1, 2025-Q2, 2025-Q3, 2025-Q4, 2026-Q2 | 27 |
| `short_workweek_temporary_layoff` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2025-Q1 | 15 |
| `short_workweek_temporary_layoff_by_industry` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2025-Q1, 2025-Q2, 2025-Q3 | 84 |
| `unemployed_citizens` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2025-Q1, 2025-Q2, 2025-Q3, 2025-Q4 | 16 |
| `unemployed_overall` | 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2025-Q2 | 10 |
| `unemployed_residents` | 2024-Q1, 2024-Q3, 2024-Q4, 2025-Q1, 2025-Q2, 2025-Q3, 2025-Q4, 2026-Q2 | 16 |

### Which reserved documents actually exist?

Only three documents lack acceptable dev/original-held-out citations: `mom-lf2024-survey-findings`, `mom-lf2024-copyright`, `mom-lf2025-copyright`. Copyright sheets support **zero** in-scope labour-statistics answerable question families. The survey-findings document is substantive, but was already supplied to dev agents: e.g. `data/runs/agent-dev-A3/gpt-6-luna.jsonl` DEV-024, DEV-027, DEV-028 and others. It cannot be reserved retroactively. Therefore **zero verified untouched substantive source documents are available** for A.

| Evidence class | Factual lookup | Numerical comparison | Cross-source synthesis | Revision conflict | Ambiguity/insufficiency/causal | Adversarial |
|---|---|---|---|---|---|---|
| Verified untouched substantive documents | 0 | 0 | 0 | 0 | 0 | 0 |
| Copyright-only uncited documents | 0 | 0 | 0 | 0 | 0 | 0 |
| Candidate reserved dataset periods | 20 drafted | 16 drafted | 8 drafted (structured sources only) | 0 answerable vintage pairs; 4 abstentions drafted | 6 boundary cases drafted | 4 safe-answer injections + 2 refusals drafted |

These are authored-case counts, not counts of independent facts or a claim of exhaustive question capacity. The last two families contain intentional nonanswers; they are not called answerable evidence. No unseen report-backed synthesis or answerable advance/final revision pair can honestly be supplied from the current reserve.

## 2. Credible designs and leakage argument

| Design | Benefits / evaluation impact | Costs, dependencies and limits | Recommendation |
|---|---|---|---|
| **A. New >=60 cases from prospectively reserved evidence** | Genuine new evidence groups; six-family coverage; meaningful test of temporal filtering/reranking on unseen report facts | Needs untouched substantive documents and paired vintages; approve new sources or establish an auditable truly unexposed reserve. Current corpus cannot satisfy that prerequisite. Source/fact duplicates across documents must also be excluded | **Recommended confirmatory design**, blocked rather than falsely labelled complete |
| **B. Group-disjoint re-split of the existing 268 cases** | Easy to describe source/period grouping and estimate feasibility without model calls | R3 and prompts were selected using current dev. Moving those examples/evidence into a new test partition does not unsee tuning. A valid fresh split requires configuration selection from scratch without contaminated groups, a new development corpus, and fresh untouched final test evidence | Reject as retrospective confirmatory evidence; exploratory only |
| **C. Paired original-held-out + new reserved-dataset diagnostic** | Preserves original paired comparisons and adds 60 new questions with zero gold-ID/observed-dev-period overlap; possible without ingestion | Existing held-out remains question-held-out; structured-only draft mostly exercises deterministic statistics, not passage ranking. No pooling to claim unseen-fact R3 generalisation; unlogged exposures remain unknown | Useful **separate descriptive companion**, never substitute for A |

Splitting by hash or changed passage ID is inadequate. Group first by document family/vintage and subject period, dataset-period (all dimensions/adjustment bases), and semantic fact equivalents appearing in reports and statistics. A source can restate another source's fact: group-disjoint IDs alone do not ensure fact-disjointness. Ingestion/indexing of a document is not automatically label leakage, but inspecting its candidate ranks/answers while tuning is evaluation exposure. The saved-run audit excludes all observed evidence; earlier reranker caches do not retain complete candidate provenance, so absence of such exposure cannot be proven. Do not assert it.

### A target strata, before authoring or any run

| Family | Target n | Required construction |
|---|---:|---|
| factual_lookup | 12 | At least 8 genuinely reserved report passages |
| numerical_comparison | 12 | Deterministic, same-series/basis operands from reserved periods |
| cross_source_synthesis | 10 | At least 8 report-backed; no invented causal interpretation |
| revision_conflict | 8 | At least 4 answerable independently labelled advance/final pairs |
| ambiguity_insufficient_causal | 10 | Predefined clarify/abstain/causal boundaries |
| adversarial | 8 | At least 4 safe-answer injection tasks and 4 refusals |
| **Total** | **60** | >=8 abstain/refuse/clarify/injection cases; no selection from system failures |

The **available draft differs openly**: 20/16/8/4/6/6 by the same order, 44 answer, 7 abstain, 3 clarify, 2 refuse, 4 ignore-injection-and-answer. All four revision cases intentionally ask for an original vintage using only a current snapshot and must abstain; they are not advance/final answerable coverage. This is why promoting it unchanged to A would be invalid.

## 3. Blind case-authoring protocol and schema

1. Before reading any new system response, lock retrieval/configuration, source-group eligibility, family counts, metrics and acceptance rule. Record the approved evidence claim. Source authoring may inspect source text/records, never system outputs for the new questions. This worker inspected old development metadata only to exclude exposure; no new-case answers were generated.
2. Build the reservation inventory against both splits and saved development evidence. Exclude every dimension/adjustment from a cited/exposed dataset-period, plus semantic duplicate facts across sources. Changed extraction IDs do not reset exposure. Record unknown candidate-pool provenance as unknown, not clean.
3. Read only the rebuilt corpus after ExtractionMerge confirms completion. For each fact choose exact current IDs, locator, population, adjustment, units and vintage; no fabricated source. For calculations independently subtract decimal operands in chronological order. Keep counts, rates, ratios and percentage points separate.
4. Write new questions, not paraphrases of existing case questions. For nonanswers specify the missing parameter/evidence or prohibited action. Owner rule: answer if the specified public fact exists; abstain for absent/unsupported publication or subject outside scope; clarify essential missing year/population/basis; refuse forecasts/individual advice/secrets/personal data; reject attack but answer a sufficiently specified public remainder. Do not reinterpret lack of historical-vintage metadata as proof the publisher never published a figure.
5. Use `experiments/gold/heldout_v2.schema.json`, compatible with the original JSONL field contract. IDs `HO-V2-001` etc.; `split=heldout`; new records **draft**, `reviewed_by=null`, no `owner_review`. Evidence arrays keep the existing source/period/dimension/ID structure. `calculation` retains formula/inputs/expected_value/unit. The draft-only schema deliberately cannot represent a completed owner review: after genuine review, version the schema/status policy rather than fabricate fields.
6. Human reviews question-only first, then sources/label, before generation. AI authoring/source checks are not human review. Record disagreements and approve revised gold before freezing. Do not edit old gold or old registered artifacts. Do not copy MOM text longer than six consecutive words or commit raw responses.
7. Mechanically verify schema, IDs, exact source/period matching, group exclusions, calculations and no duplicate questions, independently of the system. `authoring-checks.json` records this worker's direct source comparisons; no generation or retrieval was exercised. Parent should run the validator/tests below. A publication-source spot check remains human work.
8. Write the final approved gold SHA, corpus/observations/prompt/code/price fingerprints and acceptance rule **before any generation**, then generate once per registered arm. Do not tune, relabel, rerun selective cases or drop failures after observing results. Operational failures remain denominator failures; a universal implementation fault requires a labelled protocol deviation and separate whole-arm run, retaining originals.

## 4. Preregistered analysis and honest uncertainty

**Primary question (valid A only):** does R3 increase paired expected-behaviour accuracy versus hybrid for both models on fresh reserved evidence? A behavioural pass alone is not a correct supported answer. Use identical cases and harness, `planner_v1`, `answer_v3`, `gpt-6-luna` or `gpt-5.6-luna` for planner/answer, the fixed existing reranker, fixed extraction/cross-check code for every arm. Change retrieval only. Do not compare an old unpatched hybrid arm to a patched R3 arm.

**Proposed advance acceptance rule:** for **each** model, the R3-minus-hybrid paired behaviour difference must have a **97.5% two-sided paired case-bootstrap lower bound strictly >0**, 20,000 resamples, seed 20261031 (Bonferroni for two model-specific comparisons). Also report exact two-sided McNemar discordance p-values and source/evidence-component cluster-bootstrap sensitivity. No demonstrated gain is declared if cluster sensitivity includes zero, if there are fewer than 10 independent source/evidence components, if any required arm/case is missing, or if review/reservation gates fail. Secondary guardrail: R3 must not add any false-answer cases on gold nonanswer strata, and must not worsen the observed number of answers contradicting reference facts. Otherwise describe trade-offs, not an overall winner. This rule is fixed before outputs; the owner must accept it before execution.

Compute clusters as connected components of cases sharing a source document family or dataset-period group (including multi-source bridges), publish membership before runs, and resample entire components; keep paired arms and all model results for a case together. Report family counts, errors, support/coverage/calculation, cost and latency without selecting a subgroup winner. With few clusters the CI is unstable; that fails the confirmatory gate rather than being waived. The current structured draft is a diagnostic regardless of any nominal p-value.

At n=60, independent-binomial normal-approximation 95% half-width is about **12.7 points at p=.5** or **7.6 points at p=.9**; use actual reported intervals, not this approximation as a result. A 10-point paired gain is only six net cases. Approximate 80%-power detectable gain is `(1.96+.84)*sqrt(q/60)`: **16 points** if discordance q=.2, **26 points** if q=.5, before multiplicity/clustering (both worsen it). No promised power at unknown q and no equivalence conclusion from a nonsignificant result. Eight-case strata are descriptive. Zero failures out of eight has a one-sided 95% upper failure bound about **31%**, not proof of safety. Repeated evidence/shared models reduce effective information below 60 independent questions.

## 5. Execution boundary, commands and costs

`agent-exp` and `eval` now accept `--gold PATH`, passing that same file to case loading and hashing in generation/scoring provenance, without swapping the original gold file. Prompts, schema and old results remain untouched. CLI/provenance tests cover the new path routing.

Exact conditional commands and pre-run gates are in `experiments/heldout-v2/FREEZE.md`. **Do not run until gates are satisfied.** No API calls were made by this worker. No build/index/embedding was run.

**[INFERENCE] budget estimate, not a cap:** existing H mean per-case generation costs (USD) are luna6 r3 .00193 / hybrid .00124; luna5.6 r3 .00343 / hybrid .00271. At 60 cases per arm, total generation is about **$0.559**. Saved H judging totals .0283+.0236+.0298+.0228 for 31 cases scale to about **$0.202** for 60, so **$0.761** generation+judge at the historical workload. New content/tool loops can differ; this is not a guarantee or source/embedding budget. Saved usage is priced by `specs/prices.yaml` (hash `634b32441c3495b4c3ec13efa3af1e9cc99e5c7523eac3a15a5c238c3acaeb5c`); verify provider prices independently before execution. Historical pricing source: https://developers.openai.com/api/docs/pricing . No fresh price/network claim is made.

## Open decision / exact blocker

**One owner decision:** approve additional genuinely untouched source/vintage groups for confirmatory A, **or explicitly accept C's separately labelled structured-only diagnostic** (not unseen-document R3 validation). Current source inventory cannot supply the substantive untouched documents A requires; no amount of relabelling IDs or re-splitting old cases remedies that. Genuine human review and finalized code/corpus fingerprints are required before either registered generation.
