# E1b: exploratory BM25 chunk sizes 300 and 400

## Protocol (written before computing results)

**HYPOTHESIS / INFERENCE:** larger chunks may raise passage-labelled hit rates partly because they cover more text, at a context-word cost. There is no prior claim of improvement beyond 200 words. This is dev-only, exploratory, not pre-registered for a test set, and BM25 only. No API calls, embeddings, hybrid, filtering, or reranking will run.

**FACT — inputs:** code commit `acdb1f71aeb0bb42574437732466276e1262b5d0`; gold `experiments/gold/draft_cases.jsonl`, SHA256 `6169a9deca78cb5908c584bdf7d17b1c8dd9a15ff7840b3752f3bbb4febb2f9b`. Use exactly `evaluate.text_cases(evaluate.load_cases("dev"))`, as `experiments_rerank.run` does for retrieval-exp2: answer / ignore_injection_and_answer cases with nonempty evidence_text. Read only the 49 passage files named by `experiments/corpus-snapshots/v3.1.json`, verifying every file SHA256; ignore additional v4 documents. Snapshot merge200 corpus fingerprint: `f3a5734cf43dc93e1712a11b72d00d8eff6baa3b35556c366b8b18e1cf19c7b1`. Verify it against rebuilt merge200. Identify original E1 cases from saved `dev-E1-chunking/merge120.cases.jsonl` and evaluate that id subset with current gold (not a historical gold replay).

**FACT — configurations:** blocks; merge120 (120/30 words); merge200 (200/40); fixed150 (150/30); merge300 (300/60); merge400 (400/80). Existing E1 BM25 defaults: k1=1.5, b=0.75, stopwords on, period normalisation on, no stemming, ok passages only. Merge never crosses source or heading; adjacent eligible passages are grouped, normally at most 1.25× target, with whole-passage overlap that fits the overlap budget and always advances. Single oversized passages and short-tail folding can exceed that nominal cap; actual lengths will be reported. New sizes retain merge200's 20% overlap budget; merge120's historical 25% budget stays unchanged. Fixed windows are layout-blind and passage-id relevance can credit a partially included passage.

**PROTOCOL — measurements and interpretation:** report chunk counts and mean words; hit@1/3/5/8/10; MRR truncated at 10; passage_recall@5; ctx_words@5; first-relevant-rank paired better/worse/same versus merge200 (primary baseline) and merge120 (historical baseline), treating missing top-10 hits as rank 99; and hit@8 by family. Report paired hit@8 better/worse/same and percentile bootstrap 95% intervals for the paired hit@8 difference, resampling cases together 10,000 times with seed 20261110. One case changes a hit rate by 1/n; intervals describe dev-case sampling noise, not unbiased generalisation, and have no multiple-comparison correction. Secondary original E1 subset has much greater noise. Compare context cost alongside recall; a larger relevant chunk is an easier target, not necessarily more precise evidence. Count unique gold passage ids contained in at least one chunk at least 4× their own word length (descriptive threshold, not causal attribution). Show one real case's first relevant top-10 chunk using only ids, locators, words and scores. Build every BM25 config twice and require identical rows and non-timing metrics; latency is excluded from equality. Check old merge120/merge200 config and chunk-id fingerprints against pre-edit values.

**PROTOCOL — preservation and output:** runner must refuse an existing experiment directory or summary, never force/overwrite; write only `experiments/runs/dev-E1b-chunk-size/` and `experiments/runs/dev-E1b-chunk-size-SUMMARY.md`. Preserve frozen outputs byte-for-byte and record checks. Never persist passage text or questions. Estimate (do not execute) fresh corpus embeddings for merge300/400 using total chunk words × assumed 1.33 tokens/word and local `specs/prices.yaml`; report the assumption and distinguish corpus embedding cost from query embeddings and paid rerank inference.

Reproduce offline from repository root: `uv run --offline python scripts/run_chunk_size_300_400.py`. Outputs are append-only; use a fresh checkout/output location to repeat after the default output already exists.

## MEASURED RESULT — primary, n=128

Run date: 2026-11-10. All 49 passage-file hashes, all 16,419 passages, and the snapshot merge200 corpus fingerprint matched. Gold SHA256 remained the protocol value. These are the current retrieval-exp2 dev text cases; no held-out cases were read.

| config | chunks | mean words | hit@1 | @3 | @5 | @8 | @10 | MRR | passage recall@5 | ctx words@5 | vs200 B/W/S | vs120 B/W/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| blocks | 9052 | 25.09 | .0781 | .1562 | .2188 | .2812 | .3203 | .1389 | .1960 | 126.6 | 8/53/67 | 7/52/69 |
| merge120 | 2494 | 96.39 | .1797 | .3281 | .4062 | .4766 | .5156 | .2753 | .3626 | 573.7 | 31/24/73 | 0/0/128 |
| merge200 | 1847 | 127.89 | .1406 | .3359 | .4062 | .4766 | .5391 | .2589 | .3496 | 832.1 | 0/0/128 | 24/31/73 |
| fixed150 | 1900 | 148.74 | .1719 | .3359 | .4141 | .4922 | .5156 | .2729 | .3639 | 732.4 | 26/30/72 | 22/30/76 |
| merge300 | 1598 | 147.41 | .1406 | .3438 | .4062 | .4688 | .5000 | .2584 | .3483 | 1058.7 | 23/19/86 | 26/29/73 |
| merge400 | 1494 | 157.15 | .1641 | .3359 | .4297 | .5000 | .5312 | .2733 | .3553 | 1246.7 | 28/21/79 | 28/27/73 |

B/W/S compares first relevant rank, not binary hits. For paired **hit@8 versus merge200**, merge300 has 3 better / 4 worse / 121 same, difference −0.78 percentage points, bootstrap 95% interval [−4.69, +3.12] points. Merge400 has 7 better / 4 worse / 117 same, difference +2.34 points, interval [−2.34, +7.03] points. One primary case is 0.78125 points. Both intervals include zero; these are exploratory, correlated development cases, not a claim of significance or independent test performance.

Full primary/secondary tables, family hit@8, and worked-example records: [isolated summary](../../experiments/runs/dev-E1b-chunk-size-SUMMARY.md). Per-config `*.metrics.json` and `*.cases.jsonl`, and `provenance.json`, are in `experiments/runs/dev-E1b-chunk-size/`. Metrics contain both baseline paired comparisons, including binary hit@8 intervals; cases contain ranked ids/scores/locators/word counts without passage text. Heading locators longer than six words are cut to their first six words followed by an ellipsis, to stay within the six-word quotation limit (rights scan); the cut was applied to the saved files and to the runner.

### Secondary: original E1 ids identified, but one label changed

All 24 original case ids are identifiable from the saved E1 merge120 cases. **FACT:** current gold makes `DEV-034` an abstention with zero text evidence; therefore only 23 of the original 24 remain eligible under the required current selection. The first attempt stopped on this eligibility mismatch before writing outputs. It is not legitimate to fabricate a relevance label, assign a miss, or present these as an exact 24-case historical replay. The run records all original ids, the excluded id, and the 23 eligible ids. The secondary hit@8 values are blocks .3043, merge120 .4783, merge200 .5217, fixed150 .4783, merge300 .5217, merge400 .5652. Relative to merge200, merge300 changes no binary hit@8 outcomes; merge400 gains one case (4.35 points, interval [0, 13.04] points). One secondary case is 4.3478 points. Read this as a tiny descriptive subset, not corroborating held-out evidence.

### Easier-target effect and worked example

Of 140 unique gold passage ids in the primary set, the number contained in at least one chunk at least 4× the passage's own word count is: blocks 0, merge120 33, merge200 51, fixed150 41, merge300 73, merge400 84. This is corpus membership, not necessarily a retrieved or successfully used passage. Fixed-window ids can include only part of a passage. These counts support the relevance-granularity caveat, not a causal estimate of how many extra hits were caused by chunk coverage.

Worked example `DEV-004` (selected as the first input case with a relevant top-10 chunk in all four merge configs and differing ranks; no passage text):

| config | first relevant rank | chunk id | source id | locator | words | BM25 score |
|---|---:|---|---|---|---:|---:|
| merge120 | 4 | `3f5cf8a4118d03f7` | `mom-2026-q2-final` | p.6 | 106 | 7.2955 |
| merge200 | 2 | `ccd1331952a1dd77` | `mom-2026-q2-final` | p.6 | 106 | 7.3974 |
| merge300 | 2 | `0c6e5ad352ea92ea` | `mom-2026-q2-final-release` | section: Main Findings, item 1 to section: Main Findings, item 4 | 323 | 7.6985 |
| merge400 | 2 | `e041d64e80197bcd` | `mom-2026-q2-final-release` | section: Main Findings, item 1 to section: Main Findings, item 4 | 323 | 7.8400 |

Scores are index-specific and not calibrated across chunkings. Family hit@8 gains for merge400 versus merge200 occur in factual_lookup (30/50 to 33/50); all other family hit@8 totals are unchanged. Small families (especially n=2) are noisy.

## INFERENCE — honest reading

This does not establish a retrieval improvement beyond 200 words. Merge300 loses one net hit@8 and five net hit@10 cases versus merge200, while increasing top-five context words by 27.23%. Merge400 gains three net hit@8 cases but loses one net hit@10 case, with 49.83% more context. Its modest MRR/hit@5 increases coexist with broad paired intervals and substantially larger gold-containing chunks. Merge120 matches merge200's hit@8 with less context and higher MRR in this experiment, so these BM25-only observations also do not retrospectively prove that the provisional 200-word runtime choice was optimal. Nothing here re-tests hybrid retrieval, metadata filters, reranking/R3, generation, answer quality, or the expanded v4 corpus. Keep the shipped default unchanged on this evidence; a paid follow-up would require its own approved comparison and input accounting.

## ESTIMATE — paid follow-up, not executed

Assumption: 1.33 embedding tokens per whitespace word (not a tokenizer measurement), including overlap; new chunk identities require fresh embeddings, no cache reuse assumed. Cached `specs/prices.yaml` lists text-embedding-3-large at $0.13/M input tokens (the runtime model), small at $0.02/M. These are local recorded prices, not freshly verified provider quotes.

| config | total chunk words | estimated new embedding tokens | large USD | small USD | illustrative R3 candidate-text input tokens | illustrative R3 candidate-text input USD |
|---|---:|---:|---:|---:|---:|---:|
| merge300 | 235558 | 313292 | .040728 | .006266 | 752842 | .075284 |
| merge400 | 234785 | 312264 | .040594 | .006245 | 802606 | .080261 |

Both fresh large embedding corpora together: approximately $0.081322, plus query embeddings if uncached. A hybrid-only follow-up adds no chat/rerank calls. Illustrative R3 inference uses the existing pool size 30 × 128 cases × corpus-average chunk words × 1.33 tokens/word, with the existing `gpt-6-luna` input price $0.10/M. This is a candidate-text-only scenario, **not an all-in forecast or upper bound**: actual hybrid/filter pools may select systematically longer chunks; prompt, question, metadata/XML, output/reasoning tokens ($0.50/M output), query embeddings, and generation are excluded. Candidate text plus fresh large corpus embeddings is roughly $0.116012 for merge300 and $0.120855 for merge400 before those omitted costs. No embeddings, API calls, or reranking were executed.

## Observed execution and identity checks

- `git status --short && git rev-parse HEAD`: initially only unrelated untracked `untitled.md`; commit recorded above.
- `shasum -a 256 experiments/gold/draft_cases.jsonl`: protocol SHA256 matched.
- Pre-edit `uv run --offline python -c ...` built merge120/merge200 and recorded config hashes `f462aa03` / `1b6eaa43`; SHA256 of newline-joined ordered chunk ids `2a6288fef3d75546703fe8bd2b74337565f488e9a48c75a9134244259293b5a0` / `4f3724fc92fca21a507e67441846e08c73420f885d493c413c8e812926dd0e13`. Runner assertions confirmed unchanged after the two CONFIGS additions.
- `uv run --offline python scripts/run_chunk_size_300_400.py`: initial eligibility assertion failed before any outputs; after recording the changed `DEV-034` label and limiting the secondary to eligible ids, the command completed successfully. Observed: six configs each built twice, identical complete case rows (including scores) and all non-timing metrics; all 49 source file hashes and merge200 v3.1 corpus fingerprint verified. Latency naturally varies and is excluded from determinism.
- Preservation check: SHA256 compared all 12,533 pre-existing files in `experiments/runs/dev-*`, `experiments/eval/`, `experiments/heldout*/`, `experiments/gold/`, and `data/` against an in-memory pre-edit manifest: **0 changed**, no missing files. No private bytes were printed or persisted in the manifest.
- Final `git status --short && git diff --stat`: this task adds only this document, the isolated run directory/summary, and the runner, plus exactly two insertions in `src/labourlens/retrieval/chunk.py`. No existing `experiments/runs/dev-*` output appears as modified. Concurrent presentation work also appears in README, demo-plan, CSS, deck JS and two new presentation JS files; those are outside this task. The unrelated initial `untitled.md` remains untouched.
