# Evaluation of `agent-heldout-H-hybrid` (heldout, n=31)

Gold was AI-drafted; 31/31 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-4.1-mini

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.581 [0.387, 0.742] (n=31) |
| false_answer_rate | 0.048 [0.0, 0.143] (n=21) |
| over_abstention_rate | 0.323 [0.161, 0.516] (n=31) |
| key_number_recall | 0.468 [0.288, 0.653] (n=19) |
| calc_correct | 0.4 [0.0, 0.8] (n=5) |
| gold_cited_any | 0.345 [0.172, 0.517] (n=29) |
| cases_with_ungrounded_numbers | 0.0 [0.0, 0.0] (n=31) |
| answers_with_ungrounded_numbers | 0.0 [0.0, 0.0] (n=31) |
| claims_judged | 28 |
| claim_supported_rate | 1.0 [1.0, 1.0] (n=28) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=28) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=15) |
| fact_coverage | 0.438 [0.2, 0.688] (n=16) |
| answers_contradicting_a_reference_fact | 0.067 [0.0, 0.2] (n=15) |
| latency_p50_s | 5.9 |
| latency_p95_s | 9.0 |
| cost_per_case_usd | 0.00423 |
| judge_cost_total_usd | 0.0189 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.4 | 0 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.5 | 1 | 1 | 0 | 0 |
| cross_source_synthesis | 5 | 0.6 | 0 | 2 | 0 | 0 |
| factual_lookup | 5 | 0.8 | 0 | 1 | 0 | 0 |
| numerical_comparison | 6 | 0.667 | 0 | 2 | 0 | 0 |
| revision_conflict | 4 | 0.5 | 0 | 2 | 0 | 1 |

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.742 [0.581, 0.903] (n=31) |
| false_answer_rate | 0.0 [0.0, 0.0] (n=25) |
| over_abstention_rate | 0.194 [0.065, 0.323] (n=31) |
| key_number_recall | 0.646 [0.46, 0.828] (n=19) |
| calc_correct | 0.8 [0.4, 1.0] (n=5) |
| gold_cited_any | 0.414 [0.241, 0.586] (n=29) |
| cases_with_ungrounded_numbers | 0.032 [0.0, 0.097] (n=31) |
| answers_with_ungrounded_numbers | 0.032 [0.0, 0.097] (n=31) |
| claims_judged | 39 |
| claim_supported_rate | 0.846 [0.725, 0.95] (n=39) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=39) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=18) |
| fact_coverage | 0.524 [0.316, 0.727] (n=21) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=18) |
| latency_p50_s | 11.1 |
| latency_p95_s | 19.7 |
| cost_per_case_usd | 0.00271 |
| judge_cost_total_usd | 0.0228 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.6 | 0 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.833 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 5 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 5 | 0.8 | 0 | 1 | 0 | 0 |
| numerical_comparison | 6 | 1.0 | 0 | 0 | 0 | 0 |
| revision_conflict | 4 | 0.0 | 0 | 4 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.71 [0.548, 0.839] (n=31) |
| false_answer_rate | 0.0 [0.0, 0.0] (n=24) |
| over_abstention_rate | 0.226 [0.097, 0.387] (n=31) |
| key_number_recall | 0.646 [0.47, 0.811] (n=19) |
| calc_correct | 0.8 [0.4, 1.0] (n=5) |
| gold_cited_any | 0.448 [0.276, 0.621] (n=29) |
| cases_with_ungrounded_numbers | 0.0 [0.0, 0.0] (n=31) |
| answers_with_ungrounded_numbers | 0.0 [0.0, 0.0] (n=31) |
| claims_judged | 33 |
| claim_supported_rate | 1.0 [1.0, 1.0] (n=33) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=33) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=17) |
| fact_coverage | 0.591 [0.412, 0.81] (n=22) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=17) |
| latency_p50_s | 12.7 |
| latency_p95_s | 18.5 |
| cost_per_case_usd | 0.00124 |
| judge_cost_total_usd | 0.0236 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.4 | 0 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.833 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 5 | 0.8 | 0 | 1 | 0 | 0 |
| factual_lookup | 5 | 0.6 | 0 | 2 | 0 | 0 |
| numerical_comparison | 6 | 1.0 | 0 | 0 | 0 | 0 |
| revision_conflict | 4 | 0.5 | 0 | 2 | 0 | 0 |

