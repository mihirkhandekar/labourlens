# Agent end-to-end, split `heldout`, FIN2V2-r3 (available n=65)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `r3`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=65, gpt-5.6-luna=65.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.985 | 0.723 | 0.312 | 0.0 | 0.625 | 0.5 | 0.625 | 1.91 | 0.154 | 0 | 17.86 | 0.0034 |
| gpt-5.6-luna | 0.985 | 0.738 | 0.25 | 0.0 | 0.708 | 0.5 | 0.646 | 1.88 | 0.2 | 0 | 15.22 | 0.00489 |
