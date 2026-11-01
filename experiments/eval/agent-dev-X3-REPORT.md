# Evaluation of `agent-dev-X3` (dev, n=237)

Gold was AI-drafted; 14/237 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.899 [0.857, 0.937] (n=237) |
| false_answer_rate | 0.031 [0.013, 0.057] (n=229) |
| over_abstention_rate | 0.034 [0.013, 0.059] (n=237) |
| key_number_recall | 0.874 [0.831, 0.916] (n=153) |
| calc_correct | 0.792 [0.625, 0.958] (n=24) |
| gold_cited_any | 0.804 [0.746, 0.857] (n=189) |
| cases_with_ungrounded_numbers | 0.127 [0.084, 0.173] (n=237) |
| answers_with_ungrounded_numbers | 0.127 [0.084, 0.173] (n=237) |
| claims_judged | 373 |
| claim_supported_rate | 0.834 [0.785, 0.88] (n=373) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=373) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=181) |
| fact_coverage | 0.802 [0.754, 0.847] (n=303) |
| answers_contradicting_a_reference_fact | 0.011 [0.0, 0.029] (n=174) |
| latency_p50_s | 13.6 |
| latency_p95_s | 40.2 |
| cost_per_case_usd | 0.00484 |
| judge_cost_total_usd | 0.2557 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.943 | 1 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.773 | 2 | 0 | 0 | 3 |
| cross_source_synthesis | 35 | 0.914 | 0 | 3 | 0 | 0 |
| factual_lookup | 70 | 0.957 | 2 | 1 | 0 | 0 |
| numerical_comparison | 34 | 0.824 | 2 | 4 | 0 | 0 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.895 [0.852, 0.932] (n=237) |
| false_answer_rate | 0.031 [0.009, 0.057] (n=229) |
| over_abstention_rate | 0.034 [0.013, 0.059] (n=237) |
| key_number_recall | 0.829 [0.777, 0.876] (n=153) |
| calc_correct | 0.792 [0.625, 0.917] (n=24) |
| gold_cited_any | 0.778 [0.72, 0.836] (n=189) |
| cases_with_ungrounded_numbers | 0.114 [0.076, 0.156] (n=237) |
| answers_with_ungrounded_numbers | 0.114 [0.076, 0.156] (n=237) |
| claims_judged | 300 |
| claim_supported_rate | 0.887 [0.838, 0.934] (n=300) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=300) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=181) |
| fact_coverage | 0.734 [0.679, 0.787] (n=305) |
| answers_contradicting_a_reference_fact | 0.023 [0.006, 0.046] (n=174) |
| latency_p50_s | 13.9 |
| latency_p95_s | 40.8 |
| cost_per_case_usd | 0.00298 |
| judge_cost_total_usd | 0.237 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.857 | 1 | 3 | 0 | 1 |
| ambiguity_insufficient_causal | 44 | 0.727 | 3 | 0 | 0 | 4 |
| cross_source_synthesis | 35 | 0.943 | 0 | 2 | 0 | 1 |
| factual_lookup | 70 | 0.971 | 1 | 1 | 0 | 0 |
| numerical_comparison | 34 | 0.882 | 2 | 2 | 0 | 0 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 0 | 0 |

