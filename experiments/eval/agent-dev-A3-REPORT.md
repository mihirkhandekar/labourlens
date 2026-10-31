# Evaluation of `agent-dev-A3` (dev, n=237)

Gold was AI-drafted; 14/237 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.903 [0.861, 0.941] (n=237) |
| false_answer_rate | 0.03 [0.009, 0.052] (n=231) |
| over_abstention_rate | 0.025 [0.008, 0.046] (n=237) |
| key_number_recall | 0.847 [0.802, 0.891] (n=153) |
| calc_correct | 0.75 [0.583, 0.917] (n=24) |
| gold_cited_any | 0.841 [0.788, 0.889] (n=189) |
| cases_with_ungrounded_numbers | 0.051 [0.025, 0.08] (n=237) |
| answers_with_ungrounded_numbers | 0.051 [0.025, 0.08] (n=237) |
| claims_judged | 364 |
| claim_supported_rate | 0.874 [0.829, 0.916] (n=364) |
| claim_unsupported_rate | 0.003 [0.0, 0.009] (n=364) |
| answers_with_any_unsupported_claim | 0.005 [0.0, 0.016] (n=183) |
| fact_coverage | 0.765 [0.72, 0.816] (n=311) |
| answers_contradicting_a_reference_fact | 0.006 [0.0, 0.017] (n=176) |
| latency_p50_s | 15.5 |
| latency_p95_s | 34.4 |
| cost_per_case_usd | 0.0036 |
| judge_cost_total_usd | 0.2592 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.943 | 1 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.75 | 2 | 0 | 0 | 0 |
| cross_source_synthesis | 35 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 70 | 0.943 | 2 | 2 | 0 | 0 |
| numerical_comparison | 34 | 0.824 | 2 | 4 | 0 | 0 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 1 | 2 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.903 [0.865, 0.937] (n=237) |
| false_answer_rate | 0.03 [0.009, 0.057] (n=230) |
| over_abstention_rate | 0.03 [0.008, 0.051] (n=237) |
| key_number_recall | 0.821 [0.773, 0.866] (n=153) |
| calc_correct | 0.75 [0.583, 0.917] (n=24) |
| gold_cited_any | 0.836 [0.783, 0.884] (n=189) |
| cases_with_ungrounded_numbers | 0.076 [0.042, 0.11] (n=237) |
| answers_with_ungrounded_numbers | 0.076 [0.042, 0.11] (n=237) |
| claims_judged | 309 |
| claim_supported_rate | 0.887 [0.84, 0.931] (n=309) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=309) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=182) |
| fact_coverage | 0.728 [0.678, 0.779] (n=309) |
| answers_contradicting_a_reference_fact | 0.006 [0.0, 0.017] (n=175) |
| latency_p50_s | 15.4 |
| latency_p95_s | 35.6 |
| cost_per_case_usd | 0.00212 |
| judge_cost_total_usd | 0.2442 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.886 | 1 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.727 | 4 | 0 | 0 | 0 |
| cross_source_synthesis | 35 | 0.971 | 0 | 1 | 0 | 1 |
| factual_lookup | 70 | 0.971 | 1 | 1 | 0 | 0 |
| numerical_comparison | 34 | 0.882 | 1 | 3 | 0 | 0 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 0 | 0 |

