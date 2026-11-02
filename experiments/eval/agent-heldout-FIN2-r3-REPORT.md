# Evaluation of `agent-heldout-FIN2-r3` (heldout, n=31)

Gold was AI-drafted; 31/31 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.839 [0.71, 0.968] (n=31) |
| false_answer_rate | 0.036 [0.0, 0.107] (n=28) |
| over_abstention_rate | 0.097 [0.0, 0.194] (n=31) |
| key_number_recall | 0.788 [0.604, 0.935] (n=19) |
| calc_correct | 1.0 [1.0, 1.0] (n=5) |
| gold_cited_any | 0.586 [0.414, 0.759] (n=29) |
| cases_with_ungrounded_numbers | 0.097 [0.0, 0.194] (n=31) |
| answers_with_ungrounded_numbers | 0.097 [0.0, 0.194] (n=31) |
| claims_judged | 46 |
| claim_supported_rate | 0.891 [0.756, 1.0] (n=46) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=46) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=22) |
| fact_coverage | 0.708 [0.517, 0.909] (n=24) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=21) |
| latency_p50_s | 15.4 |
| latency_p95_s | 29.4 |
| cost_per_case_usd | 0.00461 |
| judge_cost_total_usd | 0.0288 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.4 | 1 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.833 | 0 | 0 | 0 | 0 |
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
| over_abstention_rate | 0.097 [0.0, 0.194] (n=31) |
| key_number_recall | 0.823 [0.667, 0.963] (n=19) |
| calc_correct | 1.0 [1.0, 1.0] (n=5) |
| gold_cited_any | 0.586 [0.414, 0.759] (n=29) |
| cases_with_ungrounded_numbers | 0.097 [0.0, 0.194] (n=31) |
| answers_with_ungrounded_numbers | 0.097 [0.0, 0.194] (n=31) |
| claims_judged | 37 |
| claim_supported_rate | 0.838 [0.667, 0.972] (n=37) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=37) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=22) |
| fact_coverage | 0.667 [0.476, 0.864] (n=24) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=21) |
| latency_p50_s | 15.4 |
| latency_p95_s | 38.1 |
| cost_per_case_usd | 0.00273 |
| judge_cost_total_usd | 0.0282 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.4 | 1 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.833 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 5 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 5 | 1.0 | 0 | 0 | 0 | 0 |
| numerical_comparison | 6 | 1.0 | 0 | 0 | 0 | 0 |
| revision_conflict | 4 | 0.75 | 0 | 1 | 0 | 0 |

