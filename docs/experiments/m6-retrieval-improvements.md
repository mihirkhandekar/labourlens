# M6 experiment: retrieval improvements (dev split)

Status: dev only, nothing locked, held-out untouched. Gold labels are AI drafts (gold v3), not owner-reviewed. Differences under about 10 points are treated as noise; every headline number carries a bootstrap 95% interval. Nothing here becomes a default without owner approval (D-029).

Code: `src/labourlens/retrieval/{period,rerank,experiments_rerank}.py`, `prompts/rerank_v1.md`; run with `uv run labourlens retrieval-exp2 --split dev`. Tests: `tests/retrieval/test_period.py`, `tests/retrieval/test_rerank.py`.

## Motivation (earlier MEASURED facts)
D-025: retrieval limits end-to-end quality. The gold passage was in the top 50 for 25 of 26 text cases but in the model's context only 58% (k=5) to 69% (k=8) of the time. The independent review of agent answers found failures dominated by retrieval misses on lookups that name a specific quarter and release type (advance versus final), because near-duplicate sections repeat across quarters and releases.

## Pre-registered design (written before any R1/R2 number was computed)
Same chunks (merge200), same embeddings (`text-embedding-3-large`, cached), same dev text cases (answerable text-evidence cases, split `dev`), same base retriever for every row: hybrid RRF of BM25 and dense, depth 50 per list, constant 60. One factor changes per row.

### Hypotheses
- **H1 (query metadata).** Questions that name a quarter and/or a release type retrieve the wrong quarter's or release's near-duplicate section. Using that metadata deterministically should raise hit@8 on the cases that carry a hint, and cost nothing in latency. Expected: R1a (hard filter) gives the larger gain on hinted cases but can lose cases whose gold lives in a different document than the one named (for example a comparison drawn from a later report); R1b (soft boost) gives a smaller gain with less risk.
- **H2 (LLM rerank).** A listwise rerank of the top 30 with a small model fixes ordering errors among near-duplicates when the question states the period and release type, at a cost of seconds and a fraction of a cent per query. Expected: hit@3/5/8 up, hit@10 roughly flat (the pool is fixed), a pool ceiling from top-30 recall.
- **H3 (combination).** Only if both help individually, the filter shrinks the pool to the right documents and the rerank orders it, so the combined gain is at least the larger single gain.
- **Null.** At this n, no configuration separates from R0 beyond noise. A negative result will be reported as such.

### Rules (general, stated before measuring; no per-case tuning)
R1 parser (`period.py`):
1. Period hint: an explicit quarter with a year (`1Q 2026`, `Q1 2026`, `2026 Q1`, `first quarter of 2026`) or a month with a year (`September 2025` maps to 3Q 2025), except a month directly after a publish/release/issued/dated word. `X to Y` between two hints expands to the quarters between. A bare `Q2`, a bare month and a bare year give no hint. All named quarters are kept.
2. Stage hint: advance / preliminary maps to `advance`; final / full report / labour market report maps to `final`. If both families appear, no stage restriction is derived.
3. A document matches the period hint if its coverage interval overlaps a named quarter, and the stage hint if its release stage equals it (documents from `specs/sources.yaml`; annual survey documents overlap the quarters of their year and have stage `annual`).
4. **R1a hard filter:** both candidate lists (BM25 and dense) are restricted to documents matching every available hint before taking the top 50 and fusing; if there is no hint, or no document matches, nothing is filtered.
5. **R1b soft boost:** after fusing as in R0, every available hint adds a bonus of 0.5 x 1/(60+1) = 0.0082 to chunks of documents matching that hint (period and stage separately). The bonus is fixed a priori: it is worth roughly a jump of 60 ranks in one list, large against rank noise but not enough to rescue a chunk that neither list ranked in its top 50. A sensitivity check at 0.25x and 1.0x is reported as exploratory and does not select the primary row.

R2 rerank (`rerank.py`, `prompts/rerank_v1.md`): the top 30 R0 chunks, labelled C1..C30 with source id, title, publication date, stage and locator, are shown as XML-escaped untrusted data to `gpt-6-luna`. It returns an ordered list of the labels it judges most useful for answering the question (at most 10, structured output). Invalid, duplicate or unknown labels are dropped; the remaining R0 order fills the rest. Any API failure falls back to the R0 order and is counted.

R3 runs only if both R1 (the better of R1a/R1b) and R2 improve hit@8 over R0 by at least 0.05 individually; then the R1 candidate pool is reranked by R2.

### Metrics and decision rules
hit@k for k in 3, 5, 8, 10 (any gold passage inside the passages of the top-k chunks, which is exactly "gold passage in the top k"); MRR over the top 10; share of gold passages covered at 8; pool recall at 30 and 50 (the ceiling for R2); per-family hit@8; bootstrap 95% CI (2000 resamples over cases, seed 0) for hit@8 and for its paired difference to R0; added latency and cost per query. The best retrieval configuration (highest hit@8, ties broken by MRR, excluding R0) then gets one end-to-end check: whether the gold passage is among the context passages the answer step would build from the first 8 chunks, compared with R0. A change is called real only if the paired-difference interval for hit@8 excludes zero; otherwise it is labelled not separable from noise.
