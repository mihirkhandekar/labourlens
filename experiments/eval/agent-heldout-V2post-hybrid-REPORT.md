# Evaluation of `agent-heldout-V2post-hybrid` (heldout, n=65)

Gold was AI-drafted; 0/65 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.815 [0.723, 0.908] (n=65) |
| false_answer_rate | 0.034 [0.0, 0.086] (n=58) |
| over_abstention_rate | 0.108 [0.031, 0.185] (n=65) |
| key_number_recall | 0.83 [0.722, 0.922] (n=45) |
| calc_correct | 1.0 [1.0, 1.0] (n=4) |
| gold_cited_any | 0.667 [0.521, 0.792] (n=48) |
| cases_with_ungrounded_numbers | 0.092 [0.031, 0.169] (n=65) |
| answers_with_ungrounded_numbers | 0.092 [0.031, 0.169] (n=65) |
| claims_judged | 67 |
| claim_supported_rate | 0.836 [0.691, 0.958] (n=67) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=67) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=43) |
| fact_coverage | 0.887 [0.794, 0.966] (n=62) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=41) |
| latency_p50_s | 10.5 |
| latency_p95_s | 23.8 |
| cost_per_case_usd | 0.00392 |
| judge_cost_total_usd | 0.0528 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.875 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.6 | 2 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.909 | 0 | 2 | 0 | 0 |
| numerical_comparison | 14 | 0.643 | 0 | 5 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.877 [0.785, 0.954] (n=65) |
| false_answer_rate | 0.016 [0.0, 0.049] (n=61) |
| over_abstention_rate | 0.062 [0.015, 0.123] (n=65) |
| key_number_recall | 0.856 [0.761, 0.935] (n=45) |
| calc_correct | 1.0 [1.0, 1.0] (n=4) |
| gold_cited_any | 0.688 [0.542, 0.812] (n=48) |
| cases_with_ungrounded_numbers | 0.046 [0.0, 0.108] (n=65) |
| answers_with_ungrounded_numbers | 0.046 [0.0, 0.108] (n=65) |
| claims_judged | 65 |
| claim_supported_rate | 0.938 [0.865, 0.988] (n=65) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=65) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=45) |
| fact_coverage | 0.769 [0.667, 0.885] (n=65) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=44) |
| latency_p50_s | 10.5 |
| latency_p95_s | 21.7 |
| cost_per_case_usd | 0.00181 |
| judge_cost_total_usd | 0.0537 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.875 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.7 | 1 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.909 | 0 | 2 | 0 | 0 |
| numerical_comparison | 14 | 0.857 | 0 | 2 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

