# Evaluation of `served-dev-S65-mcpall` (dev, n=65)

Gold was AI-drafted; 51/65 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.877 [0.8, 0.954] (n=65) |
| false_answer_rate | 0.048 [0.0, 0.113] (n=62) |
| over_abstention_rate | 0.046 [0.0, 0.108] (n=65) |
| key_number_recall | 0.771 [0.651, 0.878] (n=32) |
| calc_correct | 0.667 [0.333, 1.0] (n=6) |
| gold_cited_any | 0.714 [0.571, 0.833] (n=42) |
| cases_with_ungrounded_numbers | 0.062 [0.015, 0.123] (n=65) |
| answers_with_ungrounded_numbers | 0.062 [0.015, 0.123] (n=65) |
| claims_judged | 72 |
| claim_supported_rate | 0.889 [0.795, 0.971] (n=72) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=72) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=42) |
| fact_coverage | 0.714 [0.609, 0.815] (n=70) |
| answers_contradicting_a_reference_fact | 0.028 [0.0, 0.083] (n=36) |
| latency_p50_s | 14.3 |
| latency_p95_s | 51.4 |
| cost_per_case_usd | 0.00258 |
| judge_cost_total_usd | 0.0568 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.625 | 1 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 9 | 0.667 | 2 | 0 | 0 | 2 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 15 | 1.0 | 0 | 0 | 0 | 0 |
| numerical_comparison | 7 | 0.714 | 0 | 2 | 0 | 0 |
| revision_conflict | 4 | 1.0 | 0 | 0 | 0 | 0 |
| served_context_probe | 6 | 1.0 | 0 | 0 | 0 | 0 |
| served_diversion_probe | 8 | 1.0 | 0 | 0 | 0 | 0 |

