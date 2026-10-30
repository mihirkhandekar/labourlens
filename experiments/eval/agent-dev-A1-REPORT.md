# Evaluation of `agent-dev-A1` (dev, n=34)

Gold labels and the judge are AI-produced; nothing here is human-reviewed. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-4.1-mini

| measure | value |
|---|---|
| n_cases | 34 |
| behaviour_accuracy | 0.824 [0.706, 0.941] (n=34) |
| false_answer_rate | 0.067 [0.0, 0.167] (n=30) |
| over_abstention_rate | 0.118 [0.029, 0.235] (n=34) |
| key_number_recall | 0.659 [0.478, 0.826] (n=23) |
| calc_correct | 0.5 [0.167, 0.833] (n=6) |
| gold_cited_any | 0.516 [0.355, 0.677] (n=31) |
| answers_with_ungrounded_numbers | 0.088 [0.0, 0.206] (n=34) |
| claims_judged | 48 |
| claim_supported_rate | 0.771 |
| claim_unsupported_rate | 0.042 |
| answers_with_any_unsupported_claim | 0.077 [0.0, 0.192] (n=26) |
| fact_coverage | 0.537 |
| answers_contradicting_a_reference_fact | 0.231 [0.077, 0.385] (n=26) |
| latency_p50_s | 5.7 |
| latency_p95_s | 10.8 |
| cost_per_case_usd | 0.00455 |
| judge_cost_total_usd | 0.0405 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 1.0 | 0 | 0 | 0 | 1 |
| ambiguity_insufficient_causal | 4 | 0.5 | 2 | 0 | 1 | 1 |
| cross_source_synthesis | 7 | 0.857 | 0 | 1 | 0 | 1 |
| factual_lookup | 8 | 0.75 | 0 | 2 | 0 | 0 |
| numerical_comparison | 6 | 0.833 | 0 | 1 | 1 | 1 |
| revision_conflict | 4 | 1.0 | 0 | 0 | 0 | 2 |

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 34 |
| behaviour_accuracy | 0.765 [0.618, 0.882] (n=34) |
| false_answer_rate | 0.034 [0.0, 0.103] (n=29) |
| over_abstention_rate | 0.147 [0.029, 0.265] (n=34) |
| key_number_recall | 0.804 [0.652, 0.942] (n=23) |
| calc_correct | 0.667 [0.333, 1.0] (n=6) |
| gold_cited_any | 0.677 [0.516, 0.839] (n=31) |
| answers_with_ungrounded_numbers | 0.059 [0.0, 0.147] (n=34) |
| claims_judged | 50 |
| claim_supported_rate | 0.76 |
| claim_unsupported_rate | 0.0 |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=24) |
| fact_coverage | 0.611 |
| answers_contradicting_a_reference_fact | 0.083 [0.0, 0.208] (n=24) |
| latency_p50_s | 10.6 |
| latency_p95_s | 19.2 |
| cost_per_case_usd | 0.00302 |
| judge_cost_total_usd | 0.0357 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 1.0 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 4 | 0.25 | 1 | 0 | 0 | 0 |
| cross_source_synthesis | 7 | 0.857 | 0 | 1 | 0 | 3 |
| factual_lookup | 8 | 0.75 | 0 | 2 | 0 | 0 |
| numerical_comparison | 6 | 0.667 | 0 | 2 | 0 | 0 |
| revision_conflict | 4 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 34 |
| behaviour_accuracy | 0.706 [0.559, 0.853] (n=34) |
| false_answer_rate | 0.036 [0.0, 0.107] (n=28) |
| over_abstention_rate | 0.176 [0.059, 0.324] (n=34) |
| key_number_recall | 0.754 [0.594, 0.891] (n=23) |
| calc_correct | 0.667 [0.333, 1.0] (n=6) |
| gold_cited_any | 0.645 [0.452, 0.806] (n=31) |
| answers_with_ungrounded_numbers | 0.0 [0.0, 0.0] (n=34) |
| claims_judged | 35 |
| claim_supported_rate | 0.886 |
| claim_unsupported_rate | 0.0 |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=23) |
| fact_coverage | 0.657 |
| answers_contradicting_a_reference_fact | 0.043 [0.0, 0.13] (n=23) |
| latency_p50_s | 13.0 |
| latency_p95_s | 24.2 |
| cost_per_case_usd | 0.00142 |
| judge_cost_total_usd | 0.0335 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.8 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 4 | 0.25 | 1 | 0 | 0 | 0 |
| cross_source_synthesis | 7 | 0.857 | 0 | 1 | 0 | 2 |
| factual_lookup | 8 | 0.625 | 0 | 3 | 0 | 0 |
| numerical_comparison | 6 | 0.667 | 0 | 2 | 0 | 0 |
| revision_conflict | 4 | 1.0 | 0 | 0 | 0 | 0 |

