# Agent end-to-end, split `dev`, FIN2-r3 (available n=237)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `r3`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=237, gpt-5.6-luna=237.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.932 | 0.907 | 0.027 | 0.127 | 0.78 | 0.75 | 0.841 | 1.84 | 0.025 | 0 | 13.64 | 0.00285 |
| gpt-5.6-luna | 0.924 | 0.895 | 0.06 | 0.091 | 0.775 | 0.583 | 0.767 | 1.93 | 0.068 | 0 | 14.12 | 0.00476 |
