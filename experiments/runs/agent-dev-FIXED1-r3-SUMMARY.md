# Agent end-to-end, split `dev`, FIXED1-r3 (available n=237)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `r3`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=237.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.928 | 0.814 | 0.17 | 0.2 | 0.709 | 0.0 | 0.725 | 1.62 | 0.114 | 0 | 15.27 | 0.0027 |
