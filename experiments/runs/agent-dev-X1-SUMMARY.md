# Agent end-to-end, split `dev`, X1 (available n=237)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `r3`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=237, gpt-5.6-luna=237.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.928 | 0.886 | 0.044 | 0.145 | 0.758 | 0.667 | 0.794 | 1.88 | 0.03 | 0 | 14.67 | 0.00294 |
| gpt-5.6-luna | 0.92 | 0.911 | 0.027 | 0.127 | 0.808 | 0.75 | 0.825 | 1.92 | 0.034 | 0 | 13.29 | 0.00458 |
