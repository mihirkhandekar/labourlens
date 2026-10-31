# Agent end-to-end, split `heldout`, X-hybrid (available n=31)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `hybrid`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=31, gpt-5.6-luna=31.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.935 | 0.774 | 0.208 | 0.143 | 0.667 | 1.0 | 0.517 | 1.87 | 0.0 | 0 | 11.51 | 0.00168 |
| gpt-5.6-luna | 1.0 | 0.742 | 0.25 | 0.143 | 0.542 | 1.0 | 0.448 | 2.19 | 0.065 | 0 | 9.95 | 0.00359 |
