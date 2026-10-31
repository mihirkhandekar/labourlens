# LabourLens data sheet

Snapshot date: **2026-10-30**; manifest generated **2026-10-30T02:44:54+00:00**. Analysis window: **2024-Q1 to 2026-Q2** (answer scope). Earlier history is context only, not an answerable earlier subject period (D-031). **MEASURED RESULT (31 Oct):** corpus v2 was rebuilt twice offline from the existing immutable raw files with `extract-0.2`; 49 passage/Parquet files were byte-identical across builds (`artifacts/data-quality/determinism-v2.json`). No network refetch or raw-source change.

**Attribution.** Contains information from data.gov.sg datasets published by the Ministry of Manpower and the Singapore Department of Statistics, accessed 2026-10-30 and made available under the [Singapore Open Data Licence v1.0](https://developers.data.gov.sg/open-data-licence). Not endorsed by any agency. MOM reports and releases are cited and linked, not redistributed.

## At a glance
| | |
|---|---|
| Sources | 79: 33 statistical datasets and 46 documents |
| Statistical datasets | 33 (4 core, 29 supporting), 43,662 normalised observations, 3,790 in answer scope |
| Documents | 46: 24 PDFs and 22 HTML releases; 15,915 extracted passages (corpus v2) |
| Rights | 33 verified open-licensed datasets; 24 all-rights-reserved PDFs; 22 rights-unresolved HTML releases |
| Quality checks | Current saved build: 255 checks, **248 pass, 7 warnings, 0 failures** |
| Spot-check by a human | **Not yet done.** Sheets in `docs/human-review/` |
| Historical M1 tests | 51 passed in `artifacts/tests/pytest-m1.txt`; not a current-suite result |

## 1. Statistical datasets (data.gov.sg, Open Data Licence)
Core datasets (ADR-001) are the first four rows. The table is a selected inventory, not all 33 datasets; all source IDs, URLs, hashes and rights records are in the manifest and `data/export/sources.json`. Supporting industry, occupation and workforce-adjustment tables are included under ADR-003 and D-019.

| Source id | Title | Observations | Coverage | SHA-256 (first 10) |
|---|---|---|---|---|
| `resident_unemployment_rate` | Resident Unemployment Rate, Quarterly | 276 | 1992-Q1 to 2026-Q2 | f3be9ef6e2 |
| `vacancy_to_unemployed_ratio` | Job Vacancy to Unemployed Person Ratio | 114 | 1998-Q1 to 2026-Q2 | a6767d98d9 |
| `retrenched_employees` | Number of Retrenched Employees | 114 | 1998-Q1 to 2026-Q2 | 783e51acc3 |
| `employment_change_by_sector` | Changes in Employment by Sector | 3,692 | 1991-Q1 to 2026-Q2 | 8a5f067e69 |
| `overall_unemployment_rate`, `citizen_unemployment_rate` | Unemployment rate, overall and citizen | 276 each | 1992-Q1 to 2026-Q2 | 73166a2b08, 56cfa6f25b |
| `unemployed_overall`, `unemployed_residents` | Number unemployed | 276 each | 1992-Q1 to 2026-Q2 | e7eb43e553, 04c58b53fe |
| `job_vacancy_count`, `job_vacancy_rate` | Job vacancies | 114 each | 1998-Q1 to 2026-Q2 | fb712c4849, 26c128e2e0 |
| `recruitment_rate`, `resignation_rate` | Average monthly rates | 114 each | 1998-Q1 to 2026-Q2 | 2094a9dede, 1b2ab310fb |
| `retrenched_permanent`, `retrenched_term_contract` | Retrenched by contract type | 114 each | 1998-Q1 to 2026-Q2 | 07915e05ce, fa2de87c36 |
| `retrenched_by_industry` | Retrenched employees by industry | 4,700 | 1998-Q1 to 2026-Q2 | 9ac82750b7 |
| `reentry_6m`, `reentry_12m` | Re-entry into employment after retrenchment | 106 each | 2000-Q1 to 2026-Q2 | afc5f10982, 21ad7b0081 |

Full URLs, snapshot ids and licences: `data/export/sources.json`. Raw CSVs: `data/snapshots/`.

## 2. Documents (MOM)
| Group | Items | Rights status (in manifest) | Committed? |
|---|---|---|---|
| Quarterly labour-market reports, 2023-Q1 through 2026-Q2 | 14 PDFs | Verified all rights reserved | No |
| Labour-force publications for 2024 and 2025 | 8 PDFs, four per year | Verified all rights reserved | No |
| Job-vacancy 2025 and wage-practices 2024 reports | 2 PDFs | Verified all rights reserved | No |
| Advance and final quarterly releases, 2024-Q1 through 2026-Q2 | 20 HTML pages | **Unresolved**, not permission to redistribute | No |
| Job-vacancy 2025 and wage-practices 2024 releases | 2 HTML pages | **Unresolved**, not permission to redistribute | No |

Documents are fetched into `data/raw/` (gitignored); extracted text stays in `data/passages/` (gitignored). The repository carries identifiers, hashes, locators and links, not full MOM documents or extensive extracted text. Public accessibility does not grant redistribution permission. All 22 unresolved-rights sources stay local-only pending individual rights clearance.

## 3. Provenance
Every source has a manifest entry: original URL, publisher, title, publication and retrieval dates, release stage (advance, final, annual), snapshot id, SHA-256, rights status and note, transformation version. Every observation and passage carries `source_id`, `snapshot_id` and a locator (CSV row and column, or PDF page and block). `uv run labourlens trace <observation_id|passage_id>` prints the full chain. Snapshots are immutable and hash-addressed; re-fetching never overwrites, and `data/manifests/manifest_history.jsonl` is append-only.

## 4. Transformations (`norm-0.1`)
1. Period normalisation to calendar quarters (`2026-Q2`); the unemployment datasets use `YYYY-MM` quarter-end months and are mapped, other months are rejected.
2. Values parsed strictly. Declared missing tokens (`na`, `-`) become null with a reason. A missing value is never turned into zero.
3. Wide tables (sector) pivoted to long; the leading-whitespace hierarchy becomes `sector_path` and `sector_level`.
4. Population and adjustment labelled per series (overall, resident, citizen, establishments; seasonally adjusted or not). Never mixed.
5. Nothing is forecast or imputed.

## 5. Things a reader must know
**Three employment-change numbers per quarter.** For 2026-Q2: MOM advance release 10,700; MOM final report 11,400; sector dataset total 14,700. Advance versus final is a revision. Dataset versus final differs by 3,100 to 5,100 persons in every quarter we checked. MOM's headline excludes migrant domestic workers; the dataset's basis is unverified. That the gap is a migrant-domestic-worker effect is an **inference**, not a verified fact. See `docs/presentation-plan.md` section 3 and `artifacts/figures/fig3_employment_change_reconciliation.png`.

**Ratio is not a rate.** The vacancy-to-unemployed ratio counts vacancies per unemployed person; it is not a percentage. Our recomputation from the vacancy count and overall unemployed differs from the published ratio by up to 0.67 because they come from different surveys. Treated as a warning, not an error.

**'-' cells.** 605 industry cells (47 in the answer scope) are '-' in the source. The publisher does not say whether that means nil or suppressed, so they stay null and are never read as zero.

**Rounding and units.** Retrenchment figures are rounded by the publisher. Rates are percentages; changes between rates are percentage points.

**Not computed.** Retrenchments per 1,000 employees: no verified denominator dataset.

**PDF extraction flags.** Across the rebuilt extraction records, 7,055 PDF blocks are `table_unreliable`, 8,091 are `ok`, and 246 are `garbled`. Including HTML gives 8,614 `ok` passages. The 57 previously control-bearing `ok` blocks are now flagged, not repaired by guessing. Conservative layout headings retain narrative; footers become printed labels; note fragments retain explicit adjacency/context requirements. Article-bounded HTML preserves revision evidence while keeping rights notices in local metadata. Same-source duplicates collapse only during context assembly. Flagged tables are not a reliable numerical answer source; use compatible validated dataset records.

**Low-yield PDF.** The Labour Force 2025 survey-findings PDF yields 250 passages over 80 pages after extraction corrections (198 on frozen corpus v1). Image-heavy content is a possible explanation, not a verified diagnosis.

## 6. Quality checks and known warnings
The rebuilt `artifacts/data-quality/validation.json` and `quality-report.md` agree: **255 checks = 248 passes + 7 warnings + 0 failures**. The ingestion heuristic scanned 15,915 passages and 147 distinct statistical text values with zero hits. This is not evidence of complete injection resistance; the heuristic can miss paraphrases. Frozen corpus v1 had 13,484 passages; its retrieval/answer results must not be attributed to corpus v2. D-037 and `docs/experiments/m7-corpus-v2-runbook.md` record preservation, migration and separately labelled reruns.

Checks cover manifest integrity, schemas, periods, duplicates, ranges, hierarchy sums, extraction, dates, instruction-like source content, reconciliation and packaging. Warnings are unresolved rights for 22 HTML sources; undefined dash markers in five tables (47 retrenchment-industry, 50 permanent-industry, 288 term-contract-industry, 3 term-contract-occupation and 28 short-workweek/temporary-layoff-industry in-scope cells); and the recomputed vacancy ratio discrepancy. These are observed offline-build results, not proof of human verification.

## 7. Limits
- Extraction quality for tables is not reliable; numbers come from datasets, text supplies explanation.
- Saved page-date checks cover releases; internal PDF dates and representative extraction fidelity still need human inspection.
- No human has yet verified values; sheets are prepared (`docs/human-review/`).
- Coverage is one snapshot per source, so revision tracking is baseline-only until a second fetch is made.

## 8. Corpus v3 batch for the evidence-disjoint held-out (PREPARED, NOT YET FETCHED)

**Status:** catalogued in `specs/sources.d/heldout-v2-expansion.yaml` (D-040); nothing fetched, built, indexed or embedded. Sections 1 to 7 above describe corpus v2 (46 documents, 33 datasets) until the run in `docs/experiments/m7-corpus-v3-runbook.md` completes; **no count above has been changed**. Excluded by owner decision: MTI GDP advance/Economic Survey pairs.

| Source id | Kind | Publisher | Publication date | Stage | Rights (local-only for documents) | Fetched / SHA-256 / rows / passages |
|---|---|---|---|---|---|---|
| `mom-wage-practices2025` | PDF | MOM MRSD | 2026-05-28 | annual | all rights reserved (to re-confirm on file) | TBD |
| `mom-nwc-lower-wage2025` | PDF | MOM MRSD | 2026-10-23 (PDF creation date; confirm) | annual | all rights reserved (to re-confirm on file) | TBD |
| `mti-2026-q2-feature-ai-employment` | PDF | MTI | 2026-08-11 | not applicable | unresolved | TBD |
| `unit_labour_cost_index_quarterly` | dataset | SingStat | TBD (lastUpdated) | snapshot | Open Data Licence assumed; to verify on dataset page | TBD |
| `value_added_per_worker_quarterly` | dataset | SingStat | TBD | snapshot | as above | TBD |
| `avg_weekly_paid_hours_quarterly` | dataset | MOM | TBD | snapshot | as above | TBD |

Expected coverage (checked by the build, exact first periods): ULC 1980-Q1 to 2026-Q2; value added per worker 1991-Q1 to 2026-Q2; paid hours 1998-Q1 to 2026-Q2. Units added to the schema: `index_2015_100`, `chained_2015_dollars`, `hours_per_week`; adjustment status is `unspecified` for all three because the dataset titles do not state it.

**To fill after the run (do not pre-fill):** at-a-glance counts (sources, documents, datasets, observations, passages); quality check totals; extraction flags for the three PDFs; additivity result against `experiments/corpus-snapshots/v2.json` and `v2-observations.json`; fingerprint `experiments/corpus-snapshots/v3.json`; confirmation of each dataset's licence and of the NWC publication date.
