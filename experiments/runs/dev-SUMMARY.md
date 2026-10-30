# Retrieval experiments, split `dev` (n=24 text-evidence cases)

Gold: `experiments/gold/draft_cases.jsonl` (DRAFT, not yet human-reviewed). Baseline: merge120, stopwords on, period normalisation on, no stemming, k1=1.5, b=0.75. Differences on this few cases are small-sample; read the paired column.

## E1-chunking

| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs baseline (rank of first relevant) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| blocks | 0.2083 | 0.2917 | 0.4167 | 0.5 | 0.4583 | 0.2907 | 0.2708 | 201.6 | 1929 | 0.166 | 0 better / 10 worse / 14 same |
| merge120 | 0.3333 | 0.4167 | 0.4583 | 0.7083 | 0.5417 | 0.4142 | 0.3542 | 480.5 | 751 | 0.156 | 0 better / 0 worse / 24 same |
| merge200 | 0.375 | 0.5417 | 0.5417 | 0.7917 | 0.5833 | 0.4763 | 0.3958 | 660.3 | 645 | 0.152 | 7 better / 1 worse / 16 same |
| fixed150 | 0.25 | 0.5417 | 0.5833 | 0.6667 | 0.5833 | 0.4087 | 0.375 | 737.7 | 488 | 0.147 | 5 better / 8 worse / 11 same |
| merge120+tables | 0.2917 | 0.4583 | 0.4583 | 0.7083 | 0.5417 | 0.3994 | 0.375 | 529 | 1022 | 0.154 | 3 better / 2 worse / 19 same |

## E2-tokenisation

| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs baseline (rank of first relevant) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.3333 | 0.4167 | 0.4583 | 0.7083 | 0.5417 | 0.4142 | 0.3542 | 480.5 | 751 | 0.156 | 0 better / 0 worse / 24 same |
| stem_on | 0.25 | 0.4167 | 0.4167 | 0.625 | 0.4583 | 0.3474 | 0.3264 | 503.5 | 751 | 0.163 | 2 better / 6 worse / 16 same |
| stopwords_off | 0.3333 | 0.4583 | 0.5 | 0.75 | 0.5417 | 0.4272 | 0.4097 | 513.0 | 751 | 0.183 | 7 better / 1 worse / 16 same |
| period_norm_off | 0.2917 | 0.4167 | 0.4583 | 0.7083 | 0.5417 | 0.3947 | 0.3542 | 497.2 | 751 | 0.138 | 3 better / 3 worse / 18 same |

## E4-combined

| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs baseline (rank of first relevant) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| merge200+stopwords_off | 0.375 | 0.5417 | 0.5417 | 0.75 | 0.5833 | 0.4754 | 0.4097 | 703.7 | 645 | 0.172 | 7 better / 3 worse / 14 same |
| merge200+stopwords_off+b=0.4 | 0.3333 | 0.5 | 0.625 | 0.8333 | 0.6667 | 0.4585 | 0.5278 | 951.8 | 645 | 0.16 | 9 better / 4 worse / 11 same |

## E3-bm25-params

| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs baseline (rank of first relevant) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| k1=0.9 | 0.2917 | 0.4167 | 0.4583 | 0.625 | 0.5417 | 0.381 | 0.3542 | 557.5 | 751 | 0.155 | 0 better / 5 worse / 19 same |
| k1=1.2 | 0.3333 | 0.4167 | 0.4583 | 0.7083 | 0.5417 | 0.4147 | 0.375 | 491.9 | 751 | 0.157 | 2 better / 1 worse / 21 same |
| k1=1.5 | 0.3333 | 0.4167 | 0.4583 | 0.7083 | 0.5417 | 0.4142 | 0.3542 | 480.5 | 751 | 0.156 | 0 better / 0 worse / 24 same |
| k1=2.0 | 0.3333 | 0.4167 | 0.4583 | 0.6667 | 0.5417 | 0.4134 | 0.3542 | 439.6 | 751 | 0.15 | 3 better / 1 worse / 20 same |
| b=0.4 | 0.2917 | 0.4167 | 0.4167 | 0.7083 | 0.4583 | 0.3801 | 0.3333 | 660.4 | 751 | 0.154 | 4 better / 6 worse / 14 same |
| b=0.75 | 0.3333 | 0.4167 | 0.4583 | 0.7083 | 0.5417 | 0.4142 | 0.3542 | 480.5 | 751 | 0.156 | 0 better / 0 worse / 24 same |
| b=0.9 | 0.2917 | 0.4583 | 0.4583 | 0.6667 | 0.5417 | 0.4009 | 0.3542 | 401 | 751 | 0.153 | 2 better / 3 worse / 19 same |

