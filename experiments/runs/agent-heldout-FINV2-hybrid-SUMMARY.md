# Agent end-to-end, split `heldout`, FINV2-hybrid (available n=65)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `hybrid`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=65, gpt-5.6-luna=65.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.969 | 0.754 | 0.271 | 0.0 | 0.667 | 0.5 | 0.604 | 1.8 | 0.154 | 0 | 10.46 | 0.00171 |
| gpt-5.6-luna | 0.954 | 0.723 | 0.271 | 0.118 | 0.688 | 0.5 | 0.542 | 1.86 | 0.169 | 0 | 10.22 | 0.00344 |
