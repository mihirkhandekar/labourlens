# Evaluation of `agent-dev-X2` (dev, n=237)

Gold was AI-drafted; 14/237 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.916 [0.878, 0.949] (n=237) |
| false_answer_rate | 0.026 [0.009, 0.052] (n=232) |
| over_abstention_rate | 0.021 [0.004, 0.042] (n=237) |
| key_number_recall | 0.845 [0.798, 0.889] (n=153) |
| calc_correct | 0.75 [0.583, 0.917] (n=24) |
| gold_cited_any | 0.82 [0.767, 0.873] (n=189) |
| cases_with_ungrounded_numbers | 0.165 [0.118, 0.215] (n=237) |
| answers_with_ungrounded_numbers | 0.165 [0.118, 0.215] (n=237) |
| claims_judged | 379 |
| claim_supported_rate | 0.794 [0.742, 0.846] (n=379) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=379) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=183) |
| fact_coverage | 0.745 [0.695, 0.793] (n=314) |
| answers_contradicting_a_reference_fact | 0.017 [0.0, 0.04] (n=177) |
| latency_p50_s | 13.9 |
| latency_p95_s | 33.8 |
| cost_per_case_usd | 0.00463 |
| judge_cost_total_usd | 0.2689 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.914 | 1 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.75 | 3 | 0 | 0 | 4 |
| cross_source_synthesis | 35 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 70 | 0.971 | 1 | 1 | 0 | 0 |
| numerical_comparison | 34 | 0.882 | 1 | 3 | 0 | 0 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.903 [0.865, 0.941] (n=237) |
| false_answer_rate | 0.026 [0.009, 0.052] (n=231) |
| over_abstention_rate | 0.025 [0.008, 0.046] (n=237) |
| key_number_recall | 0.836 [0.789, 0.881] (n=153) |
| calc_correct | 0.75 [0.542, 0.917] (n=24) |
| gold_cited_any | 0.82 [0.762, 0.873] (n=189) |
| cases_with_ungrounded_numbers | 0.105 [0.068, 0.143] (n=237) |
| answers_with_ungrounded_numbers | 0.105 [0.068, 0.143] (n=237) |
| claims_judged | 315 |
| claim_supported_rate | 0.86 [0.817, 0.904] (n=315) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=315) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=182) |
| fact_coverage | 0.719 [0.674, 0.767] (n=310) |
| answers_contradicting_a_reference_fact | 0.023 [0.006, 0.045] (n=176) |
| latency_p50_s | 14.0 |
| latency_p95_s | 40.9 |
| cost_per_case_usd | 0.00285 |
| judge_cost_total_usd | 0.243 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.886 | 1 | 2 | 0 | 1 |
| ambiguity_insufficient_causal | 44 | 0.705 | 3 | 0 | 0 | 2 |
| cross_source_synthesis | 35 | 1.0 | 0 | 0 | 0 | 1 |
| factual_lookup | 70 | 0.971 | 1 | 1 | 0 | 0 |
| numerical_comparison | 34 | 0.882 | 1 | 3 | 0 | 0 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 0 | 1 |

