# Agent end-to-end, split `heldout`, V2post-r3 (available n=65)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v3` and `answer_v5`; retrieval `r3`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=65, gpt-5.6-luna=65.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.969 | 0.908 | 0.062 | 0.0 | 0.792 | 1.0 | 0.75 | 1.77 | 0.185 | 0 | 14.69 | 0.0032 |
| gpt-5.6-luna | 0.969 | 0.846 | 0.146 | 0.0 | 0.771 | 1.0 | 0.667 | 1.69 | 0.231 | 0 | 12.82 | 0.00491 |
