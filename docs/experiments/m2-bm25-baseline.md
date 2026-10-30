# M2: BM25 retrieval baseline and first experiments

**Status:** dev-split results only (n=24 text cases), on **unreviewed draft gold labels**. The held-out split has not been run (D-017: it is frozen after owner review). Nothing here is a final result.
Raw outputs: `experiments/runs/dev-*/` (per-case ranked chunk ids, scores, relevance). Summary: `experiments/runs/dev-SUMMARY.md`. Reproduce: `uv run labourlens retrieval-exp --split dev`. Test output: `artifacts/tests/pytest-m2.txt`.

## What was built
| Piece | Where | Notes |
|---|---|---|
| Chunk variants | `src/labourlens/retrieval/chunk.py` | blocks, merge120, merge200, fixed150; every chunk lists `source_passage_ids` (D-015) |
| Tokeniser | `retrieval/tokenize.py` | keeps numbers whole; maps '2Q', 'Q2', 'second quarter' to one token; stemming and stopwords are switches |
| BM25 index | `retrieval/bm25_index.py` | `bm25s` 0.3.16, persisted under `data/index/bm25/<chunk-config>-<corpus-hash>-<config-hash>`; loading against a changed corpus raises `StaleIndexError` (D-012) |
| Gold set | `experiments/gold/draft_cases.jsonl` | 65 draft cases (34 dev, 31 held-out), validated by `labourlens gold-check` (D-017) |
| Metrics and runner | `retrieval/evaluate.py`, `experiments.py` | hit@k, MRR, passage recall, page-level lenient hit, context words, latency |
| Owner review sheet | `docs/human-review/gold-review.md` | two-pass review to limit anchoring; **UNREVIEWED** |

**Correctness check (D-016):** `bm25s` was compared with a plain reference BM25 on a toy corpus. They agree on ranking. The first attempt failed because `bm25s` uses the Lucene form without the textbook `(k1+1)` multiplier, a constant factor that changes scores but not order. The reference now follows Lucene's form (documented in `bm25_index.py`).

## Setup
Queries are the question text unchanged. Scored on the **24 dev cases that have text evidence** (dev has 34 cases; the rest are numerical, clarify, abstain, or refuse and have no text evidence to retrieve). Relevance: a chunk is relevant if it contains any gold passage (stable labels, D-017). Baseline: merge120, stopwords on, period normalisation on, no stemming, k1=1.5, b=0.75. One factor changed per experiment (E1 to E3). E4 combines the best single changes and was added **after** seeing earlier results, so it is exploratory.

**History of the dev set.** The first run used 9 text cases (19 dev cases total; summary kept in `experiments/runs/dev-n9-SUMMARY.md`). Fifteen more dev cases were then drafted (DEV-020 to DEV-034) and everything was re-run on n=24. The extension changed one conclusion: b=0.4 looked slightly better at n=9 and is worse at n=24 (hit@1 0.29 vs 0.33, hit@5 0.42 vs 0.46). That is exactly the small-sample noise D-016 warns about.

## Results (dev, n=24; draft labels)
| E1 chunking | hit@1 | hit@5 | hit@10 | MRR | page_hit@5 (lenient) | context words in top 5 |
|---|---|---|---|---|---|---|
| blocks | 0.21 | 0.42 | 0.50 | 0.29 | 0.46 | 202 |
| merge120 (baseline) | 0.33 | 0.46 | 0.71 | 0.41 | 0.54 | 481 |
| merge200 | 0.38 | 0.54 | 0.79 | 0.48 | 0.58 | 660 |
| fixed150 | 0.25 | 0.58 | 0.67 | 0.41 | 0.58 | 738 |
| merge120 + table blocks | 0.29 | 0.46 | 0.71 | 0.40 | 0.54 | 529 |

| E2 / E3 / E4 (vs merge120 baseline) | hit@5 | hit@10 | MRR | Paired change in rank of first relevant |
|---|---|---|---|---|
| stemming on | 0.42 | 0.63 | 0.35 | 2 better, 6 worse |
| stopwords off | 0.50 | 0.75 | 0.43 | 7 better, 1 worse |
| period normalisation off | 0.46 | 0.71 | 0.39 | 3 better, 3 worse (no signal) |
| k1 0.9 / 1.2 / 2.0 | 0.46 each | 0.63 / 0.71 / 0.67 | 0.38 / 0.41 / 0.41 | within noise (k1=0.9 worse) |
| b 0.4 / 0.9 | 0.42 / 0.46 | 0.71 / 0.67 | 0.38 / 0.40 | neither better |
| merge200 + stopwords off | 0.54 | 0.75 | 0.48 | 7 better, 3 worse |
| merge200 + stopwords off + b=0.4 | 0.63 | 0.83 | 0.46 | 9 better, 4 worse; 952 context words |

## What the results do and do not say
- **Sample size.** n=24 is better than 9 but one case is still 4 points. Treat differences of one or two cases as noise. The repeatable directions are: merging beats raw blocks (10 cases worse with blocks, none better), merge200 beats merge120 at about 40% more context, stemming hurts, and removing stopwords helps a little. These are hypotheses for the held-out run, not conclusions.
- **Context cost.** Bigger chunks raise hit rates partly because they cover more text (202 to 738 words in the top 5). Read hit rate beside that column.
- **Why stemming might hurt** is untested. INFERENCE: it merges 'retrenched', 'retrenchment' and 'retrench' (fine) but also unrelated forms, and the questions already use the documents' own forms.
- **No config is locked** (D-018). Combined configs are post-hoc.

## Error analysis (baseline merge120, reading the 24 dev cases)
Rank of the first relevant chunk: 8 at rank 1, 3 at ranks 2 to 5, 6 at ranks 6 to 10, 7 not in the top 10. By family, the weakest is cross-source synthesis (4 of 7 not in the top 10) and revision conflicts (1 of 4 at rank 1). My reading of the 13 cases ranked below 5:
| Cause | Cases | What it suggests |
|---|---|---|
| **Vocabulary mismatch**: 'jobless', 'layoffs', 'return-to-work', 'revised down', 'upbeat', 'end of 2025' versus the documents' 'unemployed', 'retrenchments', 'returned to employment', '4Q' | DEV-008, 009, 010, 012, 025, 026 | The expected weakness of keyword search and the motivation for the dense and hybrid comparison at M3 |
| **Generic footnote chunk wins**: in 5 of the 13, the top chunk is the HTML advance release's `FOOTNOTE` block. It is **not boilerplate**: it carries real caveats (the migrant-domestic-worker exclusion, 'data are preliminary'). It matches generic queries on quarter and employment words but not the specific figure | DEV-003, 012, 029, 030 and others | Do **not** drop footnotes (they matter for revision handling). Candidates to test: smaller HTML chunks (one item each), or period-aware ranking |
| **Wrong quarter**: the same sentence pattern appears in every quarterly report and another quarter's page ranks first | DEV-008, 010, 021, 034 | Metadata filtering by period before ranking, to test at M3 or M4 |
| **Label granularity**: DEV-002's top chunk covers pp.2 to 3 but the gold passage is a neighbouring block on p.2 | DEV-002 | Why the lenient page-level metric is shown; also a question for the owner's review |
All are retrieval errors in the project taxonomy; none involve generation yet. This analysis was written from the dev cases, so any fix tested on them must be confirmed on held-out.

## Pre-registered held-out run (written before running it)
After the owner reviews and freezes the gold set (hash recorded before any held-out run), run exactly three configs once on the held-out split and report all three whatever the outcome:
1. `blocks` (unmodified reference)
2. `merge120` baseline (default tokeniser, k1=1.5, b=0.75)
3. `merge200 + stopwords off` (best single-factor combination on dev)
The config with b=0.4 is excluded from the pre-registration to limit forking paths. If the reviewed gold changes dev results, dev is re-run first and this list is revisited in writing.

## Limitations
- 24 text cases in dev; held-out still unseen.
- Gold labels are AI drafts, with only a spot-check by me of seven cases (evidence matched the stated facts when I read them). Not human-reviewed.
- One query form (the question as typed); no query rewriting.
- HTML section locators are weaker citations than PDF pages.
- Latency is sub-millisecond per query and not a differentiator at this corpus size.
