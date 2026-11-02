# Agent end-to-end, split `heldout`, FIN2V2-hybrid (available n=65)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `hybrid`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=65, gpt-5.6-luna=65.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.938 | 0.738 | 0.271 | 0.059 | 0.667 | 0.5 | 0.542 | 1.8 | 0.169 | 0 | 11.5 | 0.00167 |
| gpt-5.6-luna | 0.985 | 0.754 | 0.25 | 0.059 | 0.729 | 0.5 | 0.604 | 1.85 | 0.215 | 0 | 10.04 | 0.00348 |
