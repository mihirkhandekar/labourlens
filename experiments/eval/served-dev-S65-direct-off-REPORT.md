# Evaluation of `served-dev-S65-direct-off` (dev, n=65)

Gold was AI-drafted; 51/65 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.723 [0.615, 0.831] (n=65) |
| false_answer_rate | 0.066 [0.016, 0.131] (n=61) |
| over_abstention_rate | 0.062 [0.015, 0.123] (n=65) |
| key_number_recall | 0.763 [0.633, 0.872] (n=32) |
| calc_correct | 0.667 [0.333, 1.0] (n=6) |
| gold_cited_any | 0.69 [0.548, 0.81] (n=42) |
| cases_with_ungrounded_numbers | 0.123 [0.046, 0.2] (n=65) |
| answers_with_ungrounded_numbers | 0.123 [0.046, 0.2] (n=65) |
| claims_judged | 89 |
| claim_supported_rate | 0.843 [0.767, 0.926] (n=89) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=89) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=42) |
| fact_coverage | 0.754 [0.653, 0.857] (n=69) |
| answers_contradicting_a_reference_fact | 0.028 [0.0, 0.083] (n=36) |
| latency_p50_s | 10.1 |
| latency_p95_s | 28.6 |
| cost_per_case_usd | 0.00388 |
| judge_cost_total_usd | 0.0616 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.75 | 1 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 9 | 0.667 | 2 | 0 | 0 | 2 |
| cross_source_synthesis | 8 | 0.875 | 0 | 1 | 0 | 0 |
| factual_lookup | 15 | 1.0 | 0 | 0 | 0 | 0 |
| numerical_comparison | 7 | 0.714 | 0 | 2 | 0 | 0 |
| revision_conflict | 4 | 1.0 | 0 | 0 | 0 | 0 |
| served_context_probe | 6 | 0.667 | 1 | 1 | 0 | 0 |
| served_diversion_probe | 8 | 0.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.754 [0.646, 0.846] (n=65) |
| false_answer_rate | 0.033 [0.0, 0.082] (n=61) |
| over_abstention_rate | 0.062 [0.015, 0.123] (n=65) |
| key_number_recall | 0.766 [0.641, 0.878] (n=32) |
| calc_correct | 0.667 [0.333, 1.0] (n=6) |
| gold_cited_any | 0.714 [0.571, 0.833] (n=42) |
| cases_with_ungrounded_numbers | 0.092 [0.031, 0.169] (n=65) |
| answers_with_ungrounded_numbers | 0.092 [0.031, 0.169] (n=65) |
| claims_judged | 68 |
| claim_supported_rate | 0.868 [0.788, 0.94] (n=68) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=68) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=40) |
| fact_coverage | 0.7 [0.6, 0.809] (n=70) |
| answers_contradicting_a_reference_fact | 0.028 [0.0, 0.083] (n=36) |
| latency_p50_s | 11.2 |
| latency_p95_s | 39.6 |
| cost_per_case_usd | 0.00253 |
| judge_cost_total_usd | 0.0559 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.625 | 1 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 9 | 0.778 | 1 | 0 | 0 | 2 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 15 | 1.0 | 0 | 0 | 0 | 0 |
| numerical_comparison | 7 | 0.714 | 0 | 2 | 0 | 0 |
| revision_conflict | 4 | 1.0 | 0 | 0 | 0 | 0 |
| served_context_probe | 6 | 0.833 | 0 | 1 | 0 | 0 |
| served_diversion_probe | 8 | 0.0 | 0 | 0 | 0 | 0 |

