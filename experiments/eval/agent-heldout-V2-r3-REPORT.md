# Evaluation of `agent-heldout-V2-r3` (heldout, n=65)

Gold was AI-drafted; 0/65 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.723 [0.615, 0.815] (n=65) |
| false_answer_rate | 0.0 [0.0, 0.0] (n=51) |
| over_abstention_rate | 0.215 [0.123, 0.308] (n=65) |
| key_number_recall | 0.707 [0.574, 0.83] (n=45) |
| calc_correct | 0.5 [0.0, 1.0] (n=4) |
| gold_cited_any | 0.583 [0.438, 0.729] (n=48) |
| cases_with_ungrounded_numbers | 0.077 [0.015, 0.154] (n=65) |
| answers_with_ungrounded_numbers | 0.077 [0.015, 0.154] (n=65) |
| claims_judged | 53 |
| claim_supported_rate | 0.906 [0.83, 0.979] (n=53) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=53) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=34) |
| fact_coverage | 0.796 [0.667, 0.929] (n=49) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=34) |
| latency_p50_s | 16.5 |
| latency_p95_s | 31.4 |
| cost_per_case_usd | 0.00485 |
| judge_cost_total_usd | 0.0456 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.875 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.7 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.864 | 0 | 3 | 0 | 0 |
| numerical_comparison | 14 | 0.214 | 0 | 11 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.754 [0.646, 0.846] (n=65) |
| false_answer_rate | 0.0 [0.0, 0.0] (n=52) |
| over_abstention_rate | 0.2 [0.108, 0.292] (n=65) |
| key_number_recall | 0.707 [0.57, 0.83] (n=45) |
| calc_correct | 0.5 [0.0, 1.0] (n=4) |
| gold_cited_any | 0.583 [0.438, 0.708] (n=48) |
| cases_with_ungrounded_numbers | 0.031 [0.0, 0.077] (n=65) |
| answers_with_ungrounded_numbers | 0.031 [0.0, 0.077] (n=65) |
| claims_judged | 46 |
| claim_supported_rate | 0.935 [0.86, 1.0] (n=46) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=46) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=35) |
| fact_coverage | 0.78 [0.673, 0.898] (n=50) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=35) |
| latency_p50_s | 18.7 |
| latency_p95_s | 37.7 |
| cost_per_case_usd | 0.00334 |
| judge_cost_total_usd | 0.0426 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.875 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.8 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.909 | 0 | 2 | 0 | 0 |
| numerical_comparison | 14 | 0.214 | 0 | 11 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

