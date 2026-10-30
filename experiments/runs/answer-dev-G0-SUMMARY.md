# Answer generation, split `dev`, G0: model comparison, ORACLE evidence (gold passages placed first, then retrieved); isolates generation from retrieval (n=30 cases)

Draft gold labels. Same prompt (`answer_v1`), retrieval and k=5 for every model. Rates are over cases.

| config | valid_rate | repair_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | gold_in_context_rate | gold_cited_rate | key_number_recall | answers_with_ungrounded_numbers | latency_p50_s | total_tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-luna | 0.933 | 0.133 | 0.867 | 0.083 | 0.167 | 0.833 | 1.0 | 0.875 | 0.912 | 0.125 | 4.82 | 92397 |
| gpt-6-sol | 0.967 | 0.2 | 0.833 | 0.125 | 0.167 | 0.833 | 1.0 | 0.833 | 0.877 | 0.125 | 5.33 | 101150 |
| gpt-6.1-terra | 1.0 | 0.133 | 0.733 | 0.208 | 0.167 | 0.708 | 1.0 | 0.792 | 0.807 | 0.0 | 6.46 | 92724 |
| gpt-5.6-luna | 0.9 | 0.3 | 0.867 | 0.083 | 0.167 | 0.875 | 1.0 | 0.875 | 0.923 | 0.208 | 6.09 | 105318 |
| gpt-5.4-mini | 0.867 | 0.333 | 0.8 | 0.083 | 0.167 | 0.792 | 1.0 | 0.875 | 0.886 | 0.125 | 2.42 | 103075 |
| gpt-4.1-mini | 0.9 | 0.233 | 0.933 | 0.0 | 0.333 | 0.917 | 1.0 | 1.0 | 0.965 | 0.083 | 2.38 | 96447 |
