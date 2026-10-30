# Dense and hybrid retrieval experiments, split `dev` (n=24 text-evidence cases)

Gold labels are AI drafts, not human-reviewed. Dev tuning only. Paired column compares with the BM25 baseline (merge120, default settings).

## E5-embedding-model (dense only, merge120)

| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs BM25 baseline (rank of first relevant) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bm25 baseline | 0.2083 | 0.4167 | 0.4167 | 0.5833 | 0.4583 | 0.3131 | 0.2917 | 456.3 | 2468 | 0.198 | 0 better / 0 worse / 24 same |
| text-embedding-3-small | 0.25 | 0.5417 | 0.625 | 0.75 | 0.625 | 0.4296 | 0.3819 | 406.5 | 2468 | 389.85 | 15 better / 6 worse / 3 same |
| text-embedding-3-large | 0.4583 | 0.5833 | 0.5833 | 0.6667 | 0.5833 | 0.5314 | 0.3299 | 375.6 | 2468 | 444.402 | 13 better / 5 worse / 6 same |
| text-embedding-ada-002 | 0.4167 | 0.5 | 0.7083 | 0.875 | 0.7083 | 0.5301 | 0.4132 | 415.5 | 2468 | 654.717 | 16 better / 4 worse / 4 same |

Winner on dev by MRR then hit@10: `text-embedding-3-large`.

## E6-retrieval-mode (embedding `text-embedding-3-large`)

| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs BM25 baseline (rank of first relevant) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| merge120 bm25 | 0.2083 | 0.4167 | 0.4167 | 0.5833 | 0.4583 | 0.3131 | 0.2917 | 456.3 | 2468 | 0.185 | 0 better / 0 worse / 24 same |
| merge120 dense | 0.4583 | 0.5833 | 0.5833 | 0.6667 | 0.5833 | 0.5314 | 0.3299 | 375.6 | 2468 | 5.396 | 13 better / 5 worse / 6 same |
| merge120 hybrid-rrf | 0.4167 | 0.5833 | 0.6667 | 0.7083 | 0.6667 | 0.5181 | 0.4236 | 411.5 | 2468 | 6.15 | 11 better / 2 worse / 11 same |
| merge200 bm25 | 0.25 | 0.4583 | 0.5417 | 0.625 | 0.5833 | 0.3627 | 0.375 | 633.0 | 2106 | 0.175 | 5 better / 1 worse / 18 same |
| merge200 dense | 0.3333 | 0.5 | 0.5417 | 0.6667 | 0.5417 | 0.4434 | 0.2882 | 436.4 | 2106 | 6.041 | 10 better / 5 worse / 9 same |
| merge200 hybrid-rrf | 0.3333 | 0.5417 | 0.625 | 0.7917 | 0.6667 | 0.455 | 0.4236 | 507.2 | 2106 | 6.88 | 13 better / 2 worse / 9 same |

## E7-embedded-text-header (dense only, `text-embedding-3-large`, merge120)

| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs BM25 baseline (rank of first relevant) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| header=off | 0.4583 | 0.5833 | 0.5833 | 0.6667 | 0.5833 | 0.5314 | 0.3299 | 375.6 | 2468 | 5.449 | 13 better / 5 worse / 6 same |
| header=on | 0.4167 | 0.5417 | 0.625 | 0.7083 | 0.625 | 0.4962 | 0.375 | 356.9 | 2468 | 12.815 | 12 better / 4 worse / 8 same |

## Measured API usage (from `usage.jsonl`; tokens are as reported by the API)

| model | calls | inputs | tokens | query embedding latency |
|---|---|---|---|---|
| text-embedding-3-small | 38 | 1718 | 217501 | 340 ms median over 24 uncached query calls |
| text-embedding-3-large | 60 | 4510 | 639683 | 390 ms median over 24 uncached query calls |
| text-embedding-ada-002 | 38 | 1718 | 217501 | 625 ms median over 24 uncached query calls |

