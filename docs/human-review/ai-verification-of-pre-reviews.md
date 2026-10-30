# Independent verification of the two AI pre-reviews (M1 spot-check sheets)

**AI review by claude-agent (ReviewSpotMeta)**, 2026-10-30. This is an AI check of two other AI pre-reviews. It is **not** the owner's review. No owner sheet, gold record or reviewer/status field was changed.

Method: I recomputed every number below from `data/passages/*.jsonl`, the raw PDFs/HTML in `data/raw/` (PyMuPDF, `pdftotext -layout`, BeautifulSoup) and the raw CSVs in `data/snapshots/`. I did not import the application's extractor or normalizer, and I did not run fetch/build/eval. No MOM text is reproduced here. Passages are referred to by id, and the sheet row numbers below are the owner's.

Result values: **confirmed**, **not confirmed**, **different number**. I also list **new findings** the pre-reviews missed.

## 1. Passage pre-review

### 1a. Whole-corpus counts (recomputed)

| Claim | Result | Details |
|---|---|---|
| 13,484 passages in 46 JSONL files | confirmed | 13,484 passages in 46 files. |
| 126 passages contain a non-whitespace control character (Unicode Cc excluding `\n \r \t`): 69 garbled, 57 ok | confirmed | 126 = 69 garbled + 57 ok. |
| Four sampled reports: 27 control-bearing (15 garbled, 12 ok) | confirmed | The four reports hold 3,726 passages. Control-bearing counts per report: Q3-2025 has 0. Q4-2025, Q1-2026 and Q2-2026 each have 9 (5 garbled, 4 ok). 15 and 12 sum to 27. |
| 52 of the 57 control-bearing `ok` passages are under 60 characters; the other 5 are longer 2023-Q1 passages with U+0001 | confirmed | 52 are under 60 chars. The 5 long ones are all `mom-2023-q1-final` (pages 2 to 5) and contain U+0001. |
| The pre-review says control presence alone does not prove illegibility | confirmed, with a caveat | True of 4 of the 5 long ones, where U+0001 is a stray trailing control byte. One of them, `mom-2023-q1-final:p004:b006:a8ccfe71`, also contains a shifted-glyph garbled word in the middle of otherwise readable text, and is flagged `ok`. The pre-review did not mention this. |
| 0 passages contain U+FFFD | confirmed | 0 of 13,484. |
| `mom-2026-q2-final:p059:b002:a5dc11e0` is flagged `ok` but holds shifted glyphs/control codes | confirmed | It is 51 characters, flagged `ok`, and starts with control codes followed by shifted-letter text. `pdftotext` of the same page shows the same shift, so the page's font is unmapped. |
| The data sheet's note on garbling is incomplete (5 flagged blocks per feedback page; 4 more unflagged per report) | confirmed | The data sheet says 5 blocks per report are flagged. In each of the three reports a further 4 control-bearing blocks are `ok`. |
| 98 passages contain a standalone `A`+1 or 2 digit line, all flagged `ok`; 22 in the four reports | confirmed | 98 passages, all `ok`. 22 of them are in the four reports. This is a regex candidate count, not a visual confirmation. |
| 7,055 of 13,484 (52.32%) are `table_unreliable`; 2,233 of 3,726 (59.93%) in the four reports | confirmed | 7,055 and 2,233, as stated. The ratios 52.32% and 59.93% check out. |
| 123 raw appendix pages with a standalone A-marker and at least one stored passage, holding 3,200 passages, all with null `printed_page_label`; per report 30/33/30/30 | confirmed | I scanned raw PDF page text with my own regex. Pages: 30, 33, 30, 30 = 123. Passages: 756, 906, 754, 784 = 3,200. None has a printed label. Across the four reports, 423 passages have a printed label (the decimal-numbered pages) and 3,303 have none. |

### 1b. Sampled rows

I checked all 12 PDF rows against the raw PDF. Each stored bbox matches exactly one raw text block (max coordinate error 0.05 pt). The normalized block text equals the stored text, and the stored hash matches the text. Printed appendix labels A26, A18, A25, A26, A1, A26, A28, A14, A20 and A18 match the rendered pages for the rows that carry them. Printed numbers 26 and 16 match rows 2 and 11. For the four HTML rows I located the smallest source element, headings, superscripts and dates.

| Claim (owner sheet row) | Result | Details |
|---|---|---|
| Row 3 major: two transport rows flattened, code wraps over lines, no headers/units; `table_unreliable` appropriate | confirmed | Two rows in one 138-char block. The industry code wraps across two lines, and the values agree with the `pdftotext -layout` table (1.3, 1.1, 1.0, 1.1, 0.9 and 1.0, 1.1, 1.0, 1.0, 0.8). No headers or period labels in the passage. |
| Row 6 major: two financial rows with multiple numeric columns including a final level column | confirmed | One 156-char block holding a broad row (9.3 … 241.3) and a narrower row (10.5 … 197.0). All values agree with the layout text, and the signs agree. |
| Row 9 major: two rows, five numbers each, layout lost | confirmed | Values for both rows agree with the page: 6.3/5.1/5.7/6.5/6.6 and 5.7/4.3/5.1/5.8/5.8. |
| Row 12 major: two rows, five entries each | confirmed | Values agree: 1.1/0.9/0.9/0.9/0.7 and 1.0/0.9/0.9/0.9/0.7. |
| Row 10 minor: standalone A20 marker appended to the notes passage; `quality_flag=ok` hides it; `printed_page_label` null | confirmed | The stored text ends with the marker on its own line, after the two numbered notes. The flag is `ok` and the label is null. |
| Row 11 major: starts mid-note 2, includes the start of note 3, ends mid-note; context in b019/b021; all three flagged `ok` | confirmed | The text starts mid-sentence, then contains the start of note 3, and ends mid-sentence. The neighbouring blocks b019 and b021 are flagged `ok`, and b019 ends and b021 begins mid-sentence. Physical page 22 and printed page 16 are correct. |
| Row 13 minor: footnote superscript 4 flattened to a trailing digit | confirmed | In the HTML the 4 is a `<sup>` element. In the passage it is a bare "4" separated by spaces before the full stop. The leading "5" is the publisher's own paragraph number (the locator says item 8, so the two differ). Date and stage are right. |
| Row 15 minor: the locator's "3" comes from a superscript inside the source heading | confirmed | The heading in the source contains a `<sup>3</sup>`. The passage's leading "4." is the publisher's paragraph number. |
| Row 14 ok | confirmed | Intro sentence only, no list items inside it, date 21 September 2026 on the page. Note that the passage text starts with the publisher's own paragraph number 7, which coincides with the extractor's item index 7. This is harmless but not entirely "not publisher numbering". |
| Row 16 ok | confirmed | Whole `<p>` element, list marker (c) intact, date 11 December 2025 matches. |
| Rows 1, 2 ok (not in my sample), and the overall tally 8 ok / 3 minor / 5 major | different number | I did not examine the text of rows 1 and 2 beyond block/hash/page-label identity (which matched). Rows 4, 5, 7, 8 are covered by the seed-11 sample below. Row 8 should carry a **minor** (see N1), so the tally on the same scale is 7 ok, 4 minor, 5 major. |

Random sample of 6 `ok` rows (seed 11, `random.Random(11).sample` over the 8 ok rows = rows 16, 14, 7, 5, 8, 4):

| Row | Result | Details |
|---|---|---|
| 16 | confirmed ok | No missing or extra words. Neighbouring list items are separate passages. |
| 14 | confirmed ok | As above. |
| 7 | confirmed ok | The definition paragraph is complete. The preceding lettered item is a separate block. |
| 5 | confirmed ok | The text matches the block. It is long, and I read the whole text rather than a truncated preview. |
| 4 | confirmed ok | Complete. The section heading ("Coverage") is correct. |
| 8 | **not confirmed** | The text itself is faithful, but the passage's `section_heading` field is the page marker **A27**, not a heading. The page is printed A28, so the "heading" is the previous page's footer. The pre-review's remark that the following section heading is not merged is true of the text, but the metadata field is wrong. |

### 1c. New findings (not in the pre-review)

| # | Finding | Evidence |
|---|---|---|
| N1 | `section_heading` is a bare page marker (`A` plus digits) for 141 passages (125 `ok`, 16 `table_unreliable`) across 14 sources, 39 of them in the four sampled reports. Owner row 8 is one. The heading in a citation would then read as a page marker. | Counted from JSONL. The raw page for row 8 prints A28, while the heading says A27. |
| N2 | Row 14 and row 13: the extractor's item index and the publisher's paragraph number differ in places (row 13: item 8 versus paragraph 5; row 14: item 9 versus paragraph 8 for the last note). If a citation prints "item N", it will not match the publisher's numbering. | Compared the passage-text prefix against the locator. |
| N3 | `mom-2023-q1-final:p004:b006:a8ccfe71` is flagged `ok` and contains a shifted-glyph garbled token (see 1a). | Read the passage text. |

## 2. Statistical pre-review

| Claim | Result | Details |
|---|---|---|
| The nine CSV SHA-256 values match the listed ones | confirmed | I recomputed all nine hashes and they equal the ones in the table. |
| `observations.parquet` SHA-256 `ebe256b9…20e4`, 43,662 rows | confirmed | Same hash and same row count. |
| 1,180 in-scope rows across the eight datasets: 20, 10, 10, 260, 10, 30, 420, 420 | confirmed | Parquet rows with `in_answer_scope` for the eight sources total 1,180, with these per-source counts. |
| 47 dash cells, all null, all in `retrenched_by_industry`; zero source nulls elsewhere | confirmed | 47 `-` raw values, 47 null values, and zero in the other seven datasets. |
| Full comparison, `resident_unemployment_rate` (20 rows): 0 missing / extra / mismatched / duplicates | confirmed | I read the CSV directly, mapped month to quarter myself, included both adjustment columns, and compared on locator, period, value and dimension. |
| Full comparison, `employment_change_by_sector` (260 rows) incl. hierarchy | confirmed | I pivoted the wide table myself (26 series rows by 10 quarters) and rebuilt indentation depth (four spaces per level). The parquet `sector_level` matches in all 260 rows, and values, periods and series labels match. |
| Full comparison, `retrenched_by_industry` (420 rows, 47 nulls) | confirmed | 0 missing, 0 extra, 0 mismatched, 0 duplicate locators. |
| All 14 sampled observations match their CSV cells and normalization | confirmed | I read each locator row from the CSV: values 3.5, 2.7, 1.57, 1.72, 3670, 3030, -200, 6100, 75700, 2.1, 1.2, 1, dash, 3.1 all match. Periods, units, populations, adjustments and dimensions match the parquet. The unselected adjusted values in the same rows (2.9, 2.9, 3.4) are as stated. Sector indentation depths 12 and 8 correspond to levels 3 and 2. Row 14 is `in_answer_scope=false` and row 13 carries the declared null reason. |
| Findings 12 ok / 2 minor / 0 major | confirmed | The two minors are the sector rows with `unverified_basis`. Row 7 and row 8 are correctly levels 3 and 2. |
| Random sample of 6 `ok` rows (seed 11 over the 12 ok rows = 10, 11, 14, 12, 4, 2) | confirmed | Values, periods and dimensions agree. I also checked the dataset descriptions in the snapshot `.metadata.json` for these rows' datasets; see S1 below. No numerical defect found. |
| "Most raw CSVs do not independently establish units, population or seasonal adjustment; only the resident CSV does" | different | True of the CSV files alone. But each snapshot has a sibling `*.metadata.json` from the publisher (hashed in the same snapshot) that does say more. See S1. |

### 2a. New statistical observations

| # | Observation | Evidence |
|---|---|---|
| S1 | The pre-review treated unit/adjustment metadata as unverifiable from the snapshots, and told the owner to confirm the vacancy ratio's adjustment. The snapshot metadata file already states that the vacancy ratio is seasonally adjusted (so `seasonally_adjusted` is supported), gives the unit as ratio, and gives percent for the recruitment datasets. The resignation and recruitment descriptions define the average monthly rate and point to the Labour Market Survey (establishment-based). The resident description states that residents are citizens and PRs. | Read `data/snapshots/*/*/*.metadata.json` for the datasets listed. |
| S2 | The metadata files for retrenchment and job-vacancy counts say nothing about seasonal adjustment. The normalizer labels retrenchment `not_applicable` but job vacancy `unspecified`, though the evidence is identical. The inconsistency is cosmetic for the 1,180 rows but would matter if a caveat is generated from the label. | Compared both metadata descriptions with `adjustment` in the parquet. |
| S3 | The sector dataset's description (in its metadata file) defines employment change as a level difference, but gives no population basis. `unverified_basis` is therefore still correct. The data sheet already says the 2026-Q2 total (14,700) differs from the headline figure in the report. This pre-review did not exercise that comparison and neither did I. | Metadata and spec file. |

## 3. Is the sheet procedure sound?

Mostly yes for arithmetic and extraction fidelity, with these gaps (generator is `src/labourlens/data/review.py`; the sheet text says `data/review.py`, which does not exist):

1. **Passage sampling cannot hit the known defect classes.** Narrative rows are drawn only from `ok` passages longer than 200 characters, table rows only from `table_unreliable` longer than 100. The control-character `ok` leaks are all shorter than 60 characters, and the page-marker contamination and bad `section_heading` cases are mostly outside that sampling window. The sheet gives no coverage of these.
2. **16 and 14 rows are a smoke test, not a measurement.** They show no systematic mismatch in the sampled blocks. They cannot bound a defect rate. The sheet does not say so.
3. **The sheet links to the publisher landing page, not the PDF page, and does not tell the owner that the raw PDF is at `data/raw/<source_id>/<snapshot_id>/`.** Checking against the landing page's current file also confirms the live version, not the stored snapshot.
4. **The passage sheet has no column for metadata** (section heading, page label, release stage, date). The checks that found the real problems here are all metadata ones.
5. **The statistical sheet asks the owner to compare with the data.gov.sg view page.** For the 4,700-row industry tables, finding a single cell on that page is slow. The CSV row number is the faster check, since the raw CSV is in `data/snapshots/`.
6. **The statistical sheet's row 13 (dash) cannot be resolved by comparison.** The sheet only shows that the dash was preserved as null. It does not and cannot settle what a dash means.
7. Rights are handled correctly: no MOM text is committed; the owner reads from the gitignored `private/review/passage-text.md`.

## 4. Owner checklist (about 30 minutes, 12 items)

1. Passage row 11 (3 min): open `mom-2026-q2-final` PDF p.22 and see that the stored block starts and ends mid-note. Decide whether note-boundary splits need a merge step or only a documented limitation.
2. Passage row 10 (2 min): open PDF p.48, confirm the appended A20 marker is page furniture. Decide on a footer-strip rule.
3. Passage row 8 (2 min): note that the heading field reads A27 while the page is A28. Decide whether `section_heading` must be reset when it matches the page-marker pattern (141 passages).
4. Table rows 3, 6, 9, 12 (5 min): confirm one table in the PDF to see that the cell values match but headers are missing; confirm that no answer will quote raw table passages as numbers.
5. Feedback-form garbling (2 min): open PDF p.59 of the Q2-2026 report and confirm the page is readable on screen; decide whether the 4 unflagged control-character blocks per report (and `mom-2023-q1-final:p004:b006`) should be excluded.
6. HTML rows 13 and 15 (3 min): look at the footnote 4 and heading 3 superscripts and decide whether citations should show them differently.
7. Remaining passage rows 1, 2, 4, 5, 7, 14, 16 (6 min total): quick read against the page. Rows 4, 5, 7, 14, 16 showed no defects in any AI check; rows 1 and 2 were only checked for block identity by me. These are the part that must be human.
8. Statistical rows 1, 2, 13, 14 (3 min): open the CSV rows listed and compare. Choose these because they cover both unemployment columns, the null cell and the out-of-scope row.
9. Statistical row 3 (1 min): read the vacancy ratio description on the publisher page and see that the seasonal statement is present. This closes the open question in the statistical pre-review (S1).
10. Statistical rows 7 and 8 (2 min): open the sector dataset page and read the footnote; confirm there is no population statement, so `unverified_basis` stays.
11. Decide on dash handling (1 min): keep null with a stated reason, as now. Do not change it to zero.
12. Fill in the "Reviewer results" table, name yourself, and only then mark anything human-reviewed. Neither the pre-reviews nor this file may be used as that sign-off.

## 5. Limits of this verification

- I did not verify publisher pages online, did not compare any PDF against the live site, and did not independently check units or population of the datasets beyond the snapshot metadata files.
- The 98 and 126 counts are heuristic string counts, as in the pre-review. I confirmed them but did not visually inspect each candidate.
- I did not re-run the other four full dataset comparisons, only three plus all 14 samples.
- I did not check the seasonal-adjustment, unit or population fields for the full sample beyond the row-level and metadata-file checks described above.
