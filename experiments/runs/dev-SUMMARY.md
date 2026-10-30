# Retrieval experiments, split `dev` (n=24 text-evidence cases)

Gold: `experiments/gold/draft_cases.jsonl` (DRAFT, not yet human-reviewed). Baseline: merge120, stopwords on, period normalisation on, no stemming, k1=1.5, b=0.75. Differences on this few cases are small-sample; read the paired column.

## E1-chunking

| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs baseline (rank of first relevant) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| blocks | 0.125 | 0.1667 | 0.3333 | 0.4167 | 0.375 | 0.1939 | 0.2292 | 169.1 | 6360 | 0.218 | 1 better / 10 worse / 13 same |
| merge120 | 0.2083 | 0.4167 | 0.4167 | 0.5833 | 0.4583 | 0.3131 | 0.2917 | 456.3 | 2468 | 0.183 | 0 better / 0 worse / 24 same |
| merge200 | 0.25 | 0.4583 | 0.5417 | 0.625 | 0.5833 | 0.3627 | 0.375 | 633.0 | 2106 | 0.183 | 5 better / 1 worse / 18 same |
| fixed150 | 0.2083 | 0.4167 | 0.5 | 0.625 | 0.5 | 0.3362 | 0.3403 | 742.5 | 1514 | 0.164 | 6 better / 6 worse / 12 same |
| merge120+tables | 0.2083 | 0.4167 | 0.4167 | 0.5833 | 0.4583 | 0.3131 | 0.2917 | 479.6 | 3379 | 0.185 | 2 better / 2 worse / 20 same |

## E2-tokenisation

| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs baseline (rank of first relevant) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.2083 | 0.4167 | 0.4167 | 0.5833 | 0.4583 | 0.3131 | 0.2917 | 456.3 | 2468 | 0.183 | 0 better / 0 worse / 24 same |
| stem_on | 0.2917 | 0.3333 | 0.375 | 0.5417 | 0.4167 | 0.3439 | 0.2986 | 475.5 | 2468 | 0.193 | 3 better / 4 worse / 17 same |
| stopwords_off | 0.25 | 0.375 | 0.4583 | 0.625 | 0.5 | 0.347 | 0.3333 | 481.9 | 2468 | 0.212 | 5 better / 1 worse / 18 same |
| period_norm_off | 0.1667 | 0.4167 | 0.4167 | 0.625 | 0.4583 | 0.2895 | 0.2917 | 454.8 | 2468 | 0.163 | 2 better / 2 worse / 20 same |

## E4-combined

| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs baseline (rank of first relevant) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| merge200+stopwords_off | 0.25 | 0.5 | 0.5417 | 0.6667 | 0.5833 | 0.3781 | 0.3611 | 684.5 | 2106 | 0.197 | 7 better / 3 worse / 14 same |
| merge200+stopwords_off+b=0.4 | 0.3333 | 0.5 | 0.5 | 0.7083 | 0.5417 | 0.4222 | 0.3542 | 899.1 | 2106 | 0.202 | 7 better / 3 worse / 14 same |

## E3-bm25-params

| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs baseline (rank of first relevant) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| k1=0.9 | 0.2083 | 0.375 | 0.4167 | 0.5 | 0.4583 | 0.3067 | 0.2917 | 482.0 | 2468 | 0.172 | 1 better / 3 worse / 20 same |
| k1=1.2 | 0.2083 | 0.4167 | 0.4167 | 0.5833 | 0.5 | 0.3126 | 0.2917 | 468.6 | 2468 | 0.17 | 0 better / 1 worse / 23 same |
| k1=1.5 | 0.2083 | 0.4167 | 0.4167 | 0.5833 | 0.4583 | 0.3131 | 0.2917 | 456.3 | 2468 | 0.183 | 0 better / 0 worse / 24 same |
| k1=2.0 | 0.2083 | 0.4167 | 0.4167 | 0.5833 | 0.4583 | 0.3047 | 0.2917 | 434.7 | 2468 | 0.176 | 1 better / 3 worse / 20 same |
| b=0.4 | 0.2083 | 0.3333 | 0.4583 | 0.5 | 0.5 | 0.2972 | 0.3125 | 578.7 | 2468 | 0.179 | 2 better / 5 worse / 17 same |
| b=0.75 | 0.2083 | 0.4167 | 0.4167 | 0.5833 | 0.4583 | 0.3131 | 0.2917 | 456.3 | 2468 | 0.183 | 0 better / 0 worse / 24 same |
| b=0.9 | 0.1667 | 0.4167 | 0.4583 | 0.5833 | 0.5 | 0.2963 | 0.3333 | 390.2 | 2468 | 0.188 | 3 better / 2 worse / 19 same |

