# Agent end-to-end, split `dev`, A1 model pair (n=34 cases)

Draft gold labels. Planner and answer step use the same model. Prompts planner_v1 and answer_v2. Rates are over cases.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 1.0 | 0.706 | 0.214 | 0.167 | 0.607 | 0.667 | 0.645 | 1.91 | 0.0 | 0 | 13.18 | 0.00142 |
| gpt-5.6-luna | 0.971 | 0.765 | 0.179 | 0.167 | 0.679 | 0.667 | 0.677 | 2.12 | 0.0 | 0 | 10.78 | 0.00302 |
| gpt-4.1-mini | 0.941 | 0.824 | 0.143 | 0.333 | 0.607 | 0.5 | 0.516 | 2 | 0.294 | 0 | 5.78 | 0.00455 |
