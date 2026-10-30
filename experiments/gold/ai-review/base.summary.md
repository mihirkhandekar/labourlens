# Base-case AI pre-review

AI pre-review by claude-agent (ReviewGoldBase). This is independent AI screening for the owner's later review, not a substitute for it. No gold cases or review-status fields were changed.

## Coverage and verdicts

All 65 requested cases are covered: DEV-001–DEV-034 and HO-001–HO-031.

| Verdict | Cases |
|---|---:|
| ok | 33 |
| fix | 32 |
| drop | 0 |

Detailed, field-level proposals and performed-check evidence are in `base.jsonl`. Proposed changes are recommendations, not applied edits. Every record identifies the AI reviewer and contains all eight check entries.

## Most common issues

Issue counts are non-exclusive (35 issue entries across 32 fix cases):

| Issue type | Entries |
|---|---:|
| Missing alternative valid evidence | 15 |
| Arithmetic outside actual tool contract | 8 |
| Definition, question scope, or partial/conflicting evidence | 7 |
| Non-answer behavior mismatch | 5 |

- **Arithmetic:** every existing calculation object's expected number matches independent Decimal subtraction. Nevertheless, HO-006 asks for a cross-population comparison that `calculate_change` rejects. DEV-031 and DEV-032 supply text-only inputs. DEV-011, DEV-012, HO-017, HO-018 and HO-019 additionally require computed revision deltas in reference facts without eligible observation inputs. Proposals retain the published values and comparison direction, removing unsupported arithmetic. HO-020 likewise removes an unsupported mixed text/data delta.
- **Behavior:** DEV-014 and HO-023 should refuse unsupported causal attribution; DEV-016 and HO-026 should refuse forecasting. HO-020 asks for a cause its evidence cannot establish, so it should abstain consistently with HO-024. A lack of published AI attribution must not become proof that AI played no role.
- **Definitions and scope:** HO-003 needs the follow-up-quarter employment definition and covered-establishment denominator. DEV-009 contains a dangling PDF passage and should distinguish the earlier re-entry cohort from current-quarter layoffs. DEV-023 should say residents rather than locals. DEV-013 and HO-021 should clarify adjustment as well as population.
- **Dataset/report conflicts:** HO-011 should pin its requested dataset snapshot: its counts are 75,200 and 69,900, whereas final-release vacancy levels are 73,300 and 68,600. HO-014 should acknowledge those different levels without inventing a verified cause.
- **Alternative evidence:** repeated definitions and duplicated annual highlights create valid unlisted passage locations. Proposed additions name stable IDs, not chunks. DEV-001 also has a matching statistical observation; several cases have additional narrative evidence. These additions prevent some valid citations from being scored as misses, but are not an exhaustive semantic annotation of the corpus.

## What was actually checked

Read every cited passage for all 65 cases from local `data/passages/*.jsonl` (the actual `paths.PASSAGES` location), and every cited observation from `data/processed/observations.parquet`. Checked questions, behavior, fact support, reference paraphrasing, and tool eligibility. Recomputed all 13 calculation objects using Decimal arithmetic. No seven-word normalized verbatim overlaps were detected between the existing reference facts and their cited passages.

Alternative-evidence screening used normalized exact duplicates across the corpus, targeted topic/numeric searches, same-source numeric candidates, and same-dataset/period/dimension observation variants. Different adjustment series were not treated as interchangeable. Historical definitions can be alternatives when the question is timeless; matching words in a different-year empirical finding do not qualify. Source-specific questions retained their source restrictions.

Inspected `src/labourlens/agent/tools.py`: deterministic calculations require observation labels from the same series, with different periods. No application tests, fetch/build commands, retriever evaluations, paid API calls, or publisher re-downloads were run. Text-only reference facts were checked against passages, not falsely described as recomputed from statistical observations. Missing-evidence and causal judgments are local-corpus pre-review findings, not proof about every possible external publication.

The owner should prioritize behavior labels, the tool-incompatible calculation cases, and the vacancy/report discrepancies before accepting the smaller evidence-list additions. No case was marked for removal because each identified problem has a concrete repair within the existing tools.
