# LabourLens — current state

Updated 2 November 2026, submission audit fixes (D-064). Dated working entries, including every original result and count, are retained in [progress log 2](archive/progress-log-2.md); the earlier log is [progress log 1](archive/progress-log.md).

| Area | Current position and evidence |
|---|---|
| Implementation | Through M7 implemented. Ingestion, retrieval, bounded research agent, MCP, evaluation and report code are under `src/labourlens/`. Implementation is not owner acceptance. |
| Defaults and reporting | D-056/D-061 retain r3/base/`gpt-6-luna`; [final headline](../experiments/eval/final-mean.json) is the mean of FIN and FIN2, with both singles retained. Development gain is descriptive; neither test set demonstrates a gain. |
| Corpus | v3.1: 85 sources, 52,020 observations, 16,419 passages and 1,847 chunks, from [versioned snapshot](../experiments/corpus-snapshots/v3.1.json). Restricted raw documents, passages and indexes stay local. |
| Served route and safety | D-058/D-061 measures a mixed 65-case served-chain sample, not the full sets or browser admission. Primary context 5/6 prevents a clean protocol pass. [Fresh threats](../experiments/threats/ti06-v2-fresh-20261102/SUMMARY.md): all configurations 35/36; T-I06 remains unstable. |
| Review | 403 recorded confirmations/sign-offs, not independent verifications. [Timing audit](human-review/numbers-audit.md#3-human-review-evidence-what-the-timestamps-show-priority): final 330 in 6.2 minutes, median gap 0.39 s. First-pack 17 answer verdicts, J1–J10 and three gold cards are stronger evidence. Second-family judging is AI sensitivity evidence, not human review. |
| Verification | Dated command outcomes are in [fresh-clone check](fresh-clone-check.md). Audit-fix verification is recorded in D-064 after actual execution; no timeless test count is claimed here. |
| Open owner actions | Final package acceptance and 20-minute rehearsal; rights/protocol acceptance; provider-side spend cap; status of rotation after the recorded reviewer-session secret exposure. No rotation is evidenced here. |

Tool set v2 remains **not adopted** (D-048). Extraction gaps, post-run labels, shared original-test evidence, judge dependence and unresolved rights remain limitations, not closed defects: [evaluation report](evaluation-report.md), [data sheet](data-sheet.md), [historical e2e dispositions](human-review/e2e-review-summary.md).

**Next gate:** owner package/rehearsal and rights/protocol acceptance. Do not start a new experiment or adopt another tool set without a new explicit decision. Share a GitHub URL, fresh clone or `git archive HEAD`, never a copy of the working folder containing ignored private files.
