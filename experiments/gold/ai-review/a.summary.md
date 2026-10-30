# Gold-case pre-review A

AI pre-review by claude-agent (ReviewGoldA)

## Coverage and verdicts

- All **70** assigned cases reviewed: DEV-101–DEV-135 and DEV-201–DEV-235.
- **61 ok; 9 fix; 0 drop.** Individual findings and check evidence are in `a.jsonl`.
- Existing cases, owner review fields, observations and source passages were not changed.

## Owner attention: nine proposed fixes

| Cases | Finding | Proposed action |
|---|---|---|
| DEV-102, DEV-114 | Opening counts inherit a misleading `persons` unit from normalized records. | Describe 82,600 and 14,800 as vacancies/openings, not people. Flag the normalization issue separately. |
| DEV-116, DEV-131 | The same semantic-unit problem appears in calculation input facts. | Use openings for input counts. Keep the correct changes: −8.52% and +14.74%, respectively. |
| DEV-203, DEV-210, DEV-231 | Correct arithmetic, but calculation inputs are report-text literals rather than structured observations. | Rewrite as published-share lookups and remove `calculation`. Current decreases are correctly 6.5, 13.0 and 10.0 percentage points; the available calculator cannot accept these passage figures. |
| DEV-217 | Alternative evidence omitted from the same named release. | Add `mom-2025-q1-final-release:s02:i002:de8ee350`. |
| DEV-230 | Two additional passages in the same named report support the tracking limitation. | Add `mom-2026-q1-final:p022:b020:7059aed2` and `mom-2026-q1-final:p054:b006:84ddf2d9`. |

## Important findings that do not require changing the answer

- **DEV-219:** the original March 2025 release gives overall/resident/citizen rates of **2.0% / 2.9% / 3.1%**. Current observations give **2.0% / 2.8% / 3.0%**. The question explicitly names the release; its original figures remain correct. Do not silently replace them with a newer dataset vintage.
- **DEV-223:** original June 2025 release: **76,900 openings, 2.9%, ratio 1.35**. Current observations: **78,100, 3.0%, 1.38**. Again, retain the explicitly requested release vintage.
- **DEV-230 and DEV-235:** methodological explanations recur across quarterly reports. Cross-report corroboration IDs are recorded; source-specific questions mean those other documents are not automatically interchangeable gold replacements.
- **DEV-207:** the same salary-support caps appear in other releases. **DEV-216:** a later advance release repeats the December/September survey comparison. Relevant IDs are recorded as corroboration.
- **DEV-115, DEV-128, DEV-129, DEV-133:** the observation population remains `unverified_basis`. Dataset-bound wording avoids inventing a verified population; retain that limitation.
- DEV-132–DEV-134 are value-selection/ranking questions on supplied structured records, not calculations on text-only numbers.

## Work actually performed

- Loaded the local draft cases, **43,662** observation rows and **13,484** passage records using Python; read every cited passage for the 35 report cases.
- Inspected every cited observation for the 35 structured cases: IDs, source, period, dimension, indicator, population, adjustment, unit and value.
- Independently recomputed all **20** structured calculation results from parquet inputs, including extrema; all match the recorded expected values. Checked relative percent versus percentage-point units.
- Independently checked the three text-based decreases. They are numerically right but outside the available deterministic calculator contract.
- Inspected `src/labourlens/agent/tools.py` for statistic filters and calculator restrictions, and `src/labourlens/retrieval/gold.py` for evidence and calculation conventions.
- Searched the complete passage corpus using fact-specific patterns and normalized containment, then read accepted candidate alternatives. Also searched exact semantic duplicate observation rows. No additional identical observation records were found.
- Checked report-reference paraphrases against cited evidence: none of these 35 reference lists had a seven-word contiguous source overlap under word normalization.

## Boundaries

This is an AI pre-review, not owner sign-off. Cross-report searches are targeted and **not an exhaustive semantic equivalence audit**. Numeric matches in isolated PDF table fragments were not accepted without their definitions and header context. Text-only survey shares and policy amounts cannot be independently reconstructed from the structured observation collection; the review checked their cited passages and does not claim otherwise. No external downloads, model requests, builds or test suites were run. Tool answerability is a static code/data assessment, not an executed end-to-end agent result. No MOM passage prose is reproduced here.
