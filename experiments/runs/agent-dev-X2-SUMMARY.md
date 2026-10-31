# Agent end-to-end, split `dev`, X2 (available n=237)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `r3`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=237, gpt-5.6-luna=237.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.932 | 0.903 | 0.033 | 0.109 | 0.78 | 0.75 | 0.82 | 1.85 | 0.021 | 0 | 14.04 | 0.00285 |
| gpt-5.6-luna | 0.92 | 0.916 | 0.027 | 0.109 | 0.791 | 0.75 | 0.82 | 1.9 | 0.046 | 0 | 13.94 | 0.00463 |
