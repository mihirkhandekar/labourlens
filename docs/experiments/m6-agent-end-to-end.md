# M6: end-to-end agent experiments

**MEASURED RESULT — saved dev and held-out runs rescored on gold v3.5.** Owner review complete 31 Oct 2026: 125 cards decided by the owner (30 own verdicts, 95 by agreeing per card with AI suggestions or the three-pass AI tie-break), not independent inter-rater evidence. Forty-five gold cards are owner reviewed; 223 remain draft. Dev rescoring required no model calls; the owner completed the compatible held-out judge refresh. No answer generation was repeated.

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

Every row below comes from `experiments/eval/agent-dev-A{1,2,3,4,5}/{model}.metrics.json`, rescored on **v3.5** with `eval --no-judge`. DEV-018 has no answered claims in saved outputs, so no changed-case paid judgment was needed and matching cached judgments were reused. A1/A2 retain **235** scored cases; A3–A5 **237**. Owner-review metadata does not affect scores. No generation, retrieval or reranking rerun occurred; no paired significance claim is made across differing n.

| Run | Model | n | Behaviour [95% CI] | Over-abstain | False answer | Claim support | Unsupported claim | Fact coverage | Contradiction | Gold cited | Calculation correct | p50 / p95 s | $/case |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A1 | gpt-6-luna | 235 | 0.779 [0.728, 0.830] | 0.157 | 0.025 | 0.881 | 0.000 | 0.687 | 0.007 | 0.674 | 0.667 | 10.7 / 23.3 | 0.00137 |
| A1 | gpt-5.6-luna | 235 | 0.800 [0.749, 0.851] | 0.136 | 0.030 | 0.819 | 0.000 | 0.724 | 0.014 | 0.690 | 0.750 | 9.6 / 18.0 | 0.00274 |
| A2 | gpt-6-luna | 235 | 0.762 [0.706, 0.813] | 0.170 | 0.036 | 0.888 | 0.004 | 0.692 | 0.014 | 0.658 | 0.750 | 12.7 / 25.9 | 0.00142 |
| A2 | gpt-5.6-luna | 235 | 0.796 [0.745, 0.847] | 0.136 | 0.034 | 0.829 | 0.003 | 0.716 | 0.034 | 0.695 | 0.750 | 10.8 / 21.2 | 0.00280 |
| A3 | gpt-6-luna | 237 | 0.903 [0.865, 0.937] | 0.030 | 0.030 | 0.887 | 0.000 | 0.728 | 0.006 | 0.836 | 0.750 | 15.4 / 37.0 | 0.00212 |
| A3 | gpt-5.6-luna | 237 | 0.903 [0.861, 0.941] | 0.025 | 0.030 | 0.874 | 0.003 | 0.765 | 0.006 | 0.841 | 0.750 | 15.5 / 34.7 | 0.00360 |
| A4 | gpt-6-luna | 237 | 0.899 [0.861, 0.937] | 0.034 | 0.026 | 0.856 | 0.000 | 0.734 | 0.011 | 0.836 | 0.667 | 14.8 / 35.9 | 0.00215 |
| A4 | gpt-5.6-luna | 237 | 0.907 [0.869, 0.941] | 0.030 | 0.026 | 0.878 | 0.000 | 0.766 | 0.000 | 0.836 | 0.667 | 15.1 / 36.1 | 0.00367 |
| A5 | gpt-6-luna | 237 | 0.911 [0.873, 0.945] | 0.021 | 0.034 | 0.879 | 0.000 | 0.724 | 0.006 | 0.841 | 0.750 | 16.4 / 37.6 | 0.00217 |
| A5 | gpt-5.6-luna | 237 | 0.916 [0.878, 0.949] | 0.030 | 0.022 | 0.856 | 0.000 | 0.760 | 0.000 | 0.841 | 0.708 | 14.7 / 34.5 | 0.00369 |

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
| gpt-5.6-luna | adversarial | 35 | 0.943 | 35 | 0.943 | 0 / 0 | 1 / 1 |
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

A3 `gpt-6-luna` p95 latency is **37.0 seconds**, versus **23.3 seconds** for A1; cost is **$0.00212** versus **$0.00137** per case (respective metrics JSON files). These are single-run API/wall-time estimates, not a service-level guarantee. Judge costs are separate. Missing usage on a timed-out request can undercount provider billing.

## Limits and next evidence

Gold was AI-drafted and semantic judging remains AI-produced. Owner per-card review now covers selected records, including AI-assisted agreements; it is not blinded independent annotation. Dev has repeatedly guided choices, related model families are used, family samples are small and any-one-gold scoring can hide incomplete comparisons. Historical A1 and A3 AI reviews and the completed owner pack are distinguished in `docs/evaluation-report.md`.
**Evaluation corrections:** case-ID-only caching left stale judgments after gold changes. The cache now fingerprints the actual judge inputs; A1–A5 were rejudged (`src/labourlens/evaluation/harness.py`). Metrics record scoring-time gold/prompt/price hashes, configuration, HEAD and eligible/available n; generation provenance is distinct. The first strict calculation scorer overconstrained prose/unit wording and misparsed “not relative percent change”. It was corrected before final figures: cited deterministic records must match operands/order, operation, unit and signed result with prose direction agreement, while wording is flexible. All dev and held-out files were rescored; comparison found only `calc_correct` changed, without new generation. A3 is **0.750 [0.583, 0.917], n=24**, for both models; misses are no-answer cases and ranking questions beyond `calculate_change`, not incorrect arithmetic (`experiments/eval/agent-dev-A3/`, `src/labourlens/agent/experiments.py`). Held-out calculation rescoring is disclosed as a scoring-code deviation. `cases_with_ungrounded_numbers` uses all scored cases; the old answers-named metric is an alias.

**Complete held-out v3.5 finding:** behaviour accuracy is **0.871 [0.742, 0.968] / 0.839 [0.710, 0.968]** for r3 and **0.710 [0.548, 0.839] / 0.742 [0.581, 0.903]** for hybrid, in luna6/luna5.6 order (registered held-out metrics). Paired gains remain **+0.161 [0.000, 0.323] / +0.097 [-0.032, 0.226]** (`experiments/heldout/paired.txt`, n=31, 10,000 resamples, seed 20261030). Neither demonstrates a gain under the registered rule. HO-022's owner-approved correction raises both arms equally; it is not a model improvement. Original v3.2–v3.4 results and paired histories remain preserved in `docs/evaluation-report.md` and `experiments/heldout/`. Keep r3 provisional.


**H5 has no demonstrated benefit; A5 is complete.** With DEV-018 now labelled clarify under v3.5, A5 behaviour is **0.911 / 0.916**, versus A3 **0.903 / 0.903**: gains **+0.008 / +0.013** with overlapping intervals (current A3/A5 metrics, luna6/luna5.6 order). This remains inconclusive, not equivalence. `planner_v2` is not adopted; `planner_v1` stays default. p95 latency **37.6 / 34.5 s** (nearest-rank, current metrics files) and cost **$0.00217 / $0.00369** per case reflect the original generation runs.

**Corpus v2 extraction-only X1 (separately labelled):** after merging the extraction fixes and migrating gold evidence IDs (D-037/D-041, gold v3.6), the same r3, `planner_v1`, `answer_v3` workflow was run with cross-check off. Frozen corpus-v1 rows remain unchanged. Retrieval hit@8 is R3 **0.953 [0.914, 0.984]** on v2 versus **0.969 [0.938, 0.992]** on v1; dev behaviour is **0.886 [0.844, 0.924] / 0.911 [0.873, 0.945]** versus A3 **0.903 / 0.903**; held-out r3 is **0.839 / 0.839** and hybrid **0.774 / 0.742** versus v1 r3 **0.871 / 0.839** and hybrid **0.710 / 0.742** (luna6 / luna5.6 order). Intervals overlap throughout: no measurable quality change. The diagnostic paired held-out difference is **+0.065 [-0.065, 0.194]** and **+0.097 [-0.032, 0.226]** on the same 31 questions (`experiments/heldout/paired-corpus-v2.txt`). Full side-by-side tables, caveats and artifact paths are in `docs/evaluation-report.md`.
**Corpus v3 regression check X2 (separately labelled; not an ablation):** the development split on the served system, that is corpus v3, the 14 runtime changes of `docs/experiments/m7-e2e-fixes.md`, the cross-check on, `r3`, `planner_v1`, `answer_v3`, gold v3.6, both luna models. Several factors changed at once, so no cause can be assigned. Behaviour accuracy is **0.903 [0.865, 0.941] / 0.916 [0.878, 0.949]** against A3 **0.903 / 0.903** and X1 **0.886 / 0.911** (luna6 / luna5.6 order); false-answer rate, over-abstention, key-number recall, calculation correctness, claim support, fact coverage and gold citation all keep overlapping intervals. One measure moved: ungrounded-number cases rose to **0.105 [0.068, 0.143] / 0.165 [0.118, 0.215]** from A3 **0.076 / 0.051**; the `gpt-5.6-luna` interval no longer overlaps A3's **[0.025, 0.080]**, but B2 widened what the check counts and part of the rise is already in X1 (**0.101**). `gpt-6-luna` p95 is **40.9 s** against **37.0 s** in A3. Full table, caveats and the threat rerun `m7-e2efix-20261031` (gpt-6-luna 36/36, gpt-5.6-luna 35/36, T-I06 not shown stable) are in `docs/evaluation-report.md`. Sources: `experiments/eval/agent-dev-X2/`, `experiments/threats/m7-e2efix-20261031/`.

**Held-out v2 (separately labelled; D-045):** the signed 65-case set on sources no earlier case cites, corpus v3, one run per arm. With `gpt-6-luna`, r3 scored **0.754** and hybrid **0.708**, a paired difference of **+0.046** (3 better, 0 worse, 90% interval [0.015, 0.092], McNemar exact p = 0.25); `gpt-5.6-luna` scored 0.723 and 0.723. The pre-registered rule is met for the primary model; the effect is three cases; I would not call it a confirmed gain; the second model shows none. Both arms are held back mostly by a tool coverage gap (arithmetic on report figures), not retrieval. The original 31-case held-out result is unchanged and the sets are not pooled. See `docs/experiments/m7-heldout-v2-result.md`.

The earlier small agent report (`docs/experiments/m4-agent.md`) is superseded by these larger dev runs where it covers the same questions. Earlier retrieval and answer-only experiments remain mechanism studies, not directly comparable scoreboards. Full error analysis, reviewer status, held-out pre-registration and remaining decisions are in `docs/evaluation-report.md`.
