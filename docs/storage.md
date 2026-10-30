# How documents and data are stored

Today (M1, built) and planned (later milestones, **PROPOSAL** until decided at the M2 and M3 gates, see D-009).

## Layers
| Layer | What | Where | In git? | Status |
|---|---|---|---|---|
| 1. Raw files | Original downloads exactly as fetched: MOM PDFs and HTML, and dataset CSVs | `data/raw/<source_id>/<snapshot_id>/` for documents; `data/snapshots/<source_id>/<snapshot_id>/` for dataset CSVs plus `*.metadata.json` | CSVs and metadata **yes**; MOM documents **no** (all rights reserved or unresolved) | Built |
| 2. Manifest | One record per source: URL, publisher, dates, release stage, snapshot id, SHA-256, rights status | `data/manifests/manifest.json` plus append-only `manifest_history.jsonl` | Yes | Built |
| 3. Structured observations | One row per statistic: value, unit, period, population, adjustment, missing reason, source locator | `data/processed/observations.parquet`; `quarantine.parquet`; `derived_indicators.parquet` | Yes (small, open licence) | Built |
| 4. Passages | One record per text block with page, section, locator, quality flag, text, text hash | `data/passages/<source_id>.jsonl` | **No** (contains MOM text) | Built |
| 5. Keyword index (BM25) | Searchable index over passages | planned `data/index/` | No (derived from MOM text) | M2, not built |
| 6. Dense index (embeddings) | Vectors for passages; store chosen at M3 (file-based first) | planned `data/index/` | No | M3, not built |
| 7. Answer and trace logs | Runs, tool calls, citations, feedback | planned `experiments/` and `feedback.jsonl` | Metadata yes, MOM text no | M4 to M6 |

## Why files and not a database server
The corpus is small (4,187 passages across 16 documents; 17 datasets, 10,896 rows). Files in Parquet and JSONL are reproducible, diffable, easy to hash, and need no service to run. DuckDB can query the Parquet directly when needed. A database server would add setup and failure modes without helping the assessment. Revisit if the corpus grows by orders of magnitude.

## Rebuild rule
Everything from layer 3 up is derived and can be rebuilt from layers 1 and 2 with `labourlens build`. A reviewer without the MOM documents can rebuild all statistical layers from the committed CSV snapshots; passages need `labourlens fetch --kind documents` run locally.

## Rights handling
Layers that hold MOM text (1 for documents, 4, 5, 6) stay local. A hosted demo (D-007) must rebuild them at startup behind an allow-list and show only short cited excerpts. Each passage carries `rights_status` and `commit_text` so code can enforce this.
