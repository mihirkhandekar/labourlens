# Independent AI review — M1 source fidelity and corpus sanity

**Review type:** independent AI inspection, **not human review**. Date: 2026-10-31. No human reviewer fields were populated. Only this report was written; no corpus, application, sample-sheet or gold changes were made.

## Independence, scope and method

**VERIFIED FACT:** Both requested spot-check sheets have empty reviewer-result tables. Their input Flag / Our value columns are pipeline/sample metadata, not reviewer verdicts; I did not treat those flags as truth. I did not open any forbidden prior-review file or study material and encountered no prior verdict. README mentions the existence of earlier AI reviews, without their findings; no earlier verdict informed this report.

**REQUIREMENT:** Inspect the 16 passage samples and 14 observation samples independently, then examine the entire current local corpus. Assessment PDF, section 2, requires provenance, usage constraints, transformations and data-quality checks; section 6 requires genuinely human review, which this report does not satisfy.

**MEASURED RESULT:** Read-only programs were executed as `uv run --offline python -c <program>` through Python subprocesses with `UV_OFFLINE=1`. They used pandas, PyMuPDF, BeautifulSoup and standard-library CSV/hash/Unicode tools. No network or paid command was used, and no test suite, fetch, rebuild or model experiment was run. All executed inspection programs completed successfully. The initial positional `get_text('blocks')` comparison was discarded: passage block indices are reading-order indices, not raw PDF block numbers. Final checks independently compared source `get_text('dict')` span text and rounded block rectangles; all 12 sampled PDF texts and bboxes match actual raw source blocks. All 12 PDF sample regions were rendered and visually inspected, with full-page renders for three suspect samples and three missing-page examples. All four HTML samples were checked against raw DOM text and headings.

**Limits:** The publisher evidence here is the locally saved official CSV and metadata, not a fresh independent publisher-site download. Live publisher values, authenticity of the original HTTP acquisition, and changes after the saved snapshot are **not checked**. Snapshot hash agreement establishes internal provenance integrity, not external authenticity. PDF rendering plus extraction checks are AI inspection, not a human reading. I did not visually inspect every page, manually interpret every table, or prove absence of arbitrary obfuscated instructions. No claim about downstream retrieval filtering follows from an ingestion-only check.

## Passage spot checks — one row per owner-sheet item

Raw PDF/HTML paths resolve from `data/manifests/manifest.json` by source_id and raw_path; extracted records are in `data/passages/<source_id>.jsonl`. All PDF rectangles below are the stored [x0,y0,x1,y1] in PDF points, verified equal to the raw text-block rectangle rounded to one decimal. All sampled PDF text is readable, without encoding garbling. HTML normalized text agrees with raw DOM in all four cases. Matching literal text does not imply self-contained context or usable table structure.

| Sheet # | Exact passage id | Raw locator / verified bbox | Verdict | Independent evidence |
|---|---|---|---|---|
| 1 | `mom-2025-q3-final:p059:b011:5fd0aa50` | PDF p.59; `[72.0, 543.2, 525.9, 590.7]` | **match** | Survey coverage narrative faithfully retained; 25-employee threshold and the 2006 extension agree. Section is Coverage; no garbling. |
| 2 | `mom-2025-q3-final:p032:b037:432f5c93` | PDF p.32; `[56.7, 738.5, 540.8, 760.4]` | **match** | Footnote 15 agrees visually, including Manufacturing 45.5→45.2 hours / 3.6→3.1 overtime and food-service 39.5→38.9 / 1.1→0.9. Printed page 26 agrees. Chart heading supplies context; no garbling. |
| 3 | `mom-2025-q3-final:p051:b021:661903e0` | PDF p.51; `[63.7, 297.3, 543.8, 326.2]` | **match; table intentionally unreliable** | Two transport rows and five numeric entries per row agree visually (land: 1.3,1.1,1.0,1.1,0.9; water: 1.0,1.1,1.0,1.0,0.8). No column headers in passage; flag correctly prevents standalone numeric interpretation. Section 7.2 agrees. |
| 4 | `mom-2025-q4-final:p055:b006:5e3f4ad2` | PDF p.55; `[72.0, 237.0, 525.9, 283.2]` | **match** | Employment definition retains self-employment and the national-service exclusion. Coverage subsection agrees; no garbling. |
| 5 | `mom-2025-q4-final:p056:b013:fbf4d810` | PDF p.56; `[72.0, 534.9, 526.0, 655.7]` | **match** | Narrative distinguishes frictional, structural and cyclical unemployment faithfully. Limitations subsection agrees; no garbling. |
| 6 | `mom-2025-q4-final:p031:b031:20de054b` | PDF p.31; `[43.7, 431.7, 575.5, 461.1]` | **match; metadata incomplete** | Two finance-related table rows agree; first row contains 9.3,4.9,8.9,0.8,2.5,5.7,2.1,-1.3,241.3. Table flag is correct. Stored section is generic Statistical Updates, rather than table 1.1; headers/units remain outside the block. |
| 7 | `mom-2026-q1-final:p054:b015:1f957942` | PDF p.54; `[93.6, 661.5, 520.6, 704.1]` | **match** | Narrative about vacancy recruitment actions matches, including advertising, agencies and interviews. Definitions subsection agrees; no garbling. |
| 8 | `mom-2026-q1-final:p056:b002:6f57fe7e` | PDF p.56; `[93.6, 122.4, 520.6, 189.3]` | **mismatch: section metadata** | Text and bbox match the turnover discussion, but section_heading is A27, a preceding-page footer. Rendered page is printed A28; actual paragraph continues turnover limitations. Missing printed label is distinct from correct physical p.56. |
| 9 | `mom-2026-q1-final:p042:b030:0776a24c` | PDF p.42; `[67.9, 406.0, 540.2, 430.9]` | **match; table intentionally unreliable** | Finance rows agree, including 6.3,5.1,5.7,6.5,6.6 and 5.7,4.3,5.1,5.8,5.8. Section 6.1 agrees; values are in thousands on page, not standalone count observations. Header omitted; correct table flag. |
| 10 | `mom-2026-q2-final:p048:b049:a897f425` | PDF p.48; `[60.4, 694.0, 458.5, 736.6]` | **mismatch: footer contamination** | Two notes about establishment coverage and annual averaging match; physical p.48 is correct. Extracted block also appends the printed footer A20, while printed_page_label is null. Hours section is correct. No word garbling. |
| 11 | `mom-2026-q2-final:p022:b020:7059aed2` | PDF p.22; `[56.7, 537.0, 540.8, 568.2]` | **unclear: context-fragmented** | Stored text exactly matches a raw text block, and printed page 16 agrees, but starts inside note (2), ends inside note (3), and omits the latter’s continuation about public-sector coverage. The same bbox intersects adjacent lines because of overlapping PDF blocks. No cross-page text or invented numbers; unsuitable as a self-contained definition. |
| 12 | `mom-2026-q2-final:p046:b031:7d6f5b76` | PDF p.46; `[66.2, 426.8, 541.5, 456.0]` | **match; table intentionally unreliable** | Finance rows agree: 1.1,0.9,0.9,0.9,0.7 and 1.0,0.9,0.9,0.9,0.7. Section 7.2 and table flag agree; resignation units and period headers occur elsewhere on page. |
| 13 | `mom-2026-q2-advance:s01:i008:86484167` | HTML `s01:i008` | **match** | Raw HTML article paragraph 5 agrees: retrenchments 3,830→4,500 and incidence 1.6→1.9 per 1,000. Advance status correct. Item 8 is extraction ordinal, not publisher paragraph number. HTML has no PDF page/bbox. |
| 14 | `mom-2026-q2-final-release:s01:i007:f07b514a` | HTML `s01:i007` | **match** | Raw HTML paragraph 7’s policy-support introduction agrees. Final status and article heading agree; item 7 is extraction ordinal. No page/bbox expected. |
| 15 | `mom-2025-q3-advance:s02:i004:bfea3fb7` | HTML `s02:i004` | **mismatch: heading footnote** | Raw HTML paragraph 4 agrees and advance status is correct. Stored section Main Findings 3 wrongly incorporates a superscript footnote marker: raw DOM is strong > span > Main Findings + sup(3). Item 4 is section-local extraction ordinal; no page/bbox expected. |
| 16 | `mom-2025-q3-final-release:s01:i012:472fa426` | HTML `s01:i012` | **match** | Raw HTML subparagraph (c), covering graduate programmes and application routes, agrees. Article heading and final status agree. Item 12 is extraction ordinal; no page/bbox expected. |

**Interpretation:** Literal source-block fidelity is strong on this sample (12/12 PDF, 4/4 HTML), but sample 8 has a wrong section, sample 10 includes a footer, sample 11 has incomplete semantic context, and sample 15 has a heading/footnote merge. Tables 3/6/9/12 preserve numbers but flatten row/column relationships; their `table_unreliable` flags are appropriate and are not extraction passes for numerical analysis.

## Statistical spot checks — one row per owner-sheet item

For every row below I opened the exact CSV in the observation’s snapshot directory, parsed the owner-sheet csv_row as a 1-based physical CSV record including the header, and selected the named column. **All 14 raw_value strings match the CSV cell; all 14 referenced CSV hashes match their manifest SHA-256.** Raw source quarter/month keys and dimensions were checked, not just values. Month endpoints March/June/September/December map to Q1/Q2/Q3/Q4, not to quarter averages. A matching result below is therefore **snapshot-local**, with live publisher agreement unverified.

Every sampled record has `release_stage=dataset_snapshot`, which accurately identifies its saved dataset version but does **not** independently establish whether a particular cell was provisional, final or revised. Publisher employment-change metadata explicitly permits industry reclassification revisions. No row-specific revision flag or earlier statistical snapshot was available for these samples. Other report releases must not silently override these dataset values.

| Sheet # | Observation id / source | CSV locator and independent value/period check | Labels, status and verdict |
|---|---|---|---|
| 1 | `9e3b178b6b85f234`; resident_unemployment_rate | row 139, non_seasonally_adj_unemp_rate = 3.5; raw 2026-06 → 2026-Q2 | **match**: percent, resident, not_adjusted. Adjacent adjusted cell is 2.9: do not confuse the two. |
| 2 | `4caa3fbd0df137f1`; resident_unemployment_rate | row 136, same column = 2.7; 2025-09 → 2025-Q3 | **match**: percent, resident, not_adjusted; adjusted counterpart is 2.9. |
| 3 | `ce87ebbfe18bb7ce`; vacancy_to_unemployed_ratio | row 109, jv_to_ue = 1.57; 2024-Q4 | **match**: ratio, seasonally_adjusted, population not_applicable. Saved publisher metadata expressly states seasonal adjustment. |
| 4 | `a84eaacb4cda2a28`; vacancy_to_unemployed_ratio | row 107, jv_to_ue = 1.72; 2024-Q2 | **match**: same series/units/adjustment as row 3. |
| 5 | `a62a15204fcba505`; retrenched_employees | row 112, retrench = 3670; 2025-Q3 | **match**: persons, establishments, not_applicable adjustment. Publisher metadata describes redundant permanent staff plus early-ended term contracts; establishment survey coverage is not resident-only coverage. |
| 6 | `0f99b5c79172c310`; retrenched_employees | row 106, retrench = 3030; 2024-Q1 | **match**: same series and population basis as row 5. |
| 7 | `7f5d5cef621d53dc`; employment_change_by_sector | row 26, 20251Q = -200; arts/recreation sector agrees | **match value/period; unclear population basis**: persons; not_applicable adjustment; population explicitly unverified_basis, not overall or resident. Source metadata supports change from preceding period but does not settle the excluded-worker basis. |
| 8 | `8530778cbaf4bd36`; employment_change_by_sector | row 17, 20261Q = 6100; combined property/professional/administrative sector agrees | **match value/period; unclear population basis**: same limitations as row 7; industry reclassification revisions are disclosed in saved metadata. |
| 9 | `642a17683020895f`; job_vacancy_count | row 113, job_vacancy = 75700; 2025-Q4 | **mismatch in review sheet only**: Parquet correctly says vacancies, whereas the sample sheet still says persons. Establishments, adjustment unspecified. The CSV and Parquet number agree. |
| 10 | `bd6e4286a15fb297`; recruitment_rate_by_occupation | row 334, recruitment_rate = 2.1; 2025-Q3; production/transport/cleaning/labour occupation group agrees | **match**: percent, establishments, adjustment unspecified. Saved column metadata confirms percent; do not infer seasonal adjustment. |
| 11 | `2d282c9a1ae8c215`; recruitment_rate_by_industry | row 4414, recruitment_rate = 1.2; 2024-Q4; transport-equipment industry agrees | **match**: percent, establishments, adjustment unspecified; saved column metadata confirms percent. |
| 12 | `236138a9f359e9af`; resignation_rate | row 114, resignation_rate = 1; 2026-Q1 | **match**: percent, establishments, adjustment unspecified; monthly_resignation_rate indicator is a monthly average during the quarter, consistent with saved publisher definition, not a quarterly cumulative rate. |
| 13 | `05cb21cfc6f40801`; retrenched_by_industry | row 4427, retrench = dash; 2024-Q4; accommodation agrees | **match**: value null, raw dash preserved, missing_reason explicitly leaves nil versus suppression unresolved; persons, establishments, not_applicable adjustment. Not zero. |
| 14 | `2b6e9c88c668657c`; resident_unemployment_rate | row 114, non_seasonally_adj_unemp_rate = 3.1; 2020-03 → 2020-Q1 | **match**: resident, percent, not_adjusted; in_answer_scope=false correctly excludes the pre-2024 observation. Adjusted counterpart is 3.4. |

**Owner attention:** Rows 7/8 retain honest uncertainty rather than silently claiming a verified population definition. These rows cannot certify comparability against a report employment series with a different worker-exclusion basis. All row-specific final/revised-status claims remain unverified beyond the snapshot label.

## Whole-corpus sanity results

### Passages: duplicates, emptiness, controls and instruction-like content

- **MEASURED RESULT:** 13,484 passages across 46 documents (24 PDF, 22 HTML). Empty/whitespace-only texts: **0**. Duplicate passage IDs: **0**. Text SHA-256 mismatches: **0**.
- **Duplicates:** whitespace-normalized exact text forms **640 repeated groups**, with **3,307 excess copies** beyond one per group. Within-document repeats form **354 groups / 869 excess copies**. These counts are not automatically corruption: repeated definitions, notes and independently published versions can be legitimate. But repeated HTML browser/navigation content is not report evidence. For example, `mom-2025-q3-advance:s00:i001:66f5e4f8` and six other releases share an obsolete browser/TLS instruction; adjacent i002/i003 are site-navigation categories. Preserve provenance but exclude boilerplate from evidence passages and avoid treating copies as independent corroboration.
- **Control characters: failed clean-text criterion.** 126 passages contain C0 controls other than ordinary newline/carriage-return/tab; 69 are marked garbled, but **57 are incorrectly marked ok**. Example `mom-2026-q2-final:p059:b002:a5dc11e0` has U+0014, U+0011 and nine U+0003 characters and visually nonsensical encoded text. Similar blocks occur on feedback pages across reports. Five additional ok examples in `mom-2023-q1-final` occur on pages 2–5, so the issue is not exclusively a feedback-page footer. The garbling function in `src/labourlens/data/pdf_extract.py:45-67` skips all blocks under 60 characters, explaining short contaminated blocks escaping the flag. C0 control detection must not depend on length. Do not “repair” shifted characters into assumed English.
- **Instruction-like content: literal absence is false.** A broad case-insensitive scan for instruction, please/must, do-not, system/assistant/developer-role patterns, secret disclosure, and command/execution language yielded 84 candidate passages. Context inspection identifies publisher copyright/citation instructions, feedback requests, contact requests, ordinary statistical prose false positives, and seven copies of the browser-configuration instruction. A narrower role-override/secret/command scan finds only those seven browser-step hits. I found **no overt malicious role-override or secret-exfiltration payload in these matches**; this is not proof that arbitrary injection is absent. Treat all retained text as untrusted, and remove irrelevant site/feedback instructions from answer evidence. Legitimate citation requirements may belong in rights metadata, not the retrieval body.
- Quality labels in the full corpus: **6,360 ok; 7,055 table_unreliable; 69 garbled**. Their existence is not proof every table or corrupt passage is correctly flagged; the 57 control-containing ok blocks are concrete false negatives.

### Physical PDF page coverage

Coverage is “at least one retained passage on physical page”, not complete recovery of its text/images. Every stored PDF page_number is within the raw PDF page count. Covers often intentionally disappear; missing narrative pages are materially different. Figures embedded as images are not recovered by a text-only extraction.

| Source id | Raw PDF pages | Pages with passages | Missing physical pages |
|---|---:|---:|---|
| `mom-2023-q1-final` | 53 | 51 | 1, 13 |
| `mom-2023-q2-final` | 54 | 53 | 1 |
| `mom-2023-q3-final` | 54 | 53 | 1 |
| `mom-2023-q4-final` | 67 | 66 | 1 |
| `mom-2024-q1-final` | 54 | 53 | 1 |
| `mom-2024-q2-final` | 55 | 54 | 1 |
| `mom-2024-q3-final` | 55 | 54 | 1 |
| `mom-2024-q4-final` | 57 | 56 | 1 |
| `mom-2025-q1-final` | 55 | 54 | 1 |
| `mom-2025-q2-final` | 61 | 60 | 1 |
| `mom-2025-q3-final` | 64 | 62 | 1, 30 |
| `mom-2025-q4-final` | 64 | 63 | 1 |
| `mom-2026-q1-final` | 59 | 58 | 1 |
| `mom-2026-q2-final` | 59 | 58 | 1 |
| `mom-jv2025` | 34 | 33 | 1 |
| `mom-lf2024-copyright` | 2 | 2 | none |
| `mom-lf2024-coverage-methodology` | 12 | 12 | none |
| `mom-lf2024-survey-findings` | 73 | 66 | 16, 20, 35, 47, 51, 56, 66 |
| `mom-lf2024-survey-highlights` | 1 | 1 | none |
| `mom-lf2025-copyright` | 1 | 1 | none |
| `mom-lf2025-coverage-methodology` | 12 | 12 | none |
| `mom-lf2025-survey-findings` | 80 | 72 | 7, 41, 52, 56, 64, 68, 72, 73 |
| `mom-lf2025-survey-highlights` | 1 | 1 | none |
| `mom-wage-practices2024` | 33 | 33 | none |

**Major omission verified:** `mom-2025-q3-final`, physical p.30 (printed 24), has **691 extractable text characters** but **zero passages**. The rendered page includes substantive prose on vacancy/unemployment matching and concluding labour-market interpretation, not merely a cover or image-only chart. Raw dict text breaks that prose into individual blocks shorter than 120 characters. The font-based heading rule in `pdf_extract.py:153-156` classifies these short body blocks as headings and drops them, even when their content is ordinary narrative. This is a source-coverage failure, not an upstream inaccessible page.

The `mom-2023-q1-final` missing p.13 and `mom-lf2025-survey-findings` missing p.7 were also rendered: they contain charts, not blank pages. The latter includes notes; image/chart contents remain unavailable as passages. Other uncovered non-cover LF pages have 35–200 extractable characters each; their full visual content was not individually audited. Do not present page coverage percentages as extraction recall. Record intentional chart-only/cover exclusions separately from lost prose and caption/notes.

### Structured observations: uniqueness, nulls, quarters and units

- **MEASURED RESULT:** 43,662 rows; 3,790 in the supported answer window. Duplicate observation_id: **0**. Duplicates on `(source_id,indicator_id,period,population,adjustment,dimension)`: **0**. Scope flags disagreeing with 2024-Q1..2026-Q2 membership: **0**.
- No nulls in identifiers, source/snapshot/locator, indicator/period/bounds, raw value, unit/population/adjustment, release stage, scope or transformation version. Empty dimension/path strings are intentional for undimensioned/non-sector series and were not miscounted as NaN.
- Values missing: **7,457**, of which **416 in scope**. All 7,457 have a missing_reason; no non-null numeric value has a missing_reason. Reasons: **4,777** unresolved dash-marker cells, **2,600** explicit na cells, **80** generic dash-token cells. sector_level is null on **35,862** nonhierarchical rows. These are not fabricated zeroes; the generic dash reason is less expressive but still preserves missingness.
- Unit consistency within each `(source_id,indicator_id,population,adjustment,dimension)` series: **0 mixed-unit series**. **Consistency does not imply correctness:** `job_vacancy_count` correctly uses vacancies for all 114 rows, but both dimensioned vacancy-count datasets use persons throughout (**4,700 industry rows + 450 occupation rows**, including **470 in-scope rows**). These count unfilled positions, not employed/unemployed persons, and should also use vacancies. Exact examples: `6c867791ec735e1e` (2026-Q2, wholesale trade, 3,600) and `3dce369080f10288` (2026-Q2, professional/managerial/technical grouping, 39,300).
- All four originally approved datasets contain all ten requested quarters; population/adjustment/dimension-aware grouping confirms this, rather than merely taking the union of dates. Across all 33 datasets, **31** have complete ten-quarter coverage in every scoped series; the two short-workweek/temporary-layoff datasets stop at 2025-Q4. Their 15 series each have eight quarters, missing 2026-Q1/Q2; this is an availability limit, not permission to impute zeros. The complete row-by-dataset accounting follows.

| Dataset | Scoped rows | Scoped series | Missing requested quarters | Null scoped values | Unit |
|---|---:|---:|---|---:|---|
| `citizen_unemployment_rate` | 20 | 2 | none | 0 | percent |
| `employment_change_by_sector` | 260 | 26 | none | 0 | persons |
| `job_vacancies_by_industry` | 420 | 42 | none | 0 | persons |
| `job_vacancies_by_occupation` | 50 | 5 | none | 0 | persons |
| `job_vacancy_count` | 10 | 1 | none | 0 | vacancies |
| `job_vacancy_rate` | 10 | 1 | none | 0 | percent |
| `job_vacancy_rate_by_industry` | 420 | 42 | none | 0 | percent |
| `job_vacancy_rate_by_occupation` | 50 | 5 | none | 0 | percent |
| `overall_unemployment_rate` | 20 | 2 | none | 0 | percent |
| `recruitment_rate` | 10 | 1 | none | 0 | percent |
| `recruitment_rate_by_industry` | 420 | 42 | none | 0 | percent |
| `recruitment_rate_by_occupation` | 30 | 3 | none | 0 | percent |
| `reentry_12m` | 10 | 1 | none | 0 | percent |
| `reentry_6m` | 10 | 1 | none | 0 | percent |
| `resident_unemployment_rate` | 20 | 2 | none | 0 | percent |
| `resignation_rate` | 10 | 1 | none | 0 | percent |
| `resignation_rate_by_industry` | 420 | 42 | none | 0 | percent |
| `resignation_rate_by_occupation` | 30 | 3 | none | 0 | percent |
| `retrenched_by_industry` | 420 | 42 | none | 47 | persons |
| `retrenched_by_occupation` | 30 | 3 | none | 0 | persons |
| `retrenched_employees` | 10 | 1 | none | 0 | persons |
| `retrenched_permanent` | 10 | 1 | none | 0 | persons |
| `retrenched_permanent_by_industry` | 420 | 42 | none | 50 | persons |
| `retrenched_permanent_by_occupation` | 30 | 3 | none | 0 | persons |
| `retrenched_term_contract` | 10 | 1 | none | 0 | persons |
| `retrenched_term_contract_by_industry` | 420 | 42 | none | 288 | persons |
| `retrenched_term_contract_by_occupation` | 30 | 3 | none | 3 | persons |
| `short_workweek_temporary_layoff` | 24 | 3 | 2026-Q1, 2026-Q2 | 0 | persons |
| `short_workweek_temporary_layoff_by_industry` | 96 | 12 | 2026-Q1, 2026-Q2 | 28 | persons |
| `unemployed_citizens` | 20 | 2 | none | 0 | persons |
| `unemployed_overall` | 20 | 2 | none | 0 | persons |
| `unemployed_residents` | 20 | 2 | none | 0 | persons |
| `vacancy_to_unemployed_ratio` | 10 | 1 | none | 0 | ratio |

## Overall assessment and boundaries

**MEASURED RESULT:** Sampled CSV cells, literal PDF blocks, raw DOM text, IDs, hashes, scope flags and uniqueness are internally consistent. **PROPOSAL:** Do not sign off M1 source extraction as fully trustworthy yet: lost narrative, corrupt ok passages and vacancy units require correction, followed by a genuinely human spot check. Original raw snapshots should remain immutable; changes should be regenerated derived artifacts with explicit parser/normalization versioning and updated sample sheets, not edited source bytes.

This review deliberately does not decide whether the current wider corpus expansion was approved, certify publisher licences, certify a held-out result, or certify source authenticity from the internet. Those are separate checks. No human-review requirement is completed by this document.

## Issues ranked by severity

No critical issue was established within this source-inspection scope. Major means potentially misleading evidence or materially missing source content; minor means local metadata/noise/documentation defects. Locations below identify observed artifacts, not speculative downstream behaviour.

| Severity | Exact id / location | Evidence | Suggested fix |
|---|---|---|---|
| major | `data/passages/mom-2025-q3-final.jsonl`; missing physical p.30 / printed 24; `src/labourlens/data/pdf_extract.py:153-156` | 691 raw text characters; rendered substantive narrative; zero retained passages. Short 11-point body blocks are mistaken for headings and discarded. | Recognize true headings using layout/context, retain adjacent prose fragments, and record expected exclusions; add regression coverage for this specific page without rewriting raw PDF. |
| major | `data/passages/`; example `mom-2026-q2-final:p059:b002:a5dc11e0`; `src/labourlens/data/pdf_extract.py:45-67` | 126 control-containing blocks, 57 labelled ok; the example contains 11 C0 characters. Length guard exempts short corrupt blocks. | Detect controls at all lengths; flag/exclude unreadable blocks and feedback boilerplate while retaining raw provenance. Do not silently guess decoded wording. |
| major | `data/processed/observations.parquet`, sources `job_vacancies_by_industry` and `job_vacancies_by_occupation`; examples `6c867791ec735e1e`, `3dce369080f10288` | All 5,150 dimensioned vacancy rows say persons; the aggregate correctly says vacancies. 470 affected rows are in scope. | Use vacancies consistently for count-of-position series, regenerate affected exports/metadata and review dependent labels/calculation compatibility. |
| minor | `mom-2026-q1-final:p056:b002:6f57fe7e` | Correct prose and bbox, but section_heading=A27 is a previous-page footer; actual printed page A28. | Exclude alphanumeric appendix page labels from heading detection; preserve/inherit the real turnover subsection. |
| minor | `mom-2026-q2-final:p048:b049:a897f425` | Notes block appends A20 footer and printed_page_label is null. | Recognize appendix page labels including footer text merged into blocks; separate footer without changing substantive notes. |
| minor | `mom-2026-q2-final:p022:b020:7059aed2` | Exact PDF block starts inside note (2) and stops inside note (3); source continuation excluded. | Chunk complete adjacent notes and retain their bounding-box unions / source block links, or clearly mark fragments requiring context. |
| minor | `mom-2025-q3-advance:s02:i004:bfea3fb7` and section metadata | Main Findings 3 contains DOM superscript footnote 3, not part of the heading. | Separate superscript reference markers from semantic section titles. |
| minor | `mom-2025-q3-advance:s00:i001:66f5e4f8` plus six duplicate releases; i002/i003 navigation | Obsolete browser/TLS instructions and navigation appear as ok research passages. Broad scan finds 84 instruction-like candidates, including legitimate publisher instructions. | Restrict extraction to article content; retain rights instructions in rights metadata and treat remaining source text as untrusted. Do not claim instruction-like text is wholly absent. |
| minor | Duplicate groups in `data/passages/`; e.g. `mom-2025-q3-final:p010:b027:adbe54e1` and `mom-2025-q3-final:p032:b032:adbe54e1` | 640 normalized text duplicate groups / 3,307 excess copies; 354 groups repeat within one document. Some are legitimate notes, some boilerplate. | Remove boilerplate and deduplicate context assembly while preserving every genuine source/version citation; do not indiscriminately delete revision evidence. |
| minor | `docs/human-review/statistical-spot-check.md:15`, sample 9 / `642a17683020895f` | Review sheet unit persons is stale; current Parquet unit vacancies is correct. | Regenerate the spot-check sheet with current units before the owner reviews it; leave human result cells empty. |
| minor | Scoped `short_workweek_temporary_layoff` and `short_workweek_temporary_layoff_by_industry` | 15 series have only eight of ten requested quarters, absent 2026-Q1/Q2. | Expose actual coverage and abstain for unavailable quarters; do not imply the supported window guarantees every dataset’s coverage. |
| minor | `7f5d5cef621d53dc`, `8530778cbaf4bd36`; sampled structured release-stage metadata | Population basis remains explicitly unverified; dataset_snapshot cannot establish cell-specific revision status. Local-only review cannot confirm live publisher agreement. | Keep uncertainty visible and verify definitions/status with the owner’s publisher check before claiming compatible populations or final/revised cells. |

## Actions taken after this review (owner note)
- Fixed: unit for `job_vacancies_by_industry` and `job_vacancies_by_occupation` changed from persons to vacancies in the specs; data rebuilt (255 checks, 0 failed) and exported. Dev and held-out agent runs were produced before this fix, so evidence for those series was rendered with the old unit label; numeric values are unaffected.
- Fixed: stale unit in `statistical-spot-check.md` sample 9.
- Not changed, by design: PDF extraction issues (Q3 2025 physical p.30 narrative loss, 57 control-character passages flagged ok, appendix-label headings, duplicates). Changing extraction changes passage ids and invalidates the frozen retrieval and held-out results. Recorded as known limitations and as the next fix after the owner's review.
