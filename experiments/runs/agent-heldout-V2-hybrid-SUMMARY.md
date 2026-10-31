# Agent end-to-end, split `heldout`, V2-hybrid (available n=65)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `hybrid`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=65, gpt-5.6-luna=65.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.954 | 0.708 | 0.292 | 0.059 | 0.646 | 0.5 | 0.562 | 1.83 | 0.138 | 0 | 10.56 | 0.00159 |
| gpt-5.6-luna | 0.954 | 0.723 | 0.292 | 0.059 | 0.667 | 0.5 | 0.542 | 1.91 | 0.154 | 0 | 10.9 | 0.0036 |
