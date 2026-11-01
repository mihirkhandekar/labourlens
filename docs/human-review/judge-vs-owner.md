# Judge versus the owner's own verdicts on 40 saved answers

Offline computation from files only; no model calls. This is an additional comparison, not a validation of the judge in general.

## What is compared

- **Owner verdicts:** 40 cards in the `answers` tab of the owner export (`private/human-review/owner-exports/review-results.json`, identical to `review-results (8).json`), verdict right / partly correct / wrong. 23 of those cards were first agreed with an AI suggestion; the owner re-decided all 23 by own click in the pending-review export (`pending-review (1).json`, stream `answers`, queue `redo`). The redo changed **0** of the 23 verdicts, so the final owner counts are **25 right, 6 partly, 9 wrong**, all `owner_manual`. Private comments are not used here.
- **Which answers:** the 40 development cases in `experiments/human-review-sample/selection.json` (seed 20261030; 6 per family plus 4 status-mismatch cases; a failure-enriched sample), answered by the A1 `gpt-6-luna` run. The case ID is the key: the answer card, `experiments/eval/agent-dev-A1/gpt-6-luna.cases.jsonl` and `gpt-6-luna.judgements.json` all use the same dev case ID, and all 40 IDs are present in all three. The mapping is exact, with no inference.
- **Judge output used:** per-case fields derived from the judge in `cases.jsonl`: `claims_unsupported`, `facts_contradicted`, `claims_partial`, `facts_covered` against `facts_total`. These were scored on gold v3.5 by the same saved judgements.

## Mappings fixed before computing

- **Mapping A (judge only, the pre-registered one):** judge flags an answer if it has at least one unsupported claim or at least one contradicted reference fact. Compared with owner "wrong" (positive) against owner not-wrong, and with owner "right" against no flag. "Partly" is reported separately.
- **Mapping B (derived verdict, as in the earlier AI-pre-review comparison):** wrong if behaviour is not OK, false answer, or Mapping A flag; partly if a reference fact is uncovered or a claim is only partially supported; else right. This **mixes in deterministic behaviour scoring** (status versus gold), which is not the judge.

## Results (n = 40)

The judge judges claims only for answers that make claims. **23 of the 40 answers** have judged claims. The other 17 are abstentions, refusals or clarifications with no claims: 7 owner-right, 1 owner-partly (DEV-018) and 9 owner-wrong.

**Mapping A**

| Owner verdict | Judge flag (unsupported or contradicted) | No flag |
|---|---:|---:|
| wrong (9) | 0 | 9 |
| partly (6) | 0 | 6 |
| right (25) | 0 | 25 |

The judge flagged **0 of 40** answers. All 9 owner-wrong answers are non-answers (behaviour failures against the gold label, decided by deterministic status scoring), so there is no judged claim in them. Kappa for owner-wrong versus judge flag is 0.00 (agreement 31/40, 77.5%, only because both sides are mostly "no"). **Kappa is not meaningful here: the judge never fired, and no owner-wrong answer contained a judged claim.** On the 23 answered cards the owner marked none wrong (18 right, 5 partly), consistent with no unsupported flags, but this has zero positives on either side. It cannot show that the judge catches unsupported claims; it shows only that on these 23 answers the owner did not mark any wrong, and the judge flagged none.

**Mapping B (3 classes; mixes behaviour scoring with the judge)**

| Owner \ derived | right | partly | wrong |
|---|---:|---:|---:|
| right (25) | 17 | 8 | 0 |
| partly (6) | 0 | 5 | 1 |
| wrong (9) | 0 | 0 | 9 |

Agreement 31/40 (77.5%), Cohen's kappa 0.64 (my calculation). Binary views: wrong versus other 39/40 (97.5%, kappa 0.93); right versus not-right 32/40 (80%, kappa 0.61). These figures are driven by behaviour scoring for the 9 wrong cases and the one partly case (DEV-018), which are non-answers. On the 23 answered cards alone, derived verdict versus owner: right/right 10, right/partly 8, partly/partly 5 (18 owner-right, 5 owner-partly); agreement 15/23 (65%), kappa for right versus not-right 0.35.

## What this does and does not show

- The derived judge verdict never called an owner-wrong answer right or an owner-right answer wrong, and flagged every owner-partly answer that had claims as at least partly. On answered cards the judge is stricter than the owner: 8 of 18 owner-right answers have an uncovered reference fact or partly supported claim (the owner accepted them as right; consistent with the AI pre-review finding that the judge is stricter on fact coverage).
- It does **not** show that the judge detects unsupported or contradicted claims: there are none to detect in this sample by either the judge or the owner.
- 40 answers, one reviewer who saw the answers after AI pre-review and after scoring, a failure-enriched non-random sample of one configuration (A1 `gpt-6-luna`), development cases only. No confidence interval is given; with these counts it would be wide and uninformative. This is not independent inter-rater evidence and not population accuracy.
- The judge is `gpt-6.1-terra`, an AI model that shares a provider and related family with the generators; owner verdicts are the only human reference, and the judge was not tuned on them.
