# Agent end-to-end, split `heldout`, FINV2-r3 (available n=65)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `r3`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=65, gpt-5.6-luna=65.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.985 | 0.708 | 0.333 | 0.0 | 0.583 | 0.5 | 0.583 | 1.77 | 0.154 | 0 | 16.82 | 0.0031 |
| gpt-5.6-luna | 0.969 | 0.723 | 0.271 | 0.0 | 0.708 | 0.5 | 0.604 | 1.83 | 0.169 | 0 | 16.07 | 0.00502 |
