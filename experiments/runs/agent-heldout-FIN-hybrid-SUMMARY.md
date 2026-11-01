# Agent end-to-end, split `heldout`, FIN-hybrid (available n=31)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v1` and `answer_v3`; retrieval `hybrid`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=31, gpt-5.6-luna=31.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 1.0 | 0.839 | 0.125 | 0.143 | 0.667 | 1.0 | 0.655 | 1.94 | 0.0 | 0 | 9.77 | 0.00155 |
| gpt-5.6-luna | 1.0 | 0.839 | 0.125 | 0.143 | 0.708 | 1.0 | 0.448 | 2.1 | 0.0 | 0 | 10.73 | 0.00335 |
