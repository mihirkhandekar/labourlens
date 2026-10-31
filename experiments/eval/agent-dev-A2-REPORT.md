# Evaluation of `agent-dev-A2` (dev, n=237)

Gold was AI-drafted; 14/237 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 235 |
| behaviour_accuracy | 0.796 [0.745, 0.847] (n=235) |
| false_answer_rate | 0.034 [0.015, 0.059] (n=203) |
| over_abstention_rate | 0.136 [0.094, 0.179] (n=235) |
| key_number_recall | 0.767 [0.71, 0.824] (n=151) |
| calc_correct | 0.75 [0.583, 0.917] (n=24) |
| gold_cited_any | 0.695 [0.631, 0.759] (n=187) |
| cases_with_ungrounded_numbers | 0.064 [0.034, 0.098] (n=235) |
| answers_with_ungrounded_numbers | 0.064 [0.034, 0.098] (n=235) |
| claims_judged | 292 |
| claim_supported_rate | 0.829 [0.77, 0.885] (n=292) |
| claim_unsupported_rate | 0.003 [0.0, 0.011] (n=292) |
| answers_with_any_unsupported_claim | 0.006 [0.0, 0.019] (n=155) |
| fact_coverage | 0.716 [0.661, 0.772] (n=264) |
| answers_contradicting_a_reference_fact | 0.034 [0.007, 0.068] (n=148) |
| latency_p50_s | 10.8 |
| latency_p95_s | 20.6 |
| cost_per_case_usd | 0.0028 |
| judge_cost_total_usd | 0.2157 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.943 | 1 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.773 | 2 | 0 | 0 | 2 |
| cross_source_synthesis | 35 | 0.771 | 0 | 8 | 0 | 3 |
| factual_lookup | 70 | 0.743 | 2 | 16 | 0 | 0 |
| numerical_comparison | 33 | 0.818 | 2 | 4 | 0 | 0 |
| revision_conflict | 18 | 0.778 | 0 | 4 | 1 | 1 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 235 |
| behaviour_accuracy | 0.762 [0.706, 0.813] (n=235) |
| false_answer_rate | 0.036 [0.01, 0.067] (n=195) |
| over_abstention_rate | 0.17 [0.123, 0.221] (n=235) |
| key_number_recall | 0.715 [0.654, 0.774] (n=151) |
| calc_correct | 0.75 [0.583, 0.917] (n=24) |
| gold_cited_any | 0.658 [0.588, 0.722] (n=187) |
| cases_with_ungrounded_numbers | 0.098 [0.064, 0.136] (n=235) |
| answers_with_ungrounded_numbers | 0.098 [0.064, 0.136] (n=235) |
| claims_judged | 232 |
| claim_supported_rate | 0.888 [0.835, 0.938] (n=232) |
| claim_unsupported_rate | 0.004 [0.0, 0.014] (n=232) |
| answers_with_any_unsupported_claim | 0.007 [0.0, 0.02] (n=147) |
| fact_coverage | 0.692 [0.634, 0.75] (n=247) |
| answers_contradicting_a_reference_fact | 0.014 [0.0, 0.036] (n=140) |
| latency_p50_s | 12.7 |
| latency_p95_s | 24.7 |
| cost_per_case_usd | 0.00142 |
| judge_cost_total_usd | 0.187 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.857 | 1 | 3 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.727 | 3 | 1 | 0 | 0 |
| cross_source_synthesis | 35 | 0.714 | 0 | 10 | 0 | 3 |
| factual_lookup | 70 | 0.771 | 1 | 15 | 0 | 0 |
| numerical_comparison | 33 | 0.818 | 2 | 4 | 0 | 0 |
| revision_conflict | 18 | 0.611 | 0 | 7 | 1 | 0 |

