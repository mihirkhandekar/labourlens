# Evaluation of `agent-heldout-FIN2V2-r3` (heldout, n=65)

Gold was AI-drafted; 0/65 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.738 [0.631, 0.831] (n=65) |
| false_answer_rate | 0.0 [0.0, 0.0] (n=53) |
| over_abstention_rate | 0.185 [0.092, 0.277] (n=65) |
| key_number_recall | 0.722 [0.589, 0.837] (n=45) |
| calc_correct | 0.5 [0.0, 1.0] (n=4) |
| gold_cited_any | 0.646 [0.5, 0.771] (n=48) |
| cases_with_ungrounded_numbers | 0.031 [0.0, 0.077] (n=65) |
| answers_with_ungrounded_numbers | 0.031 [0.0, 0.077] (n=65) |
| claims_judged | 50 |
| claim_supported_rate | 0.9 [0.792, 0.981] (n=50) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=50) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=36) |
| fact_coverage | 0.765 [0.655, 0.886] (n=51) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=36) |
| latency_p50_s | 15.2 |
| latency_p95_s | 27.6 |
| cost_per_case_usd | 0.00489 |
| judge_cost_total_usd | 0.0449 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.875 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.6 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.955 | 0 | 1 | 0 | 0 |
| numerical_comparison | 14 | 0.214 | 0 | 11 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.723 [0.615, 0.831] (n=65) |
| false_answer_rate | 0.0 [0.0, 0.0] (n=50) |
| over_abstention_rate | 0.231 [0.138, 0.338] (n=65) |
| key_number_recall | 0.674 [0.533, 0.8] (n=45) |
| calc_correct | 0.5 [0.0, 1.0] (n=4) |
| gold_cited_any | 0.625 [0.479, 0.75] (n=48) |
| cases_with_ungrounded_numbers | 0.0 [0.0, 0.0] (n=65) |
| answers_with_ungrounded_numbers | 0.0 [0.0, 0.0] (n=65) |
| claims_judged | 43 |
| claim_supported_rate | 0.93 [0.854, 1.0] (n=43) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=43) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=33) |
| fact_coverage | 0.729 [0.612, 0.857] (n=48) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=33) |
| latency_p50_s | 17.9 |
| latency_p95_s | 38.4 |
| cost_per_case_usd | 0.0034 |
| judge_cost_total_usd | 0.0425 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.875 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.8 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.818 | 0 | 4 | 0 | 0 |
| numerical_comparison | 14 | 0.214 | 0 | 11 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

