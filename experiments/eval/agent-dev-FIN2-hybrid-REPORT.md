# Evaluation of `agent-dev-FIN2-hybrid` (dev, n=237)

Gold was AI-drafted; 237/237 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.848 [0.802, 0.89] (n=237) |
| false_answer_rate | 0.028 [0.009, 0.051] (n=217) |
| over_abstention_rate | 0.084 [0.051, 0.122] (n=237) |
| key_number_recall | 0.821 [0.772, 0.871] (n=153) |
| calc_correct | 0.708 [0.5, 0.875] (n=24) |
| gold_cited_any | 0.709 [0.646, 0.772] (n=189) |
| cases_with_ungrounded_numbers | 0.127 [0.089, 0.173] (n=237) |
| answers_with_ungrounded_numbers | 0.127 [0.089, 0.173] (n=237) |
| claims_judged | 330 |
| claim_supported_rate | 0.77 [0.717, 0.825] (n=330) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=330) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=168) |
| fact_coverage | 0.709 [0.659, 0.763] (n=292) |
| answers_contradicting_a_reference_fact | 0.012 [0.0, 0.031] (n=162) |
| latency_p50_s | 10.1 |
| latency_p95_s | 21.3 |
| cost_per_case_usd | 0.00352 |
| judge_cost_total_usd | 0.2494 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.943 | 1 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.75 | 2 | 0 | 0 | 3 |
| cross_source_synthesis | 35 | 0.886 | 0 | 4 | 0 | 0 |
| factual_lookup | 70 | 0.843 | 1 | 10 | 0 | 0 |
| numerical_comparison | 34 | 0.824 | 2 | 4 | 0 | 0 |
| revision_conflict | 19 | 0.895 | 0 | 2 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.81 [0.759, 0.857] (n=237) |
| false_answer_rate | 0.038 [0.014, 0.067] (n=210) |
| over_abstention_rate | 0.114 [0.076, 0.156] (n=237) |
| key_number_recall | 0.72 [0.663, 0.778] (n=153) |
| calc_correct | 0.708 [0.542, 0.875] (n=24) |
| gold_cited_any | 0.656 [0.587, 0.72] (n=189) |
| cases_with_ungrounded_numbers | 0.131 [0.089, 0.173] (n=237) |
| answers_with_ungrounded_numbers | 0.131 [0.089, 0.173] (n=237) |
| claims_judged | 269 |
| claim_supported_rate | 0.818 [0.76, 0.877] (n=269) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=269) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=163) |
| fact_coverage | 0.655 [0.603, 0.71] (n=275) |
| answers_contradicting_a_reference_fact | 0.019 [0.0, 0.045] (n=155) |
| latency_p50_s | 10.2 |
| latency_p95_s | 24.1 |
| cost_per_case_usd | 0.00167 |
| judge_cost_total_usd | 0.2343 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.886 | 1 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.705 | 4 | 0 | 0 | 2 |
| cross_source_synthesis | 35 | 0.829 | 0 | 6 | 0 | 0 |
| factual_lookup | 70 | 0.829 | 1 | 11 | 0 | 0 |
| numerical_comparison | 34 | 0.824 | 2 | 4 | 0 | 0 |
| revision_conflict | 19 | 0.789 | 0 | 4 | 0 | 1 |

