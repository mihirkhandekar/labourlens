# Evaluation of `agent-heldout-FINV2-r3` (heldout, n=65)

Gold was AI-drafted; 0/65 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.723 [0.615, 0.831] (n=65) |
| false_answer_rate | 0.0 [0.0, 0.0] (n=52) |
| over_abstention_rate | 0.2 [0.108, 0.292] (n=65) |
| key_number_recall | 0.733 [0.6, 0.844] (n=45) |
| calc_correct | 0.5 [0.0, 1.0] (n=4) |
| gold_cited_any | 0.604 [0.458, 0.729] (n=48) |
| cases_with_ungrounded_numbers | 0.015 [0.0, 0.046] (n=65) |
| answers_with_ungrounded_numbers | 0.015 [0.0, 0.046] (n=65) |
| claims_judged | 50 |
| claim_supported_rate | 0.9 [0.795, 0.981] (n=50) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=50) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=35) |
| fact_coverage | 0.84 [0.737, 0.94] (n=50) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=35) |
| latency_p50_s | 16.1 |
| latency_p95_s | 34.2 |
| cost_per_case_usd | 0.00502 |
| judge_cost_total_usd | 0.0424 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.875 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.6 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.909 | 0 | 2 | 0 | 0 |
| numerical_comparison | 14 | 0.214 | 0 | 11 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.708 [0.6, 0.815] (n=65) |
| false_answer_rate | 0.0 [0.0, 0.0] (n=49) |
| over_abstention_rate | 0.246 [0.154, 0.354] (n=65) |
| key_number_recall | 0.667 [0.533, 0.793] (n=45) |
| calc_correct | 0.5 [0.0, 1.0] (n=4) |
| gold_cited_any | 0.583 [0.438, 0.729] (n=48) |
| cases_with_ungrounded_numbers | 0.0 [0.0, 0.0] (n=65) |
| answers_with_ungrounded_numbers | 0.0 [0.0, 0.0] (n=65) |
| claims_judged | 44 |
| claim_supported_rate | 0.955 [0.889, 1.0] (n=44) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=44) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=32) |
| fact_coverage | 0.66 [0.551, 0.8] (n=47) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=32) |
| latency_p50_s | 16.8 |
| latency_p95_s | 34.0 |
| cost_per_case_usd | 0.0031 |
| judge_cost_total_usd | 0.0384 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.75 | 0 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.8 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.818 | 0 | 4 | 0 | 0 |
| numerical_comparison | 14 | 0.214 | 0 | 11 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

