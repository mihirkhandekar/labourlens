# Data processing log: what we did to the data, and why

Every cleaning, normalisation, extraction and exploration choice in M1, in one place, so any of them can be explained later. Each row names the code that does it and the evidence it works. A choice is listed even when the answer was "we deliberately did nothing". Dates: 2026-10-30 unless stated. Code is under `src/labourlens/data/`; specs under `specs/`.

Principle behind all of it: **never change a number silently, never guess a meaning, and keep the original.** Anything uncertain is flagged or left null with a reason.

## A. Acquisition
| # | What we did | Why | Where / evidence |
|---|---|---|---|
| A1 | Downloaded datasets through the data.gov.sg API, throttled to one call per 13 s | Limit is 5 requests a minute; `datastore_search` already hit HTTP 429 | `data/acquire.py` |
| A2 | Host allow-list and redirect re-check | Fetching only from known publishers is a security control | `acquire.py`, check `manifest.*` |
| A3 | Stripped the signed S3 URL token from stored records | It is a credential-like value | check `manifest.no_signed_url_material` |
| A4 | Stored every download in a hash-addressed snapshot folder; append-only manifest history | Later fetches must never overwrite what an earlier answer was based on | `raw_store.py`; `manifest_history.jsonl` |
| A5 | Re-fetched the four Labour Force 2025 PDFs after finding the manifest rights status was out of sync with the catalog | Rights must match the catalog; the re-fetch gave new snapshot ids | `docs/progress.md` log |

## B. Normalisation of the statistical datasets (`norm-0.1`)
| # | What we did | Why | Alternative rejected | Evidence |
|---|---|---|---|---|
| B1 | One YAML spec per dataset (expected columns, measures, unit, population, adjustment, missing tokens, plausible range) | Schema drift must fail loudly; the spec doubles as documentation | A bespoke parser per file | `specs/datasets/*.yaml`; test `test_schema_drift_is_fatal` |
| B2 | Periods mapped to calendar quarters (`2026-Q2`). Unemployment files use `YYYY-MM`; only quarter-end months (03, 06, 09, 12) are accepted | Avoid silent mis-dating | Rounding odd months to a quarter | `normalize.py`; `test_periods_and_values.py` |
| B3 | Values parsed with a strict numeric regex; undeclared text goes to a quarantine list | `float()` would hide thousand separators, `%`, and stray text | Coercion | quarantine = 0 rows on all 33 datasets |
| B4 | `na` and `-` become null with a reason; real zeros stay zero | Missing is not nil. The publisher does not say whether `-` means nil or suppressed | Filling with 0 | `test_quarterly_long_dash_and_na_are_null_not_zero`; 605 `-` industry cells, 47 in scope |
| B5 | Wide sector table pivoted to long; leading-whitespace hierarchy (4 spaces per level) turned into `sector_path` and `sector_level`; odd indents and orphan rows quarantined | Keeps the parent-child structure so totals can be checked | Flattening the labels | check `sector.children_sum_to_parent_within_rounding` |
| B6 | Hand-curated 42-industry hierarchy for `retrenched_by_industry` | The CSV is a flat list of industry names, but some are subtotals of others | Treating all industries as flat (would double count) | check `industry.children_sum_to_parent_within_rounding` |
| B7 | Every series labelled with population (overall, resident, citizen, establishments, or `unverified_basis`) and adjustment (SA, not adjusted, not applicable, or `unspecified`) | The assessment's data-integrity rule: never mix definitions | One merged "unemployment" series | `StatisticalObservation` model |
| B8 | Rate-style series without a documented adjustment (`resignation_rate`, `recruitment_rate`, `job_vacancy_rate`) labelled `unspecified`; `reentry_6m`, `reentry_12m` and the sector table population `unverified_basis` | The dataset pages do not say; we do not guess | Assuming SA | `docs/data-sheet.md` section 5 |
| B9 | Scope flag `in_answer_scope` for 2024-Q1 to 2026-Q2; earlier history retained | Answers are bounded; history is context for charts | Dropping older rows | 3,790 of 43,662 rows in scope |
| B10 | Plausible-range checks are **validation only** and never filter rows | Outlier removal would hide real shocks such as 2020 | Clipping outliers | checks `*.values_in_plausible_range` |
| B11 | Observation ids are deterministic hashes of source, snapshot, indicator, period, population, adjustment, dimension | Same input gives the same ids; supports tracing and idempotence | Random ids | `test_build_is_idempotent` |
| B12 | Nothing was imputed, forecast, seasonally adjusted by us, or converted between units | Out of scope and unverifiable | | |

**Update, 3 Nov 2026 (D-077).** Row B9 is history: the scope flag `in_answer_scope` now covers 2020-Q1 to 2026-Q2, giving 11,228 of 52,020 rows in scope (4,300 under the 2024-Q1 to 2026-Q2 flag; the 3,790 above was corpus v1). Earlier rows are still retained. The data was rebuilt with `labourlens build` (276 checks, 0 failed; the hierarchy check now skips parent rows whose child cells are publisher `-` markers), then `labourlens export`, `labourlens eda` and `labourlens build-report`. Every dataset has rows from 2020-Q1; the two short-workweek datasets end at 2025-Q4. Missing `-` cells stay missing, never zero. The EDA figure ranges in section F were computed on the earlier window; the regenerated EDA over the wider window shows resident unemployment (SA) between 2.5% and 4.6% across 2020-Q1 to 2026-Q2.

## C. Derived indicators (consistency checks, not answers)
`derived.py` computes three things so the data checks itself. Each row lists the observation ids it came from.
1. Retrenchment parts (permanent plus term contract) minus total. Source rounds to 10 persons, so small gaps are expected.
2. Seasonally adjusted minus not-adjusted unemployment rate, in percentage points.
3. Vacancy ratio recomputed as vacancy count divided by SA overall unemployed, compared with the published ratio. Result: differs by up to 0.67 because vacancies come from an establishment survey and unemployment from a household survey. Recorded as a warning, not an error.

Deliberately **not** computed: retrenchments per 1,000 employees (no verified denominator dataset).

## D. Document extraction (`extract-0.1`)
| # | What we did | Why | Known cost |
|---|---|---|---|
| D1 | PDF text read as positioned blocks, not plain page text | Plain extraction gives no reading-order guarantee, and these reports mix columns, infographics and tables | Heuristic; ordering can still be wrong |
| D2 | Two-column pages read left column then right column | Prose runs in columns | Can misorder unusual layouts; no case flagged `multicolumn_uncertain` |
| D3 | Headings detected by font size (at least 1.15 times the median body size) or bold; kept as `section_heading` on later passages, not as passages | Gives each passage its section context for citations | A bold short line can be mis-read as a heading |
| D4 | Blocks under 40 characters dropped and counted (about 490 to 620 per report) | Page numbers, labels and fragments are noise for retrieval | **This also drops short infographic number panels.** Numbers come from datasets for that reason |
| D5 | Garbled blocks (font-encoding garbage, found on the last page of three reports) flagged `garbled`, not repaired | Repair would invent text | 5 blocks per affected report |
| D6 | Numeric-dense blocks flagged `table_unreliable` (about 55 to 60% of passages) | Flattened tables lose row and column alignment; wrong numbers are worse than none | Table prose also gets flagged sometimes |
| D7 | Passage id = source, page, block, text hash | Stable, citable, detects text change | |
| D8 | Printed page label recorded alongside PDF page number | Citations should match what a reader sees | Not found on every page |
| D9 | HTML: removed script, style, nav, footer; rejoined split ordinals ("19" and "th"); fallback to line-break structure when fewer than 8 paragraphs; locator is `section: heading, item n` | HTML has no pages; page templates add noise | Not checked which releases used the fallback |
| D10 | HTML page dates read from the `<time>` tag and compared with the catalog | Advance versus final timing drives conflict handling | All 8 match |
| D11 | **Not done:** no OCR, no table reconstruction, no header/footer removal, no deduplication of repeated boilerplate | Not needed for M1; each would add risk | Possible M2 refinements, to be decided on evidence |

## E. Reconciliation: how we found the three employment numbers
We looked for the same quantity (total employment change) in three places: the advance release, the final release and the sector dataset. A regex pulled the headline from the HTML releases; I then read all 8 matches by hand and they were correct. The consistent gap to the dataset is **consistent with** a migrant-domestic-worker difference, which is an **inference** (the MOM headline excludes them; the dataset basis is unverified). Code: `reconcile.py`. Test: `test_reconciliation_matches_hand_read_values`.

## F. Exploratory data analysis
The assessment asks for at least two findings with visualisations. We chose findings that serve the product, not decoration.
| Finding | Why chosen | Figure | Design notes |
|---|---|---|---|
| 1. Vacancies per unemployed person fell from 2.34 (2023-Q1) to 1.48 (2026-Q2) while resident unemployment (SA) stayed 2.6% to 2.9% | Shows a core cross-dataset question and why units matter (ratio versus percent) | `fig1_vacancy_vs_unemployment.png` | Dual axis, shaded answer-scope window, source line. Dual axes can mislead; axes are labelled and the claim is descriptive only |
| 2. Retrenchments rose 20.6% in 2026-Q2 (3,830 to 4,620); services about 77% of the top-level industry total | Tests the industry hierarchy and the `-` handling | `fig2_retrenchment.png` | Top-level industries only, to avoid double counting |
| 3. Advance, final and dataset totals differ every quarter | Direct evidence for the revisions and conflict requirement | `fig3_employment_change_reconciliation.png` | Three series per quarter, values labelled |
All findings are descriptive, not causal. They were generated from the validated store (`eda.py`, output `artifacts/data-quality/eda-findings.md`) and have **not** been reviewed by you yet. Figures are about 2.1:1, not 16:9; they will be resized when the report page is built (M7).

## G. Validation
142 checks across manifest, schema, coverage, duplicates, ranges, hierarchy sums, extraction, packaging and reconciliation. Detail: `artifacts/data-quality/quality-report.md`. Tests: `artifacts/tests/pytest-m1.txt`.

## H. Things we chose not to do (so nobody asks later)
- No outlier removal, imputation, smoothing, forecasting or re-seasonalisation.
- No LLM involvement in any data step.
- No MOM text committed, no PDF in git.
- No claim of human verification yet.


## D-019 corpus expansion (30 Oct 2026)
- Added 30 documents (10 quarterly report PDFs 1Q2023 to 2Q2025, 12 advance/final releases 1Q24 to 2Q25, 8 context documents) and 16 quarterly datasets (job vacancy, recruitment, resignation, retrenchment by industry or occupation; citizen unemployment; short work-week). Result: 46 documents, 13,484 passages, 33 datasets, 43,662 observations, 254 checks, 0 failed.
- Rejected at selection: 4 paid-hours datasets (the model has no hours unit) and 6 re-entry datasets (no publisher description).
- Check change: `in_scope_rows_cover_10_quarters` became `in_scope_rows_cover_declared_quarters`. Two short work-week datasets end at 2025-Q4 (declared in their specs), so the expected quarter list stops at the spec's `expected_last_period`. This is not a weakened threshold: every declared quarter must still exist for every series.
- Reconciliation was NOT extended. A trial extension to 2024-Q1..2025-Q2 mismatched: some advance releases give no figure, wording differs, and one final release gives a full-year total (44,500). The 4 hand-verified quarters remain. Also seen while reading (not investigated further): the 1Q 2024 total-employment change appears as 4,700 in the 2Q 2024 release and 3,200 in the 1Q 2025 release, a revision chain.
- 22 sources have unresolved rights (all HTML releases); they stay local-only.
