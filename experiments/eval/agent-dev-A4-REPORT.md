# Evaluation of `agent-dev-A4` (dev, n=237)

Gold labels and the judge are AI-produced; nothing here is human-reviewed. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.907 [0.869, 0.941] (n=237) |
| false_answer_rate | 0.009 [0.0, 0.022] (n=225) |
| over_abstention_rate | 0.051 [0.025, 0.08] (n=237) |
| key_number_recall | 0.843 [0.794, 0.891] (n=160) |
| calc_correct | 0.792 [0.625, 0.958] (n=24) |
| gold_cited_any | 0.818 [0.768, 0.874] (n=198) |
| answers_with_ungrounded_numbers | 0.059 [0.03, 0.093] (n=237) |
| claims_judged | 362 |
| claim_supported_rate | 0.887 [0.841, 0.929] (n=362) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=362) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=181) |
| fact_coverage | 0.77 [0.722, 0.818] (n=313) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=181) |
| latency_p50_s | 15.1 |
| latency_p95_s | 34.7 |
| cost_per_case_usd | 0.00367 |
| judge_cost_total_usd | 0.2481 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 1.0 | 0 | 0 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.773 | 2 | 0 | 0 | 0 |
| cross_source_synthesis | 35 | 0.971 | 0 | 1 | 0 | 0 |
| factual_lookup | 70 | 0.929 | 0 | 5 | 0 | 0 |
| numerical_comparison | 34 | 0.824 | 0 | 6 | 0 | 0 |
| revision_conflict | 19 | 1.0 | 0 | 0 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 237 |
| behaviour_accuracy | 0.886 [0.844, 0.924] (n=237) |
| false_answer_rate | 0.013 [0.0, 0.031] (n=223) |
| over_abstention_rate | 0.059 [0.03, 0.089] (n=237) |
| key_number_recall | 0.793 [0.736, 0.846] (n=160) |
| calc_correct | 0.833 [0.667, 0.958] (n=24) |
| gold_cited_any | 0.808 [0.753, 0.864] (n=198) |
| answers_with_ungrounded_numbers | 0.055 [0.03, 0.084] (n=237) |
| claims_judged | 299 |
| claim_supported_rate | 0.88 [0.828, 0.926] (n=299) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=299) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=180) |
| fact_coverage | 0.738 [0.69, 0.789] (n=309) |
| answers_contradicting_a_reference_fact | 0.011 [0.0, 0.028] (n=180) |
| latency_p50_s | 14.8 |
| latency_p95_s | 35.6 |
| cost_per_case_usd | 0.00215 |
| judge_cost_total_usd | 0.2411 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 35 | 0.943 | 0 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 44 | 0.727 | 3 | 0 | 0 | 0 |
| cross_source_synthesis | 35 | 0.971 | 0 | 1 | 0 | 1 |
| factual_lookup | 70 | 0.929 | 0 | 5 | 0 | 0 |
| numerical_comparison | 34 | 0.824 | 0 | 6 | 0 | 0 |
| revision_conflict | 19 | 0.947 | 0 | 1 | 0 | 1 |

