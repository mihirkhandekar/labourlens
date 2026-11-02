# Tagged retrieval re-run protocol

**Pre-declared, 2 November 2026, before implementation or measurement.** This is a development-only re-run, not new held-out evidence. No result is claimed here.

## Analysis rules

Keep the existing R0, R1a, R1b, soft-bonus sensitivity, R2 and conditional R3 algorithms, cases, bootstrap seed and R3 gate unchanged. Report every executed configuration, including negative or null effects. Compare within this run against its R0; do not pool scores with the frozen R-series. Differences against the historical series may reflect corpus, gold and code changes, not a retrieval-only causal effect.

`--tag V31` writes configuration metrics and case scores under `experiments/runs/dev-R-V31-R*/`, and `SUMMARY.md` plus `summary.json` under `experiments/runs/dev-R-V31/`. A used tag is rejected before execution; frozen untagged outputs remain untouched. Untagged behaviour remains the legacy convention.

Record actual chunk corpus hash, chunk count, matched corpus snapshot version, current gold SHA-256 and code commit for tagged results. Identify v3.1 only if the live chunk hash and count match its snapshot. The summary must explain that this re-runs the development comparison on the current corpus and gold with isolated caches, rather than replacing the frozen R-series.

## Cache audit and isolation

The legacy dense matrix filename hashes chunk IDs but does not explicitly include model or text hashes; query-vector keys hash only the question. The legacy rerank key includes model, prompt, question and candidate IDs, but not the full current corpus. They are not sufficient proof of the current build. Tagged runs therefore use a private cache namespace under `data/runs/dev-R-<tag>/`, further keyed by actual corpus hash and embedding configuration. Dense and query vectors and rerank responses all stay there. The shared embedding cache may still supply exact model-and-text keyed vectors; missing embeddings require the API.

`--no-rerank` disables reranking calls only, not embeddings. Do not run a trial without an API key unless all needed embeddings are proven cached. Offline tests use synthetic chunks and stubbed dependencies and must never call the API.

Parent command after changes are committed and an API key is available: `uv run labourlens retrieval-exp2 --tag V31`. Use a new tag if that output already exists. The existing rerank budget and stopping rule remain unchanged.

## Methods comparison on the same cases (pre-declared 2 November 2026, before code and before any number was computed)

Purpose: the deck showed BM25, dense and hybrid hit@10 on an early 24-case, 46-document build, and later showed hybrid (R0) hit@8 on 128 development cases at corpus v3.1. The two cannot be compared. This note fixes one comparison before it is run.

Rules, none to be changed after seeing results:

1. Cases: the 128 development text cases that `retrieval-exp2` scores (gold file as recorded in `dev-R-V31`); corpus v3.1 (1,847 `merge200` chunks), `text-embedding-3-large`. Nothing is tuned.
2. Methods: BM25 only (top 50 from `BM25Index.search`, the list R0 fuses); dense only (cosine ranking from the frozen v3.1 matrix); hybrid = the R0 definition (reciprocal rank fusion, c=60, depth 50 of each list). No filter, boost or rerank.
3. Metrics: hit@8 (headline, same as R0) and hit@10 (to show k), plus MRR@10; 95% percentile case-bootstrap intervals (2,000 resamples, seed 0, the `bootstrap` helper of this module). Paired hybrid-minus-BM25 and hybrid-minus-dense hit@8 differences with the same bootstrap and better/worse counts.
4. Offline only: cached dense matrix and query vectors in `data/runs/dev-R-V31/`. If a vector or the matrix is missing the command stops without calling the API.
5. Consistency check: hybrid first-relevant ranks must equal `dev-R-V31-R0/scores.jsonl` case by case; the count of matching cases is recorded, and any mismatch is reported, not hidden.
6. Output: `experiments/runs/dev-R-V31-methods/` only (`metrics.json`, `scores.jsonl`, `SUMMARY.md`). The summary states why the early 24-case figure differs (cutoff k, case pool, corpus size) and shows all three methods at both k on the same 128 cases. Reported whatever the ordering is, including if hybrid is not best.
7. Command: `uv run labourlens retrieval-exp2 --tag V31 --methods`.
