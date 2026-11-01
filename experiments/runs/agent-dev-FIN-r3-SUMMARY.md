# Agent end-to-end, split `dev`, FIN-r3 (available n=237)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `r3`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=237, gpt-5.6-luna=237.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.945 | 0.886 | 0.055 | 0.127 | 0.78 | 0.667 | 0.82 | 1.81 | 0.03 | 0 | 15.06 | 0.00284 |
| gpt-5.6-luna | 0.92 | 0.899 | 0.049 | 0.109 | 0.786 | 0.708 | 0.799 | 1.92 | 0.055 | 0 | 14.96 | 0.00461 |
