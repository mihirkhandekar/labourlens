# Evaluation of `agent-heldout-V31-hybrid` (heldout, n=65)

Gold was AI-drafted; 0/65 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.723 [0.615, 0.831] (n=65) |
| false_answer_rate | 0.019 [0.0, 0.058] (n=52) |
| over_abstention_rate | 0.2 [0.108, 0.292] (n=65) |
| key_number_recall | 0.722 [0.593, 0.837] (n=45) |
| calc_correct | 0.5 [0.0, 1.0] (n=4) |
| gold_cited_any | 0.604 [0.458, 0.729] (n=48) |
| cases_with_ungrounded_numbers | 0.046 [0.0, 0.108] (n=65) |
| answers_with_ungrounded_numbers | 0.046 [0.0, 0.108] (n=65) |
| claims_judged | 61 |
| claim_supported_rate | 0.934 [0.852, 1.0] (n=61) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=61) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=36) |
| fact_coverage | 0.88 [0.787, 0.964] (n=50) |
| answers_contradicting_a_reference_fact | 0.029 [0.0, 0.086] (n=35) |
| latency_p50_s | 9.9 |
| latency_p95_s | 17.2 |
| cost_per_case_usd | 0.00338 |
| judge_cost_total_usd | 0.044 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.875 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.6 | 1 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 1 |
| factual_lookup | 22 | 0.909 | 0 | 2 | 0 | 0 |
| numerical_comparison | 14 | 0.214 | 0 | 11 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.708 [0.6, 0.815] (n=65) |
| false_answer_rate | 0.0 [0.0, 0.0] (n=51) |
| over_abstention_rate | 0.215 [0.123, 0.308] (n=65) |
| key_number_recall | 0.696 [0.559, 0.822] (n=45) |
| calc_correct | 0.5 [0.0, 1.0] (n=4) |
| gold_cited_any | 0.562 [0.417, 0.688] (n=48) |
| cases_with_ungrounded_numbers | 0.015 [0.0, 0.046] (n=65) |
| answers_with_ungrounded_numbers | 0.015 [0.0, 0.046] (n=65) |
| claims_judged | 45 |
| claim_supported_rate | 0.956 [0.889, 1.0] (n=45) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=45) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=34) |
| fact_coverage | 0.735 [0.636, 0.868] (n=49) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=34) |
| latency_p50_s | 10.3 |
| latency_p95_s | 18.7 |
| cost_per_case_usd | 0.00161 |
| judge_cost_total_usd | 0.039 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.875 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.6 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.864 | 0 | 3 | 0 | 0 |
| numerical_comparison | 14 | 0.214 | 0 | 11 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

