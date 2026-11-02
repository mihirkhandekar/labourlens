# Evaluation of `agent-heldout-FIN2V2-hybrid` (heldout, n=65)

Gold was AI-drafted; 0/65 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.754 [0.646, 0.846] (n=65) |
| false_answer_rate | 0.019 [0.0, 0.057] (n=53) |
| over_abstention_rate | 0.185 [0.092, 0.277] (n=65) |
| key_number_recall | 0.748 [0.622, 0.859] (n=45) |
| calc_correct | 0.5 [0.0, 1.0] (n=4) |
| gold_cited_any | 0.604 [0.458, 0.729] (n=48) |
| cases_with_ungrounded_numbers | 0.031 [0.0, 0.077] (n=65) |
| answers_with_ungrounded_numbers | 0.031 [0.0, 0.077] (n=65) |
| claims_judged | 62 |
| claim_supported_rate | 0.839 [0.708, 0.943] (n=62) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=62) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=37) |
| fact_coverage | 0.843 [0.75, 0.935] (n=51) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=36) |
| latency_p50_s | 10.0 |
| latency_p95_s | 19.4 |
| cost_per_case_usd | 0.00348 |
| judge_cost_total_usd | 0.0479 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.875 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.7 | 1 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.955 | 0 | 1 | 0 | 0 |
| numerical_comparison | 14 | 0.214 | 0 | 11 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.738 [0.631, 0.846] (n=65) |
| false_answer_rate | 0.019 [0.0, 0.058] (n=52) |
| over_abstention_rate | 0.2 [0.108, 0.292] (n=65) |
| key_number_recall | 0.696 [0.559, 0.822] (n=45) |
| calc_correct | 0.5 [0.0, 1.0] (n=4) |
| gold_cited_any | 0.542 [0.396, 0.667] (n=48) |
| cases_with_ungrounded_numbers | 0.046 [0.0, 0.108] (n=65) |
| answers_with_ungrounded_numbers | 0.046 [0.0, 0.108] (n=65) |
| claims_judged | 50 |
| claim_supported_rate | 0.98 [0.93, 1.0] (n=50) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=50) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=36) |
| fact_coverage | 0.7 [0.586, 0.841] (n=50) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=35) |
| latency_p50_s | 11.5 |
| latency_p95_s | 19.6 |
| cost_per_case_usd | 0.00167 |
| judge_cost_total_usd | 0.0431 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.75 | 0 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.7 | 1 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.955 | 0 | 1 | 0 | 0 |
| numerical_comparison | 14 | 0.214 | 0 | 11 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

