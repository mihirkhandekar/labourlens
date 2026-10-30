# Answer generation, split `dev`, G4: k=8 for the two cheapest cautious models (the owner's prefer-declining policy, D-026) (n=30 cases)

Draft gold labels. Prompt `answer_v1`; retrieval fixed; k=5 unless the label says otherwise. Rates are over cases.

| config | valid_rate | repair_rate | behavior_accuracy | over_abstention_rate | false_answer_rate | numbers_complete_rate | gold_in_context_rate | gold_cited_rate | key_number_recall | answers_with_ungrounded_numbers | latency_p50_s | total_tokens | cost_per_case_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gpt-5.6-luna k=8 | 0.967 | 0.167 | 0.767 | 0.167 | 0.333 | 0.708 | 0.692 | 0.583 | 0.763 | 0.083 | 5.61 | 121210 | 0.00121 |
| gpt-6-luna k=8 | 0.967 | 0.233 | 0.7 | 0.292 | 0.0 | 0.625 | 0.692 | 0.5 | 0.728 | 0.25 | 6.1 | 131538 | 0.00066 |
