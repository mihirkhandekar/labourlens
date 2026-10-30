# Evaluation of `agent-heldout-H-hybrid` (heldout, n=31)

Gold labels and the judge are AI-produced; nothing here is human-reviewed. Judge model: `gpt-6.1-terra` (different from the generators). Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.

## gpt-4.1-mini

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.581 [0.387, 0.742] (n=31) |
| false_answer_rate | 0.095 [0.0, 0.238] (n=21) |
| over_abstention_rate | 0.323 [0.161, 0.516] (n=31) |
| key_number_recall | 0.439 [0.254, 0.633] (n=18) |
| calc_correct | 0.4 [0.0, 0.8] (n=5) |
| gold_cited_any | 0.357 [0.179, 0.536] (n=28) |
| cases_with_ungrounded_numbers | 0.0 [0.0, 0.0] (n=31) |
| answers_with_ungrounded_numbers | 0.0 [0.0, 0.0] (n=31) |
| claims_judged | 28 |
| claim_supported_rate | 1.0 [1.0, 1.0] (n=28) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=28) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=15) |
| fact_coverage | 0.467 [0.2, 0.733] (n=15) |
| answers_contradicting_a_reference_fact | 0.067 [0.0, 0.2] (n=15) |
| latency_p50_s | 5.9 |
| latency_p95_s | 9.0 |
| cost_per_case_usd | 0.00423 |
| judge_cost_total_usd | 0.0183 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.6 | 0 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.333 | 2 | 1 | 0 | 0 |
| cross_source_synthesis | 5 | 0.6 | 0 | 2 | 0 | 0 |
| factual_lookup | 5 | 0.8 | 0 | 1 | 0 | 0 |
| numerical_comparison | 6 | 0.667 | 0 | 2 | 0 | 0 |
| revision_conflict | 4 | 0.5 | 0 | 2 | 0 | 1 |

## gpt-5.6-luna

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.742 [0.581, 0.871] (n=31) |
| false_answer_rate | 0.04 [0.0, 0.12] (n=25) |
| over_abstention_rate | 0.194 [0.065, 0.355] (n=31) |
| key_number_recall | 0.626 [0.439, 0.811] (n=18) |
| calc_correct | 0.8 [0.4, 1.0] (n=5) |
| gold_cited_any | 0.429 [0.25, 0.607] (n=28) |
| cases_with_ungrounded_numbers | 0.032 [0.0, 0.097] (n=31) |
| answers_with_ungrounded_numbers | 0.032 [0.0, 0.097] (n=31) |
| claims_judged | 39 |
| claim_supported_rate | 0.846 [0.725, 0.95] (n=39) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=39) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=18) |
| fact_coverage | 0.55 [0.333, 0.75] (n=20) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=18) |
| latency_p50_s | 11.1 |
| latency_p95_s | 19.7 |
| cost_per_case_usd | 0.00271 |
| judge_cost_total_usd | 0.0228 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.8 | 0 | 1 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.667 | 1 | 0 | 0 | 0 |
| cross_source_synthesis | 5 | 1.0 | 0 | 0 | 0 | 0 |
| factual_lookup | 5 | 0.8 | 0 | 1 | 0 | 0 |
| numerical_comparison | 6 | 1.0 | 0 | 0 | 0 | 0 |
| revision_conflict | 4 | 0.0 | 0 | 4 | 0 | 0 |

## gpt-6-luna

| measure | value |
|---|---|
| n_cases | 31 |
| behaviour_accuracy | 0.677 [0.516, 0.839] (n=31) |
| false_answer_rate | 0.042 [0.0, 0.125] (n=24) |
| over_abstention_rate | 0.226 [0.097, 0.387] (n=31) |
| key_number_recall | 0.626 [0.452, 0.8] (n=18) |
| calc_correct | 0.8 [0.4, 1.0] (n=5) |
| gold_cited_any | 0.464 [0.286, 0.643] (n=28) |
| cases_with_ungrounded_numbers | 0.0 [0.0, 0.0] (n=31) |
| answers_with_ungrounded_numbers | 0.0 [0.0, 0.0] (n=31) |
| claims_judged | 33 |
| claim_supported_rate | 1.0 [1.0, 1.0] (n=33) |
| claim_unsupported_rate | 0.0 [0.0, 0.0] (n=33) |
| answers_with_any_unsupported_claim | 0.0 [0.0, 0.0] (n=17) |
| fact_coverage | 0.571 [0.4, 0.789] (n=21) |
| answers_contradicting_a_reference_fact | 0.0 [0.0, 0.0] (n=17) |
| latency_p50_s | 12.7 |
| latency_p95_s | 18.5 |
| cost_per_case_usd | 0.00124 |
| judge_cost_total_usd | 0.0236 |

| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |
|---|---|---|---|---|---|---|
| adversarial | 5 | 0.4 | 0 | 2 | 0 | 0 |
| ambiguity_insufficient_causal | 6 | 0.667 | 1 | 0 | 0 | 0 |
| cross_source_synthesis | 5 | 0.8 | 0 | 1 | 0 | 0 |
| factual_lookup | 5 | 0.6 | 0 | 2 | 0 | 0 |
| numerical_comparison | 6 | 1.0 | 0 | 0 | 0 | 0 |
| revision_conflict | 4 | 0.5 | 0 | 2 | 0 | 0 |

