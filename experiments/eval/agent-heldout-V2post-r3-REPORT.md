# Evaluation of `agent-heldout-V2post-r3` (heldout, n=65)

Gold was AI-drafted; 0/65 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.846 [0.754, 0.923] (n=65) |
| false_answer_rate | 0.0 [0.0, 0.0] (n=58) |
| over_abstention_rate | 0.108 [0.046, 0.185] (n=65) |
| key_number_recall | 0.841 [0.737, 0.933] (n=45) |
| calc_correct | 1.0 [1.0, 1.0] (n=4) |
| gold_cited_any | 0.667 [0.521, 0.792] (n=48) |
| cases_with_ungrounded_numbers | 0.046 [0.0, 0.108] (n=65) |
| answers_with_ungrounded_numbers | 0.046 [0.0, 0.108] (n=65) |
| claims_judged | 57 |
| claim_supported_rate | 0.895 [0.797, 0.978] (n=57) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=57) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=41) |
| fact_coverage | 0.855 [0.762, 0.947] (n=62) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=41) |
| latency_p50_s | 12.8 |
| latency_p95_s | 33.0 |
| cost_per_case_usd | 0.00491 |
| judge_cost_total_usd | 0.0476 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.875 | 0 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.7 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.909 | 0 | 2 | 0 | 0 |
| numerical_comparison | 14 | 0.714 | 0 | 4 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.908 [0.831, 0.969] (n=65) |
| false_answer_rate | 0.0 [0.0, 0.0] (n=62) |
| over_abstention_rate | 0.046 [0.0, 0.108] (n=65) |
| key_number_recall | 0.844 [0.75, 0.928] (n=45) |
| calc_correct | 1.0 [1.0, 1.0] (n=4) |
| gold_cited_any | 0.75 [0.625, 0.875] (n=48) |
| cases_with_ungrounded_numbers | 0.015 [0.0, 0.046] (n=65) |
| answers_with_ungrounded_numbers | 0.015 [0.0, 0.046] (n=65) |
| claims_judged | 58 |
| claim_supported_rate | 0.897 [0.806, 0.981] (n=58) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=58) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=45) |
| fact_coverage | 0.766 [0.662, 0.87] (n=64) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=45) |
| latency_p50_s | 14.7 |
| latency_p95_s | 38.1 |
| cost_per_case_usd | 0.0032 |
| judge_cost_total_usd | 0.0554 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.875 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.8 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.955 | 0 | 1 | 0 | 0 |
| numerical_comparison | 14 | 0.857 | 0 | 2 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

