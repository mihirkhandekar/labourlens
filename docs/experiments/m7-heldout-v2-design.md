# M7 — Evidence-disjoint held-out v2 (design A on corpus v3)

**31 October 2026. Status: run once on corpus v3 (65 cases, owner-approved gold, signed in `experiments/heldout-v2/FREEZE.md`). The pre-registered rule is met for the primary model; the effect is three cases; I would not call it a confirmed gain; the second model shows none. Result and error analysis: [`m7-heldout-v2-result.md`](m7-heldout-v2-result.md), D-045.** The sections below are the design as written before the run.

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
6. Case schema: `experiments/gold/heldout_v2.schema.json` (JSON Schema 2020-12). It matches the fields of `draft_cases.jsonl` and adds `source_group`, `context_only_evidence_data` and `notes`. IDs are `HO-V2-NNN`. At design time: `review_status=draft`, `reviewed_by=null`, no `owner_review`. (Superseded 1 Nov 2026: the 65 cases were later reviewed card by card by the owner, each by the owner's own click, before the run. One reviewer, not independent inter-rater evidence.)
7. Human review follows, question first and then sources and label, before any run. The pack tab "Held-out v2" uses the same Fast review controls as the gold tab, has no AI suggestions and cannot be endorsed. Disagreements are written to a separate proposals file and never edit gold.

## 5. Preregistered analysis and honest uncertainty

Comparison and exact commands: `experiments/heldout-v2/FREEZE.md`. In short, one factor (retrieval `r3` versus `hybrid`), two models, same harness, one run per arm. **Revision 2 of the rule (31 Oct 2026, before any run; D-042):** the primary model `gpt-6-luna` decides. It needs a one-sided 95% lower bound above zero for the paired behaviour-accuracy difference under both the case bootstrap and the evidence-component bootstrap, at least 20 evidence-carrying components (22 exist, published in `components.json`), no added false answers, and complete paired data. `gpt-5.6-luna` is a pre-specified replication that is reported and does not gate. Reference-contradicting answers are reported, not a veto. Revision 1 (both models, 97.5% two-sided, both vetoes) is withdrawn because the simulation below shows it passes only 11-19% of the time at a true +10 points. `labourlens paired` implements the rule (`src/labourlens/evaluation/paired.py`, seed 20261031, 20,000 resamples, tested) and refuses arms scored under a different gold file. A pass would support a bounded claim about fresh evidence, not unseen-domain generalisation. A fail means "not demonstrated", not "no gain".

**Power, simulated (MEASURED RESULT; `experiments/heldout-v2/power.py`, output `power.txt`, seed 20261101).** Paired outcomes were simulated on the real structure (65 cases, 39 components, 34 report-text answerable cases, 17 non-answer cases) with R3 worse on 4% of cases and better on (effect + 4)%, with and without clustering and with flips confined to the report-text cases; the two models are treated as independent, which real ones are not. For true paired effects of +5, +10 and +16 points, revision 1 passes 1.5-2.6%, 11-19% and 31-53% of the time. Revision 2 passes 21-24%, 45-54% and 68-84%. At zero true effect revision 2 passes 3.0-5.2% of the time against about 0% for revision 1: **the adopted rule is weaker and more likely to pass by chance**, at its intended 5% one-sided level. Letting either model pass would give 6-10% false positives and was rejected; a conjunction over both models would lose most of the power. The original held-out gains were +10 and +16 points, so a true gain of that size is now demonstrated roughly half the time or better, not rarely, and still not reliably at +5. Strata of 8 are descriptive only. Fourteen dataset-only answerable cases and the 17 non-answer cases are mostly insensitive to retrieval and dilute the contrast; the report-text-only sensitivity is reported alongside but cannot replace the registered rule.

Cost, inferred from saved usage: about $0.82 for generation plus judging of 65 cases across both models and both arms (`FREEZE.md`) when written; the signed quote was about $0.94. The run has since been made (see the status line).

## 6. What this does not do

It does not make the system independent of the evaluation design, does not validate the revision family, does not test indirect injection, and does not promote the structured-only cases. It supplies fresh evidence and a rule that cannot be tuned after seeing results.

## Owner decisions (resolved before the run)

1. The 65 cases were reviewed by the owner (59 cards by own click, 6 agreeing with an AI suggestion) and approved unchanged.
2. The five AI-article cases were kept as `answer` (D-031); the MTI-free sensitivity is in the result report.
3. The rule and fingerprints in `experiments/heldout-v2/FREEZE.md` were signed and the paid run was authorised and executed.
