# LabourLens data sheet

Corpus: **v3.1** (the current build, `extract-0.3`, D-052; identical to v3 in sources, observations and passage count) (manifest generated **2026-10-31T05:38:08+00:00**; rights fields of three dataset entries amended afterwards, see section 7). Analysis window: **2024-Q1 to 2026-Q2** (answer scope). Earlier history is context only, not an answerable earlier subject period (D-031). All counts below are read from `data/manifests/manifest.json`, `data/processed/observations.parquet`, `data/passages/*.jsonl` and `artifacts/data-quality/validation.json`; nothing is estimated.

**Attribution.** Contains information from data.gov.sg datasets published by the Ministry of Manpower and the Singapore Department of Statistics, accessed 2026-10-30 and 2026-10-31, made available under the [Singapore Open Data Licence v1.0](https://developers.data.gov.sg/open-data-licence) where that licence applies (see the rights column). Not endorsed by any agency. MOM and MTI reports and releases are cited and linked, not redistributed.

## At a glance
| | |
|---|---|
| Sources | **85**: 36 statistical datasets and 49 documents |
| Statistical datasets | 36 (4 core, 32 supporting), **52,020** normalised observations, **4,300** in answer scope, 0 quarantined rows |
| Documents | 49: 27 PDFs and 22 HTML releases; **16,419** extracted passages in 49 files (`extract-0.3`, corpus v3.1; v3 was `extract-0.2`) |
| Passage quality flags | 9,052 `ok`, 7,121 `table_unreliable`, 246 `garbled` (all control-character); corpus v3 had 9,040 / 7,093 / 286, the 40 extra `garbled` being symbol-ratio false positives fixed in v3.1 (section 5, D-052) |
| Rights | 33 datasets `verified_open_licence`; **3 datasets `assumed_open_unverified`** (local-only); 26 PDFs `verified_all_rights_reserved`; 23 documents `unresolved` (22 HTML releases and the MTI feature PDF) |
| Quality checks | Saved build: **276 checks, 269 pass, 7 warnings, 0 failures** |
| Chunks (`merge200`, `ok` passages only) | 1,847 on corpus v3 and on v3.1 (4 chunk ids and 10 chunk texts differ, all in the MTI article) |
| Spot-check by a human | Updated 1 Nov 2026: the owner went through the 30 source checks (16 passage extraction, 14 statistical rows) in the review interface and recorded a decision on each, after AI pre-review. Final source decisions: 18 matches and 12 minor; the first export (19 matches, 11 minor) is historical. Agreement of those decisions with the AI suggestion was 29 of 30 (agreement, not accuracy). The checks are AI-drafted, signed off by the owner; one reviewer, after AI pre-review and after the saved runs were scored; not independent inter-rater evidence. The owner accepted five disclosed frozen extraction gaps after inspecting the original pages (J10, accept_limits); the gaps were not fixed in the saved runs. Detail in `docs/human-review/owner-review-final-summary.md` |
| Historical M1 tests | 51 passed in `artifacts/tests/pytest-m1.txt`; not a current-suite result |

## Corpus version history
| Version | Sources | Passages | Chunks | Extraction | Fingerprint | Used by |
|---|---|---|---|---|---|---|
| **v1 (frozen)** | 79 (33 datasets, 46 documents) | 13,484 | not recorded | `extract-0.1` | `experiments/corpus-snapshots/v1.json` | Dev and held-out v1 results, E1 to E7 retrieval runs, G and A1 to A5 answer and agent runs, threat suite; all frozen, never rescored on another corpus |
| **v2** | 79 (33 datasets, 46 documents) | 15,915 | 1,732 | `extract-0.2` | `experiments/corpus-snapshots/v2.json`, `v2-observations.json` (33 sources, 43,662 rows) | X1 extraction-only dev run and the held-out diagnostic rerun (D-037, D-041) |
| **v3** | 85 (36 datasets, 49 documents) | 16,419 | 1,847 | `extract-0.2` | `experiments/corpus-snapshots/v3.json` (immutable) | Every measured v3 evaluation, including the 65 held-out v2 cases (labels owner-reviewed before the run; see `docs/experiments/m7-heldout-v2-result.md`); served on the Droplet until the v3.1 upload |
| **v3.1 (current build)** | 85 (36 datasets, 49 documents) | 16,419 | 1,847 | `extract-0.3` | `experiments/corpus-snapshots/v3.1.json`, diff `v3.1-diff.json` | Local data on disk; the site after the re-embed and upload. 40 MTI passages relabelled (D-052); 48 of 49 passage files byte-identical to v3 once the `parser_version` value is reverted; two builds gave 52 byte-identical files (`determinism-v3.1.json`). Current-corpus evidence now includes the D-055 fresh re-run, FIN/FIN2 final evaluations, V31 retrieval, the 65-case served-chain sample and fresh 2 Nov threat run (D-061); earlier results retain their original build labels |

The post-fix T-I06 threat run (`experiments/threats/m7-ti06-postfix-20261031`) does not record its corpus label in its `SUMMARY.md`. v3 is additive: every v2 passage file and every v2 per-source observation hash is unchanged (corpus tests in `tests/data/test_corpus_v3_additive.py` passed on the local build; two builds gave 52 byte-identical files, `artifacts/data-quality/determinism-v3.json`). Metrics reported for v1 or v2 must not be read as v3 results (D-040).

## 1. Statistical datasets (data.gov.sg)
Core datasets (ADR-001) are the first four rows. Supporting industry, occupation and workforce-adjustment tables are included under ADR-003 and D-019; the three corpus-v3 tables follow D-040. Full URLs, snapshot ids and rights records are in the manifest and `data/export/sources.json` (that export predates v3 and omits the six v3 sources until `labourlens export` is rerun).

| Source id | Observations | In scope | Coverage | SHA-256 (first 10) | Rights (manifest) |
|---|---|---|---|---|---|
| `resident_unemployment_rate` | 276 | 20 | 1992-Q1 to 2026-Q2 | f3be9ef6e2 | open licence (ODL), verified |
| `vacancy_to_unemployed_ratio` | 114 | 10 | 1998-Q1 to 2026-Q2 | a6767d98d9 | open licence (ODL), verified |
| `retrenched_employees` | 114 | 10 | 1998-Q1 to 2026-Q2 | 783e51acc3 | open licence (ODL), verified |
| `employment_change_by_sector` | 3,692 | 260 | 1991-Q1 to 2026-Q2 | 8a5f067e69 | open licence (ODL), verified |
| `avg_weekly_paid_hours_quarterly` | 114 | 10 | 1998-Q1 to 2026-Q2 | 6efbf95d8d | ODL **assumed, not verified**; local-only |
| `citizen_unemployment_rate` | 276 | 20 | 1992-Q1 to 2026-Q2 | 56cfa6f25b | open licence (ODL), verified |
| `job_vacancies_by_industry` | 4,700 | 420 | 1998-Q1 to 2026-Q2 | d1097e7ba3 | open licence (ODL), verified |
| `job_vacancies_by_occupation` | 450 | 50 | 1998-Q1 to 2026-Q2 | 7ce7b94317 | open licence (ODL), verified |
| `job_vacancy_count` | 114 | 10 | 1998-Q1 to 2026-Q2 | fb712c4849 | open licence (ODL), verified |
| `job_vacancy_rate` | 114 | 10 | 1998-Q1 to 2026-Q2 | 26c128e2e0 | open licence (ODL), verified |
| `job_vacancy_rate_by_industry` | 4,700 | 420 | 1998-Q1 to 2026-Q2 | 2eb9ffdce1 | open licence (ODL), verified |
| `job_vacancy_rate_by_occupation` | 450 | 50 | 1998-Q1 to 2026-Q2 | cffa55da17 | open licence (ODL), verified |
| `overall_unemployment_rate` | 276 | 20 | 1992-Q1 to 2026-Q2 | 73166a2b08 | open licence (ODL), verified |
| `recruitment_rate` | 114 | 10 | 1998-Q1 to 2026-Q2 | 2094a9dede | open licence (ODL), verified |
| `recruitment_rate_by_industry` | 4,700 | 420 | 1998-Q1 to 2026-Q2 | 99efe67f00 | open licence (ODL), verified |
| `recruitment_rate_by_occupation` | 342 | 30 | 1998-Q1 to 2026-Q2 | 2068a1fd41 | open licence (ODL), verified |
| `reentry_12m` | 106 | 10 | 2000-Q1 to 2026-Q2 | 21ad7b0081 | open licence (ODL), verified |
| `reentry_6m` | 106 | 10 | 2000-Q1 to 2026-Q2 | afc5f10982 | open licence (ODL), verified |
| `resignation_rate` | 114 | 10 | 1998-Q1 to 2026-Q2 | 1b2ab310fb | open licence (ODL), verified |
| `resignation_rate_by_industry` | 4,700 | 420 | 1998-Q1 to 2026-Q2 | 7b2e8dfe7c | open licence (ODL), verified |
| `resignation_rate_by_occupation` | 342 | 30 | 1998-Q1 to 2026-Q2 | 35e9bfd3e0 | open licence (ODL), verified |
| `retrenched_by_industry` | 4,700 | 420 | 1998-Q1 to 2026-Q2 | 9ac82750b7 | open licence (ODL), verified |
| `retrenched_by_occupation` | 342 | 30 | 1998-Q1 to 2026-Q2 | 2372ea3b98 | open licence (ODL), verified |
| `retrenched_permanent` | 114 | 10 | 1998-Q1 to 2026-Q2 | 07915e05ce | open licence (ODL), verified |
| `retrenched_permanent_by_industry` | 4,700 | 420 | 1998-Q1 to 2026-Q2 | fb1671f718 | open licence (ODL), verified |
| `retrenched_permanent_by_occupation` | 342 | 30 | 1998-Q1 to 2026-Q2 | ac6b96b757 | open licence (ODL), verified |
| `retrenched_term_contract` | 114 | 10 | 1998-Q1 to 2026-Q2 | fa2de87c36 | open licence (ODL), verified |
| `retrenched_term_contract_by_industry` | 4,700 | 420 | 1998-Q1 to 2026-Q2 | 39ebe96980 | open licence (ODL), verified |
| `retrenched_term_contract_by_occupation` | 342 | 30 | 1998-Q1 to 2026-Q2 | 7156b1b6f4 | open licence (ODL), verified |
| `short_workweek_temporary_layoff` | 336 | 24 | 1998-Q1 to 2025-Q4 | 0f959d8327 | open licence (ODL), verified |
| `short_workweek_temporary_layoff_by_industry` | 1,344 | 96 | 1998-Q1 to 2025-Q4 | caff893ccd | open licence (ODL), verified |
| `unemployed_citizens` | 276 | 20 | 1992-Q1 to 2026-Q2 | b5a0ca2544 | open licence (ODL), verified |
| `unemployed_overall` | 276 | 20 | 1992-Q1 to 2026-Q2 | e7eb43e553 | open licence (ODL), verified |
| `unemployed_residents` | 276 | 20 | 1992-Q1 to 2026-Q2 | 04c58b53fe | open licence (ODL), verified |
| `unit_labour_cost_index_quarterly` | 4,836 | 260 | 1980-Q1 to 2026-Q2 | d6a9eae1cf | ODL **assumed, not verified**; local-only |
| `value_added_per_worker_quarterly` | 3,408 | 240 | 1991-Q1 to 2026-Q2 | 5a108683ed | ODL **assumed, not verified**; local-only |
| **Total (36)** | **52,020** | **4,300** | | | |

**What "verified" means here.** The manifest note on every dataset says the Open Data Licence text was read at the licence URL on 2026-10-30 and that the data.gov.sg metadata API exposes no per-dataset licence field, so the dataset-level licence label was not independently read from the script-rendered dataset page. `verified_open_licence` therefore means the licence text was read and the dataset was accepted under D-004, not that each page was checked. The three corpus-v3 datasets carry an additional caveat (licence assumed from the same platform) and are recorded `assumed_open_unverified` with `redistribution_policy: local_only`. The `fetch` code now derives the status from what was checked: a dataset is `verified_open_licence` only if its spec records `licence_verified_on` or its existing manifest entry was already verified; otherwise it is `assumed_open_unverified` and its raw CSV is stored under `data/raw/` rather than the committed `data/snapshots/`.

## 2. Documents (MOM and MTI)
| Group | Items | Rights status (manifest) | Committed? |
|---|---|---|---|
| Quarterly labour-market reports, 2023-Q1 through 2026-Q2 | 14 PDFs | Verified all rights reserved | No |
| Labour-force publications for 2024 and 2025 | 8 PDFs, four per year | Verified all rights reserved | No |
| Job-vacancy 2025 and wage-practices 2024 reports | 2 PDFs | Verified all rights reserved | No |
| Wage-practices 2025 and National Wages Council lower-wage 2025 (corpus v3) | 2 PDFs | Verified all rights reserved (notice read before fetch; re-confirm on the file) | No |
| MTI 2026-Q2 feature article on AI and employment (corpus v3) | 1 PDF | **Unresolved**: the article's own notice has not been read | No |
| Advance and final quarterly releases, 2024-Q1 through 2026-Q2 | 20 HTML pages | **Unresolved**, not permission to redistribute | No |
| Job-vacancy 2025 and wage-practices 2024 releases | 2 HTML pages | **Unresolved**, not permission to redistribute | No |

Documents are fetched into `data/raw/` (gitignored); extracted text stays in `data/passages/` (gitignored). The repository carries identifiers, hashes, locators and links, not full MOM or MTI documents or extensive extracted text. Public accessibility does not grant redistribution permission. All 23 unresolved-rights sources stay local-only pending individual clearance.

## 3. Provenance
Every source has a manifest entry: original URL, publisher, title, publication and retrieval dates, release stage (advance, final, annual), snapshot id, SHA-256, rights status and note, transformation version. Every observation and passage carries `source_id`, `snapshot_id` and a locator (CSV row and column, or PDF page and block). `uv run labourlens trace <observation_id|passage_id>` prints the full chain. Snapshots are immutable and hash-addressed; re-fetching never overwrites, and `data/manifests/manifest_history.jsonl` is append-only. Exception, disclosed: the three corpus-v3 dataset entries were amended in place (and their one history line each) to change `rights_status` and `redistribution_policy`; hashes, snapshot ids and paths are unchanged. This changes the SHA-256 of `manifest.json` from `5bb67d4e...` (recorded in `experiments/corpus-snapshots/v3.json`, frozen and not edited) to `55ad2b51...`.

## 4. Transformations (`norm-0.1`)
1. Period normalisation to calendar quarters (`2026-Q2`); the unemployment datasets use `YYYY-MM` quarter-end months and are mapped, other months are rejected.
2. Values parsed strictly. Declared missing tokens (`na`, `-`) become null with a reason. A missing value is never turned into zero.
3. Wide tables (sector, unit labour cost, value added per worker) pivoted to long; the leading-whitespace hierarchy becomes `sector_path` and `sector_level`.
4. Population and adjustment labelled per series (overall, resident, citizen, establishments, employees; seasonally adjusted or not; `unspecified` for the three v3 tables because their titles do not state it). Never mixed.
5. Nothing is forecast or imputed.

## 5. Things a reader must know
**Three employment-change numbers per quarter.** For 2026-Q2: MOM advance release 10,700; MOM final report 11,400; sector dataset total 14,700. Advance versus final is a revision. Dataset versus final differs by 3,100 to 5,100 persons in every quarter we checked. MOM's headline excludes migrant domestic workers; the dataset's basis is unverified. That the gap is a migrant-domestic-worker effect is an **inference**, not a verified fact. See `docs/archive/planning/presentation-plan.md` section 3 and `artifacts/figures/fig3_employment_change_reconciliation.png`.

**Reconciliation and revisions rest on little.** `reconcile.py` checks four hand-verified quarters. `artifacts/data-quality/revisions.json` reports `baseline_only_no_earlier_snapshot` for every dataset: only one snapshot of each exists, so **no dataset revision has been observed**, and none can be ruled out.

**Ratio is not a rate.** The vacancy-to-unemployed ratio counts vacancies per unemployed person; it is not a percentage. Our recomputation from the vacancy count and overall unemployed differs from the published ratio by up to 0.67 (maximum 0.6651, mean 0.5956 over the 10 in-scope quarters) because they come from different surveys. Treated as a warning, not an error.

**'-' cells.** 416 in-scope cells across five tables are '-' in the source (47, 50, 288, 3 and 28; section 6). The publisher does not say whether that means nil or suppressed, so they stay null and are never read as zero.

**Seasonality of the v3 index tables.** The unit labour cost, value added per worker and paid-hours tables carry `adjustment: unspecified`, and at least the unit labour cost series is visibly seasonal (the first quarter of a year can sit well above the second in the file). Adjacent-quarter comparisons on these series are unsafe; compare the same quarter across years.

**Rounding and units.** Retrenchment figures are rounded by the publisher. Rates are percentages; changes between rates are percentage points. New units: `index_2015_100`, `chained_2015_dollars`, `hours_per_week`.

**Not computed.** Retrenchments per 1,000 employees: no verified denominator dataset.

**PDF extraction flags (corpus v3.1, `extract-0.3`, rebuilt 1 Nov 2026).** Across all 49 documents: 9,052 `ok`, 7,121 `table_unreliable`, 246 `garbled`. The 246 control-character blocks are real font-encoding debris (mostly reader-feedback forms and cover boilerplate) and are flagged, not repaired by guessing. Corpus v3 (`extract-0.2`) also flagged 40 legible MTI passages `garbled` through the symbol-ratio signal (significance legends, coefficient rows with asterisks, typeset estimating equations). The refined rule (D-052) ignores statistical symbols in that signal and recognises starred coefficient rows as tables: 16 of the 40 became `ok`, 24 `table_unreliable`, and 4 further `ok` passages with starred coefficients became `table_unreliable`; no passage became `garbled`. Passage ids, text and flags outside the MTI article are unchanged; the only other difference is the `parser_version` value. Numbers and checks: `experiments/corpus-snapshots/v3.1-diff.json`, `v3.1.json`. `table_unreliable` passages are kept but not retrieved.

**Corpus-v3 PDFs.** `mom-wage-practices2025`: 32 pages, 174 passages (151 `ok`, 23 `table_unreliable`). `mom-nwc-lower-wage2025`: 18 pages, 112 passages (all `ok`); its publication date, 2026-10-23, is the PDF creation date and is **not confirmed** against the publisher's newsroom. `mti-2026-q2-feature-ai-employment`: 23 pages, 218 passages (v3.1: 175 `ok`, 43 `table_unreliable`, 0 `garbled`; v3: 163, 15, 40); the MTI running page header is kept as a passage on some pages and `printed_page_label` is empty for all of them, so citations show the PDF page number.

**Low-yield PDF.** The Labour Force 2025 survey-findings PDF yields 250 passages over 80 pages after extraction corrections (198 on frozen corpus v1). Image-heavy content is a possible explanation, not a verified diagnosis.

## 6. Quality checks and known warnings
`artifacts/data-quality/validation.json` and `quality-report.md` agree: **276 checks = 269 passes + 7 warnings + 0 failures**. The seven warnings: unresolved rights for 23 sources (22 HTML releases and the MTI PDF; kept local-only); undefined dash markers in five tables (47 retrenchment-by-industry, 50 permanent-by-industry, 288 term-contract-by-industry, 3 term-contract-by-occupation and 28 short-workweek/temporary-layoff-by-industry in-scope cells); and the recomputed vacancy-ratio discrepancy. These are observed offline-build results, not proof of human verification.

Checks cover manifest integrity, schemas, periods, duplicates, ranges, hierarchy sums, extraction, dates, instruction-like source content, reconciliation and packaging. `manifest.raw_files_match_sha256` re-hashes every present raw file against the manifest. A local-only file that is absent (a fresh clone has no `data/raw/` and no v3 dataset CSVs) is reported as "local-only, not present" and is not a failure; a missing or altered committed file still fails. The injection heuristic scanned the corpus passages and statistical text values; it is not evidence of complete injection resistance, because it can miss paraphrases. Frozen corpus v1 had 13,484 passages; its results must not be attributed to a later corpus.

## 7. Corpus-v3 batch (fetched 2026-10-31)
Catalogued in `specs/sources.d/heldout-v2-expansion.yaml` (D-040); fetched, built, indexed and embedded (embeddings cost: estimated USD 0.0030 for 101 new vectors and 22,736 tokens, `artifacts/data-quality/embedding-plan-v3.json`; the billed amount is not recorded). Excluded by owner decision: MTI GDP advance and Economic Survey pairs.

| Source id | Kind | Publisher | Publication date | Stage | Rights (manifest) | SHA-256 (first 10) | Rows / passages |
|---|---|---|---|---|---|---|---|
| `mom-wage-practices2025` | PDF | MOM MRSD | 2026-05-28 | annual | all rights reserved; local-only | aed7135a23 | 174 passages |
| `mom-nwc-lower-wage2025` | PDF | MOM MRSD | 2026-10-23 (PDF creation date; unconfirmed) | annual | all rights reserved; local-only | 9e49b9683c | 112 passages |
| `mti-2026-q2-feature-ai-employment` | PDF | MTI | 2026-08-11 | not applicable | unresolved; local-only | 045f7a56cc | 218 passages |
| `unit_labour_cost_index_quarterly` | dataset | SingStat | 2026-08-11 (lastUpdated) | snapshot | ODL assumed, not verified; local-only | d6a9eae1cf | 4,836 rows (260 in scope) |
| `value_added_per_worker_quarterly` | dataset | SingStat | 2026-08-11 (lastUpdated) | snapshot | ODL assumed, not verified; local-only | 5a108683ed | 3,408 rows (240 in scope) |
| `avg_weekly_paid_hours_quarterly` | dataset | MOM | 2026-09-22 (lastUpdated) | snapshot | ODL assumed, not verified; local-only | 6efbf95d8d | 114 rows (10 in scope) |

Coverage checked by the build (exact first periods): ULC 1980-Q1 to 2026-Q2; value added per worker 1991-Q1 to 2026-Q2; paid hours 1998-Q1 to 2026-Q2. Missing cells are `na` in the source and stay null: 1,200 (ULC) and 864 (value added), all before the answer scope. The three raw CSVs live under `data/snapshots/<source_id>/` on the author's machine and are **gitignored** until the licence is verified on each dataset page; the committed manifest and the committed `observations.parquet` still describe them. The three MOM/MTI PDFs are local-only like every document.

## 8. Limits
- Extraction quality for tables is not reliable; numbers come from datasets, text supplies explanation.
- Saved page-date checks cover releases; internal PDF dates and representative extraction fidelity still need human inspection.
- Source checks: the owner recorded decisions on 30 items (passage extraction and statistical rows) in the review interface on 1 Nov 2026, after AI pre-review (final 18 matches / 12 minor; first export 19 / 11). AI-drafted, signed off by the owner; one reviewer, after AI pre-review and after the saved runs were scored; not independent inter-rater evidence. Sheets and summaries are in `docs/human-review/`.
- Coverage is one snapshot per source, so revision tracking is baseline-only until a second fetch is made.
- A fresh clone has the manifest, the committed dataset snapshots and the processed tables, but not the PDFs, passages, indexes or the three v3 dataset CSVs. `uv run pytest -q` skips corpus tests there; `labourlens build` stops with a message naming the absent raw file, because a rebuild needs the local corpus.

## 9. Open licence items and what the rights scan covers

**Derived rows from the three assumed-licence datasets are committed.** `data/processed/observations.parquet` holds 8,358 normalised rows from `unit_labour_cost_index_quarterly` (4,836), `value_added_per_worker_quarterly` (3,408) and `avg_weekly_paid_hours_quarterly` (114). Only their raw CSVs are kept out of git. The parquet file's hash is pinned in the held-out v2 freeze record, so the rows were not removed. If the licence turns out not to be the Open Data Licence, the rows are the first thing to remove, with a new freeze note.

Unresolved items, in one place:

1. The three datasets above: licence assumed, not read from the dataset page.
2. For the 33 datasets marked verified, the Open Data Licence text was read, but no per-dataset licence field exists in the API, so no dataset page was read for the label (section 4).
3. 22 MOM HTML releases: rights unresolved; local-only.
4. The MTI 2026-Q2 feature PDF: its own notice was not read; local-only.
5. `mom-wage-practices2025` and `mom-nwc-lower-wage2025`: notice to be re-confirmed on the file; local-only.
6. The repository licence is stated in `LICENSE`; data, fonts and MOM/MTI material keep their own terms.

**Contact fields.** data.gov.sg dataset metadata lists named officer email addresses. They were replaced with `redacted@mom.gov.sg` in the committed metadata files on this branch. No hash covers those files (checked: none of their SHA-256 values appears in any tracked file), and the CSV hashes are unchanged. The generic `feedback@data.gov.sg` address is kept. Unredacted officer addresses remain in Git history as published by data.gov.sg; this is not a claim of historical removal.

**Rights-scan scope.** `labourlens rights-scan` compares tracked text files with the local MOM/MTI passages in `data/passages/`. It cannot run without them: in a clone it prints `NOT CHECKED` (and exits 2 with `--require-corpus`). It skips binary files (Parquet, PNG, fonts) and files over 5 MB, matches exact words only (a paraphrase is not detected) and does not scan paths in `specs/rights-scan-allowlist.txt`. Those paths are dataset and source records, frozen gold files and frozen run outputs; their longest matches are publisher legal notices (18 words), dataset definitions under the Open Data Licence (78 words), document titles (16 words) and, in the signed held-out v2 gold file, one 7-word survey statistic phrase. Over-long runs found in committed judge and review outputs were cut to six words after scoring; counts are in `experiments/rights-truncation-sidecar.json`, so those files are no longer byte-identical to the run that produced them. Pre-truncation section headings and a few review-note sentences remain in history; the cleanup did not rewrite history.

The current allowlist has **21 entries**. Blanket patterns include `data/snapshots/*`, `data/manifests/*`, `specs/*`, `data/export/*.json`, `experiments/gold/archive/*`, `experiments/triage/*/raw.jsonl`, `experiments/context/*/raw.jsonl` and `experiments/served/*.jsonl`. Python `fnmatch` permits `*` to match `/`; future files below these paths may therefore be excluded without individual review. Hash preservation explains an exception, not rights clearance.

From the D-064 audit-fix commit, the scanner joins consecutive passages within the same document to include boundary windows; earlier scans did not. It still does not read Git history. It excludes PDF and other listed binary/archive/lock suffixes and windows with fewer than four alphabetic tokens. `NOT CHECKED` normally exits zero without corpus; CI in a fresh clone therefore does not certify source-text clearance.

**Packaging records.** `data/export/sources.json` remains a dated, pre-v3 export, not the current source catalogue; use the manifest. `web/static/data/report.json` is generated by `labourlens build-report` from repository inputs and the then-current commit, so its embedded commit can lag a subsequent commit. Historical test artefact paths were replaced by `<repo>` only; local `/Users` paths remain in history. The submission audit identified five commits containing paths; this is not a count of commits adding or removing the literal string. Historical authoring prompts under `prompts/meta/` are absent from the current tree but remain in history.
