# Evaluation of `agent-dev-A3` (dev, n=237)

Gold labels and the judge are AI-produced; nothing here is human-reviewed. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.907 [0.869, 0.945] (n=237) |
| false_answer_rate | 0.009 [0.0, 0.022] (n=227) |
| over_abstention_rate | 0.042 [0.017, 0.068] (n=237) |
| key_number_recall | 0.835 [0.786, 0.88] (n=160) |
| calc_correct | 0.875 [0.75, 1.0] (n=24) |
| gold_cited_any | 0.828 [0.773, 0.884] (n=198) |
| answers_with_ungrounded_numbers | 0.051 [0.025, 0.08] (n=237) |
| claims_judged | 364 |
| claim_supported_rate | 0.874 [0.833, 0.914] (n=364) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=364) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=183) |
| fact_coverage | 0.77 [0.721, 0.817] (n=317) |
| answers_contradicting_a_reference_fact | 0.005 [0.0, 0.016] (n=183) |
| latency_p50_s | 15.5 |
| latency_p95_s | 34.4 |
| cost_per_case_usd | 0.0036 |
| judge_cost_total_usd | 0.2599 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.971 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.75 | 2 | 0 | 0 | 0 |
| cross_source_synthesis | 35 | 0.971 | 0 | 1 | 0 | 0 |
| factual_lookup | 70 | 0.929 | 0 | 5 | 0 | 0 |
| numerical_comparison | 34 | 0.882 | 0 | 4 | 0 | 0 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 0 | 2 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.89 [0.848, 0.928] (n=237) |
| false_answer_rate | 0.018 [0.004, 0.036] (n=224) |
| over_abstention_rate | 0.055 [0.03, 0.084] (n=237) |
| key_number_recall | 0.798 [0.744, 0.848] (n=160) |
| calc_correct | 0.875 [0.75, 1.0] (n=24) |
| gold_cited_any | 0.808 [0.753, 0.864] (n=198) |
| answers_with_ungrounded_numbers | 0.076 [0.042, 0.11] (n=237) |
| claims_judged | 309 |
| claim_supported_rate | 0.883 [0.839, 0.926] (n=309) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=309) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=182) |
| fact_coverage | 0.725 [0.677, 0.774] (n=313) |
| answers_contradicting_a_reference_fact | 0.005 [0.0, 0.016] (n=182) |
| latency_p50_s | 15.4 |
| latency_p95_s | 35.6 |
| cost_per_case_usd | 0.00212 |
| judge_cost_total_usd | 0.2456 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.914 | 0 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.727 | 4 | 0 | 0 | 0 |
| cross_source_synthesis | 35 | 0.943 | 0 | 2 | 0 | 1 |
| factual_lookup | 70 | 0.929 | 0 | 5 | 0 | 0 |
| numerical_comparison | 34 | 0.882 | 0 | 4 | 0 | 0 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 0 | 0 |

