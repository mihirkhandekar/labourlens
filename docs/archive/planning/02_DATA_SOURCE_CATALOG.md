> **Historical planning document (30 Oct 2026), written before implementation.** Statements such as "not yet approved" or "not executed" describe that date, not the current state. Current status is in [`docs/progress.md`](../../progress.md), decisions in [`docs/decisions.md`](../../decisions.md) and requirements evidence in [`docs/requirements-matrix.md`](../../requirements-matrix.md).

# Source catalog and initial verification notes

**Status:** planning evidence verified from publisher pages on 30 October 2026. **No dataset API extraction or PDF corpus ingestion has been executed in this planning pack.** These entries must be confirmed programmatically and captured in a machine-readable manifest during Milestone 1.

## Dataset inventory — approved structured sources

| ID | Publisher | Official data.gov.sg URL | Preliminary schema observations | Caveats / transformations |
|---|---|---|---|---|
| `resident_unemployment` | MOM | https://data.gov.sg/datasets/d_d1d755e060dd6b01a8024ba60b21b831/view | `period` (`YYYY-MM`, quarter-end month), `residential_status`, `seasonally_adj_unemp_rate`, `non_seasonally_adj_unemp_rate` | `2026-06` => `2026-Q2` while retaining source date; separate SA/NSA; population = residents; unit percent |
| `vacancy_unemployed_ratio` | MOM | https://data.gov.sg/datasets/d_80c0cf251ee9a26d240808297f52c820/view | `quarter`, `jv_to_ue` | Seasonally adjusted; unit ratio, NOT percentage; preserve exact series definition |
| `retrenchments` | MOM | https://data.gov.sg/datasets/d_000d49cda016c13522d7d5be6a050f59/view | `quarter`, `retrench` | Count values stored as TEXT; handle suppression/missing markers rather than coercing to 0 |
| `employment_by_sector` | SingStat (source MOM) | https://data.gov.sg/datasets/d_31dec7667bc2c6b945a262cd60958eaf/view | `DataSeries` plus one column per quarter, e.g. `20262Q`, `20261Q` | Wide-to-long unpivot; sector hierarchy and totals, SSIC footnotes, rounding and revisions; unit persons |

These publisher pages currently show data through Q2 2026. That is **source-page evidence**, not proof of success against the dataset API.

### Source links and methodological footnotes
- Resident unemployment: quarter-end `YYYY-MM` field and seasonally adjusted revision policy: https://data.gov.sg/datasets/d_d1d755e060dd6b01a8024ba60b21b831/view
- Vacancy ratio: seasonally adjusted, source survey coverage notes: https://data.gov.sg/datasets/d_80c0cf251ee9a26d240808297f52c820/view
- Retrenchments: source measure stored as text and definition of retrenchment: https://data.gov.sg/datasets/d_000d49cda016c13522d7d5be6a050f59/view
- Sector employment: wide layout, rounding and industry classifications: https://data.gov.sg/datasets/d_31dec7667bc2c6b945a262cd60958eaf/view

### Do not silently assume
- A release date of the dataset page equals the exact publication timestamp of each observation.
- All ten selected quarters have complete and comparable observations for all industries.
- The data.gov.sg UI's displayed row counts represent cleaned/usable data rows in the pipeline.
- `total employment`, `resident employment`, `employment level`, and `employment change by sector` are interchangeable.
- SA and NSA unemployment values can be compared without clear selection and labeling.
- Vacancy/unemployment *ratio* is a vacancy *rate*.
- A dash, suppression marker, `NA`, or blank is numeric zero.

## Publication inventory — approved unstructured sources

| Source ID | Official reference page / document | Release stage | Role |
|---|---|---|---|
| `mom-2025-q3-final` | https://stats.mom.gov.sg/Pages/Labour-Market-Report-3Q-2025.aspx | Final, 11 Dec 2025 | Earlier report language, methodologies and comparison context |
| `mom-2025-q4-final` | https://stats.mom.gov.sg/Pages/Labour-Market-Report-4Q-2025.aspx | Final, 20 Mar 2026 | End-2025 labour-market context |
| `mom-2026-q1-final` | https://stats.mom.gov.sg/Pages/Labour-Market-Report-1Q-2026.aspx | Final, 15 Jun 2026 | Before/after comparison with 2026 Q2 |
| `mom-2026-q2-final` | https://stats.mom.gov.sg/Pages/Labour-Market-Report-2Q-2026.aspx | Final, 21 Sep 2026 | Latest full report in approved answer scope |
| `mom-2026-q2-advance` | https://www.mom.gov.sg/newsroom/press-releases/2026/0731-labour-market-advance-release-2q-2026 | Advance, 31 Jul 2026 | A genuine preliminary-versus-final provenance exercise |

**Known primary source revision example:** Q2 2026 total employment increase was 10,700 in the advance release (31 Jul) and 11,400 in the final report (21 Sep). The correct behavior is to distinguish release stages and dates rather than label one as an unexplained contradiction.
- Advance official release: https://www.mom.gov.sg/newsroom/press-releases/2026/0731-labour-market-advance-release-2q-2026
- Final official release: https://www.mom.gov.sg/newsroom/press-releases/2026/0921-labour-market-report---second-quarter-2026

### Rights and redistribution — critical

**data.gov.sg data:** data.gov.sg identifies the four datasets under the Singapore Open Data Licence; that licence permits reuse and redistribution subject to attribution and other conditions. Use the actual licence and attribution notices, and do not imply governmental endorsement.
- Official licence: https://developers.data.gov.sg/open-data-licence
- API/website terms: https://data.gov.sg/privacy-and-terms

**MOM full report PDFs:** The Q3 2025 full PDF visibly contains a copyright notice stating that further reproduction requires permission and requests attribution to `MRSD, MOM`. Do **not** assume the Open Data Licence covering data.gov.sg applies to the PDFs. Check each report's rights/usage notice individually before any redistribution.
- Official Q3 2025 PDF for rights inspection: https://stats.mom.gov.sg/iMAS_PdfLibrary/mrsd-Labour-Market-Report-3Q-2025.pdf

**Default repository handling:**
- Keep acquired full PDF files and large text dumps local, gitignored, not bundled into a publicly shared GitHub repository.
- Commit source metadata/manifests, source URLs, parser code, small derived statistics where permitted, hashes, and a reproducible download procedure.
- Use short necessary quotations only if permitted; prefer your own summaries and links to the original source for public documentation.
- Clearly label local-only corpus access when evaluating fresh-clone reproducibility; provide public sample fixtures only when rights permit.

## API acquisition plan — verified documentation, not executed

data.gov.sg documents a whole-dataset flow:
1. Identify dataset ID from official URL.
2. Call documented `initiate-download` endpoint for CSV datasets.
3. Poll the documented `poll-download` endpoint for the download URL, observing its expected statuses and server guidance.
4. Download bytes, preserve as immutable raw file, verify content type, hash with SHA-256, record retrieval time UTC, and avoid committing source secrets.
5. If API fails or is rate-limited, offer a **clearly labelled manual official-site download fallback** with the same manifest requirements. Never pretend the API succeeded.

Official guide: https://guide.data.gov.sg/developer-guide/dataset-apis/download-dataset

Use real publisher URLs and verify final downloadable PDF links from the official pages; never guess PDF filenames without checking. The 2025 Q3 full PDF link above is verified; verify all others in the implementation gate.

## A source record should include
`source_id, source_type, title, publisher, source_url, download_url_if_verified, licence_name, licence_url, redistribution_policy, publication_date, retrieval_utc, reporting_period, release_stage, content_type, raw_filename, byte_count, sha256, source_revision_notes, access_method, retrieval_status`.

## What remains open
- Resolve and validate direct URLs for all report files; inspect their copyright notices.
- Test API response schemas and whether rate limits require credentials.
- Confirm full interval coverage 2024-Q1 through 2026-Q2 per metric/sector.
- Decide whether the Q2 advance is better ingested as HTML or full PDF and how page citations apply to each.
- Confirm raw-file storage/redistribution policy appropriate to interview repository visibility.
- Pin parser, dataframe, analytics and download tool versions after smoke testing.
