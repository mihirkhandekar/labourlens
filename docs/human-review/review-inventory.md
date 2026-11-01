# Review inventory

Every review stream in the project, with counts computed from files by `uv run labourlens review-inventory`. “Owner manual” means the review interface recorded a click on that card as `owner_manual` (the interface stamps this for any click or key; it does not show that the card was read). “Agreed with AI” means the owner pressed Agree for that one card in the first pack. “AI only” means an AI reviewed it and the owner has not decided it. “Untouched” means neither. Raw reviewer files and the owner’s export stay private.

Inputs: gold `experiments/gold/draft_cases.jsonl` SHA-256 `6169a9deca78cb5908c584bdf7d17b1c8dd9a15ff7840b3752f3bbb4febb2f9b`; main owner export (reviewer Mihir, exported 2026-10-31T03:28:14.630Z) SHA-256 `60f2ec210d4527ef6cfa1225e5998e21a6c8a0dc8b3119193822ff666b0e4ce5`; 27 AI source files hashed (listed in the pending-review export).

| Stream | What is reviewed | Population | Owner manual | Agreed with AI | AI only | Untouched | Where the AI view comes from | Where the owner’s decisions are stored | Wording for the report |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| Gold: original held-out cases (HO-001…031) | Is the expected behaviour, evidence and facts of each case right? | 31 | 31 | 0 | 0 | 0 | private/human-review/pending-ai/Pend{A,B}{1,2,3}.jsonl (fresh blind, two per dev case); experiments/gold/ai-review/{base,a,b,c}.jsonl; experiments/gold/ai-review-2/{a,b}.jsonl; experiments/gold/ai-review-3/v3.jsonl; docs/human-review/ai-adjudication.md; private/human-review/tiebreak/ | `owner_review` on each record of `experiments/gold/gold_v3.7.jsonl` (the provenance file: 268 owner_manual, 0 agreed_with_ai_suggestion); `experiments/gold/draft_cases.jsonl` (v3.6, still read by scoring) shows only the earlier decisions (3 owner_manual, 42 agreed_with_ai_suggestion, 223 draft); full export in the private main export | 31 reviewed by the owner’s own click and 0 by the owner agreeing with an AI suggestion, per card. |
| Gold: 14 extra owner-decision dev cases | Same question, for the dev cases the owner was asked to look at | 14 | 14 | 0 | 0 | 0 | private/human-review/pending-ai/Pend{A,B}{1,2,3}.jsonl (fresh blind, two per dev case); experiments/gold/ai-review/{base,a,b,c}.jsonl; experiments/gold/ai-review-2/{a,b}.jsonl; experiments/gold/ai-review-3/v3.jsonl; docs/human-review/ai-adjudication.md; private/human-review/tiebreak/ | `owner_review` on each record of `experiments/gold/gold_v3.7.jsonl` (the provenance file: 268 owner_manual, 0 agreed_with_ai_suggestion); `experiments/gold/draft_cases.jsonl` (v3.6, still read by scoring) shows only the earlier decisions (3 owner_manual, 42 agreed_with_ai_suggestion, 223 draft); full export in the private main export | 14 reviewed by the owner’s own click and 0 by the owner agreeing with an AI suggestion, per card. |
| Gold: remaining dev cases | Same question; these are the development cases the system was tuned on | 223 | 223 | 0 | 0 | 0 | private/human-review/pending-ai/Pend{A,B}{1,2,3}.jsonl (fresh blind, two per dev case); experiments/gold/ai-review/{base,a,b,c}.jsonl; experiments/gold/ai-review-2/{a,b}.jsonl; experiments/gold/ai-review-3/v3.jsonl; docs/human-review/ai-adjudication.md; private/human-review/tiebreak/ | `owner_review` on each record of `experiments/gold/gold_v3.7.jsonl` (the provenance file: 268 owner_manual, 0 agreed_with_ai_suggestion); `experiments/gold/draft_cases.jsonl` (v3.6, still read by scoring) shows only the earlier decisions (3 owner_manual, 42 agreed_with_ai_suggestion, 223 draft); full export in the private main export | 223 reviewed by the owner’s own click and 0 by agreeing with an AI suggestion, per card. |
| Held-out v2 cases (HO-V2-001…065) | Were the 65 new test questions and labels right? (signed and frozen before the run) | 65 | 65 | 0 | 0 | 0 | private/human-review/heldout-v2-ai/{A,B,C}.jsonl | `owner_review` on each record of `experiments/gold/heldout_v2_v1.jsonl`; export `experiments/heldout-v2/owner-review-export.json`; signed block in `experiments/heldout-v2/FREEZE.md` | 65 by the owner’s own click, 0 by agreeing with an AI suggestion. |
| Saved model answers (sample of 40) | Is each saved answer right, partly right or wrong? | 40 | 40 | 0 | 0 | 0 | experiments/human-review-sample/*.md (two AI passes); private/human-review/tiebreak/ | private main export (`review-results (8).json`, tab answers); summary `docs/human-review/owner-review-summary.md` | 40 verdicts by the owner’s own click, 0 by agreeing with an AI suggestion. |
| Source checks: passage extraction | Does the extracted text or value match the original page or table row? | 16 | 16 | 0 | 0 | 0 | docs/human-review/ai-pre-review-*-spot-check.md; docs/human-review/ai-verification-of-pre-reviews.md | private main export (tab sources) | 16 by the owner’s own click, 0 by agreeing with an AI suggestion. |
| Source checks: statistical rows | Does the extracted text or value match the original page or table row? | 14 | 14 | 0 | 0 | 0 | docs/human-review/ai-pre-review-*-spot-check.md; docs/human-review/ai-verification-of-pre-reviews.md | private main export (tab sources) | 14 by the owner’s own click, 0 by agreeing with an AI suggestion. |
| Owner decisions J1–J10 | Methodology and acceptance choices (rubric, rights, limits) | 10 | 10 | 0 | 0 | 0 | none (judgement calls; AI adjudication lists them) | private main export (tab decisions); `docs/human-review/owner-review-summary.md` | 10 chosen by the owner. J10 is "accept_limits": accepted with the frozen extraction gaps disclosed, not fixed (own clicks on five original pages). |
| Owner label-change proposals | Label changes the owner proposed in the main pack | 2 | 2 | 0 | 0 | 0 | none | `experiments/gold/proposed_label_changes.jsonl`; chat confirmations quoted in `experiments/gold/CHANGELOG.md` | 2 applied in gold v3.5 on the owner’s chat confirmation (HO-022, DEV-018); 0 still waiting. Chat confirmation is the owner’s decision but not a per-card click in a pack. |
| Held-out v2 structured draft (60 cases) | The reserved structured-only draft of v2 (`HO-V2S-…`), kept on file and not used for the signed test | 60 | 0 | 0 | 0 | 60 | none | nothing | kept as a draft: never reviewed by anyone and not part of any result. |
| Threat-suite cases and verdicts | Does the system resist injection, secret requests and unsafe tools? | 36 | 0 | 0 | 36 | 0 | automatic scorer (experiments/threats/runs/*.verdicts.jsonl) | nothing (no human verdicts exist) | scored automatically; not human-reviewed. |
| Automatic judge validation | Does the automatic judge agree with a reference? | 40 | 0 | 0 | 40 | 0 | AI pre-review used as reference (docs/evaluation-report.md) | nothing | validated against an AI pre-review only. The owner’s manual answer verdicts could serve as the human reference but this has not been computed. |
| Extraction and evidence audits | Were extraction fixes and evidence ids migrated correctly? | 3 | 0 | 0 | 3 | 0 | experiments/heldout-v2/evidence-audit*.json; experiments/gold/evidence-migration-v3.6.json; docs/experiments/m7-extraction-fixes.md | nothing | machine and AI audits only; J10 covers the human acceptance. |
| AI reviews of documents, deck, site and code | End-to-end, copy, deck, site and security reviews | 8 | 0 | 0 | 8 | 0 | docs/human-review/e2e-review-data.md, docs/human-review/e2e-review-deliverables.md, docs/human-review/e2e-review-evaluation.md, docs/human-review/e2e-review-runtime-answer-path.md, docs/human-review/e2e-review-security-deploy.md, docs/human-review/e2e-review-summary.md, docs/human-review/independent-ai-review-m1-2.md, docs/human-review/independent-ai-review-m1.md | nothing | AI reviews only; never described as human review. |

Labelling and verdict streams together (gold, held-out v2, saved answers, source checks): 403 items, 403 by the owner’s own click, 0 by agreeing with an AI suggestion, 0 AI-reviewed only, 0 untouched.

## Status wording that is true today

- Gold labels were drafted by AI. The owner then went through them in the review interface and signed off on every case, answer verdict and source check (four separate streams, 403 items in total: 268 gold questions, 65 held-out v2 questions, 40 saved system answers and 30 source checks; only the first two are questions). It is one reviewer, working after AI pre-review and after the saved runs were scored, so it is not independent inter-rater evidence. The page stamps `owner_manual` for any click or key; the pending pack has no Agree-with-AI control and no manual-only filter.
- AI-only streams (threat suite, judge validation, audits, document reviews) are never called human review.

## Technical facts about the recorded decisions

The page records `owner_manual` for any click or key, so the label shows that the interface received an input. Agreement with a suggestion is not accuracy. The 40 answer verdicts equal the independent AI review’s counts (25/6/9); the redo changed 0 of 23; agreement with the AI suggestion is 198/198 for gold, with four change-clicks, none applied. Strongest human evidence: the first pack (17 answer verdicts, J1 to J10, 3 gold cards), the four change-clicks, J10 and the owner’s written policy decisions (D-031, D-034, D-035, D-036, D-047). Final source checks: 18 matches and 12 minor differences (the first export had 19 and 11). Not independent inter-rater evidence; evaluations were not rescored on v3.7.

## Pending items

### gold dev, never decided by the owner (0)

none

### held-out v2 agreed with AI (optional redo) (0)

none

### answers agreed with AI (optional redo) (0)

none

### passage checks agreed with AI (optional redo) (0)

none

### statistical checks agreed with AI (optional redo) (0)

none

### owner label-change proposals not yet applied (0)

none

## How to finish

1. `uv run labourlens pending-review-pack`, then open `private/human-review/pending-review/index.html` and decide the cards (every click is recorded as `owner_manual`; the pack has no “Manual only” or Agree control).
2. `uv run labourlens pending-ingest --review-export <downloaded file>` (dry run), then add `--write`.
