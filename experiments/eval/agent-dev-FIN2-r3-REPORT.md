# Evaluation of `agent-dev-FIN2-r3` (dev, n=237)

Gold was AI-drafted; 237/237 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.895 [0.852, 0.932] (n=237) |
| false_answer_rate | 0.022 [0.004, 0.044] (n=226) |
| over_abstention_rate | 0.046 [0.021, 0.076] (n=237) |
| key_number_recall | 0.828 [0.775, 0.875] (n=153) |
| calc_correct | 0.583 [0.375, 0.792] (n=24) |
| gold_cited_any | 0.767 [0.709, 0.825] (n=189) |
| cases_with_ungrounded_numbers | 0.139 [0.097, 0.186] (n=237) |
| answers_with_ungrounded_numbers | 0.139 [0.097, 0.186] (n=237) |
| claims_judged | 363 |
| claim_supported_rate | 0.771 [0.718, 0.824] (n=363) |
| claim_unsupported_rate | 0.003 [0.0, 0.009] (n=363) |
| answers_with_any_unsupported_claim | 0.006 [0.0, 0.017] (n=176) |
| fact_coverage | 0.735 [0.686, 0.786] (n=298) |
| answers_contradicting_a_reference_fact | 0.023 [0.006, 0.047] (n=171) |
| latency_p50_s | 14.1 |
| latency_p95_s | 31.5 |
| cost_per_case_usd | 0.00476 |
| judge_cost_total_usd | 0.2593 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.914 | 1 | 1 | 0 | 1 |
| ambiguity_insufficient_causal | 44 | 0.795 | 1 | 0 | 0 | 2 |
| cross_source_synthesis | 35 | 0.943 | 0 | 2 | 0 | 0 |
| factual_lookup | 70 | 0.957 | 1 | 2 | 0 | 0 |
| numerical_comparison | 34 | 0.765 | 2 | 6 | 0 | 1 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 1 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.907 [0.873, 0.941] (n=237) |
| false_answer_rate | 0.03 [0.009, 0.056] (n=232) |
| over_abstention_rate | 0.021 [0.004, 0.042] (n=237) |
| key_number_recall | 0.839 [0.795, 0.885] (n=153) |
| calc_correct | 0.75 [0.583, 0.917] (n=24) |
| gold_cited_any | 0.841 [0.788, 0.889] (n=189) |
| cases_with_ungrounded_numbers | 0.118 [0.08, 0.156] (n=237) |
| answers_with_ungrounded_numbers | 0.118 [0.08, 0.156] (n=237) |
| claims_judged | 326 |
| claim_supported_rate | 0.828 [0.772, 0.881] (n=326) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=326) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=184) |
| fact_coverage | 0.74 [0.688, 0.791] (n=312) |
| answers_contradicting_a_reference_fact | 0.006 [0.0, 0.017] (n=177) |
| latency_p50_s | 13.6 |
| latency_p95_s | 34.1 |
| cost_per_case_usd | 0.00285 |
| judge_cost_total_usd | 0.2565 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.943 | 0 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.682 | 5 | 0 | 0 | 2 |
| cross_source_synthesis | 35 | 0.971 | 0 | 1 | 0 | 0 |
| factual_lookup | 70 | 0.971 | 1 | 1 | 0 | 0 |
| numerical_comparison | 34 | 0.912 | 1 | 2 | 0 | 0 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 0 | 0 |

