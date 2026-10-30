# Agent end-to-end, split `heldout`, H-r3 (n=31 cases, answer prompt answer_v3)

Draft gold labels. Planner and answer step use the same model. Prompts planner_v1 and answer_v2. Rates are over cases.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.935 | 0.839 | 0.087 | 0.125 | 0.652 | 1.0 | 0.643 | 1.84 | 0.0 | 0 | 14.02 | 0.00193 |
| gpt-5.6-luna | 0.935 | 0.871 | 0.043 | 0.25 | 0.826 | 1.0 | 0.714 | 2.03 | 0.032 | 0 | 17.33 | 0.00343 |
| gpt-4.1-mini | 0.871 | 0.742 | 0.174 | 0.375 | 0.565 | 0.4 | 0.536 | 2.1 | 0.29 | 0 | 7.28 | 0.00496 |
