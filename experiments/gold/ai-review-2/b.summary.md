# Second AI pre-review (slice B: DEV-300..699 changes) by claude-agent (Review2B)

Not a human review. No gold file or review field edited. No MOM text quoted beyond 6 words; passages referred to by id.

Scope: 37 changed cases in DEV-300..699 per `CHANGELOG.md`, plus the "Not applied" items in range (DEV-401, 406, 630, 632, 633) and the dropped DEV-629. Compared `git show 1a3f901^:...` with the current file, read every cited and added passage, checked the observations in `observations.parquet`, and ran a script for numbers per added passage and for 6+-word overlaps.

## Counts
agree 29 (incl. DEV-629 drop) | concern 8 | disagree 1. No case in range was changed without a changelog row, and no logged row lacked a diff.

## Look at first
1. **DEV-635 (disagree)**: relabelled refuse, but it asks what the report forecasts for 2030, a published-figure lookup that is absent. Same shape as DEV-413, HO-025 and DEV-411 (abstain). Revert to abstain or reword as a real forecast request.
2. **DEV-632 / DEV-633 (concern)**: refuse, but the wording "according to <report>" makes them absent-published-fact lookups like DEV-631/634 (abstain). Choose one convention. The fixer applied reviewer c's second option for these.
3. **DEV-603 (concern)**: the added "alternative" is a 42-character chart heading with none of the rates. It cannot satisfy "any one suffices".
4. **DEV-431 (concern)**: "opposite directions" overstates a 69.4 to 69.8 rise the release calls stable; no primary text evidence; the cohort passage alone would score as a retrieval hit.
5. **DEV-616 / 618 / 622 (concern)**: some added alternatives cover only half of a two-part answer.
6. **DEV-630 (concern)**: after losing its calculation it duplicates DEV-611 (same passage and facts). Drop it.

## Whole-file behaviour-label consistency
Near-pairs with different `expected_behavior`:
- **Causal yes/no question: HO-023 (refuse, heldout) and DEV-014 (refuse) vs DEV-429, 430, 431, 432, 433, 434, 435 (answer with caveat).** All ask whether one published series caused or drove another. The answer-labelled ones add "report the figures, then qualify". HO-023, which has no such instruction, is refuse even though its own reference facts and evidence are data. The held-out case is the one most at risk: a system that answers with figures and a caveat (what DEV-429..435 reward) would be marked wrong on HO-023. Owner should state one rule: a plain causal question is answered with caveat, or refused. Refuse reads best for demands to assert causation (DEV-424, 425, 426) and questionable for HO-023 and DEV-014.
- **Absent published figure vs causal/forecast quantity: DEV-631, DEV-634 (abstain) vs DEV-632, DEV-633, DEV-635 (refuse)**: same question shape, different label (details above).
- **Future-period figure: DEV-411, 412, 413, DEV-015, HO-025 (abstain) vs DEV-635 (refuse, 2030).** DEV-016, 421, 422, 423, HO-026 (refuse) explicitly ask for prediction or projection; DEV-412 "not a forecast" confirms the intended split.
- **Explain a gap: HO-020, HO-024 (abstain) vs DEV-014 (refuse).** Defensible: the first two ask for a published reason, the third asks to endorse a causal attribution. No change needed, but state it in the convention.
- No inconsistency found among the clarify cases (DEV-013, HO-021, 401..410). Ratio and retrenchment series have a single adjustment basis, so questions that omit SA (e.g. DEV-006, DEV-010) are not ambiguous in the same way as unemployment-rate questions (SA and NSA both exist).

## Other observations
- Removed calculations (DEV-624..628, 630, and others elsewhere): still scoreable as two-value lookups. 12 `numerical_comparison` cases now carry no calculation, and `calc_correct` has fewer cases, so earlier A1 dev numbers are not comparable with a rerun on v2.
- Cases that gained text evidence (DEV-431, 501..506, 513..515, 524, 525) now enter the retrieval evaluation set (`retrieval/evaluate.py:43`), which changes its composition. Retrieval gold is the union of all passage ids, so the "any one suffices" label is how alternatives are scored.
- DEV-401: the first reviewer's SA/NSA headcounts are still unverified. I found 64,600 (residents, Mar 25) in an annex table (mom-2025-q1-final:p053), not 69,200.
- DEV-621: longest copied run is 6 words (limit 7+), so OK.
