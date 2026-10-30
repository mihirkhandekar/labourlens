# AI pre-review by claude-agent (ReviewGoldB)

## Coverage and verdicts

- Reviewed DEV-301–DEV-335 and DEV-401–DEV-435: **70 cases**.
- **63 ok, 7 fix, 0 drop**. Per-case findings and evidence checks are in `b.jsonl`.
- This is an independent AI pre-review, not the owner’s final review. Existing gold labels and review fields were not modified.

## Highest-priority corrections

1. **DEV-325, DEV-327 — observation month is not publication date.** The Q3 2025 final-release passage was published **11 December 2025**; the Q4 2024 final-release passage was published **19 March 2025**. Reword their source descriptions. Current-series values remain **2.9% resident** and **3.0% citizen**, respectively; their contemporaneous release values remain **2.8%** and **2.9%**.
2. **DEV-308 — reference quarter is not the retrenchment cohort.** The **55.0%** six-month result in reference-quarter 2024-Q2 concerns people retrenched in **2023-Q4**, not a 2024-Q2 retrenchment cohort. Definition evidence: `mom-2024-q2-final:p020:b024:b33400b2` and `mom-2024-q2-final:p049:b013:9a39e4e7`.
3. **DEV-310, DEV-431 — distinguish cohorts as well as horizons.** Reference-quarter 2026-Q2 six-month **54.9%** concerns **2025-Q4** retrenchments, whereas twelve-month **69.8%** concerns **2025-Q2** retrenchments. They are not one cohort followed twice. Add `mom-2026-q2-final:p022:b019:218fc96b`. DEV-431 additionally needs passage evidence for its resident-population wording because the cited dataset records `unverified_basis`; `mom-2026-q2-final-release:s01:i003:1d7fc2bc` supplies it.
4. **DEV-401 — two clarification axes, not one.** March 2025 residents: **69,200 SA** versus **64,600 NSA**; population clarification alone still leaves different answers.
5. **DEV-406 — relative-date label depends on runtime context.** With this session’s date, the preceding quarter is **2026-Q3**, outside the supported window. Without a date anchor, clarification is sensible. Make the unresolved anchor explicit, or fix the anchor and label the out-of-window request as abstain. Confidence is lower because this is an evaluation-context design issue rather than a false statistical fact.

## What was independently checked

- Loaded **13,484 passages** from the actual `data/passages` location (the task’s `data/processed/passages` description does not match this checkout), and **43,662 observations** from `data/processed/observations.parquet`.
- Read the D-017/D-026 policy sections, gold schema, and static query/calculation boundaries in `src/labourlens/agent/tools.py`.
- Inspected every cited passage for this slice; matched every cited observation’s source, period, dimension, population, adjustment, unit and value. No missing or mismatched cited IDs were found.
- Independently read all numeric reference levels. Recomputed two-period directions/differences using decimal arithmetic. No case in this slice has a non-null `calculation` field, and none requires arithmetic on text-only figures.
- For each of **DEV-411–DEV-420**, independently searched every passage and the observation metadata/schema. Date variants for the three future-quarter requests returned no passage matches and their exact observation periods were absent. **1980** returned no passage matches and **1980-Q1** no observations; the resident series begins **1992-Q1**. Quantum returned **four** passages, all inspected and unrelated to computing-job vacancies. Blockchain, nomad, Tampines, Punggol and nonbinary variants returned no relevant passages or observation categories. The observation table’s latest period is **2026-Q2**. These ten abstain labels stand.
- Confirmed ambiguity actually changes the answer: population-specific unemployment, SA versus NSA, count versus rate, multiple Q2 years, opposite re-entry trends, different manufacturing rate trends, separate work-reduction indicators, and PME versus PMET totals. DEV-406 has the context caveat above.
- Refusal cases **DEV-421–DEV-428** ask for prohibited forecasts, causal certainty, or personal employment choices rather than separable factual subquestions. Their refuse labels stand. Descriptive-plus-causal-caveat cases **DEV-429–DEV-435** remain answer, not blanket refusal.
- Revision cases have actual passage-level versions and publication dates; observation snapshot IDs indicate **30 October 2026** acquisitions. Advance/final sequencing is supported. Dataset-versus-release discrepancies are not automatically attributed to revision when adjustment or population metadata are unresolved. The source-specific numerical values in DEV-321–DEV-335 agree with the local evidence.
- Checked the question/reference paraphrases against their cited passages: none exceeded six consecutive matching words. No MOM passage text is reproduced in these committed review outputs.

## Alternative evidence and limitations

`b.jsonl` identifies inspected optional passages supporting individual numerical facts where available. Such fragments should not automatically become primary evidence for a whole synthesis. Missing cohort/population evidence is specifically actionable in the fixes above. Relevant source and number searches also produced unrelated table/definition matches; those were not promoted to gold evidence.

This was local-data and static-code review, not a retrieval benchmark or live model/tool execution. It establishes factual support, not a guarantee that the deployed retriever finds every passage. Alternative-evidence enumeration is not claimed exhaustive; a final owner review can add further semantically equivalent evidence. No paid calls, fetch/build commands, git operations, or edits to existing files were performed. No tests, builds, or formatters were run.
