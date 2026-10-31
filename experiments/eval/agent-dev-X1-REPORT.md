# Evaluation of `agent-dev-X1` (dev, n=237)

Gold was AI-drafted; 14/237 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.911 [0.873, 0.945] (n=237) |
| false_answer_rate | 0.03 [0.009, 0.056] (n=232) |
| over_abstention_rate | 0.021 [0.004, 0.042] (n=237) |
| key_number_recall | 0.858 [0.81, 0.901] (n=153) |
| calc_correct | 0.75 [0.583, 0.917] (n=24) |
| gold_cited_any | 0.825 [0.772, 0.878] (n=189) |
| cases_with_ungrounded_numbers | 0.101 [0.068, 0.139] (n=237) |
| answers_with_ungrounded_numbers | 0.101 [0.068, 0.139] (n=237) |
| claims_judged | 381 |
| claim_supported_rate | 0.801 [0.749, 0.851] (n=381) |
| claim_unsupported_rate | 0.003 [0.0, 0.008] (n=381) |
| answers_with_any_unsupported_claim | 0.005 [0.0, 0.016] (n=184) |
| fact_coverage | 0.756 [0.706, 0.805] (n=311) |
| answers_contradicting_a_reference_fact | 0.028 [0.006, 0.056] (n=177) |
| latency_p50_s | 13.3 |
| latency_p95_s | 34.2 |
| cost_per_case_usd | 0.00458 |
| judge_cost_total_usd | 0.2673 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.914 | 1 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.75 | 3 | 0 | 0 | 3 |
| cross_source_synthesis | 35 | 1.0 | 0 | 0 | 1 | 0 |
| factual_lookup | 70 | 0.971 | 1 | 1 | 0 | 1 |
| numerical_comparison | 34 | 0.853 | 2 | 3 | 0 | 0 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 0 | 2 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.886 [0.844, 0.924] (n=237) |
| false_answer_rate | 0.035 [0.013, 0.061] (n=229) |
| over_abstention_rate | 0.034 [0.013, 0.059] (n=237) |
| key_number_recall | 0.814 [0.763, 0.862] (n=153) |
| calc_correct | 0.667 [0.458, 0.833] (n=24) |
| gold_cited_any | 0.794 [0.735, 0.847] (n=189) |
| cases_with_ungrounded_numbers | 0.08 [0.046, 0.118] (n=237) |
| answers_with_ungrounded_numbers | 0.08 [0.046, 0.118] (n=237) |
| claims_judged | 309 |
| claim_supported_rate | 0.887 [0.846, 0.926] (n=309) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=309) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=182) |
| fact_coverage | 0.728 [0.678, 0.777] (n=301) |
| answers_contradicting_a_reference_fact | 0.011 [0.0, 0.029] (n=174) |
| latency_p50_s | 14.7 |
| latency_p95_s | 35.4 |
| cost_per_case_usd | 0.00294 |
| judge_cost_total_usd | 0.2398 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.914 | 1 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.682 | 4 | 0 | 0 | 2 |
| cross_source_synthesis | 35 | 1.0 | 0 | 0 | 0 | 1 |
| factual_lookup | 70 | 0.971 | 1 | 1 | 0 | 0 |
| numerical_comparison | 34 | 0.794 | 2 | 5 | 0 | 0 |
| revision_conflict | 19 | 0.947 | 0 | 1 | 0 | 0 |

