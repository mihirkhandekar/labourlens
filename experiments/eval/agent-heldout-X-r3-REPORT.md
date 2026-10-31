# Evaluation of `agent-heldout-X-r3` (heldout, n=31)

Gold was AI-drafted; 31/31 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.839 [0.71, 0.968] (n=31) |
| false_answer_rate | 0.036 [0.0, 0.107] (n=28) |
| over_abstention_rate | 0.097 [0.0, 0.194] (n=31) |
| key_number_recall | 0.858 [0.716, 0.972] (n=19) |
| calc_correct | 1.0 [1.0, 1.0] (n=5) |
| gold_cited_any | 0.552 [0.379, 0.724] (n=29) |
| cases_with_ungrounded_numbers | 0.032 [0.0, 0.097] (n=31) |
| answers_with_ungrounded_numbers | 0.032 [0.0, 0.097] (n=31) |
| claims_judged | 45 |
| claim_supported_rate | 0.822 [0.659, 0.945] (n=45) |
| claim_unsupported_rate | 0.022 [0.0, 0.07] (n=45) |
| answers_with_any_unsupported_claim | 0.045 [0.0, 0.136] (n=22) |
| fact_coverage | 0.667 [0.464, 0.857] (n=24) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=21) |
| latency_p50_s | 13.6 |
| latency_p95_s | 31.8 |
| cost_per_case_usd | 0.00392 |
| judge_cost_total_usd | 0.0286 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.4 | 1 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.833 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 5 | 1.0 | 0 | 0 | 1 | 0 |
| factual_lookup | 5 | 1.0 | 0 | 0 | 0 | 0 |
| numerical_comparison | 6 | 1.0 | 0 | 0 | 0 | 0 |
| revision_conflict | 4 | 0.75 | 0 | 1 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.839 [0.71, 0.968] (n=31) |
| false_answer_rate | 0.0 [0.0, 0.0] (n=28) |
| over_abstention_rate | 0.097 [0.0, 0.194] (n=31) |
| key_number_recall | 0.777 [0.611, 0.918] (n=19) |
| calc_correct | 1.0 [1.0, 1.0] (n=5) |
| gold_cited_any | 0.621 [0.448, 0.793] (n=29) |
| cases_with_ungrounded_numbers | 0.032 [0.0, 0.097] (n=31) |
| answers_with_ungrounded_numbers | 0.032 [0.0, 0.097] (n=31) |
| claims_judged | 34 |
| claim_supported_rate | 0.912 [0.769, 1.0] (n=34) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=34) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=21) |
| fact_coverage | 0.625 [0.423, 0.826] (n=24) |
| answers_contradicting_a_reference_fact | 0.048 [0.0, 0.143] (n=21) |
| latency_p50_s | 17.6 |
| latency_p95_s | 43.3 |
| cost_per_case_usd | 0.00268 |
| judge_cost_total_usd | 0.027 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.4 | 0 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.833 | 0 | 0 | 0 | 1 |
| cross_source_synthesis | 5 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 5 | 1.0 | 0 | 0 | 0 | 0 |
| numerical_comparison | 6 | 1.0 | 0 | 0 | 0 | 0 |
| revision_conflict | 4 | 0.75 | 0 | 1 | 0 | 0 |

