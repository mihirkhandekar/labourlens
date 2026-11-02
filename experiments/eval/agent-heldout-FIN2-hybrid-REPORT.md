# Evaluation of `agent-heldout-FIN2-hybrid` (heldout, n=31)

Gold was AI-drafted; 31/31 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.806 [0.645, 0.935] (n=31) |
| false_answer_rate | 0.037 [0.0, 0.111] (n=27) |
| over_abstention_rate | 0.129 [0.032, 0.258] (n=31) |
| key_number_recall | 0.779 [0.628, 0.918] (n=19) |
| calc_correct | 1.0 [1.0, 1.0] (n=5) |
| gold_cited_any | 0.552 [0.379, 0.724] (n=29) |
| cases_with_ungrounded_numbers | 0.129 [0.032, 0.258] (n=31) |
| answers_with_ungrounded_numbers | 0.129 [0.032, 0.258] (n=31) |
| claims_judged | 48 |
| claim_supported_rate | 0.854 [0.708, 0.976] (n=48) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=48) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=21) |
| fact_coverage | 0.8 [0.65, 0.929] (n=25) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=20) |
| latency_p50_s | 10.6 |
| latency_p95_s | 24.1 |
| cost_per_case_usd | 0.00366 |
| judge_cost_total_usd | 0.0271 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.6 | 1 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.833 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 5 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 5 | 0.8 | 0 | 1 | 0 | 0 |
| numerical_comparison | 6 | 1.0 | 0 | 0 | 0 | 0 |
| revision_conflict | 4 | 0.5 | 0 | 2 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.774 [0.613, 0.903] (n=31) |
| false_answer_rate | 0.038 [0.0, 0.115] (n=26) |
| over_abstention_rate | 0.161 [0.032, 0.29] (n=31) |
| key_number_recall | 0.628 [0.433, 0.818] (n=19) |
| calc_correct | 1.0 [1.0, 1.0] (n=5) |
| gold_cited_any | 0.552 [0.379, 0.724] (n=29) |
| cases_with_ungrounded_numbers | 0.097 [0.0, 0.194] (n=31) |
| answers_with_ungrounded_numbers | 0.097 [0.0, 0.194] (n=31) |
| claims_judged | 34 |
| claim_supported_rate | 0.853 [0.677, 1.0] (n=34) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=34) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=20) |
| fact_coverage | 0.545 [0.333, 0.75] (n=22) |
| answers_contradicting_a_reference_fact | 0.053 [0.0, 0.158] (n=19) |
| latency_p50_s | 11.3 |
| latency_p95_s | 23.3 |
| cost_per_case_usd | 0.00153 |
| judge_cost_total_usd | 0.0279 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.4 | 1 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.833 | 0 | 0 | 0 | 1 |
| cross_source_synthesis | 5 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 5 | 1.0 | 0 | 0 | 0 | 0 |
| numerical_comparison | 6 | 1.0 | 0 | 0 | 0 | 0 |
| revision_conflict | 4 | 0.25 | 0 | 3 | 0 | 0 |

