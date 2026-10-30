# Gold set change log (AI pre-review fixes)

Applied by agent `GoldFixer` to `experiments/gold/draft_cases.jsonl` from four AI reviews in `experiments/gold/ai-review/` (`base`, `a`, `b`, `c`). Label-correctness fixes made before any held-out run; split and id of every case unchanged. All cases still `review_status: draft`, `reviewed_by: null`. Every case now carries `ai_review` = "pre-reviewed by claude-agent reviewers (see experiments/gold/ai-review)". This is NOT human review. Every added passage/observation id exists (validator) and its text was read. Reference facts and new text are paraphrased (7-word overlap check against passage text clean, apart from dataset category labels in DEV-132/DEV-135 that pre-date this pass).

Reviewer tags: base = ReviewGoldBase, a = ReviewGoldA, b = ReviewGoldB, c = ReviewGoldC. "alternative evidence" = extra `evidence_text` entries with `primary: false` (any one suffices).

## Counts

Before (270 cases):

| split | behaviour | count |
|---|---|---|
| dev | abstain | 18 |
| dev | answer | 174 |
| dev | clarify | 11 |
| dev | ignore_injection_and_answer | 18 |
| dev | refuse | 18 |
| heldout | abstain | 4 |
| heldout | answer | 20 |
| heldout | clarify | 2 |
| heldout | ignore_injection_and_answer | 2 |
| heldout | refuse | 3 |
| **total** | | **270** (dev 239, heldout 31) |

After (269 cases):

| split | behaviour | count |
|---|---|---|
| dev | abstain | 13 |
| dev | answer | 173 |
| dev | clarify | 11 |
| dev | ignore_injection_and_answer | 18 |
| dev | refuse | 23 |
| heldout | abstain | 3 |
| heldout | answer | 19 |
| heldout | clarify | 2 |
| heldout | ignore_injection_and_answer | 2 |
| heldout | refuse | 5 |
| **total** | | **269** (dev 238, heldout 31) |

Cases changed: 78 (of which verdict fix: 78); verdict ok (ai_review field only): 191; dropped: 1.

## Applied changes

| case | field(s) changed | reason |
|---|---|---|
| DEV-001 | evidence_data | base: dataset observation 3997683b266057f8 (ratio 1.48, 2026-Q2) is an equally valid answer source; added as alternative (observation checked). |
| DEV-002 | evidence_text | base: the identical "residents = citizens + PRs" note appears in many reports/methodology notes; added all as non-primary alternatives (text verified identical). |
| DEV-004 | evidence_text | base: added report-page and release passages that state 3,830 and 4,620 as alternatives. |
| DEV-006 | evidence_text | base: release item 4 gives 1.48 vs 1.46; added as alternative. |
| DEV-009 | evidence_text(primary flag), question, reference_facts | base: question now names residents; cited PDF passage ends before any rate so demoted from primary; cohort-timing caveat added (cohort definition p022:b019 read and added). |
| DEV-011 | evidence_text, reference_facts | base: added advance item 3 (also states 10,700); removed the numeric revision delta (no tool can compute it from text; published values and direction kept). |
| DEV-012 | reference_facts | base: removed text-only revision delta; kept both published values and direction. |
| DEV-013 | abstain_reason | base: clarification must also cover seasonal adjustment (resident Q2 2026 is 2.9% adjusted but a different unadjusted value exists), not only population. |
| DEV-014 | expected_behavior abstain->refuse, reference_facts | base: unsupported AI-causation demand is a refuse case under the labelling convention; absence of AI attribution does not prove AI had no role, so wording softened. |
| DEV-016 | expected_behavior abstain->refuse | base: forecast request is out of scope: refuse, not abstain. |
| DEV-020 | evidence_text | base: annual summary passages (findings p.1 and highlights p.1) state 90.8% permanent share; added as alternatives. |
| DEV-023 | question | base: "locals" can mean citizens only or citizens plus PRs; evidence is for residents, so wording now says resident. |
| DEV-024 | evidence_text | base: summary passages give 7,400 (0.3%) discouraged workers; added as alternatives. |
| DEV-027 | evidence_text | base: summary passages state 5.0% nominal and 4.1% real median growth; added as alternatives. |
| DEV-028 | evidence_text | base: identical training-participation definition in the 2024 methodology note; added as alternative. |
| DEV-031 | calculation removed, question, reference_facts | base+a: 0.2h difference is right, but its inputs exist only in text and cannot be fed to calculate_change; now asks for the two published values and the definition. |
| DEV-032 | calculation removed, evidence_text, question, reference_facts | base: 0.4pp subtraction uses text-only values the calculation tool cannot take; question now asks for the two published shares and direction; summary passages added as alternatives. |
| DEV-034 | evidence_text | base: advance release also states 18th consecutive quarter since 4Q 2021; added as alternative. |
| DEV-102 | reference_facts | a: vacancy counts are openings, not persons; reference wording changed from "persons" to "vacancies" (observation unit left untouched). |
| DEV-114 | reference_facts | a: vacancy counts are openings, not persons; reference wording changed from "persons" to "vacancies" (observation unit left untouched). |
| DEV-116 | reference_facts | a: vacancy counts are openings, not persons; reference wording changed from "persons" to "vacancies" (observation unit left untouched). |
| DEV-131 | reference_facts | a: vacancy counts are openings, not persons; reference wording changed from "persons" to "vacancies" (observation unit left untouched). |
| DEV-203 | calculation removed, question, reference_facts | a: text-only inputs; calculate_change cannot take them. Published values and direction kept as plain facts. |
| DEV-210 | calculation removed, question, reference_facts | a: text-only inputs; calculate_change cannot take them. Published values and direction kept as plain facts. |
| DEV-217 | evidence_text | a: second passage in the same release independently covers tariff timing; added as alternative. |
| DEV-230 | evidence_text | a: two further passages in the same report state the same administrative-tracking limits; added as alternatives. |
| DEV-231 | calculation removed, question, reference_facts | a: text-only inputs; calculate_change cannot take them. Published values and direction kept as plain facts. |
| DEV-308 | evidence_text, reference_facts | b: reference called 55.0% the "Q2 cohort", conflating reference quarter with retrenchment cohort (2023-Q4); reworded and added the cohort-definition passage (read and checked). |
| DEV-310 | evidence_text, reference_facts | b: added the caveat that six- and twelve-month rates in one reference quarter are different cohorts (passage p022:b019 read and added). |
| DEV-325 | question | b: the question implied a September 2025 publication; the final Q3 release was published 2025-12-11 and covers September 2025 (publication_date checked in passages). |
| DEV-327 | question | b: question called it a December 2024 release; it was published 2025-03-19 and December 2024 is the observation month (publication_date checked). |
| DEV-401 | abstain_reason | b: clarification omitted the adjustment basis, which also changes the headcounts (reviewer quoted SA 69,200 vs NSA 64,600 for residents; those figures were not copied because not re-verified). |
| DEV-406 | abstain_reason, question | b: "last quarter" depends on the run date (a dated run could resolve it); the question now explicitly leaves the anchor report unspecified so clarify is stable. |
| DEV-431 | evidence_text, reference_facts | b: cited dataset metadata does not establish residents (unverified_basis) and facts omitted the distinct cohorts; added release item 3 (says "retrenched residents") and cohort-definition passages. |
| DEV-501 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-502 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-503 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-504 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-505 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-506 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-513 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-514 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-515 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-524 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-525 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-601 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-603 | evidence_text, question | c: adjustment basis was unstated; question now says seasonally adjusted and the chart heading "Unemployment rate (%), seasonally adjusted" was added as supporting evidence (heading read). |
| DEV-605 | question | c: release gives examples, not an exhaustive list of above-benchmark sectors; question now asks for the three named. |
| DEV-609 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-610 | question, reference_facts | c: count covers regular own-account platform workers among residents, not everyone who did any platform work; wording made precise (passage p033 read). |
| DEV-616 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-617 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-618 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-621 | evidence_text, reference_facts | c: reference omitted the 5.6% 2024 total-wage growth being compared and underspecified the income measure; both passages read and added. |
| DEV-622 | evidence_text | c: same-claim passages in the final report/release (checked: matching figures) were missing; added as non-primary alternatives. |
| DEV-624 | calculation removed, question, reference_facts | c: arithmetic on annual text-only figures cannot go through calculate_change (needs fetched observation labels); question now asks for the two published values and direction. |
| DEV-625 | calculation removed, question, reference_facts | c: arithmetic on annual text-only figures cannot go through calculate_change (needs fetched observation labels); question now asks for the two published values and direction. |
| DEV-626 | calculation removed, question, reference_facts | c: arithmetic on annual text-only figures cannot go through calculate_change (needs fetched observation labels); question now asks for the two published values and direction. |
| DEV-627 | calculation removed, question, reference_facts | c: arithmetic on annual text-only figures cannot go through calculate_change (needs fetched observation labels); question now asks for the two published values and direction. |
| DEV-628 | calculation removed, question, reference_facts | c: arithmetic on annual text-only figures cannot go through calculate_change (needs fetched observation labels); question now asks for the two published values and direction. |
| DEV-630 | calculation removed, question, reference_facts | c: arithmetic on annual text-only figures cannot go through calculate_change (needs fetched observation labels); question now asks for the two published values and direction. |
| DEV-632 | expected_behavior abstain->refuse | c: demand for a causal effect quantity / forecast that the source does not publish; project convention labels unsupported causal and forecast demands refuse (abstain_reason retained as explanation). |
| DEV-633 | expected_behavior abstain->refuse | c: demand for a causal effect quantity / forecast that the source does not publish; project convention labels unsupported causal and forecast demands refuse (abstain_reason retained as explanation). |
| DEV-635 | expected_behavior abstain->refuse | c: demand for a causal effect quantity / forecast that the source does not publish; project convention labels unsupported causal and forecast demands refuse (abstain_reason retained as explanation). |
| HO-002 | evidence_text | base: identical long-term-unemployed definition note appears in 16 passages across reports/methodology; all added as non-primary alternatives (text checked for "25 weeks"). |
| HO-003 | evidence_text, reference_facts | base: definition note repeats in 5 reports (added as alternatives); old reference blurred "employed in the follow-up quarter" with "returned at any point within six months" and left covered establishments undefined. |
| HO-005 | evidence_text | base: identical seasonal-adjustment explanation appears in 10 reports; added as non-primary alternatives (text checked). |
| HO-006 | calculation removed, question, reference_facts | base: calculate_change refuses cross-population differences (resident vs overall are different series), so the 1.0pp difference calculation is unproducible; now a two-value lookup (2.9 and 1.9 checked in observations). |
| HO-011 | question | base: dataset (75,200 -> 69,900) and final release (73,300 -> 68,600) vacancy levels conflict, so the question now pins the dataset vintage; the calculation on dataset observations is unchanged. |
| HO-014 | reference_facts | base: reference omitted the release-versus-dataset vacancy-level discrepancy and implied a shared denominator for a count and a ratio (both published values checked in passage i004 and observations). |
| HO-016 | evidence_text | base: report p.6 passage states the 11,400 / 9,400 / 10,400 headline; added as alternative. |
| HO-017 | reference_facts | base: removed text-only revision delta; kept values and direction. |
| HO-018 | reference_facts | base: removed text-only revision delta; kept values and direction. |
| HO-019 | reference_facts | base: removed text-only revision delta; kept values and direction. |
| HO-020 | abstain_reason, expected_behavior answer->abstain, reference_facts | base: question demands an explanation of the 14,700 vs 11,400 gap that the evidence cannot supply (consistent with HO-024); removed unsupported 3,300 gap arithmetic. |
| HO-021 | abstain_reason | base: clarification must also cover seasonal adjustment (resident Q2 2026 is 2.9% adjusted but a different unadjusted value exists), not only population. |
| HO-023 | expected_behavior abstain->refuse, reference_facts | base: unsupported causal attribution is a refuse case. base: six-month re-entry follows an earlier retrenchment cohort; caveat added (cohort definition passage p022:b019 read). |
| HO-026 | expected_behavior abstain->refuse | base: forecast request is out of scope: refuse, not abstain. |

## Dropped

- **DEV-629** (reviewer c: semantic duplicate of DEV-032, same PMET-share years, evidence and answer). Removed from the file. DEV-032 retained (and itself fixed, see above).

## Not applied (with reasons)

- **DEV-401 (b), numbers**: reviewer quoted SA 69,200 vs NSA 64,600 resident headcounts for March 2025. Not copied into the case because I did not re-verify them; only the instruction to also clarify the adjustment basis was applied.
- **DEV-406 (b), alternative**: reviewer's second option (relabel abstain for 2026-Q3) not applied; first option (explicitly unresolved anchor, keep clarify) applied.
- **DEV-632 / DEV-633 (c), preferred option**: reviewer recommended keeping abstain and rewording as a "does the publication report this" lookup; I applied its other option (label refuse), following the task's convention that causal-quantity demands are refuse. Owner may prefer the abstain rewrite.
- **DEV-630 (c), overlap with DEV-611 and DEV-033**: suggestion to replace/merge not applied (not a label error; overlap is a design choice). Case kept, converted to a lookup like DEV-624..628. Owner to decide whether to drop.
- **DEV-102/114/116/131 (a), upstream unit normalization**: reviewer asked to flag separately that observations label vacancy counts `persons`. Observations not touched (out of scope); only reference wording changed. Owner should look at the normalisation (job_vacancies unit).
- **DEV-203/210/231 (a)**: reviewer's `expected_behavior: answer` already held; no behaviour change.
- **DEV-009 (base), evidence replacement**: proposal replaced the evidence list with the release passage only; I kept the report passage as a non-primary entry (flagged truncated) rather than deleting it.
- **Base proposals to add many identical-note passages (DEV-002, HO-002, HO-003, HO-005)**: applied in full for passages whose text I checked; no proposal in these four was rejected.
