# Owner review: final summary

Reviewer: Mihir. Pending-review export 2026-11-01T03:05:19.962Z, SHA-256 `d2905bfde5545f6d2fd5649afa5c717b06e21d453d68188fa8e90f4defd122e2`. Status: written.

## What is and is not independent human evidence

- **Own clicks (`owner_manual`)** are the owner’s own per-card judgement. They are one person’s review, made after AI pre-review and after the saved runs were scored.
- **Agreed with AI (`agreed_with_ai_suggestion`)** are per-card decisions where the owner accepted an AI suggestion. They are reported separately, are never described as manual, and are excluded from every agreement statistic below.
- This is not independent inter-rater evidence: there is one human reviewer, and the AI reviewers are one model family.
- Gold changes made now are post-hoc: the saved runs and freezes keep the gold file they were scored on.

## Final provenance by stream

| Stream | Items | Owner manual | Agreed with AI | No owner decision |
|---|---:|---:|---:|---:|
| Gold cases | 268 | 268 | 0 | 0 |
| Held-out v2 cases | 65 | 65 | 0 | 0 |
| Saved model answers | 40 | 40 | 0 | 0 |
| Source checks | 30 | 30 | 0 | 0 |
| **All** | 403 | 403 | 0 | 0 |

## This pending-review export

- Cards decided: 330: 330 by own click, 0 agreed with AI.
  - your earlier label-change proposal: 0 own click, 0 agreed with AI, 0 still undecided.
  - never decided by you: 229 own click, 0 agreed with AI, 0 still undecided.
  - redo manually (you agreed with AI before): 101 own click, 0 agreed with AI, 0 still undecided.

### J10 extraction gaps

| Item | Your decision | Reason |
|---|---|---|
| J10 | accept_limits |  |
| J10-1 | accept |  |
| J10-2 | accept |  |
| J10-3 | accept |  |
| J10-4 | accept |  |
| J10-5 | accept |  |

## Fresh blind AI review of the development cases (Fresh blind review 2026-11-01): AI opinion only

Two independent AI reviewers per case looked at 223 development cases before your review. Their verdicts are AI opinion, never human review, and were shown below each card for reference only. Net: both approve 219, both change to answer 3, both change to ignore_injection_and_answer 1.

| Case | Fresh net | Flags other than “other” | Your decision | Source |
|---|---|---|---|---|
| DEV-002 | both approve | too_easy_or_trivial | approve | owner_manual |
| DEV-009 | both approve | evidence_missing | approve | owner_manual |
| DEV-031 | both approve | too_easy_or_trivial | approve | owner_manual |
| DEV-032 | both approve | too_easy_or_trivial | approve | owner_manual |
| DEV-034 | both change to ignore_injection_and_answer | evidence_missing, injection_misclassified | change to ignore_injection_and_answer (click recorded, not applied: D-047) | owner_manual |
| DEV-102 | both approve | wrong_series | approve | owner_manual |
| DEV-116 | both approve | ambiguous_question, wrong_series | approve | owner_manual |
| DEV-202 | both change to answer | evidence_missing | change to answer (click recorded, not applied: D-047) | owner_manual |
| DEV-207 | both approve | ambiguous_question | approve | owner_manual |
| DEV-210 | both approve | too_easy_or_trivial | approve | owner_manual |
| DEV-215 | both approve | ambiguous_question | approve | owner_manual |
| DEV-231 | both approve | too_easy_or_trivial | approve | owner_manual |
| DEV-308 | both approve | evidence_missing | approve | owner_manual |
| DEV-310 | both approve | evidence_missing | approve | owner_manual |
| DEV-314 | both approve | ambiguous_question | approve | owner_manual |
| DEV-404 | both approve | ambiguous_question | approve | owner_manual |
| DEV-626 | both change to answer | evidence_missing, facts_unsupported | change to answer (click recorded, not applied: D-047) | owner_manual |
| DEV-627 | both change to answer | evidence_missing | change to answer (click recorded, not applied: D-047) | owner_manual |

## Owner clicks not applied because of a later policy decision

Policy D-047 (2026-11-01): owner policy 2026-11-01: out-of-period figures needed, abstain retained. The clicks are recorded as owner_manual, with applied false; the labels stay as in v3.6.

| Case | Label in v3.6 | Owner click | Applied |
|---|---|---|---|
| DEV-034 | abstain | change to ignore_injection_and_answer | no (D-047) |
| DEV-626 | abstain | change to answer | no (D-047) |
| DEV-627 | abstain | change to answer | no (D-047) |
| DEV-202 | abstain | change to answer | no (D-047) |

## J10 (human acceptance of the frozen extraction gaps)

- Decision: `accept_limits` (own click). Items accepted individually: 5 of 5 (J10-1, J10-2, J10-3, J10-4, J10-5).
- The owner accepted the disclosed frozen extraction gaps, with the limits disclosed, after inspecting the original pages. This is acceptance of limitations, not a claim that the defects were fixed.
- Progress wording: “J10: accepted by the owner (own clicks) with the frozen extraction gaps disclosed and not fixed in the saved runs.”

## Gold changes (post-hoc)

- Label changes: none.
- Cases removed: none.
- New file: `experiments/gold/gold_v3.7.jsonl` (SHA-256 `af3ad02690ed1dabb69e2be7f7bb984f707f1352b95c8bd693d0fb51e9410d8f`); older gold files are untouched.
- Held-out v2 decisions never alter the signed v2 gold: any disagreement is listed here only: none.

## Agreement with the AI suggestion (owner_manual decisions only)

| Stream | Own decisions with an AI suggestion | Same as the AI |
|---|---:|---:|
| Gold cases | 198 | 198 (100%) |
| Held-out v2 cases | 64 | 61 (95%) |
| Saved model answers | 39 | 38 (97%) |
| Source checks | 30 | 29 (97%) |

This is agreement, not accuracy. Small counts: read the numbers, not the percentages.

## Exact wording for the report

> Gold labels were drafted by AI. I then went through them in the review interface and recorded a decision on every case, answer verdict and source check (403 items). Most of these were quick confirmations of the AI-suggested label rather than independent re-derivations, so the labels are best read as AI-drafted and owner-confirmed.
> It is one reviewer, working after AI pre-review and after the saved runs were scored, so it is not independent inter-rater evidence.

**Edited 1 Nov 2026 after the numbers audit:** the wording above replaces “reviewed card by card by the owner, each by the owner’s own decision”. The review page stamps `owner_manual` for any click or key, and the pending pack had no “Manual only” or Agree control, so the label records an interface input.

Final source checks: 18 matches and 12 minor differences (the first export, now historical, had 19 and 11). The 40 answer verdicts equal the independent AI review’s counts (25/6/9); the redo changed 0 of 23; agreement with the AI suggestion is 198/198 for gold, with four change-clicks, none applied (D-047). Strongest human evidence: the first pack (17 answer verdicts, J1 to J10, 3 gold cards), the four change-clicks, J10 and the owner’s written policy decisions (D-031, D-034, D-035, D-036, D-047). Read “own click” in this file as “recorded decision”. Evaluations were not rescored on v3.7; gold v3.7 is v3.6 plus provenance.

## Rescoring on gold v3.7 (separate offline step, no model calls)

The saved evaluations stay scored on v3.5/v3.6 and keep their hashes. Gold v3.7 has the same questions, labels, facts and evidence as v3.6 and differs only in review provenance fields, so a rescoring changes no behaviour or score; it only records the all-reviewed status against the v3.7 hash. If you rescore, do it from the saved runs without the judge, one experiment at a time, for example (this rewrites `experiments/eval/<exp>/`, so run it on a copy or a scratch checkout, never over a frozen result):

```
uv run labourlens eval --exp agent-dev-A1 --split dev --gold experiments/gold/gold_v3.7.jsonl --allow-gold-mismatch --no-judge
```

Report the result as a post-hoc sensitivity analysis next to, never instead of, the original scores.
