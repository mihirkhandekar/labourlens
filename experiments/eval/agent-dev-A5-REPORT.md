# Evaluation of `agent-dev-A5` (dev, n=237)

Gold was AI-drafted; 14/237 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.916 [0.878, 0.949] (n=237) |
| false_answer_rate | 0.022 [0.004, 0.043] (n=230) |
| over_abstention_rate | 0.03 [0.008, 0.051] (n=237) |
| key_number_recall | 0.862 [0.816, 0.905] (n=153) |
| calc_correct | 0.708 [0.542, 0.875] (n=24) |
| gold_cited_any | 0.841 [0.788, 0.889] (n=189) |
| cases_with_ungrounded_numbers | 0.084 [0.051, 0.122] (n=237) |
| answers_with_ungrounded_numbers | 0.084 [0.051, 0.122] (n=237) |
| claims_judged | 369 |
| claim_supported_rate | 0.856 [0.805, 0.904] (n=369) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=369) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=180) |
| fact_coverage | 0.76 [0.714, 0.808] (n=304) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=175) |
| latency_p50_s | 14.7 |
| latency_p95_s | 34.0 |
| cost_per_case_usd | 0.00369 |
| judge_cost_total_usd | 0.2674 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.971 | 1 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.773 | 2 | 0 | 0 | 0 |
| cross_source_synthesis | 35 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 70 | 0.957 | 1 | 2 | 0 | 0 |
| numerical_comparison | 34 | 0.824 | 1 | 5 | 0 | 0 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.911 [0.873, 0.945] (n=237) |
| false_answer_rate | 0.034 [0.013, 0.06] (n=232) |
| over_abstention_rate | 0.021 [0.004, 0.038] (n=237) |
| key_number_recall | 0.832 [0.785, 0.877] (n=153) |
| calc_correct | 0.75 [0.583, 0.917] (n=24) |
| gold_cited_any | 0.841 [0.788, 0.894] (n=189) |
| cases_with_ungrounded_numbers | 0.076 [0.046, 0.11] (n=237) |
| answers_with_ungrounded_numbers | 0.076 [0.046, 0.11] (n=237) |
| claims_judged | 313 |
| claim_supported_rate | 0.879 [0.831, 0.922] (n=313) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=313) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=185) |
| fact_coverage | 0.724 [0.671, 0.772] (n=312) |
| answers_contradicting_a_reference_fact | 0.006 [0.0, 0.017] (n=177) |
| latency_p50_s | 16.4 |
| latency_p95_s | 37.5 |
| cost_per_case_usd | 0.00217 |
| judge_cost_total_usd | 0.248 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.971 | 1 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.727 | 4 | 0 | 0 | 0 |
| cross_source_synthesis | 35 | 0.971 | 0 | 1 | 0 | 0 |
| factual_lookup | 70 | 0.971 | 1 | 1 | 0 | 0 |
| numerical_comparison | 34 | 0.853 | 2 | 3 | 0 | 1 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 0 | 0 |

