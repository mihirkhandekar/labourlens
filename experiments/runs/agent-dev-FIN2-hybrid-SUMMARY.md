# Agent end-to-end, split `dev`, FIN2-hybrid (available n=237)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `hybrid`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=237, gpt-5.6-luna=237.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.966 | 0.81 | 0.148 | 0.145 | 0.621 | 0.708 | 0.656 | 1.85 | 0.034 | 0 | 10.25 | 0.00167 |
| gpt-5.6-luna | 0.949 | 0.848 | 0.11 | 0.109 | 0.72 | 0.708 | 0.709 | 1.98 | 0.059 | 0 | 10.09 | 0.00352 |
