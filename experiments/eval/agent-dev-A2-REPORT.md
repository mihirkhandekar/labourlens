# Evaluation of `agent-dev-A2` (dev, n=237)

Gold labels and the judge are AI-produced; nothing here is human-reviewed. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 235 |
| behaviour_accuracy | 0.804 [0.753, 0.855] (n=235) |
| false_answer_rate | 0.01 [0.0, 0.025] (n=199) |
| over_abstention_rate | 0.153 [0.106, 0.2] (n=235) |
| key_number_recall | 0.758 [0.697, 0.815] (n=158) |
| calc_correct | 0.833 [0.667, 0.958] (n=24) |
| gold_cited_any | 0.689 [0.622, 0.755] (n=196) |
| answers_with_ungrounded_numbers | 0.064 [0.034, 0.098] (n=235) |
| claims_judged | 292 |
| claim_supported_rate | 0.815 [0.756, 0.87] (n=292) |
| claim_unsupported_rate | 0.003 [0.0, 0.011] (n=292) |
| answers_with_any_unsupported_claim | 0.006 [0.0, 0.019] (n=155) |
| fact_coverage | 0.719 [0.664, 0.771] (n=270) |
| answers_contradicting_a_reference_fact | 0.019 [0.0, 0.045] (n=155) |
| latency_p50_s | 10.8 |
| latency_p95_s | 20.6 |
| cost_per_case_usd | 0.0028 |
| judge_cost_total_usd | 0.2187 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 1.0 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.773 | 2 | 0 | 0 | 1 |
| cross_source_synthesis | 35 | 0.743 | 0 | 9 | 0 | 3 |
| factual_lookup | 70 | 0.729 | 0 | 19 | 0 | 0 |
| numerical_comparison | 33 | 0.879 | 0 | 4 | 0 | 0 |
| revision_conflict | 18 | 0.778 | 0 | 4 | 1 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 235 |
| behaviour_accuracy | 0.757 [0.702, 0.813] (n=235) |
| false_answer_rate | 0.016 [0.0, 0.037] (n=190) |
| over_abstention_rate | 0.191 [0.14, 0.243] (n=235) |
| key_number_recall | 0.702 [0.64, 0.762] (n=158) |
| calc_correct | 0.875 [0.75, 1.0] (n=24) |
| gold_cited_any | 0.643 [0.571, 0.709] (n=196) |
| answers_with_ungrounded_numbers | 0.098 [0.064, 0.136] (n=235) |
| claims_judged | 232 |
| claim_supported_rate | 0.884 [0.831, 0.932] (n=232) |
| claim_unsupported_rate | 0.004 [0.0, 0.014] (n=232) |
| answers_with_any_unsupported_claim | 0.007 [0.0, 0.02] (n=147) |
| fact_coverage | 0.694 [0.637, 0.755] (n=252) |
| answers_contradicting_a_reference_fact | 0.014 [0.0, 0.034] (n=147) |
| latency_p50_s | 12.7 |
| latency_p95_s | 24.7 |
| cost_per_case_usd | 0.00142 |
| judge_cost_total_usd | 0.1896 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.886 | 0 | 3 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.727 | 3 | 1 | 0 | 0 |
| cross_source_synthesis | 35 | 0.686 | 0 | 11 | 0 | 3 |
| factual_lookup | 70 | 0.729 | 0 | 19 | 0 | 0 |
| numerical_comparison | 33 | 0.879 | 0 | 4 | 0 | 0 |
| revision_conflict | 18 | 0.611 | 0 | 7 | 1 | 0 |

