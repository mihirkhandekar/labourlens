# Agent end-to-end, split `dev`, X3 (available n=237)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v3` and `answer_v5`; retrieval `r3`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=237, gpt-5.6-luna=237.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.937 | 0.895 | 0.044 | 0.127 | 0.786 | 0.792 | 0.778 | 1.76 | 0.042 | 0 | 13.86 | 0.00298 |
| gpt-5.6-luna | 0.928 | 0.899 | 0.044 | 0.127 | 0.824 | 0.792 | 0.804 | 1.84 | 0.105 | 1 | 13.61 | 0.00484 |
