# Evaluation of `agent-heldout-X-hybrid` (heldout, n=31)

Gold was AI-drafted; 31/31 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.742 [0.581, 0.871] (n=31) |
| false_answer_rate | 0.04 [0.0, 0.12] (n=25) |
| over_abstention_rate | 0.194 [0.065, 0.355] (n=31) |
| key_number_recall | 0.644 [0.47, 0.821] (n=19) |
| calc_correct | 1.0 [1.0, 1.0] (n=5) |
| gold_cited_any | 0.448 [0.276, 0.621] (n=29) |
| cases_with_ungrounded_numbers | 0.032 [0.0, 0.097] (n=31) |
| answers_with_ungrounded_numbers | 0.032 [0.0, 0.097] (n=31) |
| claims_judged | 40 |
| claim_supported_rate | 0.8 [0.651, 0.93] (n=40) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=40) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=19) |
| fact_coverage | 0.667 [0.45, 0.85] (n=21) |
| answers_contradicting_a_reference_fact | 0.056 [0.0, 0.167] (n=18) |
| latency_p50_s | 9.9 |
| latency_p95_s | 17.4 |
| cost_per_case_usd | 0.00359 |
| judge_cost_total_usd | 0.0242 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.6 | 1 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.833 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 5 | 0.8 | 0 | 1 | 0 | 0 |
| factual_lookup | 5 | 0.8 | 0 | 1 | 0 | 0 |
| numerical_comparison | 6 | 1.0 | 0 | 0 | 0 | 0 |
| revision_conflict | 4 | 0.25 | 0 | 3 | 0 | 1 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.774 [0.613, 0.903] (n=31) |
| false_answer_rate | 0.038 [0.0, 0.115] (n=26) |
| over_abstention_rate | 0.161 [0.032, 0.29] (n=31) |
| key_number_recall | 0.66 [0.456, 0.842] (n=19) |
| calc_correct | 1.0 [1.0, 1.0] (n=5) |
| gold_cited_any | 0.517 [0.345, 0.69] (n=29) |
| cases_with_ungrounded_numbers | 0.032 [0.0, 0.097] (n=31) |
| answers_with_ungrounded_numbers | 0.032 [0.0, 0.097] (n=31) |
| claims_judged | 34 |
| claim_supported_rate | 0.882 [0.742, 1.0] (n=34) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=34) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=20) |
| fact_coverage | 0.696 [0.5, 0.857] (n=23) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=19) |
| latency_p50_s | 11.5 |
| latency_p95_s | 25.5 |
| cost_per_case_usd | 0.00168 |
| judge_cost_total_usd | 0.0241 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.6 | 1 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.833 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 5 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 5 | 0.8 | 0 | 1 | 0 | 0 |
| numerical_comparison | 6 | 1.0 | 0 | 0 | 0 | 0 |
| revision_conflict | 4 | 0.25 | 0 | 3 | 0 | 0 |

