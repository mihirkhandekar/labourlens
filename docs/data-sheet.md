# LabourLens data sheet

Snapshot date: **2026-10-30**. Analysis window: **2024-Q1 to 2026-Q2** (answer scope). Earlier history is kept for context charts only. Machine-readable twin: `data/manifests/manifest.json`; quality detail: `artifacts/data-quality/quality-report.md`.

**Attribution.** Contains information from data.gov.sg datasets published by the Ministry of Manpower and the Singapore Department of Statistics, accessed 2026-10-30 and made available under the [Singapore Open Data Licence v1.0](https://developers.data.gov.sg/open-data-licence). Not endorsed by any agency. MOM reports and releases are cited and linked, not redistributed.

## At a glance
| | |
|---|---|
| Statistical datasets | 17 (4 core, 13 supporting), 10,896 normalised observations, 880 in answer scope |
| Documents | 16 (4 MOM quarterly reports, 8 advance/final press releases, 4 Labour Force 2025 PDFs) |
| Quality checks | 142 run, 0 failed, 3 warnings (listed below) |
| Spot-check by a human | **Not yet done.** Sheets in `docs/human-review/` |
| Tests | 51 pass (`artifacts/tests/pytest-m1.txt`) |

## 1. Statistical datasets (data.gov.sg, Open Data Licence)
Core datasets (ADR-001) are first four rows; the rest are supporting (ADR-003).

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
| Quarterly labour market reports 3Q25, 4Q25, 1Q26, 2Q26 | 4 PDFs, 59 to 64 pages each | All rights reserved (notice read in the PDFs) | No |
| Labour Force in Singapore 2025 | 4 PDFs | All rights reserved (notice read in the PDFs) | No |
| Advance and final press releases for the same four quarters | 8 HTML pages | **Unresolved**: MOM terms-of-use page could not be read by an automated fetch | No |

Documents are fetched by script into `data/raw/` (gitignored). Extracted text lives in `data/passages/` (gitignored). The repository carries ids, hashes, locators and links only.

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

**Garbled PDF text.** The last page of each of three reports (reader feedback form) uses an unmapped font. 5 blocks per report are detected as garbled and flagged; they are excluded from retrieval later. Table-like blocks (about 55 to 60% of passages) are flagged `table_unreliable`: do not quote numbers from them without checking the dataset.

**Low-yield PDF.** The Labour Force 2025 survey-findings PDF yields 198 passages over 80 pages, probably image-heavy; flagged by a warning check.

## 6. Quality checks and known warnings
142 checks (manifest integrity, schema, period coverage, duplicates, ranges, hierarchy sums, extraction, page dates, reconciliation, packaging). Warnings: (1) 8 HTML releases have unresolved rights; (2) 47 in-scope industry cells are '-'; (3) the recomputed vacancy ratio differs from the published one.

## 7. Limits
- Extraction quality for tables is not reliable; numbers come from datasets, text supplies explanation.
- Page dates for 8 releases match the catalogue; MOM reports' internal dates were not independently audited beyond that.
- No human has yet verified values; sheets are prepared (`docs/human-review/`).
- Coverage is one snapshot per source, so revision tracking is baseline-only until a second fetch is made.
