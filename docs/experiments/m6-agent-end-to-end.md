# M6: end-to-end agent experiments

**MEASURED RESULT — dev gold v3.2 with corrected judge cache and calculation scoring.** Human source/gold/answer review is incomplete. The registered held-out run executed against unreviewed AI labels; results are in `docs/evaluation-report.md`. Semantic scores supersede stale cache entries. The first strict calculation scorer was found defective and corrected before these final figures; it does not show a numerical-capability collapse.

## Hypotheses and controlled changes

These hypotheses describe the comparisons being analysed. They are not claimed to be a timestamped pre-registration of the completed agent runs.

- **H1:** period/release filtering followed by reranking reduces missing-evidence abstentions relative to hybrid retrieval, at higher latency and cost.
- **H2:** explicit missing/conflicting-data instructions improve answers beyond the existing prompt and code-generated data-quality notes.
- **H3:** widening a weak filtered candidate pool improves on filter-plus-rerank alone.
- **H4:** the alternative generator improves quality enough to justify its price. Nearby model scores may be indistinguishable in this sample.
- **H5:** the planner should research the legitimate part of a question containing rules-override wording; `planner_v2` tests this without changing retrieval or answer prompt.

| Run | Reference | Single changed factor |
|---|---|---|
| A1 | Baseline | Hybrid BM25/dense RRF; `answer_v3` |
| A2 | A1 | `answer_v4` adds missing/conflicting-data instructions |
| A3 | A1 | Retrieval `r3`: period/release filter, then LLM rerank of the top 30 candidates |
| A4 | A3 | Retrieval `r3w`: widening fallback for a small or lexically weak filtered pool |
| A5 | A3 | Planner prompt `planner_v2`; retrieval `r3` and `answer_v3` unchanged |

Each model row uses that model for planner and answer. Reranking uses `gpt-6-luna`. Code-generated `data_quality_notes` exist in **all** runs; A2 is not a notes-on versus notes-off experiment. Configuration details: `src/labourlens/agent/experiments.py`, `src/labourlens/agent/graph.py`, `prompts/answer_v3.md`, `prompts/answer_v4.md`, and `docs/experiments/m6-retrieval-improvements.md`.

## Results

Every row comes from `experiments/eval/agent-dev-A{1,2,3,4,5}/{model}.metrics.json`, rescored against gold **v3.2**. Adjacent `.cases.jsonl` files hold case scores; raw restricted-text runs remain local in `data/runs/agent-dev-A*/`. A1/A2 exclude changed questions/dropped cases and cover **235** cases; A3/A4/A5 cover **237**. D-031 relabelled **nine** dev questions under the hard supported-period rule (`experiments/gold/CHANGELOG.md`); this is a transparent scope-policy correction, not a new generation result. Each run has its own bootstrap interval. No paired significance claim is made across different populations.

| Run | Model | n | Behaviour [95% CI] | Over-abstain | False answer | Claim support | Unsupported claim | Fact coverage | Contradiction | Gold cited | Calculation correct | p50 / p95 s | $/case |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A1 | gpt-6-luna | 235 | 0.779 [0.728, 0.830] | 0.157 | 0.025 | 0.881 | 0.000 | 0.687 | 0.007 | 0.674 | 0.667 | 10.7 / 22.8 | 0.00137 |
| A1 | gpt-5.6-luna | 235 | 0.804 [0.753, 0.855] | 0.136 | 0.030 | 0.819 | 0.000 | 0.724 | 0.014 | 0.690 | 0.750 | 9.6 / 18.0 | 0.00274 |
| A2 | gpt-6-luna | 235 | 0.762 [0.706, 0.813] | 0.170 | 0.036 | 0.888 | 0.004 | 0.692 | 0.014 | 0.658 | 0.750 | 12.7 / 24.7 | 0.00142 |
| A2 | gpt-5.6-luna | 235 | 0.800 [0.749, 0.851] | 0.136 | 0.034 | 0.829 | 0.003 | 0.716 | 0.034 | 0.695 | 0.750 | 10.8 / 20.6 | 0.00280 |
| A3 | gpt-6-luna | 237 | 0.903 [0.865, 0.937] | 0.030 | 0.030 | 0.887 | 0.000 | 0.728 | 0.006 | 0.836 | 0.750 | 15.4 / 35.6 | 0.00212 |
| A3 | gpt-5.6-luna | 237 | 0.903 [0.861, 0.941] | 0.025 | 0.030 | 0.874 | 0.003 | 0.765 | 0.006 | 0.841 | 0.750 | 15.5 / 34.4 | 0.00360 |
| A4 | gpt-6-luna | 237 | 0.899 [0.861, 0.937] | 0.034 | 0.026 | 0.856 | 0.000 | 0.734 | 0.011 | 0.836 | 0.667 | 14.8 / 35.6 | 0.00215 |
| A4 | gpt-5.6-luna | 237 | 0.911 [0.878, 0.945] | 0.030 | 0.026 | 0.878 | 0.000 | 0.766 | 0.000 | 0.836 | 0.667 | 15.1 / 34.7 | 0.00367 |
| A5 | gpt-6-luna | 237 | 0.907 [0.869, 0.941] | 0.021 | 0.034 | 0.879 | 0.000 | 0.724 | 0.006 | 0.841 | 0.750 | 16.4 / 37.5 | 0.00217 |
| A5 | gpt-5.6-luna | 237 | 0.911 [0.873, 0.945] | 0.030 | 0.022 | 0.856 | 0.000 | 0.760 | 0.000 | 0.841 | 0.708 | 14.7 / 34.0 | 0.00369 |

Rates use different eligible populations. `over_abstention_rate` divides by all evaluated cases. `false_answer_rate` excludes over-abstentions from its denominator; it is not conditional on gold non-answer cases. Claim support and unsupported-claim rates pool judged claims. Fact coverage pools reference facts in judged answers. Contradiction is the fraction of judged answers with any contradicted reference fact. Gold-cited and calculation-correct exclude ineligible/null cases. See `docs/evaluation-report.md` and `src/labourlens/evaluation/harness.py`; each metrics JSON provides denominators and intervals for all rates.

Zero unsupported claims is the judge's observation on answered, judged claims only. Partial support is a separate category. It does not mean every answer was complete or correct.

## Stratified behaviour: A1 versus A3

Source: `by_family` in the A1 and A3 metrics files above. Counts are shown separately where eligibility changed. These are descriptive slices, not family-level significance tests.

| Model | Family | A1 n | A1 behaviour | A3 n | A3 behaviour | A1 / A3 over-abstentions | A1 / A3 false answers |
|---|---|---:|---:|---:|---:|---:|---:|
| gpt-6-luna | adversarial | 35 | 0.857 | 35 | 0.886 | 3 / 2 | 1 / 1 |
| gpt-6-luna | ambiguity_insufficient_causal | 44 | 0.773 | 44 | 0.727 | 0 / 0 | 2 / 4 |
| gpt-6-luna | cross_source_synthesis | 35 | 0.800 | 35 | 0.971 | 6 / 1 | 0 / 0 |
| gpt-6-luna | factual_lookup | 70 | 0.743 | 70 | 0.971 | 17 / 1 | 1 / 1 |
| gpt-6-luna | numerical_comparison | 33 | 0.818 | 34 | 0.882 | 5 / 3 | 1 / 1 |
| gpt-6-luna | revision_conflict | 18 | 0.667 | 19 | 1.000 | 6 / 0 | 0 / 0 |
| gpt-5.6-luna | adversarial | 35 | 0.971 | 35 | 0.943 | 0 / 0 | 1 / 1 |
| gpt-5.6-luna | ambiguity_insufficient_causal | 44 | 0.773 | 44 | 0.750 | 0 / 0 | 2 / 2 |
| gpt-5.6-luna | cross_source_synthesis | 35 | 0.771 | 35 | 1.000 | 8 / 0 | 0 / 0 |
| gpt-5.6-luna | factual_lookup | 70 | 0.786 | 70 | 0.943 | 14 / 2 | 1 / 2 |
| gpt-5.6-luna | numerical_comparison | 33 | 0.788 | 34 | 0.824 | 5 / 4 | 2 / 2 |
| gpt-5.6-luna | revision_conflict | 18 | 0.722 | 19 | 1.000 | 5 / 0 | 0 / 0 |

## Findings

**H1 has a clear dev effect.** A3 behaviour improves from **0.779 to 0.903** for `gpt-6-luna` and **0.804 to 0.903** for `gpt-5.6-luna`; marginal intervals do not overlap A1. Over-abstention falls and gold citation rises (metric files above). This is not a paired significance claim across differing n. Lookup, synthesis and revision gains are largest descriptively; ambiguity remains weak.

**H2 has no demonstrated benefit.** A2 behaviour intervals overlap A1 for both models. Other metrics move in mixed directions. Keep `answer_v3`; the experiment does not establish equivalence or prove the added rule can never help.

**H3 has no demonstrated benefit.** A4's behaviour remains close to A3 with overlapping intervals; other measures do not establish a consistent improvement. The widening rule is not adopted.

**H4 does not establish a model winner.** A3 behaviour is **0.903** for both models with overlapping intervals. Alternative-model fact coverage is higher, but so is cost (A3 metric files). Keep `gpt-6-luna`, retrieval `r3`, `answer_v3` and `planner_v1` (D-030/D-032 in `docs/decisions.md`), pending owner confirmation of the retrieval default.

A3 `gpt-6-luna` p95 latency is **35.6 seconds**, versus **22.8 seconds** for A1; cost is **$0.00212** versus **$0.00137** per case (respective metrics JSON files). These are single-run API/wall-time estimates, not a service-level guarantee. Judge costs are separate. Missing usage on a timed-out request can undercount provider billing.

## Limits and next evidence

Gold and semantic judging are AI-produced. The dev set has been used repeatedly for choices. Reranker, judge and generators share a provider/family. Some family samples are small. Any-one-gold citation credit can hide incomplete comparisons. The independent AI answer review concerns A1, not A3. None replaces owner review.
**Evaluation corrections:** case-ID-only caching left stale judgments after gold changes. The cache now fingerprints the actual judge inputs; A1–A5 were rejudged (`src/labourlens/evaluation/harness.py`). Metrics record scoring-time gold/prompt/price hashes, configuration, HEAD and eligible/available n; generation provenance is distinct. The first strict calculation scorer overconstrained prose/unit wording and misparsed “not relative percent change”. It was corrected before final figures: cited deterministic records must match operands/order, operation, unit and signed result with prose direction agreement, while wording is flexible. All dev and held-out files were rescored; comparison found only `calc_correct` changed, without new generation. A3 is **0.750 [0.583, 0.917], n=24**, for both models; misses are no-answer cases and ranking questions beyond `calculate_change`, not incorrect arithmetic (`experiments/eval/agent-dev-A3/`, `src/labourlens/agent/experiments.py`). Held-out calculation rescoring is disclosed as a scoring-code deviation. `cases_with_ungrounded_numbers` uses all scored cases; the old answers-named metric is an alias.

**Held-out finding, v3.4 rescoring:** paired differences are **+0.161 [0.000, 0.323]** and **+0.097 [-0.032, 0.226]** for the respective luna models (`experiments/heldout/paired.txt`). Neither demonstrates a gain under the registered rule. Keep r3 provisional. The original v3.2 execution and v3.3/v3.4 adjudications are shown side by side in `docs/evaluation-report.md`; no new model calls occurred. Three v3.4 post-run edits lower or leave scores unchanged. A clean pre-registered rerun on frozen human-reviewed gold would be stronger evidence; current human review remains pending.


**H5 has no demonstrated benefit; A5 is complete.** `planner_v2` was motivated by DEV-503/505 zero-tool abstentions. Versus A3, behaviour changes by **+0.004** and **+0.008** for the respective luna models, with fully overlapping intervals. A5 p95 latency is **37.5 / 34.0 s** and cost **$0.00217 / $0.00369** per case (A5 metrics above). This is inconclusive, not equivalence. `planner_v2` is not adopted; `planner_v1` stays default. D-031 resolves the historical-context boundary; details and remaining failure IDs are in `docs/evaluation-report.md`.

The earlier small agent report (`docs/experiments/m4-agent.md`) is superseded by these larger dev runs where it covers the same questions. Earlier retrieval and answer-only experiments remain mechanism studies, not directly comparable scoreboards. Full error analysis, reviewer status, held-out pre-registration and remaining decisions are in `docs/evaluation-report.md`.
