# Agent end-to-end, split `dev`, A2 (n=238 cases, answer prompt answer_v4)

Draft gold labels. Planner and answer step use the same model. Prompts planner_v1 and answer_v2. Rates are over cases.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.975 | 0.748 | 0.241 | 0.085 | 0.576 | 0.875 | 0.643 | 1.82 | 0.025 | 0 | 12.81 | 0.00142 |
| gpt-5.6-luna | 0.987 | 0.782 | 0.199 | 0.064 | 0.634 | 0.833 | 0.683 | 1.98 | 0.055 | 0 | 10.98 | 0.0028 |
