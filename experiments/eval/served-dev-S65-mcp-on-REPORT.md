# Evaluation of `served-dev-S65-mcp-on` (dev, n=65)

Gold was AI-drafted; 51/65 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.908 [0.846, 0.969] (n=65) |
| false_answer_rate | 0.032 [0.0, 0.079] (n=63) |
| over_abstention_rate | 0.031 [0.0, 0.077] (n=65) |
| key_number_recall | 0.836 [0.729, 0.932] (n=32) |
| calc_correct | 0.667 [0.333, 1.0] (n=6) |
| gold_cited_any | 0.69 [0.548, 0.833] (n=42) |
| cases_with_ungrounded_numbers | 0.077 [0.015, 0.154] (n=65) |
| answers_with_ungrounded_numbers | 0.077 [0.015, 0.154] (n=65) |
| claims_judged | 80 |
| claim_supported_rate | 0.838 [0.753, 0.923] (n=80) |
| claim_unsupported_rate | 0.013 [0.0, 0.039] (n=80) |
| answers_with_any_unsupported_claim | 0.024 [0.0, 0.071] (n=42) |
| fact_coverage | 0.75 [0.671, 0.841] (n=72) |
| answers_contradicting_a_reference_fact | 0.027 [0.0, 0.081] (n=37) |
| latency_p50_s | 10.2 |
| latency_p95_s | 32.0 |
| cost_per_case_usd | 0.00385 |
| judge_cost_total_usd | 0.0596 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.75 | 1 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 9 | 0.778 | 1 | 0 | 0 | 1 |
| cross_source_synthesis | 8 | 0.875 | 0 | 1 | 1 | 0 |
| factual_lookup | 15 | 1.0 | 0 | 0 | 0 | 0 |
| numerical_comparison | 7 | 0.857 | 0 | 1 | 0 | 0 |
| revision_conflict | 4 | 1.0 | 0 | 0 | 0 | 0 |
| served_context_probe | 6 | 1.0 | 0 | 0 | 0 | 0 |
| served_diversion_probe | 8 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.908 [0.831, 0.969] (n=65) |
| false_answer_rate | 0.046 [0.0, 0.108] (n=65) |
| over_abstention_rate | 0.0 [0.0, 0.0] (n=65) |
| key_number_recall | 0.87 [0.781, 0.943] (n=32) |
| calc_correct | 0.833 [0.5, 1.0] (n=6) |
| gold_cited_any | 0.738 [0.595, 0.857] (n=42) |
| cases_with_ungrounded_numbers | 0.092 [0.031, 0.169] (n=65) |
| answers_with_ungrounded_numbers | 0.092 [0.031, 0.169] (n=65) |
| claims_judged | 78 |
| claim_supported_rate | 0.91 [0.835, 0.973] (n=78) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=78) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=45) |
| fact_coverage | 0.727 [0.636, 0.817] (n=77) |
| answers_contradicting_a_reference_fact | 0.026 [0.0, 0.077] (n=39) |
| latency_p50_s | 12.4 |
| latency_p95_s | 34.7 |
| cost_per_case_usd | 0.00268 |
| judge_cost_total_usd | 0.0586 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.75 | 1 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 9 | 0.667 | 2 | 0 | 0 | 2 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 15 | 1.0 | 0 | 0 | 0 | 0 |
| numerical_comparison | 7 | 1.0 | 0 | 0 | 0 | 0 |
| revision_conflict | 4 | 1.0 | 0 | 0 | 0 | 0 |
| served_context_probe | 6 | 0.833 | 0 | 0 | 0 | 0 |
| served_diversion_probe | 8 | 1.0 | 0 | 0 | 0 | 0 |

