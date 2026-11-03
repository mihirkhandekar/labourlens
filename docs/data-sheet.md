# LabourLens data sheet

I built a traceable local collection of Singapore labour-market statistics and official reports. Statistics support calculations; report passages supply explanations and citations. Each record points back to a saved source, its checksum and its location in the original file.

The current collection, **v4**, contains **142 sources**, **52,020 normalised observations** and **29,760 extracted passages**. It supports questions from **2020-Q1 to 2026-Q2**. The last evaluated collection was **v3.1**, with 85 sources and a narrower **2024-Q1 to 2026-Q2** answer window. The additional documents and wider window have not been evaluated. Native model tool calling, new prompts and new tools also differ from the evaluated system; data coverage alone does not establish answer quality.

**Attribution.** Contains information from data.gov.sg datasets published by the Ministry of Manpower (MOM) and Singapore Department of Statistics, accessed 30 and 31 October 2026, under the [Singapore Open Data Licence v1.0](https://developers.data.gov.sg/open-data-licence) where applicable. LabourLens is not endorsed by any agency. MOM and Ministry of Trade and Industry (MTI) documents are linked, with originals and extracted text kept locally.

The [detailed reference](reference/data-sheet-detail.md) preserves the complete source catalogue, checksums, corpus version history, per-batch records, extraction changes and packaging audit. Counts below describe the current collection unless labelled otherwise.

## At a glance

| Item | Saved evidence and boundary |
|---|---|
| Sources | 36 statistical datasets and 106 documents: 63 PDFs and 43 HTML releases. |
| Statistics | 52,020 observations; 11,228 within the current answer window; 0 quarantined rows. The earlier window contained 4,300 observations. |
| Report text | 29,760 passages: 16,342 usable prose, 13,164 unreliable table blocks and 254 garbled blocks. Only usable prose enters the default retrieval index, giving 3,632 searchable chunks. A chunk is a short group of passages searched together. |
| Saved quality checks | v3.1: 276 checks, 269 passes, 7 warnings, 0 failures. The 3 November wider-window rebuild reports 276 checks and 0 failures; its warning count is not restated here. |
| Human source checks | One owner reviewed 30 AI-drafted checks: 16 passage checks and 14 statistical rows. Final decisions were 18 matches and 12 minor issues. This followed AI pre-review and the saved evaluation runs; it is not independent multi-reviewer evidence. |

Evidence: [current snapshot](../experiments/corpus-snapshots/v4.json), [last evaluated snapshot](../experiments/corpus-snapshots/v3.1.json), [validation output](../artifacts/data-quality/validation.json) and [human review records](human-review/README.md). A passing build establishes the checks exercised, not that every source or answer is correct.

## 1. Statistical datasets (data.gov.sg)

| Sources | Coverage and purpose | Licence status and limits |
|---|---|---|
| Four core datasets: resident unemployment rate, vacancy-to-unemployed ratio, retrenched employees and employment change by sector | Quarterly lookup and comparisons. All reach 2026-Q2. Sector totals need a population-definition caveat. | Recorded as open-licence datasets, subject to the verification limit below. |
| 29 supporting datasets | Citizen and overall unemployment, vacancies, recruitment, resignation, re-entry, retrenchment breakdowns and short-workweek/temporary-layoff measures. The two short-workweek tables end at 2025-Q4. | Same recorded open-licence status and verification limit. |
| Three additional datasets: unit labour cost, value added per worker and paid hours | Quarterly context through 2026-Q2. Seasonal-adjustment basis is unspecified. | Licence assumed, unverified. Raw CSVs stay local; **8,358 derived rows remain committed** in the processed table. |

All 36 datasets contain rows from 2020-Q1; 34 reach 2026-Q2. Earlier rows are retained as history. Some cells inside the window are missing: for example, 32 of 676 sector-employment cells and 123 of 1,092 industry-retrenchment cells. Missing values remain null.

The [full statistical catalogue](reference/data-sheet-detail.md#1-statistical-datasets-datagovsg) records each source's observation count, coverage and checksum. The [manifest](../data/manifests/manifest.json) is the current catalogue; the source export is a dated, pre-v3 export and should not be used to count current sources.

**Licence verification limit.** For the 33 datasets recorded as verified, the licence text was read, but each dataset page's licence label was not independently checked. The metadata API has no per-dataset licence field. The other three datasets were accepted on an explicit assumption that the platform licence applied. None of these records resolves an individual publisher's terms by itself.

## 2. Documents (MOM and MTI)

| Source family | Material included | Rights and public packaging |
|---|---|---|
| Quarterly labour-market publications | Reports from 2020-Q1 through 2026-Q2; advance and final releases, with gaps detailed in the batch record. | PDFs generally carry reserved rights; HTML rights are unresolved. Originals and extracted text stay local. |
| Annual labour publications | Labour-force material for 2020 to 2025, vacancy reports for 2020 to 2023 and 2025, wage-practice reports for 2020 to 2025, and a lower-wage publication. | Reserved rights except the unresolved 2020 wage-practice PDF. These are selected publications, not complete annual coverage. |
| MTI employment feature | One 2026-Q2 article about AI and employment. | Its own notice has not been read; rights unresolved, local-only. |

Across all documents, **61 PDFs** are recorded as reserved-rights sources and **45 documents** have unresolved rights: 43 HTML pages and two PDFs. Public accessibility does not permit redistribution. The repository contains identifiers, hashes, locators and links rather than full reports or extensive extracted text. [Document catalogue and rights records](reference/data-sheet-detail.md#2-documents-mom-and-mti).

## 3. Provenance

A source manifest records its URL, publisher, title, publication and retrieval dates, release stage, snapshot identifier, SHA-256 checksum, rights note and transformation version. A checksum identifies the saved bytes; it does not independently authenticate them against the publisher.

Each statistical observation and text passage records its source and snapshot, plus a CSV row/column or PDF page/block locator. `uv run labourlens trace <observation_id|passage_id>` shows that chain. Raw snapshots are hash-addressed and re-fetching does not overwrite them.

There is one recorded exception to append-only manifest history: the three assumed-licence dataset entries and their history lines were amended in place to correct rights labels. Their source hashes, identifiers and paths stayed unchanged. Some publication dates in the 2020 to 2023 additions are inferred from covers or public captures; the manifest marks them as inferred. Period filtering uses the reporting period rather than the inferred day.

## 4. Transformations (`norm-0.1`)

| Step | Treatment |
|---|---|
| Periods | Convert periods to calendar quarters. Unemployment quarter-end months are mapped to quarters; other months are rejected. |
| Values | Parse strictly. Declared missing markers become null with a reason, never zero. No forecasting or imputation. |
| Table structure | Convert wide sector and index tables into one observation per row; retain the sector hierarchy. |
| Definitions | Label population, seasonal adjustment and units per series. Overall, resident and citizen populations remain separate. Unverified definitions stay labelled as such. |
| Documents | Extract passages with source locations and quality flags. Exclude unreliable tables and garbled text from default retrieval, while retaining them locally for inspection. |

Rates use percentages; a difference between rates uses percentage points. The vacancy-to-unemployed ratio is vacancies per unemployed person, not a percentage. Dataset values, rather than guessed PDF table readings, supply calculations.

## Known quality issues

### 5. Things a reader must know

| Issue | Consequence and treatment |
|---|---|
| Different employment totals | For 2026-Q2, the advance headline is 10,700, the final headline 11,400 and the sector dataset total 14,700. Advance-to-final is a revision. The dataset population basis remains unverified; the proposed migrant-domestic-worker explanation is an inference. Do not merge the series. |
| Limited reconciliation | Four hand-verified quarters underpin the comparison. Only one snapshot exists per dataset, so no dataset revision has been observed or ruled out. |
| Published ratio differs from recomputation | Over the earlier ten-quarter window, the maximum discrepancy is 0.6651 and the mean 0.5956. Inputs come from different surveys; this is recorded as a warning. |
| Undefined dash markers | A historical check counted 416 in-window dash cells across five tables under the earlier window. The publisher's meaning is unclear; they remain missing, never zero. This count is not the current wider-window total. |
| Adjustment and rounding | The three added quarterly datasets have unspecified seasonal adjustment. Prefer same-quarter, year-on-year comparisons. Retrenchment figures are publisher-rounded. |
| Extraction gaps | Four added labour-force PDFs yield no passages. Some material is image-based or garbled; unreliable tables are excluded. The owner accepted five disclosed extraction gaps in the frozen runs after inspecting the originals. |
| Date and citation fidelity | Some publication dates are inferred; PDF citations can use file page numbers when printed labels are missing. Representative extraction and internal PDF dates still need further human inspection. |

See [reconciliation evidence](../artifacts/data-quality/reconciliation.json) and the [detailed extraction record](reference/data-sheet-detail.md#5-things-a-reader-must-know).

## Exclusions

| Excluded material | Boundary |
|---|---|
| Foreign-workforce candidates | Not selected because the source comparison found them stale for the reconciliation question. |
| Holiday, leave, trade-union and arbitration datasets | Outside the selected research questions. |
| GDP advance/final pairs | Labour-specific evidence was selected instead. The included MTI employment article is separate. |
| Unreliable tables and garbled passages | Stored locally with provenance, excluded from default retrieval. |
| Answers outside 2020-Q1 to 2026-Q2 | Historical context cannot extend the answer window. Comparisons requiring an outside endpoint must abstain. |
| Restricted or unresolved-rights documents | Excluded from public packaging, retained in the local research collection. |
| Retrenchments per 1,000 employees; imputed values | No verified denominator supports that indicator; missing values are not invented. |

## 6. Quality checks and known warnings

Checks cover source hashes, schemas, periods, duplicate rows, ranges, hierarchy sums, extraction, dates, instruction-like content, reconciliation and packaging. Absent local-only files do not fail the raw-file check; altered or missing committed files do. The instruction-like-content heuristic can miss paraphrases and does not establish complete prompt-injection resistance.

The seven v3.1 warnings cover unresolved rights, five tables with undefined dash markers and the recomputed-ratio discrepancy. Historical test and build results, including deterministic rebuild comparisons, remain in the [reference](reference/data-sheet-detail.md#6-quality-checks-and-known-warnings).

## 7a. Corpus-v4 batch (fetched 2026-11-03, D-080)

The latest batch added 57 documents covering earlier quarterly and annual publications. It preserved the 49 earlier passage files, their identifiers and chunks. The collection now covers report commentary from 2020, with the extraction gaps above. Cached vectors for all 3,632 chunks are recorded; the live container does not create embeddings at startup. [Per-family counts, inferred dates and failures](reference/data-sheet-detail.md#7a-corpus-v4-batch-fetched-2026-11-03-d-080).

## 8. Limits

The collection establishes source coverage, not evaluated performance on its new material. Evaluation uses a model-family-related judge; AI-drafted reference answers received one owner's sign-off after runs. The fresh 65-question study showed no demonstrated gain. See the [evaluation report](evaluation-report.md) for denominators and comparisons.

A fresh clone contains committed statistical snapshots and processed tables, but lacks restricted reports, passages, indexes and the three assumed-licence raw CSVs. Corpus tests skip there; rebuilding requires separately acquired local files. Single snapshots cannot establish revision history, and one reviewer's source checks cannot establish corpus-wide accuracy.

## 9. Open licence items and what the rights scan covers

**Outstanding rights:** verify the three assumed licences and the dataset-page basis for the other 33; resolve rights for 43 HTML pages and two PDFs; re-confirm notices for the two 2025 MOM additions. The 8,358 derived rows from assumed-licence datasets remain in the committed processed table because its hash is frozen in evaluation evidence. Raw-file exclusion does not clear those rows for redistribution. If terms disallow them, removal requires a new freeze record.

`uv run labourlens rights-scan` checks exact word overlap against local MOM/MTI passages. It skips binary files, files over 5 MB and 24 allowlist entries, including broad path patterns that may cover future files. It joins passage boundaries but does not scan Git history or detect paraphrases. Without local passages it reports `NOT CHECKED` and normally exits zero; `--require-corpus` exits 2. A zero finding count is neither permission nor complete rights clearance.

Named officer emails were redacted in current committed metadata; originals remain in Git history. Earlier source-text overlaps and local paths also remain in history. The [packaging audit](reference/data-sheet-detail.md#9-open-licence-items-and-what-the-rights-scan-covers) retains scanner exclusions, historical overlap counts, frozen-output changes and export caveats. Repository, data, font and publisher terms remain separate.
