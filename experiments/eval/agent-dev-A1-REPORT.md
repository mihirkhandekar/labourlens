# Evaluation of `agent-dev-A1` (dev, n=237)

Gold was AI-drafted; 14/237 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-4.1-mini

| measure | value |
|---|---|
| n_cases | 235 |
| behaviour_accuracy | 0.757 [0.702, 0.813] (n=235) |
| false_answer_rate | 0.079 [0.044, 0.113] (n=203) |
| over_abstention_rate | 0.136 [0.094, 0.179] (n=235) |
| key_number_recall | 0.685 [0.623, 0.748] (n=151) |
| calc_correct | 0.25 [0.083, 0.417] (n=24) |
| gold_cited_any | 0.61 [0.54, 0.679] (n=187) |
| cases_with_ungrounded_numbers | 0.077 [0.043, 0.115] (n=235) |
| answers_with_ungrounded_numbers | 0.077 [0.043, 0.115] (n=235) |
| claims_judged | 299 |
| claim_supported_rate | 0.876 [0.828, 0.92] (n=299) |
| claim_unsupported_rate | 0.007 [0.0, 0.017] (n=299) |
| answers_with_any_unsupported_claim | 0.012 [0.0, 0.03] (n=164) |
| fact_coverage | 0.578 [0.517, 0.642] (n=256) |
| answers_contradicting_a_reference_fact | 0.101 [0.054, 0.154] (n=149) |
| latency_p50_s | 5.8 |
| latency_p95_s | 10.7 |
| cost_per_case_usd | 0.00466 |
| judge_cost_total_usd | 0.2286 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.857 | 0 | 4 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.591 | 8 | 2 | 0 | 2 |
| cross_source_synthesis | 35 | 0.943 | 1 | 1 | 0 | 6 |
| factual_lookup | 70 | 0.786 | 5 | 10 | 2 | 1 |
| numerical_comparison | 33 | 0.515 | 2 | 14 | 0 | 2 |
| revision_conflict | 18 | 0.944 | 0 | 1 | 0 | 9 |

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 235 |
| behaviour_accuracy | 0.8 [0.749, 0.851] (n=235) |
| false_answer_rate | 0.03 [0.01, 0.054] (n=203) |
| over_abstention_rate | 0.136 [0.094, 0.183] (n=235) |
| key_number_recall | 0.762 [0.7, 0.821] (n=151) |
| calc_correct | 0.75 [0.583, 0.917] (n=24) |
| gold_cited_any | 0.69 [0.626, 0.759] (n=187) |
| cases_with_ungrounded_numbers | 0.068 [0.038, 0.102] (n=235) |
| answers_with_ungrounded_numbers | 0.068 [0.038, 0.102] (n=235) |
| claims_judged | 299 |
| claim_supported_rate | 0.819 [0.765, 0.871] (n=299) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=299) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=154) |
| fact_coverage | 0.724 [0.671, 0.779] (n=261) |
| answers_contradicting_a_reference_fact | 0.014 [0.0, 0.034] (n=148) |
| latency_p50_s | 9.6 |
| latency_p95_s | 18.0 |
| cost_per_case_usd | 0.00274 |
| judge_cost_total_usd | 0.2199 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.943 | 1 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.773 | 2 | 0 | 0 | 1 |
| cross_source_synthesis | 35 | 0.771 | 0 | 8 | 0 | 1 |
| factual_lookup | 70 | 0.786 | 1 | 14 | 0 | 0 |
| numerical_comparison | 33 | 0.788 | 2 | 5 | 0 | 0 |
| revision_conflict | 18 | 0.722 | 0 | 5 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 235 |
| behaviour_accuracy | 0.779 [0.728, 0.83] (n=235) |
| false_answer_rate | 0.025 [0.005, 0.051] (n=198) |
| over_abstention_rate | 0.157 [0.111, 0.204] (n=235) |
| key_number_recall | 0.709 [0.645, 0.773] (n=151) |
| calc_correct | 0.667 [0.458, 0.833] (n=24) |
| gold_cited_any | 0.674 [0.604, 0.738] (n=187) |
| cases_with_ungrounded_numbers | 0.055 [0.03, 0.085] (n=235) |
| answers_with_ungrounded_numbers | 0.055 [0.03, 0.085] (n=235) |
| claims_judged | 243 |
| claim_supported_rate | 0.881 [0.822, 0.935] (n=243) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=243) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=148) |
| fact_coverage | 0.687 [0.63, 0.747] (n=259) |
| answers_contradicting_a_reference_fact | 0.007 [0.0, 0.021] (n=143) |
| latency_p50_s | 10.7 |
| latency_p95_s | 22.8 |
| cost_per_case_usd | 0.00137 |
| judge_cost_total_usd | 0.2001 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.857 | 1 | 3 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.773 | 2 | 0 | 0 | 0 |
| cross_source_synthesis | 35 | 0.8 | 0 | 6 | 0 | 1 |
| factual_lookup | 70 | 0.743 | 1 | 17 | 0 | 0 |
| numerical_comparison | 33 | 0.818 | 1 | 5 | 0 | 0 |
| revision_conflict | 18 | 0.667 | 0 | 6 | 0 | 0 |

