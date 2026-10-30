# Retrieval experiments, split `dev` (n=9 text-evidence cases)

Gold: `experiments/gold/draft_cases.jsonl` (DRAFT, not yet human-reviewed). Baseline: merge120, stopwords on, period normalisation on, no stemming, k1=1.5, b=0.75. Differences on this few cases are small-sample; read the paired column.

## E1-chunking

| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs baseline (rank of first relevant) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| blocks | 0.1111 | 0.1111 | 0.3333 | 0.3333 | 0.4444 | 0.1611 | 0.2778 | 141.1 | 1929 | 0.192 | 0 better / 4 worse / 5 same |
| merge120 | 0.3333 | 0.3333 | 0.3333 | 0.5556 | 0.5556 | 0.3568 | 0.3333 | 352.3 | 751 | 0.151 | 0 better / 0 worse / 9 same |
| merge200 | 0.4444 | 0.5556 | 0.5556 | 0.7778 | 0.6667 | 0.5111 | 0.4444 | 557.9 | 645 | 0.144 | 4 better / 0 worse / 5 same |
| fixed150 | 0.1111 | 0.4444 | 0.5556 | 0.6667 | 0.5556 | 0.3194 | 0.3889 | 729.9 | 488 | 0.141 | 3 better / 3 worse / 3 same |
| merge120+tables | 0.3333 | 0.3333 | 0.3333 | 0.5556 | 0.5556 | 0.3583 | 0.3333 | 395 | 1022 | 0.16 | 1 better / 0 worse / 8 same |

## E2-tokenisation

| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs baseline (rank of first relevant) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.3333 | 0.3333 | 0.3333 | 0.5556 | 0.5556 | 0.3568 | 0.3333 | 352.3 | 751 | 0.151 | 0 better / 0 worse / 9 same |
| stem_on | 0.2222 | 0.3333 | 0.3333 | 0.4444 | 0.4444 | 0.2901 | 0.3333 | 373.8 | 751 | 0.159 | 0 better / 2 worse / 7 same |
| stopwords_off | 0.3333 | 0.3333 | 0.4444 | 0.6667 | 0.5556 | 0.3873 | 0.4444 | 434.3 | 751 | 0.149 | 3 better / 0 worse / 6 same |
| period_norm_off | 0.3333 | 0.3333 | 0.3333 | 0.6667 | 0.5556 | 0.3754 | 0.3333 | 381.2 | 751 | 0.135 | 2 better / 0 worse / 7 same |

## E4-combined

| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs baseline (rank of first relevant) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| merge200+stopwords_off | 0.3333 | 0.5556 | 0.5556 | 0.6667 | 0.6667 | 0.4444 | 0.4444 | 650.4 | 645 | 0.153 | 3 better / 1 worse / 5 same |
| merge200+stopwords_off+b=0.4 | 0.3333 | 0.5556 | 0.7778 | 0.7778 | 0.8889 | 0.4704 | 0.7222 | 900.1 | 645 | 0.151 | 4 better / 1 worse / 4 same |

## E3-bm25-params

| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs baseline (rank of first relevant) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| k1=0.9 | 0.3333 | 0.3333 | 0.3333 | 0.4444 | 0.5556 | 0.3444 | 0.3333 | 467 | 751 | 0.144 | 0 better / 1 worse / 8 same |
| k1=1.2 | 0.3333 | 0.3333 | 0.3333 | 0.5556 | 0.5556 | 0.3568 | 0.3333 | 379.8 | 751 | 0.163 | 1 better / 1 worse / 7 same |
| k1=1.5 | 0.3333 | 0.3333 | 0.3333 | 0.5556 | 0.5556 | 0.3568 | 0.3333 | 352.3 | 751 | 0.151 | 0 better / 0 worse / 9 same |
| k1=2.0 | 0.3333 | 0.3333 | 0.3333 | 0.4444 | 0.5556 | 0.3492 | 0.3333 | 324 | 751 | 0.146 | 1 better / 1 worse / 7 same |
| b=0.4 | 0.3333 | 0.3333 | 0.3333 | 0.5556 | 0.4444 | 0.3651 | 0.3333 | 568.9 | 751 | 0.147 | 2 better / 1 worse / 6 same |
| b=0.75 | 0.3333 | 0.3333 | 0.3333 | 0.5556 | 0.5556 | 0.3568 | 0.3333 | 352.3 | 751 | 0.151 | 0 better / 0 worse / 9 same |
| b=0.9 | 0.2222 | 0.3333 | 0.3333 | 0.4444 | 0.5556 | 0.2901 | 0.3333 | 292.6 | 751 | 0.144 | 0 better / 2 worse / 7 same |

