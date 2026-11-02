# Evaluation of `served-dev-S65-nostats-b` (dev, n=65)

Gold was AI-drafted; 51/65 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.692 [0.585, 0.8] (n=65) |
| false_answer_rate | 0.06 [0.0, 0.14] (n=50) |
| over_abstention_rate | 0.231 [0.138, 0.338] (n=65) |
| key_number_recall | 0.404 [0.247, 0.562] (n=32) |
| calc_correct | 0.0 [0.0, 0.0] (n=6) |
| gold_cited_any | 0.31 [0.167, 0.452] (n=42) |
| cases_with_ungrounded_numbers | 0.092 [0.031, 0.169] (n=65) |
| answers_with_ungrounded_numbers | 0.092 [0.031, 0.169] (n=65) |
| claims_judged | 46 |
| claim_supported_rate | 0.717 [0.582, 0.851] (n=46) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=46) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=30) |
| fact_coverage | 0.625 [0.512, 0.75] (n=40) |
| answers_contradicting_a_reference_fact | 0.167 [0.042, 0.333] (n=24) |
| latency_p50_s | 34.6 |
| latency_p95_s | 54.4 |
| cost_per_case_usd | 0.0035 |
| judge_cost_total_usd | 0.0431 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.5 | 1 | 2 | 0 | 1 |
| ambiguity_insufficient_causal | 9 | 0.667 | 2 | 0 | 0 | 2 |
| cross_source_synthesis | 8 | 0.75 | 0 | 2 | 0 | 1 |
| factual_lookup | 15 | 0.867 | 0 | 2 | 0 | 1 |
| numerical_comparison | 7 | 0.143 | 0 | 6 | 0 | 0 |
| revision_conflict | 4 | 0.25 | 0 | 3 | 0 | 0 |
| served_context_probe | 6 | 1.0 | 0 | 0 | 0 | 0 |
| served_diversion_probe | 8 | 1.0 | 0 | 0 | 0 | 0 |

