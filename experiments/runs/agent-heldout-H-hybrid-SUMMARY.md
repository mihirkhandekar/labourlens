# Agent end-to-end, split `heldout`, H-hybrid (available n=31)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `hybrid`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=31, gpt-5.6-luna=31, gpt-4.1-mini=31.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 1.0 | 0.677 | 0.304 | 0.125 | 0.435 | 0.0 | 0.464 | 1.77 | 0.0 | 0 | 12.66 | 0.00124 |
| gpt-5.6-luna | 1.0 | 0.742 | 0.261 | 0.125 | 0.565 | 0.0 | 0.429 | 2.23 | 0.032 | 0 | 11.05 | 0.00271 |
| gpt-4.1-mini | 0.903 | 0.581 | 0.435 | 0.25 | 0.391 | 0.0 | 0.357 | 2.06 | 0.323 | 0 | 5.89 | 0.00423 |
