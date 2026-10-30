# Answer generation, split `dev`, G3: evidence size k (chunks shown to the model), two fast models (n=30 cases)

Draft gold labels. Prompt `answer_v1`; retrieval fixed; k=5 unless the label says otherwise. Rates are over cases.

| config | valid_rate | repair_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | gold_in_context_rate | gold_cited_rate | key_number_recall | answers_with_ungrounded_numbers | latency_p50_s | total_tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-4.1-mini k=3 | 0.833 | 0.467 | 0.767 | 0.208 | 0.333 | 0.5 | 0.5 | 0.5 | 0.593 | 0.0 | 2.78 | 74539 |
| gpt-4.1-mini k=5 | 0.933 | 0.333 | 0.833 | 0.125 | 0.333 | 0.708 | 0.577 | 0.583 | 0.649 | 0.083 | 2.7 | 90931 |
| gpt-4.1-mini k=8 | 0.9 | 0.367 | 0.9 | 0.042 | 0.333 | 0.75 | 0.692 | 0.75 | 0.781 | 0.125 | 2.51 | 143018 |
| gpt-5.4-mini k=3 | 0.933 | 0.367 | 0.6 | 0.375 | 0.167 | 0.417 | 0.5 | 0.375 | 0.465 | 0.125 | 2.38 | 64679 |
| gpt-5.4-mini k=5 | 0.9 | 0.333 | 0.733 | 0.167 | 0.0 | 0.583 | 0.577 | 0.542 | 0.638 | 0.25 | 2.57 | 86984 |
| gpt-5.4-mini k=8 | 0.9 | 0.333 | 0.8 | 0.083 | 0.167 | 0.667 | 0.692 | 0.625 | 0.702 | 0.125 | 2.66 | 134744 |
