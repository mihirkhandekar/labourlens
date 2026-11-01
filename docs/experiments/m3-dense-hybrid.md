# M3 experiment: dense and hybrid retrieval (dev split)

Status: dev only, nothing locked, held-out untouched. Gold labels are AI drafts, not yet reviewed by the owner. n=24 text-evidence cases, so one case moves a metric by 4.2 points; treat gaps under about 10 points as noise.

> **Superseded 1 Nov 2026 (status of the labels).** The status line above describes the state when these runs were scored: AI-drafted labels, not yet reviewed. The owner has since gone through the gold cases in the review interface and recorded a decision on every one (gold v3.7). The labels are AI-drafted and owner-confirmed; one reviewer, after AI pre-review and after the saved runs were scored; not independent inter-rater evidence. These runs were not rescored on v3.7, and v3.7 changes no score.

Code: `src/labourlens/retrieval/dense.py`, `experiments_dense.py`; run with `uv run labourlens dense-exp --split dev`. Raw per-case outputs: `experiments/runs/dev-dense-E5|E6|E7/`; summary table: `experiments/runs/dev-dense-SUMMARY.md`. Tests: `tests/retrieval/test_dense.py`.

## Setup (decisions D-021, D-022)
Hosted OpenAI embeddings, vectors cached locally (`data/index/embeddings/`, not committed). Cosine similarity over L2-normalised vectors. Hybrid is reciprocal rank fusion (RRF, constant 60) of the top 50 from BM25 and from dense. Corpus: 46 documents, 2,468 merge120 chunks (1,694 distinct texts; 157 texts appear in more than one chunk, so identical wording is cited from several documents or release stages).

## E5: which embedding model (dense only, merge120)
| config | hit@1 | hit@5 | hit@10 | MRR | passage_recall@5 |
|---|---|---|---|---|---|
| BM25 baseline | 0.21 | 0.42 | 0.58 | 0.31 | 0.29 |
| text-embedding-3-small | 0.25 | 0.63 | 0.75 | 0.43 | 0.38 |
| text-embedding-3-large | 0.46 | 0.58 | 0.67 | 0.53 | 0.33 |
| text-embedding-ada-002 | 0.42 | 0.71 | 0.88 | 0.53 | 0.41 |

Reading: all three dense models beat BM25 on MRR (+0.12 to +0.22). large and ada-002 tie on MRR (0.531 vs 0.530); ada-002 is ahead at hit@5, hit@10 and recall, large at hit@1 by one case. The automatic winner rule (MRR, then hit@10) chose `3-large` only by 0.001 MRR, which is not a real difference. Do not read "3-large is best" from this table. ada-002 is the older model, so a tie with the newer ones is a result worth stating, not hiding.

## E6: retrieval mode (embedding 3-large)
| config | hit@5 | hit@10 | MRR | passage_recall@5 | context words@5 |
|---|---|---|---|---|---|
| merge120 bm25 | 0.42 | 0.58 | 0.31 | 0.29 | 456 |
| merge120 dense | 0.58 | 0.67 | 0.53 | 0.33 | 376 |
| merge120 hybrid | 0.67 | 0.71 | 0.52 | 0.42 | 412 |
| merge200 bm25 | 0.54 | 0.63 | 0.36 | 0.38 | 633 |
| merge200 dense | 0.54 | 0.67 | 0.44 | 0.29 | 436 |
| merge200 hybrid | 0.63 | 0.79 | 0.46 | 0.42 | 507 |

Reading: hybrid has the best hit@10 and recall@5 in both chunkings and the fewest paired losses against the baseline (2 worse). Dense alone has the best MRR (it puts the right chunk first more often). By family (hit@5, small n): factual lookup improves most (BM25 0.38 to dense/hybrid 0.75 on merge120); numerical comparison is already 1.0 for every config; adversarial and revision cases are too few to separate.

## E7: prepend document title and section heading to the embedded text (dense, 3-large)
header off: hit@10 0.67, MRR 0.53. header on: hit@10 0.71, MRR 0.50. No clear effect (opposite directions on two metrics, one case apart). The header idea (to help the model tell quarters apart) is not supported by this data.

## Cost and latency (MEASURED tokens, VERIFIED prices)
Tokens reported by the API for embedding the corpus plus 24 queries: 3-small 217,501; 3-large 639,683; ada-002 217,501. Prices from https://developers.openai.com/api/docs/pricing (read 2026-10-30; `specs/prices.yaml`): 3-small $0.02, ada-002 $0.10, 3-large $0.13 per million tokens, so the one-off cost was $0.0044, $0.0218 and $0.0832. Cost is negligible at this corpus size; the 3-large vectors are 2x the dimension of 3-small (3,072 vs 1,536), which matters for storage at scale. Query embedding latency (network call, uncached): 3-small 340 ms, 3-large 390 ms, ada-002 625 ms (median of 24). Search over the cached matrix is 5 to 7 ms, versus 0.2 ms for BM25.

## What this does and does not show
- Dense and hybrid retrieval are better than BM25 on this dev set, on every metric except raw context size. The size of the difference between embedding models is not established at n=24.
- Not tested: reranking, reciprocal-rank constant, fusion depth, query rewriting, period-aware filtering (the suspected cause of the BM25 drop after the corpus grew), and the held-out set.
- Chunking, BM25 and dense settings were tuned on the same 24 cases, so dev scores are optimistic.

## Candidate for the pre-registered held-out run (PROPOSAL, owner approval needed before the freeze)
Add to the three BM25 configs already registered in `m2-bm25-baseline.md`: (a) hybrid-RRF, merge200, one embedding model. The embedding model for that run should be chosen with more evidence than this table (more dev cases after owner review) or by the owner's call between `3-small` (cheapest, within noise) and `ada-002`/`3-large`.
