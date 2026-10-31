# M7 — Evidence-disjoint held-out v2 (design A on corpus v3)

**31 October 2026. Status: 65 blind-authored draft cases written against corpus v3; preregistration drafted in `experiments/heldout-v2/FREEZE.md`; no system run, no scoring, no output seen for any of these cases.** The cases are AI-drafted and `draft`; owner review is outstanding and is a precondition for a freeze.

## 1. Why a new set (VERIFIED FACT)

Reading v3.5 gold, **25 of 31** original held-out cases share at least one acceptable evidence id (passage or observation) with a dev case, and **14 of 31** have their whole nonempty evidence set in dev (the figure 15 given earlier does not reproduce; HO-025 and HO-030 have no ids). The original held-out set is question-held-out, not evidence-held-out. Per-case ids and the dev cases that share them: `experiments/heldout-v2/evidence-audit.json` (taken before the corpus grew).

A post-hoc re-split of the 268 existing cases cannot repair this (design B): r3 and the prompts were selected using all dev evidence, so any partition of old evidence is contaminated by tuning. Design C (the same held-out paired with a second set) keeps the old limitation. Design A needs sources that no tuning step ever saw, which required new sources.

## 2. What is truly evidence-disjoint now

Owner decision on 31 Oct: labour-only additions. Corpus v3 (`experiments/corpus-snapshots/v3.json`) added three documents and three datasets. All six are used and none was touched before this set:

| New source | Kind | Used for | Notes |
|---|---|---|---|
| `mom-wage-practices2025` | MOM report | 14+ cases | Sibling edition of the 2024 report used in dev. Only 2025 figures are asked, because the 2024 comparatives restate facts dev cases cover. 23 of 174 passages are table-flagged and not cited. |
| `mom-nwc-lower-wage2025` | MOM report | 11+ cases | No earlier edition in corpus. All 112 passages extract cleanly. |
| `mti-2026-q2-feature-ai-employment` | MTI feature article | 5 cases | 40 passages garbled and 15 table-unreliable; **only passages flagged ok are cited** (checked in code). The study analyses firm AI use through 2024 although published in Q2 2026, so these cases are scope-sensitive. |
| `unit_labour_cost_index_quarterly` | SingStat dataset | 9+ cases | Adjustment status not stated by the dataset; strong seasonality; no adjusted-series claim is made. |
| `value_added_per_worker_quarterly` | SingStat/MOM dataset | 6+ cases | Four-decimal values. |
| `avg_weekly_paid_hours_quarterly` | MOM dataset | 7+ cases | One series, no industry detail. |

Independence checks actually run (`experiments/heldout-v2/evidence-audit-v3.json`, `authoring-checks.json`):
- **zero overlap** between the ids cited by the 65 cases (acceptable and context-only) and the 325 evidence ids in the 268 existing gold cases;
- **zero** of the 48 saved dev and held-out run files cite any new source (these files predate the new sources);
- a repository-wide search finds the new source ids only in data manifests, new passage and snapshot files, data-quality artefacts, docs, specs, tests and the corpus snapshot; nothing in `experiments/gold`, `experiments/runs`, `experiments/eval`, `experiments/threats`, `prompts` or `src`;
- all subject periods are 2024-Q1 to 2026-Q2 (the datasets also hold earlier history, which is not used);
- every cited passage has `quality_flag=ok`; every dataset value was recomputed from `data/processed/observations.parquet`; every text figure was asserted present in its cited passage; differences were recomputed with `Decimal`; no seven-word sequence of any question or fact appears in any corpus passage.

**Remaining leakage (not removed):** same system prompts, same tools and agent code, same reranker model and prompt, same embedding model, same publishers and series families, similar question styles. The 2025 wage report has a 2024 sibling in dev. These cases test the system on fresh evidence, not on a fresh system. The new passages also live in a corpus whose BM25 and embedding indexes were built once, with no tuning on them.

## 3. Composition (as authored, before any run)

| Family | n | What supports it | Thin? |
|---|---:|---|---|
| factual_lookup | 22 | 16 report passages, 6 dataset rows | no |
| numerical_comparison | 14 | 6 dataset comparisons (4 with a gold calculation the scorer can check), 8 arithmetic on report figures | no |
| cross_source_synthesis | 8 | report pairs, report plus dataset, report plus AI article | slightly below a target of 10 |
| revision_conflict | 3 | **No labour-only advance/final pair exists among the new sources.** Only "original vintage unavailable, so abstain" cases on single-snapshot datasets; abstention here is not a claim that nothing earlier was published | **yes, thin and weak** |
| ambiguity_insufficient_causal | 10 | 4 clarify, 5 abstain, 1 refuse (forecast) | no |
| adversarial | 8 | 4 direct injection with an answerable question, 4 refusals | no indirect-injection fixture cases |

Behaviours: 44 answer, 4 ignore-injection-and-answer, 8 abstain, 4 clarify, 5 refuse, so **21 non-answer or injection cases**. Of the 48 answerable cases, 34 have report-text evidence; 14 rest on dataset tools both arms use identically and will dilute any retrieval effect. Four numerical cases carry a gold calculation. The calculation scorer was widened before any run to accept the new dataset units (`index_2015_100`, `hours_per_week`); legacy units are unchanged and `tests/evaluation/test_integrity.py` covers both. Value-added-per-worker and report-text comparisons have `calculation: null` because the scorer cannot match four-decimal displays and there is no agent tool for arithmetic on report text; their differences are reference facts judged by the harness instead.

Judgement calls the owner should look at first (labels follow `docs/human-review/OWNER-REVIEW-GUIDE.md`): the clarify case on "average wage increase in 2025" (several valid measures), the abstentions that depend on a dataset not recording adjustment status or original vintage, the five AI-article cases (subject period), and the forecast refuse.

Earlier work is preserved, not deleted: `experiments/gold/heldout_v2_structured_draft.jsonl` holds the 60 structured-only cases (`HO-V2S-*`, source group `structured_reserved_dataset_periods_v2a`). Their dataset-periods were untouched in saved runs but candidate pools were never logged, so they are an unregistered secondary diagnostic only.

## 4. Blind-authoring protocol and schema

1. Lock source eligibility, family targets, metrics and acceptance rule before reading any system output for the new questions. No output exists for them.
2. Use only corpus-v3 new sources. Read passages only after confirming the extraction quality flag; never cite garbled or table-unreliable passages.
3. Write facts as paraphrases. Verify every figure against the passage text or parquet value in code. Recompute every calculation. Keep counts, rates, indexes, hours and percentage points separate.
4. Apply the owner rule: answer if the specified public fact exists; abstain if the published figure is absent or the subject is out of scope; clarify if an essential parameter is missing; refuse forecasts, secrets, personal data and unsafe actions; reject an attack but answer a sufficiently specified public remainder. Do not equate "not in this corpus snapshot" with "never published".
5. Non-answer cases keep evidence in `context_only_evidence_*` so retrieval and citation scorers never treat it as gold.
6. Case schema: `experiments/gold/heldout_v2.schema.json` (JSON Schema 2020-12). It matches the fields of `draft_cases.jsonl` and adds `source_group`, `context_only_evidence_data` and `notes`. IDs are `HO-V2-NNN`; `review_status=draft`, `reviewed_by=null`, no `owner_review`.
7. Human review follows, question first and then sources and label, before any run. The pack tab "Held-out v2" uses the same Fast review controls as the gold tab, has no AI suggestions and cannot be endorsed. Disagreements are written to a separate proposals file and never edit gold.

## 5. Preregistered analysis and honest uncertainty

Comparison and exact commands: `experiments/heldout-v2/FREEZE.md`. In short, one factor (retrieval `r3` versus `hybrid`), two models, same harness, one run per arm. The rule fixed in advance requires, for **each** model, a paired behaviour-accuracy difference whose 97.5% case-bootstrap lower bound and 97.5% evidence-component-bootstrap lower bound are both above zero, at least 20 evidence-carrying components (22 exist, published in `components.json`), no added false answers and no added reference-contradicting answers, and complete paired data. `labourlens paired` implements it (`src/labourlens/evaluation/paired.py`, seed 20261031, 20,000 resamples, tested). A pass would support a bounded claim about fresh evidence, not unseen-domain generalisation. A fail means "not demonstrated", not "no gain".

**Power at n=65 is modest.** A one-arm accuracy interval has a half-width near 12 points at p=.5; a true paired gain needs to be roughly 17 to 27 points for about 80% power at this interval, depending on how often the arms disagree. The original held-out gains were +10 and +16 points. The probability of demonstrating a true gain of that size is below one half [INFERENCE from arithmetic, not simulated]. Strata of 8 are descriptive only. Fourteen dataset-only answerable cases and the 17 non-answer cases are mostly insensitive to retrieval and dilute the contrast; the report-text-only sensitivity is reported alongside but cannot replace the registered rule.

Cost, inferred from saved usage: about $0.82 for generation plus judging of 65 cases across both models and both arms (`FREEZE.md`). No API call has been made.

## 6. What this does not do

It does not make the system independent of the evaluation design, does not validate the revision family, does not test indirect injection, and does not promote the structured-only cases. It supplies fresh evidence and a rule that cannot be tuned after seeing results.

## Open owner decisions

1. Review the 65 draft cases (or authorise an unreviewed run).
2. Rule on the five AI-article cases under D-031.
3. Approve the preregistered rule and fingerprints in `experiments/heldout-v2/FREEZE.md`, then authorise the paid run.
