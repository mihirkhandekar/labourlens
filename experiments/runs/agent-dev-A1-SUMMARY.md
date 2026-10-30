# Agent end-to-end, split `dev`, A1 (n=238 cases, answer prompt answer_v3)

Draft gold labels. Planner and answer step use the same model. Prompts planner_v1 and answer_v2. Rates are over cases.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.966 | 0.756 | 0.236 | 0.064 | 0.586 | 0.833 | 0.658 | 1.84 | 0.034 | 0 | 10.72 | 0.00137 |
| gpt-5.6-luna | 0.979 | 0.782 | 0.199 | 0.064 | 0.649 | 0.833 | 0.678 | 1.97 | 0.046 | 0 | 9.73 | 0.00274 |
| gpt-4.1-mini | 0.891 | 0.782 | 0.168 | 0.17 | 0.607 | 0.375 | 0.618 | 2.07 | 0.239 | 0 | 5.76 | 0.00467 |
