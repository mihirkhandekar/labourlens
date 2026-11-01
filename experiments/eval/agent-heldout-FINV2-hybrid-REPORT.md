# Evaluation of `agent-heldout-FINV2-hybrid` (heldout, n=65)

Gold was AI-drafted; 0/65 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.723 [0.615, 0.831] (n=65) |
| false_answer_rate | 0.038 [0.0, 0.096] (n=52) |
| over_abstention_rate | 0.2 [0.108, 0.292] (n=65) |
| key_number_recall | 0.707 [0.574, 0.83] (n=45) |
| calc_correct | 0.5 [0.0, 1.0] (n=4) |
| gold_cited_any | 0.542 [0.396, 0.667] (n=48) |
| cases_with_ungrounded_numbers | 0.062 [0.015, 0.123] (n=65) |
| answers_with_ungrounded_numbers | 0.062 [0.015, 0.123] (n=65) |
| claims_judged | 62 |
| claim_supported_rate | 0.903 [0.814, 0.977] (n=62) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=62) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=37) |
| fact_coverage | 0.84 [0.735, 0.949] (n=50) |
| answers_contradicting_a_reference_fact | 0.029 [0.0, 0.086] (n=35) |
| latency_p50_s | 10.2 |
| latency_p95_s | 17.0 |
| cost_per_case_usd | 0.00344 |
| judge_cost_total_usd | 0.0482 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.875 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.6 | 2 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 1 |
| factual_lookup | 22 | 0.909 | 0 | 2 | 0 | 0 |
| numerical_comparison | 14 | 0.214 | 0 | 11 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.754 [0.646, 0.846] (n=65) |
| false_answer_rate | 0.0 [0.0, 0.0] (n=52) |
| over_abstention_rate | 0.2 [0.108, 0.292] (n=65) |
| key_number_recall | 0.696 [0.559, 0.822] (n=45) |
| calc_correct | 0.5 [0.0, 1.0] (n=4) |
| gold_cited_any | 0.604 [0.458, 0.729] (n=48) |
| cases_with_ungrounded_numbers | 0.015 [0.0, 0.046] (n=65) |
| answers_with_ungrounded_numbers | 0.015 [0.0, 0.046] (n=65) |
| claims_judged | 45 |
| claim_supported_rate | 0.956 [0.889, 1.0] (n=45) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=45) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=35) |
| fact_coverage | 0.74 [0.622, 0.872] (n=50) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=35) |
| latency_p50_s | 10.5 |
| latency_p95_s | 17.7 |
| cost_per_case_usd | 0.00171 |
| judge_cost_total_usd | 0.0409 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.875 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.8 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.909 | 0 | 2 | 0 | 0 |
| numerical_comparison | 14 | 0.214 | 0 | 11 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

