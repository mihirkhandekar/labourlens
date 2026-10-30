# Agent end-to-end, split `dev`, A5 (n=237 cases, answer prompt answer_v3)

Draft gold labels. Planner and answer step use the same model. Prompts planner_v1 and answer_v2. Rates are over cases.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.949 | 0.903 | 0.052 | 0.087 | 0.754 | 0.875 | 0.818 | 1.89 | 0.025 | 0 | 16.44 | 0.00217 |
| gpt-5.6-luna | 0.941 | 0.899 | 0.068 | 0.043 | 0.785 | 0.792 | 0.813 | 1.99 | 0.076 | 0 | 14.73 | 0.00369 |
