# M2: BM25 retrieval baseline and first experiments

**Status:** dev-split results only, on **unreviewed draft gold labels**. The held-out split has not been run (D-017: it is frozen after owner review). Nothing here is a final result.
Raw outputs: `experiments/runs/dev-*/` (per-case ranked chunk ids, scores, relevance). Summary: `experiments/runs/dev-SUMMARY.md`. Reproduce: `uv run labourlens retrieval-exp --split dev`. Test output: `artifacts/tests/pytest-m2.txt`.

## What was built
| Piece | Where | Notes |
|---|---|---|
| Chunk variants | `src/labourlens/retrieval/chunk.py` | blocks, merge120, merge200, fixed150; every chunk lists `source_passage_ids` (D-015) |
| Tokeniser | `retrieval/tokenize.py` | keeps numbers whole; maps '2Q', 'Q2', 'second quarter' to one token; stemming and stopwords are switches |
| BM25 index | `retrieval/bm25_index.py` | `bm25s` 0.3.16, persisted under `data/index/bm25/<chunk-config>-<corpus-hash>-<config-hash>`; loading against a changed corpus raises `StaleIndexError` (D-012) |
| Gold set | `experiments/gold/draft_cases.jsonl` | 50 draft cases (19 dev, 31 held-out), validated by `labourlens gold-check` (D-017) |
| Metrics and runner | `retrieval/evaluate.py`, `experiments.py` | hit@k, MRR, passage recall, page-level lenient hit, context words, latency |
| Owner review sheet | `docs/human-review/gold-review.md` | two-pass review to limit anchoring; **UNREVIEWED** |

**Correctness check (D-016):** `bm25s` was compared with a plain reference BM25 on a toy corpus. They agree on ranking. The first attempt failed because `bm25s` uses the Lucene form without the textbook `(k1+1)` multiplier, a constant factor that changes scores but not order. The reference now follows Lucene's form (documented in `bm25_index.py`).

## Setup
Queries are the question text unchanged. Scored on the **9 dev cases that have text evidence** (the other dev cases are numerical, clarify, abstain, or refuse and have no text evidence to retrieve). Relevance: a chunk is relevant if it contains any gold passage (stable labels, D-017). Baseline: merge120, stopwords on, period normalisation on, no stemming, k1=1.5, b=0.75. One factor changed per experiment (E1 to E3). E4 combines the best single changes and was added **after** seeing E1 to E3, so it is exploratory.

## Results (dev, n=9)
| E1 chunking | hit@1 | hit@5 | hit@10 | MRR | page_hit@5 (lenient) | context words in top 5 |
|---|---|---|---|---|---|---|
| blocks | 0.11 | 0.33 | 0.33 | 0.16 | 0.44 | 141 |
| merge120 (baseline) | 0.33 | 0.33 | 0.56 | 0.36 | 0.56 | 352 |
| merge200 | 0.44 | 0.56 | 0.78 | 0.51 | 0.67 | 558 |
| fixed150 | 0.11 | 0.56 | 0.67 | 0.32 | 0.56 | 730 |
| merge120 + table blocks | 0.33 | 0.33 | 0.56 | 0.36 | 0.56 | 395 |

| E2 / E3 / E4 (vs merge120 baseline) | hit@5 | hit@10 | MRR | Paired change in rank of first relevant |
|---|---|---|---|---|
| stemming on | 0.33 | 0.44 | 0.29 | 0 better, 2 worse |
| stopwords off | 0.44 | 0.67 | 0.39 | 3 better, 0 worse |
| period normalisation off | 0.33 | 0.67 | 0.38 | 2 better, 0 worse |
| k1 0.9 / 1.2 / 2.0 | 0.33 | 0.44 / 0.56 / 0.44 | 0.34 / 0.36 / 0.35 | within noise |
| b 0.4 / 0.9 | 0.33 | 0.56 / 0.44 | 0.37 / 0.29 | b=0.4 slightly better, b=0.9 worse |
| merge200 + stopwords off | 0.56 | 0.67 | 0.44 | 3 better, 1 worse |
| merge200 + stopwords off + b=0.4 | 0.78 | 0.78 | 0.47 | 4 better, 1 worse; but 900 context words |

## What the results do and do not say
- **Sample size.** n=9 means one case is 11 percentage points. Differences of one or two cases are noise. Directions that repeat (merge beats raw blocks; larger chunks help; stemming does not) are worth testing on the held-out set, not conclusions.
- **Context cost.** Bigger chunks raise hit rates partly because they cover more text. Context words in the top 5 rise from 141 to 900 across the best configs. That is more tokens (cost, and room for distraction) for the model later. Hit rate must be read with that column.
- **Stopwords off helped and period normalisation off did not hurt on these 9 cases,** which is the opposite of the usual advice. The cause is untested (INFERENCE: with very short chunks, removing words may discard signal). It is a hypothesis for the held-out run, not a finding.
- **Not tuned on held-out; combined configs are post-hoc.**

## Error analysis (reading the 9 dev cases, baseline)
Of the 9, 3 hit at rank 1, 2 later (ranks 9 and 10), 4 not in the top 10. By cause (my reading, not measured):
| Cause | Cases | What it suggests |
|---|---|---|
| **Vocabulary mismatch**: question says 'jobless', 'layoffs', 'return-to-work', 'revised down', 'end of 2025'; documents say 'unemployed', 'retrenchments', 'returned to employment', 'December' or '4Q' | DEV-008, 009, 010, 012 | The expected weakness of keyword search; the core motivation for the dense and hybrid comparison at M3 |
| **Boilerplate ranks high**: HTML advance-release `FOOTNOTE` chunks outrank real content for generic queries | DEV-003, 011, 012 | Candidate cleaning step: drop or down-weight footnote sections. Needs evidence before adoption |
| **Wrong quarter**: the same sentence pattern appears in every quarterly report, and a different quarter's page ranks first | DEV-008, 010 | Metadata filtering by period before ranking, to test at M3 or M4 |
| **Label granularity**: DEV-002's top chunk covers pp.2-3 but the gold passage is a neighbouring block on p.2 | DEV-002 | Why the lenient page-level metric is shown; also a question for the owner's review (should the gold include the neighbouring blocks?) |
Category names follow the project taxonomy: all four are retrieval errors; none involve generation yet.

## Pre-registered held-out run (written before running it)
After the owner reviews and freezes the gold set (hash recorded before any held-out run), run exactly three configs once on the held-out split and report all three whatever the outcome:
1. `blocks` (unmodified reference)
2. `merge120` baseline (default tokeniser, k1=1.5, b=0.75)
3. `merge200 + stopwords off` (best single-factor combination on dev)
The config with b=0.4 is excluded from the pre-registration to limit forking paths. If the reviewed gold changes dev results, dev is re-run first and this list is revisited in writing.

## Limitations
- 9 text cases in dev; held-out still unseen.
- Gold labels are AI drafts, with only a spot-check by me of four cases (all four evidence passages matched the stated facts when I read them). Not human-reviewed.
- One query form (the question as typed); no query rewriting.
- HTML section locators are weaker citations than PDF pages.
- Latency is sub-millisecond per query and not a differentiator at this corpus size.
