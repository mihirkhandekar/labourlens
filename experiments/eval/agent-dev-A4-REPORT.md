# Evaluation of `agent-dev-A4` (dev, n=237)

Gold was AI-drafted; 14/237 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.907 [0.869, 0.941] (n=237) |
| false_answer_rate | 0.026 [0.009, 0.048] (n=230) |
| over_abstention_rate | 0.03 [0.008, 0.051] (n=237) |
| key_number_recall | 0.862 [0.818, 0.905] (n=153) |
| calc_correct | 0.667 [0.458, 0.833] (n=24) |
| gold_cited_any | 0.836 [0.783, 0.889] (n=189) |
| cases_with_ungrounded_numbers | 0.059 [0.03, 0.093] (n=237) |
| answers_with_ungrounded_numbers | 0.059 [0.03, 0.093] (n=237) |
| claims_judged | 362 |
| claim_supported_rate | 0.878 [0.832, 0.922] (n=362) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=362) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=181) |
| fact_coverage | 0.766 [0.715, 0.813] (n=308) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=175) |
| latency_p50_s | 15.1 |
| latency_p95_s | 36.1 |
| cost_per_case_usd | 0.00367 |
| judge_cost_total_usd | 0.2507 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.943 | 1 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.773 | 2 | 0 | 0 | 0 |
| cross_source_synthesis | 35 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 70 | 0.971 | 1 | 1 | 0 | 0 |
| numerical_comparison | 34 | 0.765 | 2 | 6 | 0 | 0 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.899 [0.861, 0.937] (n=237) |
| false_answer_rate | 0.026 [0.009, 0.048] (n=229) |
| over_abstention_rate | 0.034 [0.013, 0.059] (n=237) |
| key_number_recall | 0.816 [0.767, 0.865] (n=153) |
| calc_correct | 0.667 [0.458, 0.833] (n=24) |
| gold_cited_any | 0.836 [0.783, 0.889] (n=189) |
| cases_with_ungrounded_numbers | 0.055 [0.03, 0.084] (n=237) |
| answers_with_ungrounded_numbers | 0.055 [0.03, 0.084] (n=237) |
| claims_judged | 299 |
| claim_supported_rate | 0.856 [0.799, 0.906] (n=299) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=299) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=180) |
| fact_coverage | 0.734 [0.685, 0.783] (n=305) |
| answers_contradicting_a_reference_fact | 0.011 [0.0, 0.029] (n=174) |
| latency_p50_s | 14.8 |
| latency_p95_s | 35.9 |
| cost_per_case_usd | 0.00215 |
| judge_cost_total_usd | 0.2474 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.914 | 1 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.727 | 3 | 0 | 0 | 0 |
| cross_source_synthesis | 35 | 1.0 | 0 | 0 | 0 | 1 |
| factual_lookup | 70 | 0.971 | 1 | 1 | 0 | 0 |
| numerical_comparison | 34 | 0.824 | 1 | 5 | 0 | 0 |
| revision_conflict | 19 | 0.947 | 0 | 1 | 0 | 1 |

