# Review inventory

Every review stream in the project, with counts computed from files by `uv run labourlens review-inventory`. “Owner manual” means the owner’s own click on that card. “Agreed with AI” means the owner pressed Agree for that one card. “AI only” means an AI reviewed it and the owner has not decided it. “Untouched” means neither. Raw reviewer files and the owner’s export stay private.

Inputs: gold `experiments/gold/draft_cases.jsonl` SHA-256 `6169a9deca78cb5908c584bdf7d17b1c8dd9a15ff7840b3752f3bbb4febb2f9b`; main owner export (reviewer Mihir, exported 2026-10-31T03:28:14.630Z) SHA-256 `60f2ec210d4527ef6cfa1225e5998e21a6c8a0dc8b3119193822ff666b0e4ce5`; 21 AI source files hashed (listed in the pending-review export).

| Stream | What is reviewed | Population | Owner manual | Agreed with AI | AI only | Untouched | Where the AI view comes from | Where the owner’s decisions are stored | Wording for the report |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| Gold: original held-out cases (HO-001…031) | Is the expected behaviour, evidence and facts of each case right? | 31 | 1 | 30 | 0 | 0 | experiments/gold/ai-review/{base,a,b,c}.jsonl; experiments/gold/ai-review-2/{a,b}.jsonl; experiments/gold/ai-review-3/v3.jsonl; docs/human-review/ai-adjudication.md; private/human-review/tiebreak/ | `owner_review` on each record of `experiments/gold/draft_cases.jsonl` (reviewer, decision_source, date); full export in the private main export | 1 reviewed by the owner’s own click and 30 by the owner agreeing with an AI suggestion, per card. |
| Gold: 14 extra owner-decision dev cases | Same question, for the dev cases the owner was asked to look at | 14 | 2 | 12 | 0 | 0 | experiments/gold/ai-review/{base,a,b,c}.jsonl; experiments/gold/ai-review-2/{a,b}.jsonl; experiments/gold/ai-review-3/v3.jsonl; docs/human-review/ai-adjudication.md; private/human-review/tiebreak/ | `owner_review` on each record of `experiments/gold/draft_cases.jsonl` (reviewer, decision_source, date); full export in the private main export | 2 reviewed by the owner’s own click and 12 by the owner agreeing with an AI suggestion, per card. |
| Gold: remaining dev cases | Same question; these are the development cases the system was tuned on | 223 | 0 | 0 | 223 | 0 | experiments/gold/ai-review/{base,a,b,c}.jsonl; experiments/gold/ai-review-2/{a,b}.jsonl; experiments/gold/ai-review-3/v3.jsonl; docs/human-review/ai-adjudication.md; private/human-review/tiebreak/ | nothing yet (pending-review pack) | AI-reviewed only: 223 cases (AI reviewers per case: 1: 164, 2: 20, 3: 28, 4: 11). Not reviewed by the owner. |
| Held-out v2 cases (HO-V2-001…065) | Were the 65 new test questions and labels right? (signed and frozen before the run) | 65 | 59 | 6 | 0 | 0 | private/human-review/heldout-v2-ai/{A,B,C}.jsonl | `owner_review` on each record of `experiments/gold/heldout_v2_v1.jsonl`; export `experiments/heldout-v2/owner-review-export.json`; signed block in `experiments/heldout-v2/FREEZE.md` | 59 by the owner’s own click, 6 by agreeing with an AI suggestion. |
| Saved model answers (sample of 40) | Is each saved answer right, partly right or wrong? | 40 | 17 | 23 | 0 | 0 | experiments/human-review-sample/*.md (two AI passes); private/human-review/tiebreak/ | private main export (`review-results (8).json`, tab answers); summary `docs/human-review/owner-review-summary.md` | 17 verdicts by the owner’s own click, 23 by agreeing with an AI suggestion. |
| Source checks: passage extraction | Does the extracted text or value match the original page or table row? | 16 | 0 | 16 | 0 | 0 | docs/human-review/ai-pre-review-*-spot-check.md; docs/human-review/ai-verification-of-pre-reviews.md | private main export (tab sources) | 0 by the owner’s own click, 16 by agreeing with an AI suggestion. |
| Source checks: statistical rows | Does the extracted text or value match the original page or table row? | 14 | 0 | 14 | 0 | 0 | docs/human-review/ai-pre-review-*-spot-check.md; docs/human-review/ai-verification-of-pre-reviews.md | private main export (tab sources) | 0 by the owner’s own click, 14 by agreeing with an AI suggestion. |
| Owner decisions J1–J10 | Methodology and acceptance choices (rubric, rights, limits) | 10 | 10 | 0 | 0 | 0 | none (judgement calls; AI adjudication lists them) | private main export (tab decisions); `docs/human-review/owner-review-summary.md` | 10 chosen by the owner. J10 is "inspect_more": an explicit request for more inspection, not acceptance. |
| Owner label-change proposals | Label changes the owner proposed in the main pack | 2 | 2 | 0 | 0 | 0 | none | `experiments/gold/proposed_label_changes.jsonl`; chat confirmations quoted in `experiments/gold/CHANGELOG.md` | 2 applied in gold v3.5 on the owner’s chat confirmation (HO-022, DEV-018); 0 still waiting. Chat confirmation is the owner’s decision but not a per-card click in a pack. |
| Held-out v2 structured draft (60 cases) | The reserved structured-only draft of v2 (`HO-V2S-…`), kept on file and not used for the signed test | 60 | 0 | 0 | 0 | 60 | none | nothing | kept as a draft: never reviewed by anyone and not part of any result. |
| Threat-suite cases and verdicts | Does the system resist injection, secret requests and unsafe tools? | 36 | 0 | 0 | 36 | 0 | automatic scorer (experiments/threats/runs/*.verdicts.jsonl) | nothing (no human verdicts exist) | scored automatically; not human-reviewed. |
| Automatic judge validation | Does the automatic judge agree with a reference? | 40 | 0 | 0 | 40 | 0 | AI pre-review used as reference (docs/evaluation-report.md) | nothing | validated against an AI pre-review only. The owner’s manual answer verdicts could serve as the human reference but this has not been computed. |
| Extraction and evidence audits | Were extraction fixes and evidence ids migrated correctly? | 3 | 0 | 0 | 3 | 0 | experiments/heldout-v2/evidence-audit*.json; experiments/gold/evidence-migration-v3.6.json; docs/experiments/m7-extraction-fixes.md | nothing | machine and AI audits only; J10 covers the human acceptance. |
| AI reviews of documents, deck, site and code | End-to-end, copy, deck, site and security reviews | 11 | 0 | 0 | 11 | 0 | docs/human-review/copy-audit.md, docs/human-review/deck-copy-review.md, docs/human-review/e2e-review-data.md, docs/human-review/e2e-review-deliverables.md, docs/human-review/e2e-review-evaluation.md, docs/human-review/e2e-review-runtime-answer-path.md, docs/human-review/e2e-review-security-deploy.md, docs/human-review/e2e-review-summary.md, docs/human-review/independent-ai-review-m1-2.md, docs/human-review/independent-ai-review-m1.md, docs/human-review/site-artifact-review.md | nothing | AI reviews only; never described as human review. |

Labelling and verdict streams together (gold, held-out v2, saved answers, source checks): 403 items, 79 by the owner’s own click, 101 by agreeing with an AI suggestion, 223 AI-reviewed only, 0 untouched.

## Status wording that is true today

- Do not write “all labelling was manually reviewed by the owner”. Today 79 of 403 items were decided by the owner’s own click.
- True: “The owner made a per-card decision on 180 of 403 labelling items; 79 by their own click and 101 by agreeing with an AI suggestion. The remaining 223 were checked by AI reviewers only.”
- AI-only streams (threat suite, judge validation, audits, document reviews) are never called human review.

## Pending items

### gold dev, never decided by the owner (223)

DEV-001, DEV-002, DEV-003, DEV-004, DEV-005, DEV-006, DEV-007, DEV-008, DEV-009, DEV-010, DEV-011, DEV-012, DEV-013, DEV-015, DEV-016, DEV-017, DEV-019, DEV-020, DEV-021, DEV-022, DEV-023, DEV-024, DEV-025, DEV-026, DEV-027, DEV-028, DEV-029, DEV-030, DEV-031, DEV-032, DEV-033, DEV-034, DEV-402, DEV-403, DEV-404, DEV-405, DEV-406, DEV-407, DEV-408, DEV-409, DEV-410, DEV-411, DEV-412, DEV-413, DEV-414, DEV-415, DEV-416, DEV-417, DEV-418, DEV-419, DEV-420, DEV-421, DEV-422, DEV-423, DEV-427, DEV-428, DEV-501, DEV-502, DEV-503, DEV-504, DEV-505, DEV-506, DEV-507, DEV-508, DEV-509, DEV-510, DEV-511, DEV-512, DEV-513, DEV-514, DEV-515, DEV-516, DEV-517, DEV-518, DEV-519, DEV-520, DEV-521, DEV-522, DEV-523, DEV-524, DEV-525, DEV-526, DEV-527, DEV-528, DEV-529, DEV-530, DEV-601, DEV-602, DEV-603, DEV-604, DEV-605, DEV-606, DEV-607, DEV-608, DEV-609, DEV-610, DEV-611, DEV-612, DEV-613, DEV-614, DEV-615, DEV-616, DEV-617, DEV-618, DEV-619, DEV-620, DEV-621, DEV-622, DEV-623, DEV-624, DEV-625, DEV-626, DEV-627, DEV-628, DEV-631, DEV-632, DEV-633, DEV-634, DEV-635, DEV-101, DEV-102, DEV-103, DEV-104, DEV-105, DEV-106, DEV-107, DEV-108, DEV-109, DEV-110, DEV-111, DEV-112, DEV-113, DEV-114, DEV-115, DEV-116, DEV-117, DEV-118, DEV-119, DEV-120, DEV-121, DEV-122, DEV-123, DEV-124, DEV-125, DEV-126, DEV-127, DEV-128, DEV-129, DEV-130, DEV-131, DEV-132, DEV-133, DEV-134, DEV-135, DEV-301, DEV-302, DEV-303, DEV-304, DEV-305, DEV-306, DEV-307, DEV-308, DEV-309, DEV-310, DEV-311, DEV-312, DEV-313, DEV-314, DEV-315, DEV-316, DEV-317, DEV-318, DEV-319, DEV-320, DEV-321, DEV-322, DEV-323, DEV-324, DEV-326, DEV-327, DEV-328, DEV-329, DEV-330, DEV-331, DEV-332, DEV-333, DEV-334, DEV-335, DEV-201, DEV-202, DEV-203, DEV-204, DEV-205, DEV-206, DEV-207, DEV-208, DEV-209, DEV-210, DEV-211, DEV-212, DEV-213, DEV-214, DEV-215, DEV-216, DEV-217, DEV-218, DEV-219, DEV-220, DEV-221, DEV-222, DEV-223, DEV-224, DEV-225, DEV-226, DEV-227, DEV-228, DEV-229, DEV-230, DEV-231, DEV-232, DEV-233, DEV-234, DEV-235

### held-out v2 agreed with AI (optional redo) (6)

HO-V2-001, HO-V2-002, HO-V2-003, HO-V2-004, HO-V2-052, HO-V2-053

### answers agreed with AI (optional redo) (23)

DEV-510, DEV-517, DEV-519, DEV-522, DEV-530, DEV-404, DEV-413, DEV-414, DEV-434, DEV-632, DEV-312, DEV-315, DEV-020, DEV-103, DEV-111, DEV-005, DEV-006, DEV-120, DEV-210, DEV-624, DEV-625, DEV-333, DEV-335

### passage checks agreed with AI (optional redo) (16)

passage-01, passage-02, passage-03, passage-04, passage-05, passage-06, passage-07, passage-08, passage-09, passage-10, passage-11, passage-12, passage-13, passage-14, passage-15, passage-16

### statistical checks agreed with AI (optional redo) (14)

statistical-01, statistical-02, statistical-03, statistical-04, statistical-05, statistical-06, statistical-07, statistical-08, statistical-09, statistical-10, statistical-11, statistical-12, statistical-13, statistical-14

### J10 extraction gaps (owner asked for more inspection) (6)

J10-1, J10-2, J10-3, J10-4, J10-5, J10

### owner label-change proposals not yet applied (0)

none

## How to finish

1. `uv run labourlens pending-review-pack`, then open `private/human-review/pending-review/index.html` and decide the cards (turn on “Manual only” so every decision is your own click).
2. `uv run labourlens pending-ingest --review-export <downloaded file>` (dry run), then add `--write`.
