# Evaluation of `served-dev-S65-direct-on` (dev, n=65)

Gold was AI-drafted; 51/65 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.877 [0.8, 0.954] (n=65) |
| false_answer_rate | 0.048 [0.0, 0.113] (n=62) |
| over_abstention_rate | 0.046 [0.0, 0.108] (n=65) |
| key_number_recall | 0.812 [0.693, 0.914] (n=32) |
| calc_correct | 0.667 [0.333, 1.0] (n=6) |
| gold_cited_any | 0.643 [0.5, 0.786] (n=42) |
| cases_with_ungrounded_numbers | 0.062 [0.015, 0.123] (n=65) |
| answers_with_ungrounded_numbers | 0.062 [0.015, 0.123] (n=65) |
| claims_judged | 86 |
| claim_supported_rate | 0.744 [0.624, 0.857] (n=86) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=86) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=42) |
| fact_coverage | 0.812 [0.704, 0.919] (n=69) |
| answers_contradicting_a_reference_fact | 0.056 [0.0, 0.139] (n=36) |
| latency_p50_s | 13.2 |
| latency_p95_s | 33.8 |
| cost_per_case_usd | 0.00406 |
| judge_cost_total_usd | 0.0601 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.75 | 1 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 9 | 0.667 | 2 | 0 | 0 | 2 |
| cross_source_synthesis | 8 | 0.875 | 0 | 1 | 0 | 0 |
| factual_lookup | 15 | 1.0 | 0 | 0 | 0 | 0 |
| numerical_comparison | 7 | 0.714 | 0 | 2 | 0 | 0 |
| revision_conflict | 4 | 1.0 | 0 | 0 | 0 | 0 |
| served_context_probe | 6 | 1.0 | 0 | 0 | 0 | 0 |
| served_diversion_probe | 8 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.908 [0.831, 0.969] (n=65) |
| false_answer_rate | 0.047 [0.0, 0.109] (n=64) |
| over_abstention_rate | 0.015 [0.0, 0.046] (n=65) |
| key_number_recall | 0.836 [0.729, 0.922] (n=32) |
| calc_correct | 0.833 [0.5, 1.0] (n=6) |
| gold_cited_any | 0.738 [0.595, 0.857] (n=42) |
| cases_with_ungrounded_numbers | 0.062 [0.015, 0.123] (n=65) |
| answers_with_ungrounded_numbers | 0.062 [0.015, 0.123] (n=65) |
| claims_judged | 71 |
| claim_supported_rate | 0.859 [0.76, 0.945] (n=71) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=71) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=44) |
| fact_coverage | 0.73 [0.641, 0.826] (n=74) |
| answers_contradicting_a_reference_fact | 0.026 [0.0, 0.079] (n=38) |
| latency_p50_s | 10.8 |
| latency_p95_s | 32.8 |
| cost_per_case_usd | 0.00257 |
| judge_cost_total_usd | 0.0571 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.75 | 1 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 9 | 0.667 | 2 | 0 | 0 | 2 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 15 | 1.0 | 0 | 0 | 0 | 0 |
| numerical_comparison | 7 | 0.857 | 0 | 1 | 0 | 0 |
| revision_conflict | 4 | 1.0 | 0 | 0 | 0 | 0 |
| served_context_probe | 6 | 1.0 | 0 | 0 | 0 | 0 |
| served_diversion_probe | 8 | 1.0 | 0 | 0 | 0 | 0 |

