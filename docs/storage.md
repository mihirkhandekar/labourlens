# How documents and data are stored

Layers as built (corpus v4, D-080; earlier results belong to v3.1 or older). Background: D-009.

## Layers
| Layer | What | Where | In git? | Status |
|---|---|---|---|---|
| 1. Raw files | Original downloads exactly as fetched: MOM PDFs and HTML, and dataset CSVs | `data/raw/<source_id>/<snapshot_id>/` for documents; `data/snapshots/<source_id>/<snapshot_id>/` for dataset CSVs plus `*.metadata.json` | CSVs and metadata **yes**; MOM documents **no** (all rights reserved or unresolved) | Built |
| 2. Manifest | One record per source: URL, publisher, dates, release stage, snapshot id, SHA-256, rights status | `data/manifests/manifest.json` plus append-only `manifest_history.jsonl` | Yes | Built |
| 3. Structured observations | One row per statistic: value, unit, period, population, adjustment, missing reason, source locator | `data/processed/observations.parquet`; `quarantine.parquet`; `derived_indicators.parquet` | Yes (small, open licence) | Built |
| 4. Passages | One record per text block with page, section, locator, quality flag, text, text hash | `data/passages/<source_id>.jsonl` | **No** (contains MOM text) | Built |
| 5. Keyword index (BM25) | Searchable index over passages | `data/index/bm25/` | No (derived from MOM text) | Built |
| 6. Dense index (embeddings) | Vectors for passages (hosted OpenAI embeddings, D-021), file-based | `data/index/embeddings/` | No | Built |
| 7. Answer and trace logs | Runs, tool calls, citations, feedback | `data/runs/` (raw run outputs, gitignored), `data/audit/` (audit log and `feedback.jsonl`, gitignored); committed scores and metrics in `experiments/` | Scores and metrics yes; raw outputs and MOM text no | Built |

## Why files and not a database server
The corpus is small (corpus v4: 29,760 passages across 106 documents; 36 datasets, 52,020 rows; the evaluated v3.1 had 16,419 passages across 49 documents, and earlier corpora had 13,484 and 15,915 passages). Files in Parquet and JSONL are reproducible, diffable, easy to hash, and need no service to run. DuckDB can query the Parquet directly when needed. A database server would add setup and failure modes without helping the assessment. Revisit if the corpus grows by orders of magnitude.

## Rebuild rule
Everything from layer 3 up is derived and can be rebuilt from layers 1 and 2 with `labourlens build`. A reviewer without the MOM documents can rebuild all statistical layers from the committed CSV snapshots; passages need `labourlens fetch --kind documents` run locally.

## Rights handling
Layers that hold MOM text (1 for documents, 4, 5, 6) stay local. A hosted demo (D-007) must rebuild them at startup behind an allow-list and show only short cited excerpts. Each passage carries `rights_status` and `commit_text` so code can enforce this.
