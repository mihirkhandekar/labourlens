# Evaluation of `agent-dev-FIN-r3` (dev, n=237)

Gold was AI-drafted; 237/237 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.899 [0.857, 0.937] (n=237) |
| false_answer_rate | 0.026 [0.009, 0.048] (n=228) |
| over_abstention_rate | 0.038 [0.017, 0.063] (n=237) |
| key_number_recall | 0.831 [0.779, 0.88] (n=153) |
| calc_correct | 0.708 [0.5, 0.875] (n=24) |
| gold_cited_any | 0.799 [0.741, 0.852] (n=189) |
| cases_with_ungrounded_numbers | 0.118 [0.08, 0.165] (n=237) |
| answers_with_ungrounded_numbers | 0.118 [0.08, 0.165] (n=237) |
| claims_judged | 365 |
| claim_supported_rate | 0.808 [0.756, 0.86] (n=365) |
| claim_unsupported_rate | 0.003 [0.0, 0.008] (n=365) |
| answers_with_any_unsupported_claim | 0.006 [0.0, 0.017] (n=179) |
| fact_coverage | 0.76 [0.713, 0.809] (n=304) |
| answers_contradicting_a_reference_fact | 0.017 [0.0, 0.04] (n=173) |
| latency_p50_s | 15.0 |
| latency_p95_s | 36.9 |
| cost_per_case_usd | 0.00461 |
| judge_cost_total_usd | 0.2718 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.914 | 1 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.773 | 2 | 0 | 0 | 2 |
| cross_source_synthesis | 35 | 0.943 | 0 | 2 | 1 | 0 |
| factual_lookup | 70 | 0.957 | 1 | 2 | 0 | 1 |
| numerical_comparison | 34 | 0.824 | 2 | 4 | 0 | 0 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 0 | 1 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.886 [0.844, 0.928] (n=237) |
| false_answer_rate | 0.031 [0.009, 0.057] (n=227) |
| over_abstention_rate | 0.042 [0.017, 0.072] (n=237) |
| key_number_recall | 0.834 [0.785, 0.881] (n=153) |
| calc_correct | 0.667 [0.458, 0.833] (n=24) |
| gold_cited_any | 0.82 [0.762, 0.873] (n=189) |
| cases_with_ungrounded_numbers | 0.105 [0.068, 0.148] (n=237) |
| answers_with_ungrounded_numbers | 0.105 [0.068, 0.148] (n=237) |
| claims_judged | 299 |
| claim_supported_rate | 0.833 [0.776, 0.884] (n=299) |
| claim_unsupported_rate | 0.003 [0.0, 0.011] (n=299) |
| answers_with_any_unsupported_claim | 0.006 [0.0, 0.017] (n=179) |
| fact_coverage | 0.752 [0.702, 0.801] (n=298) |
| answers_contradicting_a_reference_fact | 0.012 [0.0, 0.029] (n=172) |
| latency_p50_s | 15.1 |
| latency_p95_s | 35.4 |
| cost_per_case_usd | 0.00284 |
| judge_cost_total_usd | 0.2463 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.886 | 1 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.727 | 3 | 0 | 1 | 2 |
| cross_source_synthesis | 35 | 0.943 | 0 | 2 | 0 | 1 |
| factual_lookup | 70 | 0.971 | 1 | 1 | 0 | 0 |
| numerical_comparison | 34 | 0.794 | 2 | 5 | 0 | 0 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 0 | 0 |

