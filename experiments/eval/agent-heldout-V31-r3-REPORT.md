# Evaluation of `agent-heldout-V31-r3` (heldout, n=65)

Gold was AI-drafted; 0/65 cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. The judge is AI-produced. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.769 [0.662, 0.862] (n=65) |
| false_answer_rate | 0.0 [0.0, 0.0] (n=52) |
| over_abstention_rate | 0.2 [0.108, 0.292] (n=65) |
| key_number_recall | 0.737 [0.607, 0.852] (n=45) |
| calc_correct | 0.5 [0.0, 1.0] (n=4) |
| gold_cited_any | 0.583 [0.438, 0.708] (n=48) |
| cases_with_ungrounded_numbers | 0.062 [0.015, 0.123] (n=65) |
| answers_with_ungrounded_numbers | 0.062 [0.015, 0.123] (n=65) |
| claims_judged | 53 |
| claim_supported_rate | 0.906 [0.812, 0.98] (n=53) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=53) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=35) |
| fact_coverage | 0.84 [0.735, 0.941] (n=50) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=35) |
| latency_p50_s | 15.7 |
| latency_p95_s | 34.2 |
| cost_per_case_usd | 0.00507 |
| judge_cost_total_usd | 0.0436 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 1.0 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.8 | 0 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.909 | 0 | 2 | 0 | 0 |
| numerical_comparison | 14 | 0.214 | 0 | 11 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 65 |
| behaviour_accuracy | 0.738 [0.631, 0.831] (n=65) |
| false_answer_rate | 0.019 [0.0, 0.058] (n=52) |
| over_abstention_rate | 0.2 [0.108, 0.308] (n=65) |
| key_number_recall | 0.674 [0.537, 0.8] (n=45) |
| calc_correct | 0.5 [0.0, 1.0] (n=4) |
| gold_cited_any | 0.625 [0.479, 0.75] (n=48) |
| cases_with_ungrounded_numbers | 0.0 [0.0, 0.0] (n=65) |
| answers_with_ungrounded_numbers | 0.0 [0.0, 0.0] (n=65) |
| claims_judged | 49 |
| claim_supported_rate | 0.898 [0.818, 0.976] (n=49) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=49) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=36) |
| fact_coverage | 0.74 [0.622, 0.872] (n=50) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=35) |
| latency_p50_s | 17.6 |
| latency_p95_s | 34.2 |
| cost_per_case_usd | 0.00309 |
| judge_cost_total_usd | 0.0463 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 8 | 0.875 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 10 | 0.7 | 1 | 0 | 0 | 0 |
| cross_source_synthesis | 8 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 22 | 0.909 | 0 | 2 | 0 | 0 |
| numerical_comparison | 14 | 0.214 | 0 | 11 | 0 | 0 |
| revision_conflict | 3 | 1.0 | 0 | 0 | 0 | 0 |

