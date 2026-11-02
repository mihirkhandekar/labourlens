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
