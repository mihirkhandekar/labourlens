# Held-out v2: independent AI review summary

**Status:** AI review of the draft gold file, performed before any owner decision. **This is not human review.** The raw reviewer files stay private (they sit under `private/`, which is gitignored) and are embedded in the private owner review page.

## Provenance

- Draft gold file: `experiments/gold/heldout_v2_draft.jsonl`, SHA-256 `698940357c090c4beed4ba6532f66967dc7175297a3d1ffcd5fd6325e128fb70`, 65 cases.
- Three separate blind AI review passes (A, B, C), one verdict per case: approve, change label (with the suggested behaviour) or reject, each with a confidence. They were not shown each other’s output.
- SHA-256 of the private files: A.jsonl `4872af4b086aeb1a5f2b9ae71deef6005a50585e9a8ad2c6d14f47a213c710ca`, B.jsonl `b310aa1758c20e98f4df7f7fc15579f9e4ba3f4d1d197661089c2b08aee60cf4`, C.jsonl `670573893e9df03ba2fbce1ba2eddc667c407ff192c088e9874ddcdcf33890c4`.
- The three reviewers are the same model family. Their errors are therefore correlated, and their agreement is weaker evidence than agreement between independent people. It does not substitute for the owner’s review and is never counted as independent inter-rater evidence.

## Verdicts per reviewer

| Reviewer | approve | change label | reject |
|---|---:|---:|---:|
| A | 62 | 3 | 0 |
| B | 61 | 3 | 1 |
| C | 64 | 1 | 0 |

## AI consensus

Consensus is a verdict given by at least 2 of the 3 reviewers (and, for a change, the same suggested behaviour); otherwise the case is split.

| Consensus | Cases |
|---|---:|
| unanimous approve | 61 |
| majority change | 2 |
| majority approve (low confidence) | 1 |
| unanimous change | 1 |

## Agreement between the reviewers

- All three gave the same verdict on 62 of 65 cases.
- Pairwise agreement on the verdict: A-B 98.5%, A-C 96.9%, B-C 95.4%.
- Pairwise agreement on verdict plus suggested behaviour: A-B 98.5%, A-C 96.9%, B-C 95.4%.
- Fleiss’ kappa on the verdict: 0.611; on verdict plus suggested behaviour: 0.611.
- Kappa is unstable when almost every case gets the same verdict, as here (most cases are approvals), so read the raw agreement counts first.

## Cases that are not unanimous approvals

| Case | Family | A | B | C | Consensus | Reviewers’ main reason (first sentence, abbreviated) |
|---|---|---|---|---|---|---|
| HO-V2-020 | look up one fact | change to abstain (medium) | change to abstain (medium) | approve (low) | majority change to abstain (2 of 3) | A: Study uses 2018-2024 postings; cross-section is 'as of 2024' but the AI-use flag accumulates earlier years. B: Answer comes from regression on job-posting data spanning 2018 to 2024, mostly before 1Q 2024. C: Cross-sectional model uses 2024 data, which sits inside scope, but AI use is flagged from 2018-2024 postings; period ambiguous. |
| HO-V2-021 | look up one fact | change to abstain (medium) | change to abstain (medium) | approve (low) | majority change to abstain (2 of 3) | A: Same as 020: predicted probability 22 per cent comes from a model on 2018-2024 data and is not a Q1 2024-Q2 2026 quarterly figure; D-031 suggests abstain. B: Predicted probability comes from the 2018-2024 postings-based indicator, mostly pre-2024. C: Same period issue as 020: 2024 cross-section estimate, built from cumulative 2018-2024 postings. |
| HO-V2-022 | look up one fact | change to abstain (high) | change to abstain (medium) | change to abstain (medium) | unanimous change to abstain | A: Profit rise figure does not exist; evidence only says no significant gain, over cohorts 2019-2024 four-year windows, mostly pre-2024. B: False-premise question about four-year post-adoption effects from 2019-2024 cohorts, mostly before 1Q 2024; D-031 implies abstain. C: No profit-increase figure exists; article reports no significant gain, and the event study covers 2019-2024 cohorts. |
| HO-V2-043 | combine sources | approve (low) | reject (low) | approve (low) | majority approve (2 of 3) (low confidence, no one-click) | A: Dataset numbers verified. B: Mixed scope: the article's productivity finding comes from a 2018-2024 study window (D-031 abstain) while the dataset half is in scope. C: Article part is qualitative and dataset part is in scope, so answer with caveat; but the article claim rests on 2019-2024 cohorts, same period issue as 022. |

## Systematic issues the reviewers raised

- **Study period of the AI article** (HO-V2-020, HO-V2-021, HO-V2-022, HO-V2-043; raised by 3 of 3 reviewers): the study behind the MTI article uses data from 2018 to 2024, mostly before the supported period, so whether these may be answered is your D-031 ruling.
- **Revision cases test a missing earlier version, not a real conflict** (HO-V2-045, HO-V2-046, HO-V2-047; 3 of 3 reviewers): the corpus holds one snapshot, so abstaining is right, but a system could reasonably still give the current value.
- **Open-ended questions have more than one reasonable answer** (HO-V2-048, HO-V2-049, HO-V2-050; 3 of 3 reviewers): a system might list every reading instead of asking back. Decide whether that should also count as a good answer.
- **Minor wording mismatches** between the question and the source (HO-V2-012, HO-V2-029, HO-V2-036, HO-V2-038; 3 of 3 reviewers): all approved, noted for the record.
- **Fewer independent tests than cases** (computed from the gold file, not raised by the reviewers): 65 cases but only 22 independent evidence groups, because near-identical cases about the same source share one group.

## How the owner review page uses this

- Each card shows the three verdicts, the computed consensus and the reviewers’ issues beside the evidence.
- “Agree with AI” exists only where a consensus exists, unlocks a few seconds after a card appears, and is recorded as `agreed_with_ai_suggestion`. `v2-approve` verifies the recorded basis against the file hashes above and reports those cards separately: owner decisions, per-card agreement with AI, not independent inter-rater evidence.
- The owner’s own decisions are still `owner_manual`; the share of them that matched the AI consensus is reported with agree-with-AI cards excluded.
