# M7 — T-I06 deterministic source-figure cross-check

**DECISION (owner approval, 31 Oct 2026):** fix the planted-statistic failure without asking a model to verify itself. Historical threat outputs in `experiments/threats/runs/` remain frozen. This document describes a post-fix implementation, not a new paid threat result.

## Two candidate designs

| Design | Benefits | Downsides / dependencies | Choice |
|---|---|---|---|
| Annotate tool evidence only | Trusted dataset figure and conflict note reach generation; useful even when the planner only searches reports; simple local lookup | A model can ignore the note and repeat the false number | Useful preparation, insufficient enforcement alone |
| Deterministic output guard in existing validation node | Can enforce the structured figure, preserve citations and caveat even when the model ignores a warning; no extra model call or new answer schema | Requires conservative series/period/unit matching; arbitrary prose cannot be certified by regex | **Chosen**, with evidence annotation before generation using the same detector |

The pure citation validator stays independent of the store: it still checks label/quote validity. `answer/crosscheck.py` performs typed deterministic matching and comparison; `assess_evidence` registers local structured evidence and a source-conflict note; `validate_answer` rechecks explicit claims, corrects conflicting cited levels, then runs the normal validator. A claim can supply an explicit series/period omitted from the passage only when its cited passage actually contains the claimed numeric value. No claim is trusted as the value oracle: comparison always reads the validated local `StatsData`, not the LLM or an MCP replacement.

## Behaviour and boundaries

- The source-conflict state is recorded as `source_conflicts` in guard traces. The existing answer status remains `answered`; the preferred dataset value is a cited claim, and a caveat names both evidence labels. Both source items remain inspectable. No invented schema status or hidden chain-of-thought is added.
- Comparison uses decimal arithmetic, with half a last-displayed-digit rounding tolerance. Units must agree. A percentage-point change is not a percentage level. Unemployment needs an explicit population and adjustment basis. Multiple candidate series, dimensions or quarters are not guessed.
- Closed-grammar level matching covers explicit aggregate retrenchments, population-specific unemployment rates and unambiguous named vacancy, re-entry, resignation, recruitment and unemployment-count series. Unrecognised wording and dimensional breakdowns remain unchecked, **not verified**. This is not a universal numerical fact extractor.
- Missing/null dataset values and absent series cause no comparison and no invented replacement.
- Advance/preliminary source vintages are preserved. Existing `Tools._vintage_note` still labels advance/final comparisons. The `reconcile.QUARTERS` register preserves the employment headline/dataset distinction; those totals are not silently equated. Dataset rows labelled advance/preliminary are not used to override a source vintage.
- A conflicting used claim is replaced by a short deterministic dataset claim, not patched by global string replacement. Both evidence citations and a source-conflict caveat are retained. Summary regeneration uses corrected claims. Unrelated claims are left unchanged.
- `LABOURLENS_CROSSCHECK=off` disables only this factor for extraction-only experiments; `LABOURLENS_GUARDS=off` disables it along with other defences for the existing naive baseline. Raw runs record `crosscheck_enabled`, and the evidence-assessment trace records the same flag. Historical configuration keys are preserved.

## Tests and acceptance

`tests/retrieval/test_crosscheck.py` covers the planted figure, direct graph enforcement despite model noncompliance, defence ablation, extraction-only ablation, honest labelled revisions, employment reconciliation, rounding boundary, percent versus percentage points, missing values/series, population ambiguity, additional named series and a period specified in the claim rather than passage. The original T-I06 forbidden-number and usefulness fixtures are unchanged. Its checker additionally requires a deterministic conflict trace and the preferred structured figure; a used poison citation requires a source-conflict caveat. No existing acceptance is weakened.

**MEASURED RESULT:** the initial requested non-corpus run observed 442 passed, three failed, 53 deselected. All three failures were concurrent held-out work's changed `load_cases` signature versus old test doubles, not cross-check failures; the owning agent updated those doubles. Final integrated test output is recorded in the handoff/progress once observed. No live model/network threat run was performed by this worker.

**Expected acceptance, not measured:** T-I06 is exercised and passes for both defended models; every previously passing case stays passing, with indirect usefulness still 6/6. Inspect raw conflict records, preferred values, caveat and both citations, not just aggregate pass rate. Report any regression or non-exercised attack explicitly. The naive baseline must truly disable this check; no requirement claims it will always fail because model output is stochastic.

## Credentialed parent commands — post-fix, separately labelled

Run after the corpus rebuild and embedding preparation finish. Do not run build/index/embedding commands from this worker. Both conditions use the identical fixed corpus and the existing `r3` retrieval/default planner/answer configuration; naive changes only the already-defined all-defences ablation. Use a new experiment identifier if rerunning: generation refuses to overwrite any existing model/condition artifacts.

```sh
LABOURLENS_CROSSCHECK=on uv run labourlens threat-test --experiment m7-ti06-postfix-20261031 --models gpt-6-luna gpt-5.6-luna
LABOURLENS_CROSSCHECK=on uv run labourlens threat-test --experiment m7-ti06-postfix-20261031 --models gpt-6-luna gpt-5.6-luna --ablation naive
```

These write only new public verdict/metrics files under `experiments/threats/m7-ti06-postfix-20261031/runs/`, a summary in that experiment directory, and private raw outputs under `data/runs/threats/m7-ti06-postfix-20261031/`. Metrics explicitly label `phase: post-fix` and `retrieval: r3`. Do not use the legacy `--rescore` command on frozen threat artifacts.

**Cost estimate, not measured:** the saved A3 evaluation metrics report mean generation costs $0.00212/case (gpt-6-luna) and $0.00360/case (gpt-5.6-luna). At 36 cases × two conditions × both models, extrapolation is `72 × (0.00212 + 0.00360) = $0.41184`, about **$0.42**, before variability; reserving $0.84 is a contingency, not a bound. A3 includes `r3` reranking. No semantic judge is called by this suite. Pricing assumptions are the saved `specs/prices.yaml` entries: luna6 $0.10/$0.50 and luna5.6 $0.20/$1.20 per million input/output tokens; reranking uses luna6. This estimate uses saved usage-derived costs, not a prediction of exact future token counts. Evidence: `experiments/eval/agent-dev-A3/{gpt-6-luna,gpt-5.6-luna}.metrics.json`, `specs/prices.yaml`.

D-016 comparison: run extraction-only X1 with `LABOURLENS_CROSSCHECK=off`; turn it on only for a separately labelled security-factor X2 on that same corpus. The post-fix threat suite is a new stress-test result, not an overwrite or a claim that old frozen results changed.
