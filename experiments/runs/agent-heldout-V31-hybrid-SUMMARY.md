# Agent end-to-end, split `heldout`, V31-hybrid (available n=65)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `hybrid`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=65, gpt-5.6-luna=65.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 1.0 | 0.708 | 0.292 | 0.0 | 0.646 | 0.5 | 0.562 | 1.78 | 0.169 | 0 | 10.35 | 0.00161 |
| gpt-5.6-luna | 0.969 | 0.723 | 0.271 | 0.059 | 0.688 | 0.5 | 0.604 | 1.88 | 0.154 | 0 | 9.93 | 0.00338 |
