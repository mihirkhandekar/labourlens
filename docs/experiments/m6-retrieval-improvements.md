# M6 experiment: retrieval improvements (dev split)

Status: dev only, nothing locked, held-out untouched. Gold labels are AI drafts (gold v3), not owner-reviewed. Differences under about 10 points are treated as noise; every headline number carries a bootstrap 95% interval. Nothing here becomes a default without owner approval (D-029).

> **Superseded 1 Nov 2026 (status of the labels).** The status line above describes the state when these runs were scored: AI-drafted gold, not owner-reviewed. The owner has since gone through the gold cases in the review interface and recorded a decision on every one (gold v3.7). The labels are AI-drafted, signed off by the owner; one reviewer, after AI pre-review and after the saved runs were scored; not independent inter-rater evidence. These runs were not rescored on v3.7, and v3.7 changes no score. The limit below about AI-drafted gold and an LLM reranker sharing a notion of relevance still applies, because the labels were AI-drafted first.

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
3. A document matches the period hint if its coverage interval overlaps a named quarter, and the stage hint if its release stage equals it (documents from the source catalogue, `specs/sources.yaml` plus `specs/sources.d/*.yaml`; annual survey documents overlap the quarters of their year and have stage `annual`).
4. **R1a hard filter:** both candidate lists (BM25 and dense) are restricted to documents matching every available hint before taking the top 50 and fusing; if there is no hint, or no document matches, nothing is filtered.
5. **R1b soft boost:** after fusing as in R0, every available hint adds a bonus of 0.5 x 1/(60+1) = 0.0082 to chunks of documents matching that hint (period and stage separately). The bonus is fixed a priori: it is worth roughly a jump of 60 ranks in one list, large against rank noise but not enough to rescue a chunk that neither list ranked in its top 50. A sensitivity check at 0.25x and 1.0x is reported as exploratory and does not select the primary row.

R2 rerank (`rerank.py`, `prompts/rerank_v1.md`): the top 30 R0 chunks, labelled C1..C30 with source id, title, publication date, stage and locator, are shown as XML-escaped untrusted data to `gpt-6-luna`. It returns an ordered list of the labels it judges most useful for answering the question (at most 10, structured output). Invalid, duplicate or unknown labels are dropped; the remaining R0 order fills the rest. Any API failure falls back to the R0 order and is counted.

R3 runs only if both R1 (the better of R1a/R1b) and R2 improve hit@8 over R0 by at least 0.05 individually; then the R1 candidate pool is reranked by R2.

### Metrics and decision rules
hit@k for k in 3, 5, 8, 10 (any gold passage inside the passages of the top-k chunks, which is exactly "gold passage in the top k"); MRR over the top 10; share of gold passages covered at 8; pool recall at 30 and 50 (the ceiling for R2); per-family hit@8; bootstrap 95% CI (2000 resamples over cases, seed 0) for hit@8 and for its paired difference to R0; added latency and cost per query. The best retrieval configuration (highest hit@8, ties broken by MRR, excluding R0) then gets one end-to-end check: whether the gold passage is among the context passages the answer step would build from the first 8 chunks, compared with R0. A change is called real only if the paired-difference interval for hit@8 excludes zero; otherwise it is labelled not separable from noise.

## Current results — gold v3.2 scope correction (MEASURED, dev n=128)

**This section supersedes the v3.1 retrieval numbers retained below.** Owner decision D-031 made nine pre-2024-Q1 subject-period dev questions abstain; they are no longer answerable text cases. GoldFixer reports `gold.validate == []` and the v3.2 changelog is present. No question, retriever, prompt, chunk, vector or experiment rule was changed for this rerun. Only the answerable-case subset changed. The held-out split was not scored.

Command: `PYTHONHASHSEED=0 uv run labourlens retrieval-exp2`. Gold SHA-256: `647b26a2f0faa86be30ad897840bc1887b54f55c27268d141565b94cb22998e8`. All rerank responses were reused from cache; new spend **$0.00**, cumulative previously recorded rerank spend **$0.54**, below the $3 cap. Latency and per-query cost below describe the original cached API calls, not the six-second cached rerun. Generated metrics and per-case scores under `experiments/runs/dev-R*/` now refer to this hash.

| config | hit@3 | hit@5 | hit@8 [95% CI] | hit@10 | MRR@10 | gold-passage coverage@8 | pool recall@30 / @50 | hit@8 diff vs R0 [95% CI] | paired hit@8 better/worse | added latency p50 ms | cost $/query |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R0 | 0.3984 | 0.4922 | 0.570 [0.492, 0.656] | 0.5859 | 0.3244 | 0.485 | 0.7891 / 0.8594 | - | - | 0.0 | 0 |
| R1a | 0.6406 | 0.75 | 0.844 [0.781, 0.906] | 0.8828 | 0.5421 | 0.7539 | 0.9688 / 0.9844 | +0.273 [+0.195, +0.359] | 37 / 2 | 0.67 | 0 |
| R1b | 0.5156 | 0.5859 | 0.719 [0.648, 0.797] | 0.75 | 0.4567 | 0.6302 | 0.8828 / 0.9219 | +0.148 [+0.086, +0.211] | 19 / 0 | 0.2 | 0 |
| R2 | 0.7891 | 0.7891 | 0.789 [0.726, 0.859] | 0.7891 | 0.7643 | 0.7333 | 0.7891 / 0.8594 | +0.219 [+0.148, +0.289] | 28 / 0 | 3826.28 | 0.000876 |
| R3 | 0.9609 | 0.9688 | 0.969 [0.938, 0.992] | 0.9688 | 0.9121 | 0.9182 | 0.9688 / 0.9844 | +0.398 [+0.312, +0.484] | 52 / 1 | 3193.23 | 0.00075 |
| R1b_x0.5 | 0.5 | 0.5469 | 0.656 [0.578, 0.734] | 0.6953 | 0.4162 | 0.5677 | 0.875 / 0.9141 | +0.086 [+0.039, +0.133] | 11 / 0 | 0.21 | 0 |
| R1b_x2 | 0.5781 | 0.6953 | 0.797 [0.734, 0.867] | 0.8125 | 0.4983 | 0.707 | 0.8906 / 0.9219 | +0.227 [+0.148, +0.305] | 30 / 1 | 0.22 | 0 |

### hit@8 by family

| config | adversarial | ambiguity_insufficient_causal | cross_source_synthesis | factual_lookup | numerical_comparison | revision_conflict |
|---|---|---|---|---|---|---|
| R0 | 0.462 (n=13) | 0.0 (n=2) | 0.5 (n=34) | 0.72 (n=50) | 0.8 (n=10) | 0.316 (n=19) |
| R1a | 0.923 (n=13) | 1.0 (n=2) | 0.824 (n=34) | 0.9 (n=50) | 0.8 (n=10) | 0.684 (n=19) |
| R1b | 0.692 (n=13) | 0.0 (n=2) | 0.706 (n=34) | 0.84 (n=50) | 0.9 (n=10) | 0.421 (n=19) |
| R2 | 0.692 (n=13) | 1.0 (n=2) | 0.676 (n=34) | 0.92 (n=50) | 0.9 (n=10) | 0.632 (n=19) |
| R3 | 1.0 (n=13) | 1.0 (n=2) | 0.912 (n=34) | 1.0 (n=50) | 0.9 (n=10) | 1.0 (n=19) |
| R1b_x0.5 | 0.538 (n=13) | 0.0 (n=2) | 0.618 (n=34) | 0.78 (n=50) | 0.9 (n=10) | 0.421 (n=19) |
| R1b_x2 | 0.769 (n=13) | 0.5 (n=2) | 0.765 (n=34) | 0.92 (n=50) | 0.8 (n=10) | 0.579 (n=19) |

### hit@8 by whether the question carries a period/stage hint

| config | has_hint | no_hint |
|---|---|---|
| R0 | 0.458 (n=96) | 0.906 (n=32) |
| R1a | 0.823 (n=96) | 0.906 (n=32) |
| R1b | 0.656 (n=96) | 0.906 (n=32) |
| R2 | 0.729 (n=96) | 0.969 (n=32) |
| R3 | 0.969 (n=96) | 0.969 (n=32) |
| R1b_x0.5 | 0.573 (n=96) | 0.906 (n=32) |
| R1b_x2 | 0.76 (n=96) | 0.906 (n=32) |

Hint coverage: {"any_hint": 96, "period_hint": 91, "stage_hint": 68, "stage_conflict": 9, "filter_active_R1a": 96, "period_hint_but_no_document_in_period": 0, "hint_but_no_filter": 0}

### End-to-end context coverage (retrieval only; best config = R3)

| config | gold passage in the context built from the top-8 chunks | gold passage in the first 8 context passages |
|---|---|---|
| R0 | 0.5703 | 0.4062 |
| R3 | 0.9688 | 0.9375 |

Rerank spend on new API calls this run: $0.0000. Wall time 6s.


### Interpretation and recommendation after the correction

**The conclusion is unchanged:** R1a, R1b and R2 each improve hit@8 over R0 with paired bootstrap intervals excluding zero; R3 remains strongest. R3 versus R2 is +0.1797, 95% CI [+0.1094, +0.2500], with 24 better and one worse. The baseline falls from 0.5985 to 0.5703 as nine previously answerable, mostly easier historical questions leave the set; R3 changes only from 0.9708 to 0.9688. These are different evaluation subsets, not an improvement or regression caused by a retrieval change.

R3 gold-in-context from the first eight chunks is 0.9688 versus R0 0.5703; among the first eight distinct context passages it is 0.9375 versus 0.4062. These are retrieval coverage measures, not answer-quality or scope-policy compliance tests. The four R3 misses remain DEV-006, DEV-010, DEV-026 and DEV-310. The hard-filter blind spot and AI-drafted-gold/LLM-reranker bias remain. Ninety-six of 128 cases carry hints; the smallest strata remain too small for strong claims (ambiguity n=2, numerical n=10, adversarial n=13).

**PROPOSAL:** the evidence still favors R3 for the next retrieval comparison, or R1a if added model latency/dependence is unacceptable. This rerun itself makes no default or architectural decision; later integration/default history is recorded in D-030 and the integration section below. No agent, prompt or integration code was touched or run for this scope-correction rerun.

## Superseded v3.1 results, interpretation and original recommendation

**Historical block only:** everything from the next results heading through the original Recommendation section was measured against gold v3.1 SHA-256 `5d74402e107dae03316e7635a04d1ebc6caf9d4de9fb151174acb6391bfa589b`, n=137. Those numbers and recommendations are preserved verbatim for auditability, not current results. The hypotheses above and deviations below remain part of the experiment record. Current numbers are in the v3.2 section above.

## Results (MEASURED, dev, n=137 answerable text-evidence cases, gold v3.1)
All numbers below are copied from `experiments/runs/dev-R-SUMMARY.md` / `dev-R-summary.json` / `dev-R*/metrics.json`, produced by `PYTHONHASHSEED=0 uv run labourlens retrieval-exp2`. Gold file sha256 `5d74402e...bfa589b`; corpus 2,106 merge200 chunks. Per-case scores: `experiments/runs/dev-R*/scores.jsonl` (chunk ids, ranks, flags; no MOM text). `hit@k` equals "gold passage is among the passages of the top-k chunks". `R1b` is the pre-registered 0.5x bonus; `R1b_x0.5` and `R1b_x2` are the exploratory 0.25x and 1.0x bonuses (1/61 = 1.0x).

| config | hit@3 | hit@5 | hit@8 [95% CI] | hit@10 | MRR@10 | gold-passage coverage@8 | pool recall@30 / @50 | hit@8 diff vs R0 [95% CI] | paired hit@8 better/worse | added latency p50 ms | cost $/query |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R0 | 0.4088 | 0.5182 | 0.599 [0.518, 0.679] | 0.6131 | 0.3374 | 0.5116 | 0.8029 / 0.8686 | - | - | 0.0 | 0 |
| R1a | 0.6496 | 0.7664 | 0.854 [0.796, 0.912] | 0.8905 | 0.5402 | 0.7664 | 0.9708 / 0.9854 | +0.256 [+0.175, +0.336] | 37 / 2 | 0.58 | 0 |
| R1b | 0.5401 | 0.6131 | 0.737 [0.664, 0.810] | 0.7664 | 0.4711 | 0.6472 | 0.8905 / 0.927 | +0.139 [+0.080, +0.197] | 19 / 0 | 0.24 | 0 |
| R2 | 0.8029 | 0.8029 | 0.803 [0.737, 0.869] | 0.8029 | 0.7762 | 0.7436 | 0.8029 / 0.8686 | +0.204 [+0.139, +0.277] | 28 / 0 | 3795.81 | 0.000877 |
| R3 | 0.9635 | 0.9708 | 0.971 [0.942, 0.993] | 0.9708 | 0.9142 | 0.92 | 0.9708 / 0.9854 | +0.372 [+0.285, +0.453] | 52 / 1 | 3177.75 | 0.00075 |
| R1b_x0.5 | 0.5255 | 0.5766 | 0.679 [0.599, 0.759] | 0.7153 | 0.4284 | 0.5888 | 0.8832 / 0.9197 | +0.080 [+0.036, +0.131] | 11 / 0 | 0.24 | 0 |
| R1b_x2 | 0.5985 | 0.7153 | 0.810 [0.745, 0.876] | 0.8248 | 0.51 | 0.719 | 0.8978 / 0.927 | +0.212 [+0.139, +0.285] | 30 / 1 | 0.24 | 0 |

### hit@8 by family

| config | adversarial | ambiguity_insufficient_causal | cross_source_synthesis | factual_lookup | numerical_comparison | revision_conflict |
|---|---|---|---|---|---|---|
| R0 | 0.5 (n=14) | 0.0 (n=2) | 0.514 (n=35) | 0.745 (n=55) | 0.833 (n=12) | 0.316 (n=19) |
| R1a | 0.929 (n=14) | 1.0 (n=2) | 0.829 (n=35) | 0.909 (n=55) | 0.833 (n=12) | 0.684 (n=19) |
| R1b | 0.714 (n=14) | 0.0 (n=2) | 0.714 (n=35) | 0.855 (n=55) | 0.917 (n=12) | 0.421 (n=19) |
| R2 | 0.714 (n=14) | 1.0 (n=2) | 0.686 (n=35) | 0.927 (n=55) | 0.917 (n=12) | 0.632 (n=19) |
| R3 | 1.0 (n=14) | 1.0 (n=2) | 0.914 (n=35) | 1.0 (n=55) | 0.917 (n=12) | 1.0 (n=19) |
| R1b_x0.5 | 0.571 (n=14) | 0.0 (n=2) | 0.629 (n=35) | 0.8 (n=55) | 0.917 (n=12) | 0.421 (n=19) |
| R1b_x2 | 0.786 (n=14) | 0.5 (n=2) | 0.771 (n=35) | 0.927 (n=55) | 0.833 (n=12) | 0.579 (n=19) |

### hit@8 by whether the question carries a period/stage hint

| config | has_hint | no_hint |
|---|---|---|
| R0 | 0.49 (n=102) | 0.914 (n=35) |
| R1a | 0.833 (n=102) | 0.914 (n=35) |
| R1b | 0.676 (n=102) | 0.914 (n=35) |
| R2 | 0.745 (n=102) | 0.971 (n=35) |
| R3 | 0.971 (n=102) | 0.971 (n=35) |
| R1b_x0.5 | 0.598 (n=102) | 0.914 (n=35) |
| R1b_x2 | 0.775 (n=102) | 0.914 (n=35) |

Hint coverage: {"any_hint": 102, "period_hint": 97, "stage_hint": 69, "stage_conflict": 9, "filter_active_R1a": 102, "period_hint_but_no_document_in_period": 0, "hint_but_no_filter": 0}

### End-to-end context coverage (retrieval only; best config = R3)

| config | gold passage in the context built from the top-8 chunks | gold passage in the first 8 context passages |
|---|---|---|
| R0 | 0.5985 | 0.4161 |
| R3 | 0.9708 | 0.9416 |



Rerank usage (R2, final run): median latency 3.8 s per query, p95 7.9 s, mean 6.0k prompt and 330 completion tokens (about 300 of them reasoning), cost $0.00088 per query, 0 failed calls out of 137. R3: 3.2 s median, p95 5.9 s, $0.00075 per query, 0 failures. R1 filter or boost: under 1.2 ms added at p95 (parser plus fusion over cached lists; excludes the query embedding that R0 also needs).

### R3 against R2 (paired)
R3 minus R2 on hit@8: +0.168, 95% CI [+0.110, +0.234], 24 cases better and 1 worse.

### Reading
- **H1 supported.** Both R1 variants beat R0 beyond noise (hard filter +0.256 [+0.175, +0.336], pre-registered soft boost +0.139 [+0.080, +0.197]). Hit@8 on hinted questions goes from 0.49 to 0.83 (R1a); questions without a hint are untouched by construction (0.914). The larger effect is in the cases the earlier review flagged: revision_conflict 0.32 to 0.68, cross-source synthesis 0.51 to 0.83, adversarial 0.50 to 0.93.
- **Hard filter costs two cases.** DEV-006 (the question names 1Q 2026, but the gold passage sits in the 2Q 2026 final release, which restates the earlier quarter) falls outside the filter; DEV-313 stays inside the filter but is ranked below position 8. DEV-006 is the structural risk of a hard filter: later reports revise or restate earlier quarters, so naming a quarter does not guarantee the answer is in that quarter's own documents. A soft boost cannot lose such a case but gains less. The pre-registered boost (0.5/61) was weaker than the hard filter and the exploratory 1.0x boost recovers most of the hard-filter gain (0.810 vs 0.854) with one paired loss; this trend was seen on dev only and is NOT used to pick a primary row.
- **H2 supported, and large.** LLM rerank of the top 30 raises hit@8 to 0.803 [0.737, 0.869] (+0.204 [+0.139, +0.277], 28 better, 0 worse) and MRR from 0.337 to 0.776. The first relevant chunk is rank 1 in 103 of 137 cases (R0: 30). hit@3 = hit@5 = hit@8 = hit@10 = pool recall@30 for R2: the reranker never lost a gold chunk that was in its pool, so every remaining miss is a candidate-generation miss (27 cases). R2 helps most on the cases a lexical or embedding model confuses (factual lookup 0.745 to 0.927).
- **H3 supported.** R3 (hard filter, then rerank) reaches hit@8 0.971 [0.942, 0.993], with the first relevant chunk at rank 1 in 119 of 137 cases. Its pool recall at 30 is 0.971 because the filter lifts candidate generation (R0 pool recall@30 0.803 to R1a 0.971), and the reranker then orders it. It beats R2 by +0.168 [+0.110, +0.234]. The four remaining misses are DEV-006 (outside the filter), and DEV-010, DEV-026, DEV-310 (gold at pool ranks 31, 75 and 38).
- **Where each component helps.** The filter fixes candidate generation (pool recall); the reranker fixes ordering. Neither alone does both. R3 is at least as good as R2 in every family (numerical_comparison ties at 0.917, n=12; there the hard filter loses DEV-006 while the rerank gains elsewhere).
- **End-to-end context coverage (retrieval only, agent not run).** The share of cases where a gold passage is among the passages the answer step would put in context from the top 8 chunks rises from 0.598 (R0) to 0.971 (R3); among the first 8 context passages (after de-duplication) from 0.416 to 0.942. For comparison D-025 measured 69% at k=8 on the older, smaller gold set. This is a coverage ceiling, not an answer-quality measure: whether the model then answers correctly, cites correctly and abstains correctly is not measured here.

## Limits and threats to validity
- **AI-drafted gold, same family of judge.** The gold passages were drafted by AI and not human-reviewed; the reranker is also an LLM and may share the drafter's notion of relevance. The R2 and R3 numbers could therefore be optimistic in a way R1 (a deterministic rule) is not. Human review of a sample of R2/R3 rankings is not done.
- **Question style.** Dev questions were written to name a period and release explicitly. 102 of 137 carry a hint. The R1 gain scales with how often real users name a period; for no-hint questions R1 does nothing. The no-hint rows show R2 alone gives 0.971 vs 0.914.
- **Hard-filter blind spot.** A question about one quarter whose answer lives in a later document is lost (DEV-006). The parser also ignores bare quarters (`Q2`), bare months and years, so a question like "Q4 versus Q1 2026" is filtered only to the quarter that carries a year. This rule was not changed after seeing results.
- **Pre-registration deviations.** (1) The first implementation read only `specs/sources.yaml`, missing the expansion-batch documents in `specs/sources.d/`, so 37 hinted questions found no document and R1/R3 numbers from that run were too low (R1a hit@8 0.701 at that point, R3 0.847). Found from the aggregate hint-coverage count, fixed (catalogue loader now shared with the data layer, test added), and everything was rerun; the first-run numbers are superseded and not reported as results. The rules themselves did not change. (2) Between runs the baseline moved by up to one case at hit@3 and hit@8 (0.599 to 0.606): the shared embedding cache was rewritten by concurrent processes and the hosted embedding API re-embedded some texts with tiny numeric differences that flip near-tied ranks. The experiment therefore freezes query vectors and the chunk-vector matrix on first use (`data/runs/dev-R0/`, gitignored) and the final two runs agree exactly. The bootstrap intervals are far wider than this jitter. [INFERENCE: the cache race as the cause; the symptom (a lost cache and varying near-ties) was observed.] (3) BM25 orders tied scores differently for different `k`; the experiment uses the same call (`k=50`) as the shipped hybrid for R0, and R0 matched the shipped hybrid exactly on the 10 cases checked per run.
- **Not tested:** alternative rerank models, pool sizes other than 30, rerank prompt variants (one prompt, written before measuring, never edited), position bias, cross-encoder rerankers, query rewriting, the held-out split, multi-turn questions, latency under load. The rerank ranking is stored raw in `data/runs/dev-R2/cache/` (labels only).
- Small strata (ambiguity n=2, numerical n=12, adversarial n=14) are too small for family-level claims.
- Cost and latency figures are single-run measurements from the API usage fields and wall time; prices from `specs/prices.yaml` (read 30 Oct 2026). Total spend on paid rerank calls across all runs of this experiment including reruns: $0.54 (700 cached calls, summed from the stored usage); embeddings: re-embedding of dev questions and chunks missing from the shared cache, not separately totalled (the embedding price is $0.13 per million tokens and a question is about 30 tokens).

## Recommendation (PROPOSAL, not adopted; owner approval needed)
1. Prefer R3 (period/release metadata filter, then `gpt-6-luna` listwise rerank of the top 30) as the retrieval configuration to carry into the next agent experiment, because it is the only configuration that moves the coverage ceiling (gold in the top-8 context 0.60 to 0.97) and its gain over each single component is beyond the bootstrap interval on dev.
2. If the owner prefers no added latency or LLM dependence, R1a alone (hard filter, deterministic, about 1 ms, no cost) delivers about two thirds of the coverage gain. R1b needs a stronger bonus than the pre-registered one to compete; do not tune it further on dev.
3. Before adoption: add a guard for the hard filter's blind spot (for example fall back to unfiltered candidates when the filtered pool is too weak, or filter softly for comparison and revision questions), test it as a separate one-factor change, and run the agent end to end on dev to measure answer correctness and abstention, not only coverage. Held-out evaluation should include R0, R1a and R3 as pre-registered configurations.

> Status update, 30 Oct 2026: the end-to-end experiments A3 and A4 ran afterwards (`docs/experiments/m6-agent-end-to-end.md`) and `r3` became the agent default under D-030. The section below describes the integration as first built, when it was opt-in.

## Agent integration (opt-in when built; now the default, see D-030)

**DECISION — implementation scope:** R3 is available to the bounded agent only when explicitly selected. This does not adopt a new default or claim end-to-end improvements. `AgentConfig.retrieval` and `agent-exp --retrieval` accept:

- `hybrid` (default): the original `HybridIndex.search(query, k)` path, unchanged prompts, candidate depths and ranking. The default config key is unchanged, so concurrently starting A2 processes retain the old retrieval behavior.
- `r3`: parse hints from both the planner's rewritten query and the original user question. Union their quarters; union their stage hints, disabling the stage restriction if either input contains conflicting stages or the inputs disagree. Restrict **both full candidate rankings** to matching catalogue documents before taking the first 50 of each and applying RRF (constant 60). No hint or no matching document means no filter. Rerank the first 30 fused chunks with the existing `rerank_v1` prompt and `gpt-6-luna`, then return the requested k. No rerank cache is read or written for agent calls; their paid usage is counted in the run.
- `r3w`: identical to `r3`, except widen back to unfiltered candidates before reranking when the filtered fused pool contains **fewer than 8 chunks**, or the **best filtered raw BM25 score is less than 0.5 times the unfiltered best positive BM25 score** (an empty filtered lexical list also qualifies). The lexical comparison is made before RRF, since RRF resets ranks after filtering and would conceal weak absolute matches. A zero/nonpositive unfiltered BM25 score does not activate the score criterion. These are simple fixed thresholds, **not pre-registered in the retrieval experiment and not tuned on dev cases**. R3w is a separate experimental factor, not a claim that later-report restatements are solved; a large, lexically strong but wrong-period pool can still conceal such evidence.

The rerank uses the remaining tool deadline minus a 0.25 s return margin, including candidate retrieval time in the existing 10 s tool budget. The opt-in HTTP call has a cancellable total deadline and no transport/status retries; failures, deadline exhaustion and unusable rankings retain the unreranked fused order. Existing planner/answer timeouts and prompts are unchanged. A timeout without an API usage response has unknown provider-side billing, as with other failed requests; recorded rerank cost includes returned API usage, not invented tokens.

Search events add `retrieval`, `hints`, `filter_applied`, `filtered_documents`, `filtered_chunks`, `widened`, `reranked`, `rerank_fallback`, `rerank_seconds` and `rerank_cost_usd`. Filter counts describe the surviving candidate pool **before** optional widening. The audit log preserves these fields when present and contains no passage text. Run usage adds rerank tokens, calls, seconds and cost to the existing totals and adds a `rerank_cost_usd` subtotal. No retrieval fields are emitted on the default search path.

**MEASURED RESULT — offline integration verification:** `uv run pytest tests/retrieval tests/test_audit_and_notes.py -q` passed **103 tests**. Fixed fake rankings independently reconstruct the pre-change path and check its passage order and exact tool summary. Fake clients cover filtering below the original top-50 cutoff, hint unions/conflicts, reranking, failure/deadline fallback, both widening criteria, no-hint/no-match behavior, run cost accounting, audit fields and unchanged default config keys. No network calls are made by these tests.

**Not tested:** no agent experiment, evaluation, threat suite, held-out run or paid retrieval run was executed for this integration. Two attempted smoke invocations ran in an isolated subprocess without `OPENAI_API_KEY`; both stopped at the planner with `operational failure: planner: LLMError`, zero recorded calls/cost and no search event. The owner will run the single authenticated smoke from the credential-bearing shell. Consequently real hint/filter/rerank latency/cost fields and answer status remain **unverified** here; offline tests do not establish real end-to-end quality, latency or billing. R3w has no measured retrieval-quality result.

For A3/A4, use the A1 prompts explicitly; tags name separate output directories:

```sh
uv run labourlens agent-exp --split dev --pairs gpt-6-luna gpt-5.6-luna --answer-prompt answer_v3 --retrieval r3 --tag A3
uv run labourlens agent-exp --split dev --pairs gpt-6-luna gpt-5.6-luna --answer-prompt answer_v3 --retrieval r3w --tag A4
```

These commands are instructions only; they were not run. Compare A3 to A1 for the retrieval-only factor; compare A4 to A3 for the widening-only factor.

