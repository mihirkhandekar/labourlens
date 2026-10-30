# Answer generation, dev, G1 (n=30 cases, draft gold)

| config | valid_rate | repair_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | gold_in_context_rate | gold_cited_rate | key_number_recall | answers_with_ungrounded_numbers | latency_p50_s | total_tokens | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-4.1-mini | 0.867 | 0.333 | 0.833 | 0.125 | 0.333 | 0.708 | 0.577 | 0.583 | 0.667 | 0.0 | 2.55 | 92028 | 0.00161 |
| gpt-5.4-mini | 0.967 | 0.333 | 0.7 | 0.25 | 0.167 | 0.625 | 0.577 | 0.5 | 0.645 | 0.25 | 2.66 | 91101 | 0.00335 |
| gpt-5.6-luna | 0.933 | 0.433 | 0.733 | 0.292 | 0.0 | 0.625 | 0.577 | 0.458 | 0.605 | 0.125 | 6.66 | 100558 | 0.00113 |
| gpt-6-luna | 0.933 | 0.3 | 0.6 | 0.417 | 0.0 | 0.5 | 0.577 | 0.375 | 0.57 | 0.208 | 5.58 | 96349 | 0.00051 |
| gpt-6-sol | 0.9 | 0.1 | 0.6 | 0.375 | 0.167 | 0.542 | 0.577 | 0.375 | 0.57 | 0.25 | 4.79 | 82427 | 0.00912 |
| gpt-6.1-terra | 1.0 | 0.1 | 0.567 | 0.417 | 0.0 | 0.417 | 0.577 | 0.417 | 0.465 | 0.0 | 6.34 | 79550 | 0.00432 |
