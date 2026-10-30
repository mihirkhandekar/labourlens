# Milestone 1 — Government data ingestion and provenance

**Status: PROPOSAL — HUMAN APPROVAL REQUIRED BEFORE CODING.**  
**Goal:** build a small, reproducible, legally considerate pipeline that acquires real government data, retains original bytes locally, normalizes official statistical observations, extracts citable report passages, tracks source revisions and produces audit-ready quality evidence.

## 1. Why ingestion is the first coding milestone

The RAG search index, statistical tools, answer citations, and evaluation gold labels all depend on stable identifiers and trustworthy source metadata. If data ingestion is weak, an apparently good LLM can still mix resident and overall unemployment, seasonally adjusted and raw rates, or preliminary and final figures. This milestone does **not** implement agents, LLM calls, retrieval indexes, MCP, or UI.

### Primary deliverables
1. Official-source acquisition pathway for each of four approved datasets and five approved reports, with honest API/manual fallback and a rights-aware raw-file handling policy.
2. Machine-readable source manifest and an immutable local raw snapshot with SHA-256 hashes (where licensed/access permitted).
3. Typed long-form statistical observation table, with population/adjustment/unit/source/revision metadata and validated quarter handling.
4. PDF/HTML extraction into auditable passages with stable IDs, real page numbers for PDF content, and publication/source metadata.
5. Data-quality reports, reproducibility instructions, unit/integration tests, and a small manually checked citation/observation sample.
6. An interview/study note explaining the data choices, pitfalls, source reliability, and rejected alternatives.

## 2. Decision A — Acquisition strategy

| Option | How | Advantages | Problems | Recommendation |
|---|---|---|---|---|
| A1. Manual downloads | Download CSV/PDF via official sites and store locally | Quick, easy to inspect; survives API quirks | Harder to reproduce automatically; human mistakes | Fallback |
| A2. API/live downloads | Use documented data.gov.sg endpoints and official document URLs on each run | Repeatable, potentially fresh | Network, rate limits, revision drift, changed upstream content | Not alone |
| **A3. Verified acquisition + immutable snapshot** | Fetch through official API and verified URLs, hash originals, pin manifest, allow explicitly labelled manual fallback | Best mix of reproducibility and real-world engineering | Slightly more metadata/build work | **Preferred** |

### Proposed flow (to be implemented after approval)
- Identify verified official source ID and URL from manifest.
- For data.gov.sg CSV, follow official `initiate-download` then `poll-download` documented endpoints; honor response codes/rate limits and use a bounded retry policy.
- For MOM report, follow the verified official page to the actual PDF link or ingest the official advance-release HTML when more faithful. Never guess a download URL.
- Validate media type and file signature, size cap, non-empty content, HTTP status, source host allow-list, and sha256 of exact downloaded bytes.
- Store local immutable raw bytes in versioned snapshot paths. **Do not check restricted report PDFs into public GitHub.**
- Record retrieval UTC timestamp, publisher publication date, reporting period, rights, hash, byte length, source URL, and parser version.
- Normalized output is derived from one exact snapshot ID; changes create a new snapshot, not a silent overwrite.

**Open item:** choose whether the public repository includes allowed dataset CSV snapshots or only scripts + hashes. Rights for report PDFs must be evaluated separately. Recommended: commit small structured snapshots only when terms allow, but never raw report PDFs by default.

## 3. Decision B — Dataframe and analytical store

| Option | Benefits | Costs | Recommendation |
|---|---|---|---|
| Pandas + CSV only | Few dependencies, familiar | Repeated parsing, weak persistent analytical queries | Useful interim baseline |
| SQLite normalized records | Portable/inspectable, relational | Less convenient for analytical table operations | Credible alternative |
| **Pandas -> Parquet -> DuckDB** | Good cleaning + typed snapshots + analytical SQL; local and testable | Adds `pyarrow`/DuckDB | **Preferred** |
| PostgreSQL | Strong production database | DevOps overhead unrelated to rubric | Defer |

Do **not** let the agent produce arbitrary SQL. Later statistical tools should accept typed indicator/time/dimension inputs, and application code should query the validated store.

## 4. Decision C — PDF/HTML extraction

| Option | Benefits | Risks | Recommendation |
|---|---|---|---|
| Plain PyMuPDF page text | Very fast, page-aware | Reading order, columns and tables may be scrambled | Baseline extractor |
| **PyMuPDF block/coordinate + section-aware extraction** | Preserves positions and page metadata; better citations | Custom parsing logic; need manual verification | **Preferred** |
| pdfplumber selective table extraction | Additional table inspection capabilities | Another parser dependency; inconsistent on complex PDFs | Fallback on named problem pages |
| LLM/OCR-first extraction | Can handle difficult layouts | Extra costs, potential hallucinated text, weak reproducibility | Only controlled exceptional cases |
| Official HTML as document source | Clearer text and direct URL | Lacks PDF page references; summary may omit full methodology | Useful for Q2 advance/revision evidence |

Use PyMuPDF to retain physical PDF page index (1-based) plus printed page label if discernible, section heading, block order/coordinates, text and extraction warnings. The `page.get_text()` API does not guarantee natural reading order, and table recovery needs validation. Inspect a deliberate sample of pages containing prose, multicolumn sections, tables and footnotes. If a report is not extractable faithfully, mark the passage unsuitable for high-stakes numerical answers and rely on structured series for calculations.

Rights-sensitive default: acquired full PDFs remain local and ignored from Git. If source document cannot be legally redistributed, source manifests and link-backed citations can still be public, while any extracted passages in the repository must be limited to what reuse permits. Do not silently make a public corpus dump.

## 5. Canonical data contract — proposed

### 5.1 `SourceManifestEntry`
| Field | Meaning |
|---|---|
| `source_id` | Stable identifier (`mom-2026-q2-final`) |
| `source_type` | `dataset_csv`, `report_pdf`, `release_html` |
| `publisher`, `title`, `canonical_url` | Official provenance |
| `retrieval_url` | Actual verified download URL if distinct |
| `publication_date`, `retrieval_utc` | Published vs fetched times |
| `reporting_period_start/end` | Coverage of the source |
| `release_stage` | `advance`, `final`, `revised`, `not_applicable` |
| `licence_id`, `licence_url`, `redistribution_status` | Rights decisions and unknowns |
| `snapshot_id`, `sha256`, `byte_count`, `mime_type` | Immutable raw-file identity |
| `access_method`, `retrieval_status`, `parser_version` | Reproduction and troubleshooting |
| `notes` | Definitions, warnings, manual fallback reason |

### 5.2 `StatisticalObservation`
| Field | Why needed |
|---|---|
| `observation_id` | Stable, content/version-aware reference for citations |
| `source_id`, `snapshot_id`, `source_row_or_cell` | Lineage back to the original table |
| `indicator_id` | Canonical measure (`resident_unemployment_rate`, `retrenchments`, etc.) |
| `period` | Canonical `YYYY-QN` |
| `period_start`, `period_end` | Date bounds, not just a label |
| `value` | Validated numeric value; nullable only with a reason |
| `unit` | `percent`, `people`, `ratio`, `percentage_points` (the latter mainly for derived results) |
| `population` | `resident`, `overall`, `citizen`, `not_applicable` |
| `adjustment` | `seasonally_adjusted`, `not_adjusted`, `not_applicable` |
| `sector_id`, `sector_label` | Preserve sector hierarchy if applicable |
| `release_stage`, `revision_tag` | Preliminary/final/revised status |
| `raw_value`, `missing_reason`, `transformation_version` | Cleaning audit trail |

### 5.3 `DocumentPassage`
`passage_id, source_id, snapshot_id, original_url, document_title, publication_date, release_stage, page_number_pdf_1_based_or_null, printed_page_label_or_null, section_heading, block_positions_if_available, text, extraction_method, extraction_quality_flag, source_span_or_locator, parser_version, text_sha256`

**Stable ID rule:** derive IDs deterministically from source snapshot + passage position/section + parser version. IDs may legitimately change when the source or parser changes, but no silent changes in an evaluation snapshot.

## 6. Normalization per approved dataset

| Dataset | Conversion | Key validation questions |
|---|---|---|
| Resident unemployment | Map quarter-end `YYYY-MM` to `YYYY-QN`; emit separate observations per adjustment series | Month must be 03,06,09,12; `resident` definition retained; percent vs pp |
| Vacancy/unemployment ratio | Parse `YYYY-QN` and numeric ratio | Do not convert ratio `1.48` to `1.48%`; SA status retained |
| Retrenchments | Parse `retrench` textual numbers with strict patterns and explicit missing tokens | `N/A`, `-`, suppressed or invalid text never converted to 0 |
| Employment by sector | Melt wide quarter columns into long observations, preserve source series hierarchy | Don't double-count aggregate and sub-sector rows; check signs, unit, notes on rounded totals and revisions |

### Time range and semantic integrity
- Restrict **supported answers** to 2024-Q1–2026-Q2 (10 quarters).
- The raw source files may include earlier history; do not delete it without a documented reason, but apply scope filters for questions and evaluation.
- When comparing values, require matching indicator, unit, population, seasonality, and compatible reporting period. The tool should reject mismatches.
- Example: Q2 2026 advance total employment increase of 10,700 and final increase of 11,400 must remain two distinct source-attributed observations or release facts, not collapse into one unversioned value.

## 7. Quality checks and review

### Automated checks (required)
- All nine approved source IDs represented in catalog with retrieval status and official URL.
- Every successfully retrieved source file has a non-empty byte count, UTC acquisition timestamp, a SHA-256 digest and declared MIME type.
- Idempotency: rerunning against a pinned snapshot yields identical normalized outputs and stable observation/passage IDs.
- No duplicates for canonical composite keys within a snapshot unless they represent an explicitly different release/population/adjustment.
- All usable observations parse into valid quarter/number/unit; errors quarantined with raw cell and reason, never swallowed.
- Quarter-end `YYYY-MM` normalization tests for Mar/Jun/Sep/Dec and invalid month rejection.
- Null/suppression and non-numeric retrenchment marker tests.
- Employment sector wide-to-long conversion with aggregate/hierarchy handling, including rounding tolerance in totals.
- PDF/HTML passage non-emptiness, source ID, stable ID, and real document locator; flagged extraction anomalies.
- No secrets or copyrighted full reports committed; check `.gitignore`/public package contents.

### Manual cross-checks (real human review needed)
- Spot-check at least 2 observations per statistical dataset (8 total) against official source values.
- Review at least 2 passages per report (10 total), including one table/footnote/multicolumn example, verifying the extracted ordering and page or HTML locator.
- Verify the source-revision example against the original advance and final official releases.
- Record who reviewed, date, original source link, observed result and any discrepancy; do not report agent-generated reviews as human validation.

### Proposed acceptance criteria
1. A fresh user can follow documented acquisition and normalization steps without hidden manual edits; when copyright prevents redistributing raw PDFs, the instructions explicitly acquire them from the official sites.
2. The four dataset adapters produce typed observations or a clearly reported failure; all five reports yield verifiable citable source units or clearly flagged limitations (PDF or HTML as justified).
3. A provenance record connects each normalized observation and report passage to the exact source file, URL and immutable snapshot.
4. Quality test suite passes with actual command/test output captured; errors are visible, not hidden.
5. A single deterministic data inspection/demo prints sample validated observation IDs and passage IDs, and verifies the preliminary/final distinction (not an LLM answer).
6. Data sheet and decision record state licensing, exclusions, missingness and transformations.

## 8. Suggested project components AFTER approval (not implemented by this document)

```text
src/labourlens/data/
    catalog.py              # fixed source IDs and approved URLs
    acquire.py              # official dataset/document downloads
    raw_store.py            # hash/version snapshots
    normalize.py            # indicator-specific adapters
    models.py               # typed source/observation/passage structures
    pdf_extract.py          # layout-aware PDF extraction and warnings
    validate.py             # invariant checks and quality report
    build.py                # orchestrated, repeatable ingestion pipeline

data/                       # actual raw sources handled according to rights
    raw/                    # usually gitignored
    processed/              # Parquet or equivalent; licence-aware
    manifests/

tests/data/
    test_periods.py
    test_normalizers.py
    test_provenance.py
    test_pdf_extract.py
    test_rights_packaging.py

docs/data-sheet.md
artifacts/data-quality/       # actual generated validation summaries
study/01-data-ingestion.md
```

## 9. Proposed implementation sequence after Milestone 1 approval

**M1.1** Verify API, direct report file URLs, PDF rights, and schemas. Produce actual source inventory. Stop if publisher access/terms differ materially from the plan.  
**M1.2** Implement approved manifest/typed schemas and acquisition with hashes, retries, immutable filenames, clear download errors. Test against one small dataset.  
**M1.3** Implement each dataset normalizer, tests and quarter/adjustment/unit checks. Build Parquet snapshot if chosen.  
**M1.4** Extract report text with physical page mapping and HTML locators. Run manual checks on difficult layouts before accepting passages as evidence.  
**M1.5** Build reproducible data-quality report; audit source revisions/licences; document observed errors.  
**M1.6** Run a clean-room setup/ingestion smoke test where feasible; capture commands, outputs, hashes and quality metrics. Document limitations and prepare a Git commit for owner review.

## 10. What should NOT happen during M1
- No LangGraph nodes, model calls, vector embeddings, BM25 index, MCP server, Next.js UI, dataset-only fake analytics, or evaluation scores presented as real.
- No unverified PDF URLs, invented citations, arbitrary web scraping, full report redistribution, hardcoded statistics as the whole data pipeline, or silent fallback to synthetic data.
- No claims that all data have been cleaned or manually reviewed without real artifacts to support them.

## 11. Decision gate for the owner

**Recommended bundle to approve:**
- **Acquisition:** official API + verified download URLs + immutable hashes + licensed/manual fallback.
- **Structured data:** Pandas normalization -> Parquet -> DuckDB for later typed queries.
- **Documents:** PyMuPDF text blocks and page/section locators; use HTML for advance release as needed; explicitly quarantine low-confidence PDF tables.
- **Rights:** keep full MOM PDFs local and out of public Git; publish manifests, fetch scripts and links with attribution; evaluate small derived text excerpt redistribution carefully.
- **Validation:** strict schemas, revision awareness, no null-to-zero conversions, manual sample checks, reproducibility test.

Ask the user to approve this package or request a change. **Do not start coding unless the user authorizes “Implement Milestone 1” (or equivalent).**
