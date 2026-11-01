# Review records

What "review" means in this repository, and where each record is. Nothing here is a claim of independent human review.

| Kind | Who | Files |
|---|---|---|
| **Owner review** | One person (the project owner), by own click in a local review page, after AI pre-review and after the saved runs were scored. 403 items: 268 gold cases, 65 held-out v2 cases, 40 saved answers, 30 source checks. One reviewer, so not inter-rater evidence. | [`owner-review-final-summary.md`](owner-review-final-summary.md) (current), [`owner-review-summary.md`](owner-review-summary.md) (31 Oct export, superseded), [`OWNER-REVIEW-GUIDE.md`](OWNER-REVIEW-GUIDE.md) (the rubric and procedure), [`judge-vs-owner.md`](judge-vs-owner.md), [`numbers-audit.md`](numbers-audit.md) |
| **AI review** | Language-model agents, labelled as such. Blind passes saw no earlier opinion; the adjudication pass was not blind. They are one model family, so their agreement is not independent. | [`ai-pre-review-passage-spot-check.md`](ai-pre-review-passage-spot-check.md), [`ai-pre-review-statistical-spot-check.md`](ai-pre-review-statistical-spot-check.md), [`ai-verification-of-pre-reviews.md`](ai-verification-of-pre-reviews.md), [`ai-adjudication.md`](ai-adjudication.md), [`independent-ai-review-m1.md`](independent-ai-review-m1.md), [`independent-ai-review-m1-2.md`](independent-ai-review-m1-2.md), [`heldout-v2-ai-review-summary.md`](heldout-v2-ai-review-summary.md) |
| **End-to-end AI review** (five areas: data, runtime, evaluation, security and deployment, deliverables) | Five AI reviewers, 31 Oct 2026 | [`e2e-review-summary.md`](e2e-review-summary.md), then [data](e2e-review-data.md), [runtime](e2e-review-runtime-answer-path.md), [evaluation](e2e-review-evaluation.md), [security and deployment](e2e-review-security-deploy.md), [deliverables](e2e-review-deliverables.md) |
| **Blank forms** (what the owner filled in) | none | [`gold-review.md`](gold-review.md), [`passage-spot-check.md`](passage-spot-check.md), [`statistical-spot-check.md`](statistical-spot-check.md); they hold questions and locators, no verdicts |
| **Inventory** | | [`review-inventory.md`](review-inventory.md): what was reviewed by whom, and what was not |

Gold v3.7 records the owner review as provenance fields only; no label changed and no saved evaluation was rescored on it. Four owner "change" clicks (D-047) are recorded and not applied. The decision record is in [`../decisions.md`](../decisions.md).

The review pages and exports contain source text and stay in the owner's gitignored `private/` folder; only counts and shareable comments are committed.
