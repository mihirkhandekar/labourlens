# Agent end-to-end, split `heldout`, V2post-hybrid (available n=65)

Draft gold labels. Planner and answer step use the same model. Prompts `planner_v3` and `answer_v5`; retrieval `hybrid`. Rates are over scored cases.

Scored n by configuration: gpt-6-luna=65, gpt-5.6-luna=65.

| config | valid_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | calc_correct_rate | gold_cited_any_rate | tool_calls_mean | tool_error_rate | operational_failures | latency_p50_s | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.985 | 0.877 | 0.083 | 0.059 | 0.792 | 1.0 | 0.688 | 1.82 | 0.2 | 0 | 10.52 | 0.00181 |
| gpt-5.6-luna | 0.923 | 0.815 | 0.146 | 0.118 | 0.771 | 1.0 | 0.667 | 1.82 | 0.246 | 0 | 10.47 | 0.00392 |
