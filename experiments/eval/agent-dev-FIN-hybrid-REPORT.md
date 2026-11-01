# Evaluation of `agent-dev-FIN-hybrid` (dev, n=237)

Gold was AI-drafted; 237/237 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.84 [0.793, 0.886] (n=237) |
| false_answer_rate | 0.033 [0.009, 0.06] (n=215) |
| over_abstention_rate | 0.093 [0.059, 0.131] (n=237) |
| key_number_recall | 0.786 [0.736, 0.84] (n=153) |
| calc_correct | 0.667 [0.458, 0.833] (n=24) |
| gold_cited_any | 0.677 [0.614, 0.741] (n=189) |
| cases_with_ungrounded_numbers | 0.156 [0.11, 0.203] (n=237) |
| answers_with_ungrounded_numbers | 0.156 [0.11, 0.203] (n=237) |
| claims_judged | 328 |
| claim_supported_rate | 0.753 [0.694, 0.809] (n=328) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=328) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=167) |
| fact_coverage | 0.7 [0.643, 0.753] (n=283) |
| answers_contradicting_a_reference_fact | 0.025 [0.006, 0.05] (n=160) |
| latency_p50_s | 9.3 |
| latency_p95_s | 19.9 |
| cost_per_case_usd | 0.00355 |
| judge_cost_total_usd | 0.2497 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.914 | 1 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.795 | 2 | 0 | 0 | 3 |
| cross_source_synthesis | 35 | 0.886 | 0 | 4 | 0 | 1 |
| factual_lookup | 70 | 0.843 | 2 | 9 | 0 | 0 |
| numerical_comparison | 34 | 0.794 | 2 | 5 | 0 | 1 |
| revision_conflict | 19 | 0.789 | 0 | 4 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.844 [0.797, 0.89] (n=237) |
| false_answer_rate | 0.037 [0.014, 0.065] (n=216) |
| over_abstention_rate | 0.089 [0.055, 0.127] (n=237) |
| key_number_recall | 0.761 [0.703, 0.816] (n=153) |
| calc_correct | 0.667 [0.458, 0.833] (n=24) |
| gold_cited_any | 0.693 [0.63, 0.757] (n=189) |
| cases_with_ungrounded_numbers | 0.135 [0.093, 0.181] (n=237) |
| answers_with_ungrounded_numbers | 0.135 [0.093, 0.181] (n=237) |
| claims_judged | 291 |
| claim_supported_rate | 0.784 [0.723, 0.847] (n=291) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=291) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=169) |
| fact_coverage | 0.661 [0.608, 0.714] (n=286) |
| answers_contradicting_a_reference_fact | 0.012 [0.0, 0.031] (n=161) |
| latency_p50_s | 9.9 |
| latency_p95_s | 23.9 |
| cost_per_case_usd | 0.00172 |
| judge_cost_total_usd | 0.2474 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.886 | 1 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.75 | 4 | 0 | 0 | 2 |
| cross_source_synthesis | 35 | 0.914 | 0 | 3 | 0 | 0 |
| factual_lookup | 70 | 0.871 | 1 | 8 | 0 | 0 |
| numerical_comparison | 34 | 0.794 | 2 | 5 | 0 | 0 |
| revision_conflict | 19 | 0.842 | 0 | 3 | 0 | 0 |

