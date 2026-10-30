# M6: end-to-end agent experiments

**MEASURED RESULT — development only.** The owner has not reviewed the gold labels or answer sample. The held-out set has not been run. This report describes the saved experiments, not a final generalisation estimate.

## Hypotheses and controlled changes

These hypotheses describe the comparisons being analysed. They are not claimed to be a timestamped pre-registration of the completed agent runs.

- **H1:** period/release filtering followed by reranking reduces missing-evidence abstentions relative to hybrid retrieval, at higher latency and cost.
- **H2:** explicit missing/conflicting-data instructions improve answers beyond the existing prompt and code-generated data-quality notes.
- **H3:** widening a weak filtered candidate pool improves on filter-plus-rerank alone.
- **H4:** the alternative generator improves quality enough to justify its price. Nearby model scores may be indistinguishable in this sample.

| Run | Reference | Single changed factor |
|---|---|---|
| A1 | Baseline | Hybrid BM25/dense RRF; `answer_v3` |
| A2 | A1 | `answer_v4` adds missing/conflicting-data instructions |
| A3 | A1 | Retrieval `r3`: period/release filter, then LLM rerank of the top 30 candidates |
| A4 | A3 | Retrieval `r3w`: widening fallback for a small or lexically weak filtered pool |

Each model row uses that model for planner and answer. Reranking uses `gpt-6-luna`. Code-generated `data_quality_notes` exist in **all** runs; A2 is not a notes-on versus notes-off experiment. Configuration details: `src/labourlens/agent/experiments.py`, `src/labourlens/agent/graph.py`, `prompts/answer_v3.md`, `prompts/answer_v4.md`, and `docs/experiments/m6-retrieval-improvements.md`.

## Results

Every row below comes from `experiments/eval/agent-dev-A{1,2,3,4}/{model}.metrics.json`. The corresponding `.cases.jsonl` files contain case-level scores; raw local runs are under `data/runs/agent-dev-A*/` and are not redistributed. Intervals shown are each run's own bootstrap interval. A1/A2 were rescored against final draft gold, excluding changed questions and dropped cases, leaving **235** cases; A3/A4 contain **237**. Counts: the same metric files and `experiments/gold/CHANGELOG.md`. There is no paired significance claim across those different populations.

| Run | Model | n | Behaviour [95% CI] | Over-abstain | False answer | Claim support | Unsupported claim | Fact coverage | Contradiction | Gold cited | Calculation correct | p50 / p95 s | $/case |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A1 | gpt-6-luna | 235 | 0.770 [0.719, 0.826] | 0.183 | 0.010 | 0.872 | 0.000 | 0.677 | 0.007 | 0.658 | 0.833 | 10.7 / 22.8 | 0.00137 |
| A1 | gpt-5.6-luna | 235 | 0.800 [0.749, 0.851] | 0.157 | 0.010 | 0.833 | 0.000 | 0.726 | 0.013 | 0.679 | 0.833 | 9.6 / 18.0 | 0.00274 |
| A2 | gpt-6-luna | 235 | 0.757 [0.702, 0.813] | 0.191 | 0.016 | 0.884 | 0.004 | 0.694 | 0.014 | 0.643 | 0.875 | 12.7 / 24.7 | 0.00142 |
| A2 | gpt-5.6-luna | 235 | 0.804 [0.753, 0.855] | 0.153 | 0.010 | 0.815 | 0.003 | 0.719 | 0.019 | 0.689 | 0.833 | 10.8 / 20.6 | 0.00280 |
| A3 | gpt-6-luna | 237 | 0.890 [0.848, 0.928] | 0.055 | 0.018 | 0.883 | 0.000 | 0.725 | 0.005 | 0.808 | 0.875 | 15.4 / 35.6 | 0.00212 |
| A3 | gpt-5.6-luna | 237 | 0.907 [0.869, 0.945] | 0.042 | 0.009 | 0.874 | 0.000 | 0.770 | 0.005 | 0.828 | 0.875 | 15.5 / 34.4 | 0.00360 |
| A4 | gpt-6-luna | 237 | 0.886 [0.844, 0.924] | 0.059 | 0.013 | 0.880 | 0.000 | 0.738 | 0.011 | 0.808 | 0.833 | 14.8 / 35.6 | 0.00215 |
| A4 | gpt-5.6-luna | 237 | 0.907 [0.869, 0.941] | 0.051 | 0.009 | 0.887 | 0.000 | 0.770 | 0.000 | 0.818 | 0.792 | 15.1 / 34.7 | 0.00367 |

Rates use different eligible populations. `over_abstention_rate` divides by all evaluated cases. `false_answer_rate` excludes over-abstentions from its denominator; it is not conditional on gold non-answer cases. Claim support and unsupported-claim rates pool judged claims. Fact coverage pools reference facts in judged answers. Contradiction is the fraction of judged answers with any contradicted reference fact. Gold-cited and calculation-correct exclude ineligible/null cases. See `docs/evaluation-report.md` and `src/labourlens/evaluation/harness.py`; each metrics JSON provides denominators and intervals for all rates.

Zero unsupported claims is the judge's observation on answered, judged claims only. Partial support is a separate category. It does not mean every answer was complete or correct.

## Stratified behaviour: A1 versus A3

Source: `by_family` in the A1 and A3 metrics files above. Counts are shown separately where eligibility changed. These are descriptive slices, not family-level significance tests.

| Model | Family | A1 n | A1 behaviour | A3 n | A3 behaviour | A1 / A3 over-abstentions | A1 / A3 false answers |
|---|---|---:|---:|---:|---:|---:|---:|
| gpt-6-luna | adversarial | 35 | 0.886 | 35 | 0.914 | 3 / 2 | 0 / 0 |
| gpt-6-luna | ambiguity_insufficient_causal | 44 | 0.773 | 44 | 0.727 | 0 / 0 | 2 / 4 |
| gpt-6-luna | cross_source_synthesis | 35 | 0.800 | 35 | 0.943 | 7 / 2 | 0 / 0 |
| gpt-6-luna | factual_lookup | 70 | 0.700 | 70 | 0.929 | 21 / 5 | 0 / 0 |
| gpt-6-luna | numerical_comparison | 33 | 0.818 | 34 | 0.882 | 6 / 4 | 0 / 0 |
| gpt-6-luna | revision_conflict | 18 | 0.667 | 19 | 1.000 | 6 / 0 | 0 / 0 |
| gpt-5.6-luna | adversarial | 35 | 1.000 | 35 | 0.971 | 0 / 0 | 0 / 0 |
| gpt-5.6-luna | ambiguity_insufficient_causal | 44 | 0.773 | 44 | 0.750 | 0 / 0 | 2 / 2 |
| gpt-5.6-luna | cross_source_synthesis | 35 | 0.743 | 35 | 0.971 | 9 / 1 | 0 / 0 |
| gpt-5.6-luna | factual_lookup | 70 | 0.743 | 70 | 0.929 | 18 / 5 | 0 / 0 |
| gpt-5.6-luna | numerical_comparison | 33 | 0.848 | 34 | 0.882 | 5 / 4 | 0 / 0 |
| gpt-5.6-luna | revision_conflict | 18 | 0.722 | 19 | 1.000 | 5 / 0 | 0 / 0 |

## Findings

**H1 is consistent with the dev evidence.** Both models have higher behaviour accuracy, lower over-abstention, and more gold citations under A3. The largest descriptive gains are factual lookup and revision conflict. The ambiguity/insufficient-evidence/causal family does not improve. Retrieval alone does not fix selecting clarification versus abstention or deciding which causal requests permit a caveated factual answer.

**H2 has no demonstrated benefit.** A2 behaviour intervals overlap A1 for both models. Other metrics move in mixed directions. Keep `answer_v3`; the experiment does not establish equivalence or prove the added rule can never help.

**H3 has no demonstrated benefit.** A4's behaviour is close to A3 for both models, with overlapping intervals. Calculation correctness is lower in A4. The widening rule may not address the remaining failure paths; it is not adopted as the default.

**H4 does not establish a quality winner.** A3 model behaviour intervals overlap. The alternative model has higher observed fact coverage and a higher cost per case. The current default remains `gpt-6-luna`, retrieval `r3`, and `answer_v3` (D-030 in `docs/decisions.md`), pending owner confirmation or reversal.

A3 `gpt-6-luna` p95 latency is **35.6 seconds**, versus **22.8 seconds** for A1; cost is **$0.00212** versus **$0.00137** per case (respective metrics JSON files). These are single-run API/wall-time estimates, not a service-level guarantee. Judge costs are separate. Missing usage on a timed-out request can undercount provider billing.

## Limits and next evidence

Gold and semantic judging are AI-produced. The dev set has been used repeatedly for choices. Reranker, judge and generators share a provider/family. Some family samples are small. Any-one-gold citation credit can hide incomplete comparisons. The independent AI answer review concerns A1, not A3. None replaces owner review.

**In progress, no result claimed:** `planner_v2` and A5 test whether the planner researches a legitimate question even when it also contains a rules-override instruction. The motivation is the zero-tool-call abstention on DEV-503 and DEV-505 (`experiments/eval/agent-dev-A3/gpt-6-luna.cases.jsonl`, local `data/runs/agent-dev-A3/gpt-6-luna.jsonl`); prompts are `prompts/planner_v2.md` and `planner_v2_user.md`. This does not change the A1–A4 evidence or establish a new default. The separate scope-policy disagreement for six historical-context questions is documented in `docs/evaluation-report.md`.

The earlier small agent report (`docs/experiments/m4-agent.md`) is superseded by these larger dev runs where it covers the same questions. Earlier retrieval and answer-only experiments remain mechanism studies, not directly comparable scoreboards. Full error analysis, reviewer status, held-out pre-registration and remaining decisions are in `docs/evaluation-report.md`.
