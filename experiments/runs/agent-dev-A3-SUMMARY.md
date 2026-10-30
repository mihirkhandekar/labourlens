# Agent end-to-end, split `dev`, A3 (n=237 cases, answer prompt answer_v3)

Draft gold labels. Planner and answer step use the same model. Prompts planner_v1 and answer_v2. Rates are over cases.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.954 | 0.89 | 0.068 | 0.087 | 0.743 | 0.875 | 0.808 | 1.81 | 0.025 | 0 | 15.41 | 0.00212 |
| gpt-5.6-luna | 0.945 | 0.907 | 0.052 | 0.043 | 0.78 | 0.875 | 0.828 | 1.92 | 0.051 | 0 | 15.5 | 0.0036 |
