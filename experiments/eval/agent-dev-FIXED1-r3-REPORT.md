# Evaluation of `agent-dev-FIXED1-r3` (dev, n=237)

Gold was AI-drafted; 237/237 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.814 [0.764, 0.865] (n=237) |
| false_answer_rate | 0.053 [0.024, 0.087] (n=206) |
| over_abstention_rate | 0.131 [0.089, 0.173] (n=237) |
| key_number_recall | 0.741 [0.681, 0.802] (n=153) |
| calc_correct | 0.0 [0.0, 0.0] (n=24) |
| gold_cited_any | 0.725 [0.661, 0.783] (n=189) |
| cases_with_ungrounded_numbers | 0.076 [0.046, 0.114] (n=237) |
| answers_with_ungrounded_numbers | 0.076 [0.046, 0.114] (n=237) |
| claims_judged | 288 |
| claim_supported_rate | 0.795 [0.741, 0.848] (n=288) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=288) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=162) |
| fact_coverage | 0.731 [0.669, 0.789] (n=242) |
| answers_contradicting_a_reference_fact | 0.033 [0.007, 0.066] (n=151) |
| latency_p50_s | 15.3 |
| latency_p95_s | 28.3 |
| cost_per_case_usd | 0.0027 |
| judge_cost_total_usd | 0.2364 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.943 | 1 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.795 | 5 | 2 | 0 | 3 |
| cross_source_synthesis | 35 | 0.943 | 0 | 2 | 0 | 1 |
| factual_lookup | 70 | 0.914 | 3 | 3 | 0 | 0 |
| numerical_comparison | 34 | 0.324 | 2 | 21 | 0 | 0 |
| revision_conflict | 19 | 0.895 | 0 | 2 | 0 | 3 |

