# Corpus-v2 migration and credentialed evaluation runbook

**DECISION (D-037, owner, 31 Oct 2026):** adopt `extraction-fixes` and evaluate the corrected corpus separately. No fresh model-based quality result exists yet. All pre-existing result artifacts are **frozen corpus v1**, including agent A1–A5, registered H-r3/H-hybrid, retrieval dev-R*, their scoring sensitivities and the original held-out freeze. Do not overwrite or rescore those artifacts against migrated IDs.

## Preparation actually executed (unpaid, offline)

- `git tag corpus-v1-frozen HEAD`: premerge `8b8c3a9`.
- `git merge --no-commit --no-ff extraction-fixes`: clean merge of `80a287b`; no conflicts, no worker commit. The parent must finalize the merge commit after reviewing all concurrent work.
- Preserved actual premerge passages/index/embedding cache/manifests/processed tables/quality under gitignored `private/corpus-v1-frozen/`; saved the exact v3.5 gold there. Copied the original isolated-worktree `private/extraction-before/` into this checkout (46 baseline passage files). No raw source was changed or fetched.
- `uv run --offline labourlens build`: 43,662 observations, zero quarantine, 255 checks / zero failures. A second invocation through `labourlens.data.build.run()` compared hashes before/after: all 49 passage/Parquet files byte-identical (`artifacts/data-quality/determinism-v2.json`). Quality: 248 pass / seven warnings; injection heuristic: 15,915 passages and 147 statistical text values, zero hits.
- Built and saved `BM25Index.build(chunks, BM25Config()).save('merge200')` from the new passages. Index: `data/index/bm25/merge200-794cf9c9814d-4659afc7`; corpus SHA-256 `794cf9c9814d1f451803adb7de81a829ebda0d708cb98d9a268e7c2fdc0063e0`. There are 1,732 chunks; the index builder is API-free. Dense runtime construction is deferred until credentials are available.
- Gold v3.6 migrates only `passage_ids` in 96 cases. Audit: `experiments/gold/evidence-migration-v3.6.json`; all 61 absent IDs map; no unmapped ID. Three additional dangling `partial_evidence_text` references (DEV-011, DEV-023, HO-016) were found by `gold.validate()` and migrated/disclosed separately. Fifty-four mappings have exact joined text; seven drop only section headings or appendix footer tokens, retaining narrative. Every mapping lists affected cases/fields, text hashes and token overlap. Non-ID fields have the same digest, including labels, facts, calculations, locators, primary flags and owner provenance. This is not new human review.
- Surviving metadata changes: 67 (the branch's original 66 plus D-035's later-added HO-023 cohort-definition passage). No suitability/label change is silently inferred from those changes.
- Corpus fingerprints: `experiments/corpus-snapshots/v1.json` and `v2.json`; no publisher text is included. Original `experiments/heldout/FREEZE.md` remains unchanged.
- Local token estimation used `uv run --offline --with tiktoken python ...`, after the parent cached the package and `cl100k_base` encoding. Initial attempts without that prerequisite failed (module unavailable / absent offline package), before any index or paid request ran.

**Verification handoff:** main agent runs `uv run pytest -q -m 'not corpus'` once after all peer edits land, then `uv run pytest -q tests/data -m corpus`. New gold regression checks all mappings, the exact gold hash and unchanged non-ID projection; merged extraction fixtures exercise expected corrupt-text failures. This worker did not run pytest concurrently with peers. No test pass is claimed here.

## Exact embedding preparation

`artifacts/data-quality/embedding-plan-v2.json` records:

| Item | Count / value |
|---|---:|
| Model / header | `text-embedding-3-large` / off (unchanged) |
| Chunk inputs / unique input texts | 1,732 / 1,282 |
| Unique cached inputs | 506 |
| New unique vectors | **776** |
| Exact local `cl100k_base` input tokens for those misses | **176,211** |
| Saved price (`specs/prices.yaml`) | $0.13 / million input tokens |
| Estimated chunk-embedding cost | **$0.02290743** |

The cache key is SHA-256 of model + NUL + exact embedded text, not passage ID. ID-only changes can reuse vectors; merged text and metadata-driven chunk boundary changes require new ones. Do not clear the cache. The exact arithmetic above is an estimate based on local tokenization; API usage is the billing authority. Retried billed requests can change spend. At preparation time, 258 of 268 static gold-question embeddings were missing from the shared cache (6,974 tokens, $0.00090662 if all requested); retrieval's frozen query-vector files may avoid some requests. Dynamic agent search queries are additional and cannot be known before execution.

## Credentialed commands — run in this order

Run from the repository root with `OPENAI_API_KEY` supplied through the existing secure environment. Never put credentials in shell history, logs or committed files. Single writer: no concurrent build/fetch/index/embedding command. The explicit crosscheck-off setting holds the newly added T-I06 mitigation off for extraction-only X1; all existing input/output guards remain on. Test the mitigation separately as X2 with `LABOURLENS_CROSSCHECK=on` on this same corpus. Preserve run provenance and record negative results.

### 1. Fill only missing production chunk vectors

There is no standalone embedding CLI; construct the existing dense index:

```sh
uv run python -c "from labourlens.retrieval import chunk as c, dense as d, runtime as r; chunks=c.build_chunks(c.CONFIGS[r.CHUNK_CONFIG], c.load_passages()); index=d.DenseIndex(chunks, d.DenseConfig(r.EMBEDDING_MODEL)); print(index.matrix.shape)"
```

Expected shape is `(1732, 3072)` for the unchanged default dimensions; observe rather than assert an API result in advance. Estimated incremental chunk cost **$0.02290743**. Writes only content-keyed missing vectors and local usage logs under `data/index/embeddings/`. Existing frozen backup is untouched.

### 2. Rerun the R0–R3 retrieval study under a new namespace

The existing CLI has hard-coded legacy output names. Do **not** invoke bare `labourlens retrieval-exp2`, which would overwrite dev-R*. This exact wrapper redirects public study artifacts and private vector files without changing the retrieval algorithms or the pre-existing gate for running R3:

```sh
uv run python -c "from pathlib import Path; from labourlens import paths; from labourlens.retrieval import experiments_rerank as e; out=paths.EXPERIMENTS/'runs'/'extraction-v2-X1'; assert not out.exists(), 'new namespace required'; out.mkdir(parents=True); e.RUNS=out; e.MATRIX_FILE=paths.ROOT/'data/runs/extraction-v2-X1/dense_matrix.npy'; e.QV_FILE=paths.ROOT/'data/runs/extraction-v2-X1/query_vectors.json'; e.run('dev', True)"
```

Outputs are `experiments/runs/extraction-v2-X1/dev-R*/` and its summary. Raw rerank responses remain private in the existing content-keyed cache. Saved frozen-v1 R2 and R3 spend was $0.11209 + $0.09598 = **$0.20807** for 128 text cases; use **about $0.21**, plus uncached query embeddings, as a planning estimate, not a promise or new measurement. The implementation's $3 rerank budget remains in force. R3 may be skipped if its existing R1/R2 gain rule is not met; record that negative result rather than force the branch. This study is dev-only; do not tune on held-out results.

### 3. A3-equivalent extraction-only dev run (237 cases, both registered models)

```sh
LABOURLENS_CROSSCHECK=off uv run labourlens agent-exp --split dev --pairs gpt-6-luna gpt-5.6-luna --planner-prompt planner_v1 --answer-prompt answer_v3 --retrieval r3 --tag X1
uv run labourlens eval --exp agent-dev-X1 --split dev --labels gpt-6-luna gpt-5.6-luna
```

The first command saves new private generation and rights-safe score artifacts under `agent-dev-X1`; the second creates new judge/metrics artifacts, not frozen A3 rescoring. Confirm raw records show `crosscheck_enabled: false`. Generation estimate including reranking: **$0.688565 luna6 + $1.256306 luna5.6 = $1.944871**. Judge estimate: **$0.2442 + $0.2592 = $0.5034**. Total approximately **$2.45**, plus dynamic query embeddings. Before execution ensure this new tag has not already been used; on a deliberate rerun choose a new tag rather than overwrite X1.

### 4. Old held-out diagnostic on corpus v2 (31 cases, not new held-out evidence)

Freeze the intended command/configuration and current v3.6 hash (`6169a9deca78cb5908c584bdf7d17b1c8dd9a15ff7840b3752f3bbb4febb2f9b`) before execution. This is a corpus migration sensitivity/diagnostic, **not a fresh confirmatory comparison or evidence-disjoint holdout**. Do not use it to tune or select the security fix or retrieval. The separate held-out redesign must retain its own labels, evidence-disjoint contract, approval/freeze and identifiers.

```sh
LABOURLENS_CROSSCHECK=off uv run labourlens agent-exp --split heldout --pairs gpt-6-luna gpt-5.6-luna --planner-prompt planner_v1 --answer-prompt answer_v3 --retrieval r3 --tag X-r3
uv run labourlens eval --exp agent-heldout-X-r3 --split heldout --labels gpt-6-luna gpt-5.6-luna
LABOURLENS_CROSSCHECK=off uv run labourlens agent-exp --split heldout --pairs gpt-6-luna gpt-5.6-luna --planner-prompt planner_v1 --answer-prompt answer_v3 --retrieval hybrid --tag X-hybrid
uv run labourlens eval --exp agent-heldout-X-hybrid --split heldout --labels gpt-6-luna gpt-5.6-luna
```

| Step | Generation incl. saved rerank estimate | Judge estimate | Combined |
|---|---:|---:|---:|
| Held-out R3 luna6 | $0.080469 | $0.0283 | $0.108769 |
| Held-out R3 luna5.6 | $0.153806 | $0.0298 | $0.183606 |
| Held-out hybrid luna6 | $0.038516 | $0.0236 | $0.062116 |
| Held-out hybrid luna5.6 | $0.083962 | $0.0228 | $0.106762 |
| Four-arm total | $0.356753 | $0.1045 | **$0.461253** |

These are estimates from saved usage repriced with `specs/prices.yaml`, not observed corpus-v2 costs. Details: `artifacts/data-quality/corpus-v2-cost-estimates.json`. Planner/answer cost is recomputed as `(prompt_tokens × model_input_rate + completion_tokens × model_output_rate)/1e6`; recorded rerank usage is added separately, because legacy `cost_per_case_usd` does not include it. Judges use the saved totals as a workload estimate. Actual context sizes, tool paths, retries and caching change spend. Approximate planned sum: embeddings $0.02290743 + retrieval $0.20807 + dev $2.448271 + old held-out $0.461253 = **$3.14050143**, before new query embeddings, retry variation or separate X2/security/evidence-disjoint runs.

## Reproduction and reporting boundary

For historical reproduction, use the `corpus-v1-frozen` code tag in a separate checkout and copy the private frozen stores and exact saved v3.5 gold there; do not restore them over the active corpus-v2 directory. The original registered run's generation gold is still the version/hash in `experiments/heldout/FREEZE.md`, not v3.5 or v3.6. Archived v3.5 is for reproducing the latest saved-output adjudication scores. Code tags alone cannot preserve gitignored data. Keep both local backups and original raw snapshots available.

After paid execution, record actual usage/configuration hashes and per-case outputs under the new identifiers, compare against frozen corpus v1 without replacing it, investigate failures, and distinguish extraction-only X1 from crosscheck-on X2 and the separately designed evidence-disjoint evaluation. No quality gain is established by the passage count or by this runbook.
