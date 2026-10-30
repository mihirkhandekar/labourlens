# Second AI pre-review, slice A (by claude-agent Review2A)

Not human review. Slice: the 78 changelog rows plus the "Not applied" items (DEV-001..DEV-635 and HO-002..HO-026 changed cases). Output: `a.jsonl`, one object per case.

Method: diffed each case against `git show 1a3f901^`, read every added passage and observation, recomputed calculations, checked reference-fact numbers against cited text/observations (automated number check plus reading), ran a 7-token overlap check between new text and cited passages (only DEV-610: numbers-only run, harmless), and compared behaviour labels with all other refuse/abstain cases.

## Counts
- agree: 66
- concern: 12
- disagree: 0

No wrong numbers, no unsupported facts and no wrong calculations found. Removed calculations (DEV-031/032/203/210/231/624-628/630, HO-006) are all now answerable with the actual tools (two-value lookups with a direction).

## Look at these first
1. **DEV-014, DEV-632, DEV-633, DEV-635 (refuse relabels).** Convention is mixed.
   - DEV-014 asks "why / was it AI" and the release partly answers it; refuse conflicts with its own reference facts and evidence, and with DEV-431, which is labelled answer despite a causal premise.
   - DEV-632/633 resemble abstain cases DEV-631/634 (a publication-specific figure that does not exist).
   - DEV-635 asks what the report forecasts, which is an absent published fact like DEV-015 and DEV-411..413. Revert to abstain unless the wording becomes "Forecast ...".
   - Owner should fix one rule for "causal/forecast wording + absent figure".
2. **HO-023.** The new cohort-timing fact has no supporting passage in the evidence list (p022:b019 was read but not added). Add it or drop the fact.
3. **HO-016.** The added alternative states only the total headline, not the resident/non-resident split the question needs. Remove it from the alternatives.
4. **DEV-630.** Now an exact duplicate of DEV-611 (same facts and passage). Drop it.
5. **DEV-603.** The added alternative is a bare chart heading; it must not count as sufficient alone.
6. **DEV-431.** Causal premise in an answer-labelled case; add a rubric note or reword. The cohort passage is not an alternative for the figures.
7. **DEV-023** (the advance-release alternative sits under a question pinned to the final release), **DEV-203** (the new question does not say which two points in time), **DEV-325** (SA not stated in the question): low-severity wording fixes.

Minor notes (verdict agree):
- DEV-102/114/116/131: observation unit is still `persons` in the store.
- DEV-027, DEV-617, DEV-618, DEV-622: added alternatives cover only part of a multi-part question.
- DEV-401: the reviewer's figures check out (resident SA 69,200 vs NSA 64,600).
- HO-020: abstain is fine; partial answers must be credited.

Items "not applied" by the fixer: DEV-401 numbers (verified correct, optional to add), DEV-406 alternative (not needed), DEV-632/633 (see above; I lean abstain), DEV-630 (drop), DEV-102/114/116/131 (unit normalisation, still open), DEV-203/210/231 (answer already held; fine), DEV-009 (keeping the truncated passage as non-primary is fine).
