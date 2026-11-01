# Agent end-to-end, split `dev`, FIN-hybrid (available n=237)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `hybrid`. Rates are over scored cases.

Scored n by configuration: gpt-5.6-luna=237.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-5.6-luna | 0.949 | 0.84 | 0.121 | 0.127 | 0.687 | 0.667 | 0.677 | 1.96 | 0.051 | 0 | 9.34 | 0.00355 |
