# Statistical spot-check — AI pre-review

**AI pre-review by claude-agent (ReviewSpotStats)**  
Date: 2026-10-30. This is an independent AI check, not owner sign-off. The owner's original sheet is unchanged.

## Result and evidence boundary

**MEASURED RESULT:** All 14 sampled observations match their original CSV cells and the declared normalization contract. The independent eight-dataset comparison covers **1,180 in-scope observations**, with **0 missing, 0 extra, 0 mismatched rows and 0 duplicate source locators**. All 47 source dash cells in these datasets remain null. No numerical, period, dimension or normalization defect was found.

**Important limitation:** Most raw CSVs contain only a quarter, a measure and sometimes a dimension. They do **not** independently establish measurement units, survey population or seasonal-adjustment methodology. I compared those normalized fields with `specs/datasets/*.yaml`, the source catalogue and the data sheet, not with newly retrieved publisher documentation. Only the resident CSV directly labels population and seasonal adjustment through its status field and measure-column names. Agreement with a local contract is not independent verification that the contract's metadata is correct. `ok` below means a match within this evidence boundary; `minor` flags the already disclosed unverified population basis of the sector dataset, not an incorrect cell. No major finding.

The owner's sheet has publisher links but **no MOM report/passage cross-references**, so no passage comparison was applicable or performed. The data sheet's general employment-total reconciliation is not evidence that either sampled sector matches a report. No report agreement is claimed.

## Inputs and method

Read: `docs/human-review/statistical-spot-check.md`, `docs/data-sheet.md`, `specs/sources.yaml`, the nine relevant dataset adapter contracts, `src/labourlens/data/normalize.py`, `data/manifests/manifest.json`, the original snapshot CSVs and `data/processed/observations.parquet`.

Snapshots were located using each manifest entry's `raw_path`. These statistical originals are under **`data/snapshots/`**, not `data/raw/`; the latter contains the restricted document originals. SHA-256 of each of the nine CSVs matched its manifest entry. This verifies local snapshot identity, not authenticity against a live publisher download. No network, fetch, build, paid API or git command was used.

Checks were executed in local Python Eval with the repository's `.venv/bin/python`, using `csv`, `json`, `hashlib`, `calendar`, `datetime`, `yaml` and `pandas`. The normalized table contained 43,662 observations. Its SHA-256 at review time was:

`ebe256b992a60aa10a583e76960d3338a452e3d9b71fcf480ae34f19d76d20e4`

The comparison implementation did **not** import or call the production normalizer or its period/value helpers. It read CSVs directly, independently mapped quarter-end months to quarters, independently pivoted sector quarter columns, parsed numeric cells, preserved declared nulls and built expected records from explicit column/semantic mappings. It compared both directions by original CSV row/column locator, rather than assuming the parquet rows or the sheet's reported values were correct. The declared semantic mappings were necessarily informed by local adapter contracts, subject to the metadata limitation above.

Compared fields: source id, snapshot id, source locator, indicator id, period, period start/end, original period token, value, original value token, missing reason, unit, population, adjustment, dimension, answer-scope flag and release stage. For the wide sector table, also independently reconstructed hierarchy path and level from four-space indentation. For long industry tables, hierarchy paths/levels are contract-supplied rather than encoded in the CSV and were not independently validated; the raw industry dimension itself was compared. Observation ids were used to select the owner's 14 samples, not to generate expected numerical results.

## Every sampled observation

`r` denotes the original CSV row, counting the header as row 1. Empty dimension means the normalized empty string, not a missing numerical value. All rows below also passed the additional record-field checks described above.

| # | Observation id | Source | What I compared | Finding | Details |
|---|---|---|---|---|---|
| 1 | `9e3b178b6b85f234` | `resident_unemployment_rate` | r139, `non_seasonally_adj_unemp_rate`; original period/status and normalized value, quarter, unit, population, adjustment, dimension | ok | Original `2026-06`, `resident`, `3.5` → 2026-Q2, 3.5 percent, resident, `not_adjusted`, empty dimension. The other measure in the same row is 2.9: the sample correctly selects the non-adjusted column. Percent unit agrees with the contract; the CSV has no explicit unit field. |
| 2 | `4caa3fbd0df137f1` | `resident_unemployment_rate` | r136, same measure column and six requested fields | ok | Original `2025-09`, `resident`, `2.7` → 2025-Q3, 2.7 percent, resident, `not_adjusted`, empty dimension. Same-row adjusted value 2.9 was not substituted. |
| 3 | `ce87ebbfe18bb7ce` | `vacancy_to_unemployed_ratio` | r109, `jv_to_ue`; raw quarter/value plus declared unit/population/adjustment and empty dimension | ok | Original 2024-Q4, `1.57` → 1.57 ratio, `not_applicable` population, `seasonally_adjusted`. No percentage scaling. Seasonal adjustment comes from the contract, not an explicit CSV label. |
| 4 | `a84eaacb4cda2a28` | `vacancy_to_unemployed_ratio` | r107, `jv_to_ue`; same fields | ok | Original 2024-Q2, `1.72` → 1.72 ratio; same population/adjustment labels as row 3; empty dimension. |
| 5 | `a62a15204fcba505` | `retrenched_employees` | r112, `retrench`; raw quarter/value and declared semantics | ok | Original 2025-Q3, `3670` → 3,670 persons, `establishments`, adjustment `not_applicable`, empty dimension. Population/unit are contract metadata, not CSV fields. |
| 6 | `0f99b5c79172c310` | `retrenched_employees` | r106, `retrench`; same fields | ok | Original 2024-Q1, `3030` → 3,030 persons; same population/adjustment as row 5, empty dimension. |
| 7 | `7f5d5cef621d53dc` | `employment_change_by_sector` | r26, `20251Q`; raw signed cell, sector label/indentation and declared semantics | minor | Original `-200`, quarter column 20251Q → 2025-Q1, −200 persons; dimension `Arts, Entertainment & Recreation`, level 3. Path reconstructed through total → services-producing → other-services → this sector. Numeric/period/dimension match. Population is honestly `unverified_basis`; the CSV cannot settle it. Adjustment `not_applicable` agrees with the contract. |
| 8 | `8530778cbaf4bd36` | `employment_change_by_sector` | r17, `20261Q`; raw cell, sector label/indentation and declared semantics | minor | Original `6100`, quarter column 20261Q → 2026-Q1, 6,100 persons; dimension `Real Estate, Professional Services And Administrative & Support Services`, level 2. Reconstructed path through total → services-producing → this sector matches. Same unverified population limitation and declared adjustment as row 7. |
| 9 | `642a17683020895f` | `job_vacancy_count` | r113, `job_vacancy`; raw quarter/value and declared semantics | ok | Original 2025-Q4, `75700` → 75,700, unit `persons`, population `establishments`, adjustment `unspecified`, empty dimension. The unit label is the existing contract for vacancy count, not an independent CSV unit declaration; no assumption of seasonal adjustment. |
| 10 | `bd6e4286a15fb297` | `recruitment_rate_by_occupation` | r334, `recruitment_rate` and `occupation`; six requested fields | ok | Original 2025-Q3, `2.1`, occupation `production and transport operators, cleaners and [...]` → same period, value and exact dimension; percent, `establishments`, adjustment `unspecified` agree with the contract. |
| 11 | `2d282c9a1ae8c215` | `recruitment_rate_by_industry` | r4414, `recruitment_rate` and `industry`; six requested fields | ok | Original 2024-Q4, `1.2`, `transport equipment` → same period/value/dimension; percent, `establishments`, adjustment `unspecified` agree with the contract. |
| 12 | `236138a9f359e9af` | `resignation_rate` | r114, `resignation_rate`; raw quarter/value and declared semantics | ok | Original 2026-Q1, `1` → 1.0 percent, `establishments`, adjustment `unspecified`, empty dimension. This is the quarterly average-monthly rate per the contract, not a quarterly sum. |
| 13 | `05cb21cfc6f40801` | `retrenched_by_industry` | r4427, `retrench` and `industry`; raw dash/null handling, quarter, dimension and declared semantics | ok | Original 2024-Q4, `accommodation`, `-` → null, not zero; original dash preserved and reason `dash_marker_publisher_does_not_define_nil_vs_suppressed` retained. Persons, `establishments`, adjustment `not_applicable` agree with the contract. CSV does not define the dash's substantive meaning. |
| 14 | `2b6e9c88c668657c` | `resident_unemployment_rate` | r114, `non_seasonally_adj_unemp_rate`; raw period/status/value, declared unit and scope flag | ok | Original `2020-03`, `resident`, `3.1` → 2020-Q1, 3.1 percent, resident, `not_adjusted`, empty dimension. Correctly `in_answer_scope=false`; adjusted value 3.4 in the same row was not substituted. |

Findings: **12 ok, 2 minor, 0 major**. The minor findings repeat the data sheet's disclosed population limitation; they do not represent newly discovered normalization mismatches.

## Independent full in-scope re-derivation: eight datasets

Window: 2024-Q1 through 2026-Q2 inclusive, ten quarters. Both unemployment adjustment columns were included. Every sector, occupation and industry row in this window was included, including aggregates and missing cells; no summation of overlapping categories was performed. Missing/extra counts refer to expected-versus-actual locator sets. Mismatches count shared rows with any unequal compared field; null equals null. Duplicate locator counts were zero on both sides for every dataset.

| Dataset | Independently expected rows | Parquet rows | Source null cells | Missing | Extra | Mismatched rows |
|---|---:|---:|---:|---:|---:|---:|
| `resident_unemployment_rate` | 20 | 20 | 0 | 0 | 0 | 0 |
| `vacancy_to_unemployed_ratio` | 10 | 10 | 0 | 0 | 0 | 0 |
| `retrenched_employees` | 10 | 10 | 0 | 0 | 0 | 0 |
| `employment_change_by_sector` | 260 | 260 | 0 | 0 | 0 | 0 |
| `job_vacancy_count` | 10 | 10 | 0 | 0 | 0 | 0 |
| `recruitment_rate_by_occupation` | 30 | 30 | 0 | 0 | 0 | 0 |
| `recruitment_rate_by_industry` | 420 | 420 | 0 | 0 | 0 | 0 |
| `retrenched_by_industry` | 420 | 420 | 47 | 0 | 0 | 0 |
| **Total** | **1,180** | **1,180** | **47** | **0** | **0** | **0** |

The resignation dataset was checked for its sampled observation, but was not one of the eight full comparisons. The pre-scope sample was checked separately and is not included in the 1,180-row total.

## Original snapshot identity

For every row below, resolve the exact CSV through `data/manifests/manifest.json` → matching `source_id` → `raw_path`. Each path is `data/snapshots/<source_id>/<snapshot_id>/<dataset_id>.csv`; dataset ids and publisher URLs are in the manifest and source specifications.

| Source | Snapshot id | Verified CSV SHA-256 |
|---|---|---|
| `resident_unemployment_rate` | `20261030-f3be9ef6e208` | `f3be9ef6e208a87fd4ba0d0dc2bfaf40817a42e348a5a7bfa988a54b4917d547` |
| `vacancy_to_unemployed_ratio` | `20261030-a6767d98d9a9` | `a6767d98d9a943e1de840abdb090e67aa3d30c0f4b03e304849fbaaab7a87cf5` |
| `retrenched_employees` | `20261030-783e51acc3fc` | `783e51acc3fc129aeaa4dc9e89e1be60e5fe2729b9c988092ea52e0c092c1ee4` |
| `employment_change_by_sector` | `20261030-8a5f067e693a` | `8a5f067e693aef2c6fbe0474657ca7ae1f030fe3f6742579e8542e13dfa28193` |
| `job_vacancy_count` | `20261030-fb712c4849b2` | `fb712c4849b28ee08a1a334c6c6aa6f9a1c08d3b9286d4d9de0d20a61f5fac3a` |
| `recruitment_rate_by_occupation` | `20261030-2068a1fd412e` | `2068a1fd412e88b92c7f3914685ec5cf8ff912cd94ff0c65a710a2be6edd8151` |
| `recruitment_rate_by_industry` | `20261030-99efe67f00a4` | `99efe67f00a441d62300e455121f7e7d8c6b531d468564fc895fd92f39bbe8c8` |
| `resignation_rate` | `20261030-1b2ab310fb02` | `1b2ab310fb026f1b649cadada1890c0c84a898387ea88f47361f231b194326d4` |
| `retrenched_by_industry` | `20261030-9ac82750b76b` | `9ac82750b76bdf38358f332d43c62a7bb119c5627dccd08e22922480abeab6f8` |

## Owner review focus

- Inspect the 14 original cells using the locators above; the AI results do not replace owner review.
- Confirm publisher metadata for units, survey scope and seasonal adjustment where those are absent from the CSV, especially the vacancy ratio's adjustment and the sector dataset's population basis.
- Preserve the distinction between raw data agreement and report agreement: this check does not resolve employment-total reconciliation, prove dash means zero, or establish seasonal adjustment for `unspecified` series.
- No gold cases, reviewer attribution/status fields or existing files were modified. Only this AI pre-review file was written.
