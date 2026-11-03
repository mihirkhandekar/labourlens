# Held-out retrieval metrics

**PRE-REGISTERED, 3 November 2026, before execution.** Owner-authorised gap closure, not a new tuning round. No result is claimed by this note.

## Fixed design

Use the registered 31 cases from `experiments/gold/gold_v3.7.jsonl` (split `heldout`) and the fresh 65 from `experiments/gold/heldout_v2_v1.jsonl`. Apply the existing `evaluate.text_cases` eligibility rule: answer or ignore-injection-and-answer, with non-empty expected passage IDs. Report eligible n, excluded IDs, and all unresolved gold IDs. Keep missing/unretrievable gold in the denominator; do not repair labels or tune after inspecting results.

Use current corpus v3.1 and the development comparison's merge200 chunks, BM25 defaults, text-embedding-3-large, depth 50, RRF c=60, R1a hard period/release filter, R1b soft bonus and its fixed half/double sensitivity variants, R2 rerank-only, and R3 hard-filter-then-rerank. R3 uses the already selected R1a component, unconditionally, without choosing an arm using these sets. Include BM25, dense and hybrid. Gold, corpus, code, script, price and prompt hashes are recorded. Require the live corpus hash to match the frozen V31 snapshot before work starts.

For every configuration compute:

- Chunk hit@8: a gold passage occurs in any of the first eight chunks.
- Strict first-eight-passages hit@8: call the same `answer.context.build_context` on the first eight chunks and examine its first eight distinct context passages. This preserves its source/snapshot/text deduplication, not just passage-ID deduplication, and matches the development `coverage_check` definition.
- MRR@10: reciprocal rank of the first relevant chunk within the first ten, otherwise zero. Do not relabel passage rank as chunk MRR.
- 95% percentile case-bootstrap CIs for all three metrics, 2,000 resamples, seed 0; paired R3-minus-hybrid differences with the same case resamples. No multiplicity-adjusted or confirmatory significance claim. Report every arm and negative/null result as observed. No pass threshold, stopping on quality, selection of winners, or additional tuning.

These are retrieval-only diagnostics using the literal gold question, not model-rewritten tool queries or end-to-end answer accuracy. The 31 share evidence with development (25 of 31 in the published audit), so their metrics are optimistic. The 65 are only partly independent: questions and some sources were new, but design, shared corpus and later diagnostic reuse limit independence. Neither set is a pristine confirmatory test at this point. Bootstrap intervals describe case sampling only, not reranker sampling or gold uncertainty.

## Cache and spend policy

`python -m labourlens.retrieval.heldout_metrics` defaults to audit only and cannot call an API. Prefer the frozen V31 matrix/query vectors, then exact model-and-text-keyed shared query vectors. Store copied vectors and new rerank responses only in this experiment's private corpus-keyed cache. Reuse V31 rerank responses only when the full model/prompt/question/ordered-candidate cache key matches. Never use the legacy cross-corpus rerank cache. Missing query vectors are listed by set, case ID and exact question hash in `audit.json`; resolve the case ID in the named gold file to inspect the query. Do not publish copied questions because they can include restricted wording. An embedding estimate uses ceil(UTF-8 bytes / 4), explicitly a heuristic, at $0.13 per million tokens. This is not measured token usage.

Audit also constructs pools for available query vectors and lists R2/R3 cache misses. Rerank estimates use rendered prompt bytes / 4 plus 4,000 output tokens per missing call, at the recorded model prices. For missing vectors, separately estimate two calls per case with the 30 largest rendered chunks, not a zero rerank budget. This is a planning estimate, not an exact bill or guaranteed ceiling; missing query vectors prevent a complete pool audit and are labelled. There is no answer-generation call. New paid calls need the owner's explicit `--allow-paid`; without it a cache miss fails rather than silently substituting another method. Rerank operational/validation failures use the existing incoming-order fallback and are counted, not dropped. Sequential execution stops after observed new rerank cost exceeds $3; preserve private cache and choose a new public experiment ID for an interrupted attempt. Provider-side limits remain the owner's responsibility.

## Exact owner commands

Run from the repository root, with local corpus/cache files present. Commit this declaration and implementation before the metric run. No `.env` is loaded by the module; supply the owner's key in the environment only if paid cache misses are authorised.

```bash
# Audit only, no API calls, no retrieval quality metrics:
uv run python -m labourlens.retrieval.heldout_metrics --id heldout-retrieval-20261103-audit-d
# Preferred run, no API calls; refuses incomplete caches:
uv run python -m labourlens.retrieval.heldout_metrics --id heldout-retrieval-20261103-offline --run
# Only if the audit shows misses and the owner authorises paid calls:
uv run python -m labourlens.retrieval.heldout_metrics --id heldout-retrieval-20261103-paid --run --allow-paid
```

Each ID is single use. Outputs are `experiments/eval/<id>/audit.json`, then `metrics.json` and `scores.jsonl` on a completed metric run. Scores contain IDs/ranks only, never source text. Frozen results are never overwritten. The audit command does not compute hit rates or MRR. If corpus/cache prerequisites are unavailable, report the failure rather than running another configuration.

## Offline verification commands

```bash
uv run pytest -q tests/retrieval/test_heldout_metrics.py
# Intent-to-add makes new source, tests and this declaration visible to repository scanners:
git add -N src/labourlens/retrieval/heldout_metrics.py tests/retrieval/test_heldout_metrics.py docs/experiments/heldout-retrieval-metrics.md
uv run labourlens rights-scan
make docs-check
```

## Observed cache audit, no retrieval quality run

**MEASURED RESULT, 3 November 2026:** audit-only commands with IDs `heldout-retrieval-20261103-audit` and `heldout-retrieval-20261103-audit-b` completed without API calls. The second adds the planning estimate for unknown candidate pools; neither computed hit rates or MRR. Rights-scan found one copied-question wording violation in each audit, so those original audit bytes are retained privately, not published. The public audit uses case IDs and question hashes rather than copied questions: [rights-safe audit](../../experiments/eval/heldout-retrieval-20261103-audit-c/audit.json).

Eligible text n is **18 of 31** registered cases and **34 of 65** fresh cases. No eligible gold passage IDs are unresolved in the local corpus. All **52 exact questions** need new query embeddings in the audited cache state; existing end-to-end tool queries are not silently substituted. Estimated embedding input is 1,505 heuristic tokens, **$0.00019565**, not measured usage. Rerank candidate pools cannot yet be determined, so zero inspected cache misses is not evidence of a complete rerank cache. Planning for two calls per case, with the largest 30 rendered chunks and 4,000 output tokens each, gives **$0.385627** for up to 104 rerank calls, an estimate rather than a bill. There is no answer-generation step.

The next real metric run therefore needs owner-authorised embedding/rerank calls or pre-populated exact caches. Use the paid command above only after authorisation. No held-out retrieval-quality result is claimed in this preparation.

**Observed offline checks, 3 November 2026:** `uv run pytest -q tests/retrieval/test_heldout_metrics.py tests/retrieval/test_experiments_rerank_tag.py tests/retrieval/test_evaluate.py` passed 19 tests, including the expected network-free cache-miss failure and complete synthetic cache-only output. After intent-to-add for new public files, `uv run labourlens rights-scan` reported zero hits (21 allowlisted globs), and `make docs-check` reported zero problems in 213 Markdown files. The initial rights failure above was fixed by excluding copied question text, not by changing the scanner or adding an exception.

## Subsequent measured result

The authorised metric run is complete. See [results](heldout-retrieval-metrics-results.md) and [immutable metrics](../../experiments/eval/heldout-retrieval-20261103-paid/metrics.json). The preparation and cache-audit statements above record their pre-run state; the retrieval-quality measurement gap is now closed.
