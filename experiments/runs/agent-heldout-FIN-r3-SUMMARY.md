# Agent end-to-end, split `heldout`, FIN-r3 (available n=31)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `r3`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=31, gpt-5.6-luna=31.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.968 | 0.839 | 0.125 | 0.0 | 0.667 | 1.0 | 0.621 | 1.71 | 0.0 | 0 | 12.27 | 0.00232 |
| gpt-5.6-luna | 0.968 | 0.839 | 0.125 | 0.143 | 0.75 | 1.0 | 0.586 | 2.13 | 0.032 | 0 | 16.65 | 0.00438 |
