# Agent end-to-end, split `heldout`, V2-r3 (available n=65)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `r3`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=65, gpt-5.6-luna=65.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.954 | 0.754 | 0.271 | 0.0 | 0.688 | 0.5 | 0.583 | 1.83 | 0.154 | 0 | 18.74 | 0.00334 |
| gpt-5.6-luna | 0.954 | 0.723 | 0.292 | 0.0 | 0.667 | 0.5 | 0.583 | 1.83 | 0.185 | 0 | 16.51 | 0.00485 |
