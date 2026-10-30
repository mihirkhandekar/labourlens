# Agent end-to-end, split `dev`, A4 (n=237 cases, answer prompt answer_v3)

Draft gold labels. Planner and answer step use the same model. Prompts planner_v1 and answer_v2. Rates are over cases.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.966 | 0.886 | 0.073 | 0.065 | 0.743 | 0.833 | 0.808 | 1.81 | 0.034 | 0 | 14.8 | 0.00215 |
| gpt-5.6-luna | 0.941 | 0.907 | 0.063 | 0.043 | 0.785 | 0.792 | 0.818 | 1.93 | 0.042 | 0 | 15.07 | 0.00367 |
