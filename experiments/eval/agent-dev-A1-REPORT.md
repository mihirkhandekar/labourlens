# Evaluation of `agent-dev-A1` (dev, n=237)

Gold labels and the judge are AI-produced; nothing here is human-reviewed. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-4.1-mini

| measure | value |
|---|---|
| n_cases | 235 |
| behaviour_accuracy | 0.791 [0.74, 0.843] (n=235) |
| false_answer_rate | 0.04 [0.015, 0.069] (n=202) |
| over_abstention_rate | 0.14 [0.098, 0.187] (n=235) |
| key_number_recall | 0.698 [0.637, 0.761] (n=158) |
| calc_correct | 0.375 [0.167, 0.583] (n=24) |
| gold_cited_any | 0.622 [0.556, 0.689] (n=196) |
| answers_with_ungrounded_numbers | 0.077 [0.043, 0.115] (n=235) |
| claims_judged | 299 |
| claim_supported_rate | 0.886 [0.839, 0.927] (n=299) |
| claim_unsupported_rate | 0.007 [0.0, 0.017] (n=299) |
| answers_with_any_unsupported_claim | 0.012 [0.0, 0.03] (n=164) |
| fact_coverage | 0.58 [0.518, 0.644] (n=264) |
| answers_contradicting_a_reference_fact | 0.079 [0.043, 0.122] (n=164) |
| latency_p50_s | 5.8 |
| latency_p95_s | 10.7 |
| cost_per_case_usd | 0.00466 |
| judge_cost_total_usd | 0.2301 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.857 | 0 | 5 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.591 | 8 | 2 | 0 | 2 |
| cross_source_synthesis | 35 | 0.971 | 0 | 1 | 0 | 4 |
| factual_lookup | 70 | 0.857 | 0 | 10 | 2 | 1 |
| numerical_comparison | 33 | 0.576 | 0 | 14 | 0 | 4 |
| revision_conflict | 18 | 0.944 | 0 | 1 | 0 | 8 |

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 235 |
| behaviour_accuracy | 0.8 [0.749, 0.851] (n=235) |
| false_answer_rate | 0.01 [0.0, 0.025] (n=198) |
| over_abstention_rate | 0.157 [0.111, 0.204] (n=235) |
| key_number_recall | 0.747 [0.686, 0.806] (n=158) |
| calc_correct | 0.833 [0.667, 0.958] (n=24) |
| gold_cited_any | 0.679 [0.612, 0.745] (n=196) |
| answers_with_ungrounded_numbers | 0.068 [0.038, 0.102] (n=235) |
| claims_judged | 299 |
| claim_supported_rate | 0.833 [0.782, 0.881] (n=299) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=299) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=154) |
| fact_coverage | 0.726 [0.676, 0.779] (n=266) |
| answers_contradicting_a_reference_fact | 0.013 [0.0, 0.032] (n=154) |
| latency_p50_s | 9.6 |
| latency_p95_s | 18.0 |
| cost_per_case_usd | 0.00274 |
| judge_cost_total_usd | 0.2132 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 1.0 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.773 | 2 | 0 | 0 | 1 |
| cross_source_synthesis | 35 | 0.743 | 0 | 9 | 0 | 1 |
| factual_lookup | 70 | 0.743 | 0 | 18 | 0 | 0 |
| numerical_comparison | 33 | 0.848 | 0 | 5 | 0 | 0 |
| revision_conflict | 18 | 0.722 | 0 | 5 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 235 |
| behaviour_accuracy | 0.77 [0.719, 0.826] (n=235) |
| false_answer_rate | 0.01 [0.0, 0.026] (n=192) |
| over_abstention_rate | 0.183 [0.132, 0.234] (n=235) |
| key_number_recall | 0.691 [0.626, 0.754] (n=158) |
| calc_correct | 0.833 [0.667, 0.958] (n=24) |
| gold_cited_any | 0.658 [0.592, 0.724] (n=196) |
| answers_with_ungrounded_numbers | 0.055 [0.03, 0.085] (n=235) |
| claims_judged | 243 |
| claim_supported_rate | 0.872 [0.811, 0.929] (n=243) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=243) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=148) |
| fact_coverage | 0.677 [0.619, 0.735] (n=263) |
| answers_contradicting_a_reference_fact | 0.007 [0.0, 0.02] (n=148) |
| latency_p50_s | 10.7 |
| latency_p95_s | 22.8 |
| cost_per_case_usd | 0.00137 |
| judge_cost_total_usd | 0.2041 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.886 | 0 | 3 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.773 | 2 | 0 | 0 | 0 |
| cross_source_synthesis | 35 | 0.8 | 0 | 7 | 0 | 1 |
| factual_lookup | 70 | 0.7 | 0 | 21 | 0 | 0 |
| numerical_comparison | 33 | 0.818 | 0 | 6 | 0 | 0 |
| revision_conflict | 18 | 0.667 | 0 | 6 | 0 | 0 |

