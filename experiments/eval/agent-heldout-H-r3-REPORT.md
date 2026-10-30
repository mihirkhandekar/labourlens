# Evaluation of `agent-heldout-H-r3` (heldout, n=31)

Gold labels and the judge are AI-produced; nothing here is human-reviewed. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-4.1-mini

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.71 [0.548, 0.871] (n=31) |
| false_answer_rate | 0.115 [0.0, 0.269] (n=26) |
| over_abstention_rate | 0.161 [0.032, 0.29] (n=31) |
| key_number_recall | 0.56 [0.365, 0.754] (n=19) |
| calc_correct | 0.4 [0.0, 0.8] (n=5) |
| gold_cited_any | 0.517 [0.345, 0.69] (n=29) |
| cases_with_ungrounded_numbers | 0.065 [0.0, 0.161] (n=31) |
| answers_with_ungrounded_numbers | 0.065 [0.0, 0.161] (n=31) |
| claims_judged | 62 |
| claim_supported_rate | 0.952 [0.868, 1.0] (n=62) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=62) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=22) |
| fact_coverage | 0.462 [0.273, 0.636] (n=26) |
| answers_contradicting_a_reference_fact | 0.045 [0.0, 0.136] (n=22) |
| latency_p50_s | 7.3 |
| latency_p95_s | 21.6 |
| cost_per_case_usd | 0.00496 |
| judge_cost_total_usd | 0.0304 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.6 | 0 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.333 | 3 | 0 | 0 | 0 |
| cross_source_synthesis | 5 | 0.8 | 0 | 1 | 0 | 0 |
| factual_lookup | 5 | 1.0 | 0 | 0 | 0 | 0 |
| numerical_comparison | 6 | 0.667 | 0 | 2 | 0 | 0 |
| revision_conflict | 4 | 1.0 | 0 | 0 | 0 | 1 |

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.839 [0.71, 0.968] (n=31) |
| false_answer_rate | 0.069 [0.0, 0.172] (n=29) |
| over_abstention_rate | 0.065 [0.0, 0.161] (n=31) |
| key_number_recall | 0.832 [0.674, 0.965] (n=19) |
| calc_correct | 0.8 [0.4, 1.0] (n=5) |
| gold_cited_any | 0.69 [0.517, 0.862] (n=29) |
| cases_with_ungrounded_numbers | 0.032 [0.0, 0.097] (n=31) |
| answers_with_ungrounded_numbers | 0.032 [0.0, 0.097] (n=31) |
| claims_judged | 45 |
| claim_supported_rate | 0.911 [0.783, 1.0] (n=45) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=45) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=24) |
| fact_coverage | 0.769 [0.607, 0.917] (n=26) |
| answers_contradicting_a_reference_fact | 0.042 [0.0, 0.125] (n=24) |
| latency_p50_s | 17.3 |
| latency_p95_s | 36.1 |
| cost_per_case_usd | 0.00343 |
| judge_cost_total_usd | 0.0295 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.8 | 0 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.5 | 2 | 0 | 0 | 1 |
| cross_source_synthesis | 5 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 5 | 1.0 | 0 | 0 | 0 | 0 |
| numerical_comparison | 6 | 1.0 | 0 | 0 | 0 | 0 |
| revision_conflict | 4 | 0.75 | 0 | 1 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.839 [0.71, 0.968] (n=31) |
| false_answer_rate | 0.036 [0.0, 0.107] (n=28) |
| over_abstention_rate | 0.097 [0.0, 0.226] (n=31) |
| key_number_recall | 0.716 [0.546, 0.872] (n=19) |
| calc_correct | 0.8 [0.4, 1.0] (n=5) |
| gold_cited_any | 0.621 [0.448, 0.793] (n=29) |
| cases_with_ungrounded_numbers | 0.065 [0.0, 0.161] (n=31) |
| answers_with_ungrounded_numbers | 0.065 [0.0, 0.161] (n=31) |
| claims_judged | 39 |
| claim_supported_rate | 0.897 [0.778, 1.0] (n=39) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=39) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=22) |
| fact_coverage | 0.667 [0.458, 0.833] (n=24) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=22) |
| latency_p50_s | 14.0 |
| latency_p95_s | 26.6 |
| cost_per_case_usd | 0.00193 |
| judge_cost_total_usd | 0.0273 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.6 | 0 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.667 | 1 | 0 | 0 | 0 |
| cross_source_synthesis | 5 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 5 | 1.0 | 0 | 0 | 0 | 0 |
| numerical_comparison | 6 | 1.0 | 0 | 0 | 0 | 0 |
| revision_conflict | 4 | 0.75 | 0 | 1 | 0 | 0 |

