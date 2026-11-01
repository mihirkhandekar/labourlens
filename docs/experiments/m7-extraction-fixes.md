# M7 — extraction corrections and passage-ID migration

**DECISION / scope:** Owner-requested fixes on `extraction-fixes`, in the isolated `zuhl-extract` worktree. No frozen main-checkout data or gold labels were edited. No network, paid/model/API, embedding, retrieval, agent or evaluation command was run. This is an extraction migration, not a new retrieval-quality or answer-quality result.

## Implementation

- Parser version is `extract-0.2`. PDF headings use the page-local prose font distribution, relative size/weight, preceding gap/position, length and sentence punctuation. Appendix labels cannot be headings. Body-sized short narrative remains evidence rather than being silently discarded.
- C0 (except tab/CR/LF), DEL and C1 controls are detected before the length guard. Control-bearing short blocks are retained as `garbled`; normalization no longer strips whitespace-class controls before detection. No shifted-font wording is guessed. A single trailing U+0001 may be stripped only if the remaining text has at least four words and passes the legibility heuristic; the transformation is explicit. No real-corpus block qualified for that repair in this build.
- Footer labels, including a final appendix-label line merged into notes, fill `printed_page_label`; removed footer lines are recorded in `transformations`. `raw_text_sha256`, physical page/block coordinates and source snapshot retain access to the immutable original.
- Adjacent small-font note fragments are explicitly marked `context_required` with a quality note and `source_block_indices` containing their original and adjacent block links. Original per-block bboxes are retained, not falsely described as merged bbox unions. The reported p.22 block links 19, 20 and 21. This is the allowed mark-fragments alternative, not semantic reconstruction of notes.
- HTML extraction stays within the article/page-content region instead of widening to the form/body to satisfy a paragraph count. Superscripts are omitted from semantic headings, while body footnote evidence and revision statements remain. Copyright/reproduction instructions move to local extraction-statistics `rights_notices` metadata with the immutable raw document as provenance. Repeated article passages are retained.
- Every passage has a normalized-text `dup_group` hash. Context assembly collapses normalized identical text **only within the same source snapshot**; citation targets remain in the store. Different sources/releases/revisions are deliberately not collapsed into apparent agreement. Duplicate counts below are corpus counts, not context counts.

## Measured corpus comparison

Baseline: 46 passage JSONL files copied before the first build into gitignored `private/extraction-before/`. Raw sources were not changed. Counts are over all 46 documents, not only the supported answer window.

| Measure | Before | After |
|---|---:|---:|
| Passages | 13484 | 15915 |
| Control-bearing `ok` passages | 57 | 0 |
| Normalized duplicate groups | 640 | 727 |
| Excess duplicate copies | 3307 | 3677 |
| Q3 2025 physical p.30 passages | 0 | 7 |
| Passages with appendix labels as headings | 141 | 0 |
| Quality `ok` | 6360 | 8614 |
| Quality `table_unreliable` | 7055 | 7055 |
| Quality `garbled` | 69 | 246 |
| Quality `multicolumn_uncertain` | 0 | 0 |
| Quality `empty` | 0 | 0 |

**MEASURED RESULT:** All 57 originally control-bearing `ok` passage locators now resolve to `garbled` blocks (44 retain their IDs; 13 IDs change because previously stripped controls are retained). All 246 current control-bearing passages are `garbled`. The increased garbled count includes newly retained short corrupt blocks; it is not newly introduced corruption. Footer removal is recorded on 98 passages. No trailing-U+0001 repairs were applied to this corpus.
**MEASURED RESULT:** The real Q3 2025 physical p.30 contains seven 11-point narrative source blocks; all seven are present verbatim in the rebuilt local passages, totaling 584 characters. Its printed label is 24. The remaining extractable characters belong to the running title, figure caption and page label; this is not a claim to recover the embedded chart image.
**Interpretation:** Passage and duplicate counts rise because conservative heading recognition and retention of short corrupt provenance blocks preserve more source material. A larger passage count is not a measured retrieval improvement. Charts and flattened tables retain their prior limitations. Human source review is still required.

## Verification actually exercised

All commands ran in the isolated worktree with `--offline`; there was no fetch.

| Command | Observed result |
|---|---|
| `uv run --offline labourlens build` | Final build: 43,662 observations, zero quarantined; 255 checks, zero failures. |
| `uv run --offline pytest -q -m 'not corpus'` | 371 passed, 52 deselected; five PyMuPDF/SWIG deprecation warnings. |
| `uv run --offline pytest -q tests/data -m corpus` | 9 passed, 62 deselected; five PyMuPDF/SWIG deprecation warnings. Includes real-page fidelity, appendix metadata, note links, whole-corpus clean-`ok` check, raw hashes, provenance, packaging, observation idempotence and reconciliation checks. |
| `uv run --offline labourlens scan-sources` | 15,915 passages and 147 statistical text values scanned; zero hits. No new allow-list entry. |

Expected failure fixtures verify short C0/C1 corruption becomes `garbled`, while internal-control and too-short text is not guessed/repaired. Synthetic fixtures cover heading layout, footer separation, HTML boundaries/rights/superscripts, duplicates, revision preservation and adjacent-note fragment links. No PDF fixture or publisher paragraph is committed.

## Passage-ID accounting

IDs contain the source, physical/section locator and text-hash prefix, so a new section ordinal can change an HTML ID without changing text. “Removed IDs” and “added IDs” below are set differences, **not deletion/creation of the same number of semantic claims**. “Unchanged-text remaps” are removed IDs whose exact SHA-256 text still exists within that source; ambiguous matches are not silently resolved. “Changed text at same locator” counts removed IDs with a new record at the same physical block (PDF) or section/item locator (HTML); HTML ordinal shifts mean this is descriptive, not a safe automatic mapping.

**MEASURED RESULT:** 12,976 IDs survive; 508 old IDs are absent and 2,939 new IDs appear. 327 absent old IDs have unchanged-text candidates; 18 have multiple candidates. All rows below include documents with zero changes.

| Source | Before | After | Surviving IDs | Removed IDs | Added IDs | Unchanged-text remaps | Changed text at same locator |
|---|---:|---:|---:|---:|---:|---:|---:|
| `mom-2023-q1-final` | 766 | 822 | 755 | 11 | 67 | 0 | 10 |
| `mom-2023-q2-final` | 767 | 827 | 750 | 17 | 77 | 8 | 12 |
| `mom-2023-q3-final` | 745 | 798 | 736 | 9 | 62 | 0 | 7 |
| `mom-2023-q4-final` | 927 | 1074 | 903 | 24 | 171 | 10 | 21 |
| `mom-2024-q1-advance` | 21 | 21 | 21 | 0 | 0 | 0 | 0 |
| `mom-2024-q1-final` | 720 | 842 | 709 | 11 | 133 | 0 | 11 |
| `mom-2024-q1-final-release` | 31 | 35 | 0 | 31 | 35 | 23 | 4 |
| `mom-2024-q2-advance` | 24 | 24 | 24 | 0 | 0 | 0 | 0 |
| `mom-2024-q2-final` | 887 | 1009 | 875 | 12 | 134 | 1 | 12 |
| `mom-2024-q2-final-release` | 37 | 37 | 37 | 0 | 0 | 0 | 0 |
| `mom-2024-q3-advance` | 22 | 22 | 0 | 22 | 22 | 21 | 10 |
| `mom-2024-q3-final` | 845 | 985 | 825 | 20 | 160 | 8 | 15 |
| `mom-2024-q3-final-release` | 26 | 26 | 0 | 26 | 26 | 23 | 0 |
| `mom-2024-q4-advance` | 29 | 29 | 0 | 29 | 29 | 28 | 14 |
| `mom-2024-q4-final` | 990 | 1120 | 981 | 9 | 139 | 0 | 9 |
| `mom-2024-q4-final-release` | 32 | 29 | 0 | 32 | 29 | 29 | 13 |
| `mom-2025-q1-advance` | 24 | 24 | 24 | 0 | 0 | 0 | 0 |
| `mom-2025-q1-final` | 800 | 958 | 789 | 11 | 169 | 0 | 11 |
| `mom-2025-q1-final-release` | 23 | 19 | 0 | 23 | 19 | 19 | 11 |
| `mom-2025-q2-advance` | 26 | 22 | 0 | 26 | 22 | 22 | 11 |
| `mom-2025-q2-final` | 867 | 1069 | 861 | 6 | 208 | 0 | 6 |
| `mom-2025-q2-final-release` | 25 | 22 | 0 | 25 | 22 | 22 | 11 |
| `mom-2025-q3-advance` | 25 | 21 | 0 | 25 | 21 | 21 | 12 |
| `mom-2025-q3-final` | 889 | 1111 | 884 | 5 | 227 | 1 | 4 |
| `mom-2025-q3-final-release` | 18 | 18 | 18 | 0 | 0 | 0 | 0 |
| `mom-2025-q4-advance` | 23 | 23 | 23 | 0 | 0 | 0 | 0 |
| `mom-2025-q4-final` | 1063 | 1283 | 1052 | 11 | 231 | 1 | 10 |
| `mom-2025-q4-final-release` | 20 | 17 | 0 | 20 | 17 | 17 | 9 |
| `mom-2026-q1-advance` | 19 | 22 | 0 | 19 | 22 | 16 | 1 |
| `mom-2026-q1-final` | 868 | 1068 | 861 | 7 | 207 | 1 | 6 |
| `mom-2026-q1-final-release` | 8 | 16 | 0 | 8 | 16 | 4 | 4 |
| `mom-2026-q2-advance` | 18 | 19 | 0 | 18 | 19 | 14 | 1 |
| `mom-2026-q2-final` | 906 | 1080 | 897 | 9 | 183 | 1 | 8 |
| `mom-2026-q2-final-release` | 12 | 16 | 0 | 12 | 16 | 11 | 3 |
| `mom-jv2025` | 121 | 440 | 121 | 0 | 319 | 0 | 0 |
| `mom-jv2025-release` | 38 | 35 | 34 | 4 | 1 | 1 | 1 |
| `mom-lf2024-copyright` | 11 | 11 | 11 | 0 | 0 | 0 | 0 |
| `mom-lf2024-coverage-methodology` | 115 | 115 | 115 | 0 | 0 | 0 | 0 |
| `mom-lf2024-survey-findings` | 161 | 210 | 161 | 0 | 49 | 0 | 0 |
| `mom-lf2024-survey-highlights` | 4 | 4 | 4 | 0 | 0 | 0 | 0 |
| `mom-lf2025-copyright` | 4 | 4 | 4 | 0 | 0 | 0 | 0 |
| `mom-lf2025-coverage-methodology` | 115 | 115 | 115 | 0 | 0 | 0 | 0 |
| `mom-lf2025-survey-findings` | 198 | 250 | 198 | 0 | 52 | 0 | 0 |
| `mom-lf2025-survey-highlights` | 1 | 1 | 1 | 0 | 0 | 0 | 0 |
| `mom-wage-practices2024` | 187 | 196 | 187 | 0 | 9 | 0 | 0 |
| `mom-wage-practices2024-release` | 26 | 26 | 0 | 26 | 26 | 25 | 9 |

## Gold evidence impact (no gold edits)

Both `evidence_text` and `context_only_evidence_text` were scanned in `experiments/gold/draft_cases.jsonl`: 188 unique referenced passage IDs; 61 no longer exist; 66 surviving IDs have changed substantive metadata (section, printed label, quality or fragment requirements). New parser-version/provenance fields alone are not counted as substantive changes. Unchanged IDs guarantee unchanged text hashes, not unchanged suitability or section attribution. Every affected reference and case is listed below.

**PROPOSAL:** Review and approve remappings before adopting this corpus, re-indexing or rerunning evaluation. Do not patch frozen experiment artifacts or imply old retrieval/evaluation numbers apply to these passages. The gold file is intentionally unchanged here. Exact-text remaps can be mechanical after ambiguity review; changed-text/split candidates need evidence review.

### Missing gold IDs and replacement proposals

| Old ID | Case / evidence field | Proposed new ID(s) | Basis |
|---|---|---|---|
| `mom-2024-q1-final-release:s01:i003:b463ca65` | `DEV-202` / `context_only_evidence_text`<br>`DEV-501` / `evidence_text` | `mom-2024-q1-final-release:s02:i003:b463ca65` | unchanged exact text |
| `mom-2024-q1-final-release:s01:i007:dd6f2d09` | `DEV-201` / `evidence_text` | `mom-2024-q1-final-release:s03:i003:dd6f2d09` | unchanged exact text |
| `mom-2024-q1-final-release:s01:i011:0bc09e03` | `DEV-326` / `evidence_text` | `mom-2024-q1-final-release:s04:i001:0bc09e03` | unchanged exact text |
| `mom-2024-q1-final-release:s01:i013:567c4460` | `DEV-301` / `evidence_text` | `mom-2024-q1-final-release:s05:i001:567c4460` | unchanged exact text |
| `mom-2024-q1-final-release:s01:i015:66871b58` | `DEV-307` / `evidence_text` | `mom-2024-q1-final-release:s05:i003:5f81a2f1`<br>`mom-2024-q1-final-release:s05:i004:01b56c0a` | article paragraph/heading split; review complete replacement set |
| `mom-2024-q3-advance:s05:i001:6f5c6a06` | `DEV-212` / `evidence_text` | `mom-2024-q3-advance:s06:i001:6f5c6a06` | unchanged exact text |
| `mom-2024-q3-advance:s06:i006:4a27f455` | `DEV-210` / `evidence_text` | `mom-2024-q3-advance:s07:i006:4a27f455` | unchanged exact text |
| `mom-2024-q3-final-release:s01:i003:e7354cad` | `DEV-209` / `evidence_text`<br>`DEV-314` / `evidence_text` | `mom-2024-q3-final-release:s02:i003:e7354cad` | unchanged exact text |
| `mom-2024-q3-final-release:s01:i010:a3b96c55` | `DEV-211` / `evidence_text`<br>`DEV-514` / `evidence_text` | `mom-2024-q3-final-release:s04:i006:a3b96c55` | unchanged exact text |
| `mom-2024-q3-final-release:s01:i012:adea6048` | `DEV-503` / `evidence_text` | `mom-2024-q3-final-release:s05:i001:adea6048` | unchanged exact text |
| `mom-2024-q3-final-release:s01:i016:5de77f22` | `DEV-330` / `evidence_text` | `mom-2024-q3-final-release:s05:i005:5de77f22` | unchanged exact text |
| `mom-2024-q3-final-release:s01:i017:307edb1c` | `DEV-317` / `evidence_text` | `mom-2024-q3-final-release:s05:i006:307edb1c` | unchanged exact text |
| `mom-2024-q3-final:p037:b027:49f8f6dd` | `HO-003` / `evidence_text` | `mom-2024-q3-final:p037:b027:1db7abe7` | same physical block; footer/text transformation, review required |
| `mom-2024-q4-advance:s04:i001:3884d30d` | `DEV-216` / `evidence_text` | `mom-2024-q4-advance:s05:i001:3884d30d` | unchanged exact text |
| `mom-2024-q4-advance:s04:i002:ad98cd85` | `DEV-214` / `evidence_text` | `mom-2024-q4-advance:s05:i002:ad98cd85` | unchanged exact text |
| `mom-2024-q4-final-release:s01:i008:7990024f` | `DEV-213` / `evidence_text` | `mom-2024-q4-final-release:s02:i008:7990024f` | unchanged exact text |
| `mom-2024-q4-final-release:s02:i001:8dffa418` | `DEV-327` / `evidence_text`<br>`DEV-515` / `evidence_text` | `mom-2024-q4-final-release:s03:i001:8dffa418` | unchanged exact text |
| `mom-2024-q4-final-release:s02:i004:7ac8298c` | `DEV-303` / `evidence_text`<br>`DEV-318` / `evidence_text`<br>`DEV-504` / `evidence_text` | `mom-2024-q4-final-release:s03:i004:7ac8298c` | unchanged exact text |
| `mom-2024-q4-final-release:s02:i006:84708b24` | `DEV-215` / `evidence_text` | `mom-2024-q4-final-release:s03:i006:84708b24` | unchanged exact text |
| `mom-2024-q4-final-release:s03:i001:796888ef` | `DEV-330` / `evidence_text`<br>`DEV-332` / `evidence_text` | `mom-2024-q4-final-release:s04:i001:796888ef` | unchanged exact text |
| `mom-2025-q1-final-release:s01:i001:b0363360` | `DEV-331` / `evidence_text` | `mom-2025-q1-final-release:s02:i001:b0363360` | unchanged exact text |
| `mom-2025-q1-final-release:s01:i004:aa31236a` | `DEV-219` / `evidence_text` | `mom-2025-q1-final-release:s02:i004:aa31236a` | unchanged exact text |
| `mom-2025-q1-final-release:s01:i005:e7a4c903` | `DEV-217` / `evidence_text`<br>`DEV-315` / `evidence_text` | `mom-2025-q1-final-release:s02:i005:e7a4c903` | unchanged exact text |
| `mom-2025-q1-final-release:s01:i006:9cf7838a` | `DEV-304` / `evidence_text`<br>`DEV-505` / `evidence_text` | `mom-2025-q1-final-release:s02:i006:9cf7838a` | unchanged exact text |
| `mom-2025-q1-final-release:s02:i002:de8ee350` | `DEV-217` / `evidence_text` | `mom-2025-q1-final-release:s03:i002:de8ee350` | unchanged exact text |
| `mom-2025-q2-advance:s03:i003:6ab22584` | `DEV-220` / `evidence_text` | `mom-2025-q2-advance:s04:i003:6ab22584` | unchanged exact text |
| `mom-2025-q2-advance:s06:i001:cb4f8369` | `DEV-222` / `evidence_text` | `mom-2025-q2-advance:s07:i001:cb4f8369` | unchanged exact text |
| `mom-2025-q2-final-release:s01:i004:1b27cae6` | `DEV-223` / `evidence_text` | `mom-2025-q2-final-release:s02:i004:1b27cae6` | unchanged exact text |
| `mom-2025-q2-final-release:s01:i005:86179eaa` | `DEV-221` / `evidence_text`<br>`DEV-305` / `evidence_text`<br>`DEV-309` / `evidence_text`<br>`DEV-506` / `evidence_text` | `mom-2025-q2-final-release:s02:i005:86179eaa` | unchanged exact text |
| `mom-2025-q2-final:p043:b027:868e815f` | `HO-003` / `evidence_text` | `mom-2025-q2-final:p043:b027:da7ea854` | same physical block; footer/text transformation, review required |
| `mom-2025-q3-advance:s02:i002:6c4338fb` | `HO-017` / `evidence_text` | `mom-2025-q3-advance:s03:i002:6c4338fb` | unchanged exact text |
| `mom-2025-q3-advance:s02:i003:8c8a9b26` | `DEV-224` / `evidence_text`<br>`HO-012` / `evidence_text` | `mom-2025-q3-advance:s03:i003:8c8a9b26` | unchanged exact text |
| `mom-2025-q3-advance:s02:i004:bfea3fb7` | `HO-012` / `evidence_text` | `mom-2025-q3-advance:s03:i004:bfea3fb7` | unchanged exact text |
| `mom-2025-q3-advance:s04:i001:224a41e2` | `DEV-029` / `evidence_text` | `mom-2025-q3-advance:s05:i001:224a41e2` | unchanged exact text |
| `mom-2025-q3-advance:s05:i001:fb30808d` | `DEV-025` / `evidence_text` | `mom-2025-q3-advance:s06:i001:fb30808d` | unchanged exact text |
| `mom-2025-q3-final:p045:b028:49f8f6dd` | `HO-003` / `evidence_text` | `mom-2025-q3-final:p045:b028:1db7abe7` | same physical block; footer/text transformation, review required |
| `mom-2025-q4-final-release:s01:i002:257c8baa` | `DEV-012` / `evidence_text`<br>`DEV-334` / `evidence_text`<br>`HO-028` / `evidence_text` | `mom-2025-q4-final-release:s02:i002:257c8baa` | unchanged exact text |
| `mom-2025-q4-final-release:s01:i004:6b5d0787` | `DEV-010` / `evidence_text`<br>`DEV-328` / `evidence_text`<br>`DEV-329` / `evidence_text`<br>`HO-004` / `evidence_text` | `mom-2025-q4-final-release:s02:i004:6b5d0787` | unchanged exact text |
| `mom-2025-q4-final-release:s01:i005:9425eacc` | `DEV-030` / `evidence_text`<br>`DEV-321` / `evidence_text`<br>`DEV-525` / `evidence_text`<br>`HO-013` / `evidence_text` | `mom-2025-q4-final-release:s02:i005:9425eacc` | unchanged exact text |
| `mom-2025-q4-final-release:s04:i002:b6860fc7` | `DEV-334` / `evidence_text` | `mom-2025-q4-final-release:s05:i002:b6860fc7` | unchanged exact text |
| `mom-2026-q1-advance:s01:i001:9d4ca111` | `DEV-034` / `context_only_evidence_text` | `mom-2026-q1-advance:s02:i001:9d4ca111` | unchanged exact text |
| `mom-2026-q1-advance:s01:i003:3cd3fd75` | `HO-018` / `evidence_text`<br>`HO-024` / `evidence_text` | `mom-2026-q1-advance:s04:i001:3cd3fd75` | unchanged exact text |
| `mom-2026-q1-advance:s01:i006:8af92b1e` | `DEV-324` / `evidence_text` | `mom-2026-q1-advance:s05:i001:8af92b1e` | unchanged exact text |
| `mom-2026-q1-advance:s01:i008:937f6d9f` | `DEV-322` / `evidence_text` | `mom-2026-q1-advance:s05:i003:937f6d9f` | unchanged exact text |
| `mom-2026-q1-advance:s01:i009:76a4418c` | `DEV-231` / `evidence_text` | `mom-2026-q1-advance:s06:i001:76a4418c` | unchanged exact text |
| `mom-2026-q1-final-release:s01:i001:059b7175` | `DEV-023` / `evidence_text`<br>`DEV-034` / `context_only_evidence_text`<br>`DEV-312` / `evidence_text`<br>`DEV-335` / `evidence_text`<br>`HO-018` / `evidence_text`<br>`HO-024` / `evidence_text`<br>`HO-029` / `evidence_text` | `mom-2026-q1-final-release:s02:i001:f5dd961b` | article paragraph/heading split; review complete replacement set |
| `mom-2026-q1-final-release:s01:i002:f7f19d3b` | `DEV-026` / `evidence_text`<br>`DEV-306` / `evidence_text`<br>`DEV-322` / `evidence_text`<br>`DEV-324` / `evidence_text`<br>`HO-021` / `evidence_text`<br>`HO-029` / `evidence_text` | `mom-2026-q1-final-release:s02:i002:4e215cac`<br>`mom-2026-q1-final-release:s02:i003:0febd041`<br>`mom-2026-q1-final-release:s02:i004:093e8a1d`<br>`mom-2026-q1-final-release:s03:i001:61eb87e9`<br>`mom-2026-q1-final-release:s04:i001:f04e8d77` | article paragraph/heading split; review complete replacement set |
| `mom-2026-q1-final-release:s02:i002:2dbb0760` | `DEV-335` / `evidence_text` | `mom-2026-q1-final-release:s05:i003:2dbb0760` | unchanged exact text |
| `mom-2026-q1-final:p040:b029:49f8f6dd` | `HO-003` / `evidence_text` | `mom-2026-q1-final:p040:b029:1db7abe7` | same physical block; footer/text transformation, review required |
| `mom-2026-q2-advance:s01:i001:a424084c` | `DEV-011` / `evidence_text`<br>`HO-020` / `evidence_text` | `mom-2026-q2-advance:s02:i001:a424084c` | unchanged exact text |
| `mom-2026-q2-advance:s01:i004:d1aca6dd` | `DEV-234` / `evidence_text` | `mom-2026-q2-advance:s04:i002:d1aca6dd` | unchanged exact text |
| `mom-2026-q2-advance:s01:i006:389a7c6f` | `DEV-323` / `evidence_text` | `mom-2026-q2-advance:s05:i001:389a7c6f` | unchanged exact text |
| `mom-2026-q2-advance:s01:i008:86484167` | `HO-019` / `evidence_text` | `mom-2026-q2-advance:s06:i001:86484167` | unchanged exact text |
| `mom-2026-q2-advance:s01:i009:ddaf1f87` | `DEV-233` / `evidence_text` | `mom-2026-q2-advance:s07:i001:ddaf1f87` | unchanged exact text |
| `mom-2026-q2-final-release:s01:i001:98b26ad8` | `DEV-011` / `evidence_text`<br>`DEV-313` / `evidence_text`<br>`HO-016` / `evidence_text`<br>`HO-020` / `evidence_text` | `mom-2026-q2-final-release:s02:i001:98b26ad8` | unchanged exact text |
| `mom-2026-q2-final-release:s01:i002:cf323120` | `DEV-008` / `evidence_text`<br>`DEV-013` / `evidence_text`<br>`DEV-323` / `evidence_text`<br>`HO-021` / `evidence_text`<br>`HO-022` / `evidence_text` | `mom-2026-q2-final-release:s02:i002:cf323120` | unchanged exact text |
| `mom-2026-q2-final-release:s01:i003:1d7fc2bc` | `DEV-004` / `evidence_text`<br>`DEV-008` / `evidence_text`<br>`DEV-009` / `evidence_text`<br>`DEV-014` / `evidence_text`<br>`DEV-017` / `evidence_text`<br>`DEV-026` / `evidence_text`<br>`DEV-310` / `evidence_text`<br>`DEV-319` / `evidence_text`<br>`DEV-320` / `evidence_text`<br>`DEV-431` / `evidence_text`<br>`HO-015` / `evidence_text`<br>`HO-019` / `evidence_text`<br>`HO-023` / `evidence_text` | `mom-2026-q2-final-release:s02:i003:1d7fc2bc` | unchanged exact text |
| `mom-2026-q2-final-release:s01:i004:d20bfa82` | `DEV-001` / `evidence_text`<br>`DEV-006` / `evidence_text`<br>`DEV-316` / `evidence_text`<br>`HO-014` / `evidence_text`<br>`HO-027` / `evidence_text` | `mom-2026-q2-final-release:s02:i004:d20bfa82` | unchanged exact text |
| `mom-2026-q2-final:p040:b028:868e815f` | `HO-003` / `evidence_text` | `mom-2026-q2-final:p040:b028:da7ea854` | same physical block; footer/text transformation, review required |
| `mom-wage-practices2024-release:s04:i001:13fff465` | `DEV-609` / `evidence_text` | `mom-wage-practices2024-release:s05:i001:13fff465` | unchanged exact text |
| `mom-wage-practices2024-release:s06:i007:88cc27e8` | `DEV-002` / `evidence_text` | `mom-wage-practices2024-release:s07:i007:88cc27e8` | unchanged exact text |

### Surviving gold IDs with changed metadata

| Passage ID | Changed fields | Cases / evidence fields |
|---|---|---|
| `mom-2023-q1-final:p012:b016:efc7b4fd` | `section_heading` | `HO-002` / `evidence_text` |
| `mom-2023-q1-final:p015:b012:db7697c3` | `section_heading` | `DEV-601` / `context_only_evidence_text` |
| `mom-2023-q1-final:p047:b013:88cc27e8` | `printed_page_label` | `DEV-002` / `evidence_text` |
| `mom-2023-q2-final:p008:b001:49687607` | `section_heading` | `DEV-602` / `context_only_evidence_text`<br>`DEV-622` / `context_only_evidence_text` |
| `mom-2023-q2-final:p012:b005:efc7b4fd` | `section_heading` | `HO-002` / `evidence_text` |
| `mom-2023-q2-final:p048:b014:88cc27e8` | `printed_page_label` | `DEV-002` / `evidence_text` |
| `mom-2023-q3-final:p007:b006:c0331bb1` | `section_heading` | `DEV-603` / `context_only_evidence_text` |
| `mom-2023-q3-final:p012:b007:efc7b4fd` | `section_heading` | `HO-002` / `evidence_text` |
| `mom-2023-q3-final:p048:b014:88cc27e8` | `printed_page_label` | `DEV-002` / `evidence_text` |
| `mom-2023-q4-final:p007:b026:4079df04` | `section_heading`, `quality_note`, `context_required` | `DEV-604` / `context_only_evidence_text` |
| `mom-2023-q4-final:p012:b005:efc7b4fd` | `section_heading` | `HO-002` / `evidence_text` |
| `mom-2023-q4-final:p061:b014:88cc27e8` | `printed_page_label` | `DEV-002` / `evidence_text` |
| `mom-2024-q1-final:p006:b021:9de9b4fb` | `section_heading` | `DEV-204` / `evidence_text` |
| `mom-2024-q1-final:p007:b011:12ff959a` | `section_heading` | `DEV-501` / `evidence_text` |
| `mom-2024-q1-final:p012:b018:efc7b4fd` | `section_heading` | `HO-002` / `evidence_text` |
| `mom-2024-q1-final:p048:b014:88cc27e8` | `printed_page_label` | `DEV-002` / `evidence_text` |
| `mom-2024-q2-final:p013:b016:efc7b4fd` | `section_heading` | `HO-002` / `evidence_text` |
| `mom-2024-q2-final:p049:b014:88cc27e8` | `printed_page_label` | `DEV-002` / `evidence_text` |
| `mom-2024-q3-final:p013:b016:efc7b4fd` | `section_heading` | `HO-002` / `evidence_text` |
| `mom-2024-q3-final:p049:b014:88cc27e8` | `printed_page_label` | `DEV-002` / `evidence_text` |
| `mom-2024-q4-final:p011:b015:efc7b4fd` | `section_heading` | `HO-002` / `evidence_text` |
| `mom-2024-q4-final:p051:b014:88cc27e8` | `printed_page_label` | `DEV-002` / `evidence_text` |
| `mom-2025-q1-final:p007:b019:6f6f0736` | `section_heading` | `DEV-505` / `evidence_text` |
| `mom-2025-q1-final:p011:b013:efc7b4fd` | `section_heading` | `HO-002` / `evidence_text` |
| `mom-2025-q1-final:p049:b014:88cc27e8` | `printed_page_label` | `DEV-002` / `evidence_text` |
| `mom-2025-q2-final:p007:b017:8be1139a` | `section_heading` | `DEV-506` / `evidence_text` |
| `mom-2025-q2-final:p017:b014:efc7b4fd` | `section_heading` | `HO-002` / `evidence_text` |
| `mom-2025-q2-final:p055:b014:88cc27e8` | `printed_page_label` | `DEV-002` / `evidence_text` |
| `mom-2025-q3-final:p006:b031:c7518141` | `section_heading` | `DEV-021` / `evidence_text` |
| `mom-2025-q3-final:p007:b023:ca8f6f8b` | `section_heading` | `DEV-029` / `evidence_text`<br>`DEV-524` / `evidence_text` |
| `mom-2025-q3-final:p014:b015:efc7b4fd` | `section_heading` | `HO-002` / `evidence_text` |
| `mom-2025-q3-final:p059:b004:88cc27e8` | `printed_page_label` | `DEV-002` / `evidence_text` |
| `mom-2025-q4-final:p007:b014:637704e4` | `section_heading` | `DEV-525` / `evidence_text` |
| `mom-2025-q4-final:p007:b016:539f5b7e` | `section_heading` | `DEV-010` / `evidence_text`<br>`HO-004` / `evidence_text` |
| `mom-2025-q4-final:p013:b015:efc7b4fd` | `section_heading` | `HO-002` / `evidence_text` |
| `mom-2025-q4-final:p014:b012:f9481c30` | `section_heading` | `DEV-228` / `evidence_text` |
| `mom-2025-q4-final:p018:b017:63ca921a` | `section_heading`, `quality_note`, `context_required` | `DEV-022` / `evidence_text` |
| `mom-2025-q4-final:p022:b027:06fba174` | `section_heading`, `quality_note`, `context_required` | `DEV-229` / `evidence_text` |
| `mom-2025-q4-final:p059:b004:88cc27e8` | `printed_page_label` | `DEV-002` / `evidence_text` |
| `mom-2026-q1-final:p007:b024:7163d242` | `section_heading`, `quality_note`, `context_required` | `HO-024` / `evidence_text` |
| `mom-2026-q1-final:p022:b020:7059aed2` | `section_heading`, `quality_note`, `context_required` | `DEV-230` / `evidence_text` |
| `mom-2026-q1-final:p053:b011:0dbdeda2` | `printed_page_label` | `DEV-230` / `evidence_text` |
| `mom-2026-q1-final:p053:b015:6f82d55d` | `printed_page_label` | `DEV-232` / `evidence_text` |
| `mom-2026-q1-final:p054:b004:88cc27e8` | `printed_page_label` | `DEV-002` / `evidence_text` |
| `mom-2026-q1-final:p054:b006:84ddf2d9` | `printed_page_label` | `DEV-230` / `evidence_text` |
| `mom-2026-q2-final:p006:b072:c7c4db54` | `section_heading` | `DEV-004` / `evidence_text` |
| `mom-2026-q2-final:p007:b018:413e4014` | `section_heading` | `HO-019` / `evidence_text` |
| `mom-2026-q2-final:p007:b029:d1fa8b62` | `section_heading` | `HO-020` / `evidence_text` |
| `mom-2026-q2-final:p014:b013:efc7b4fd` | `section_heading` | `HO-002` / `evidence_text` |
| `mom-2026-q2-final:p054:b004:88cc27e8` | `printed_page_label` | `DEV-002` / `evidence_text` |
| `mom-2026-q2-final:p055:b005:611009ca` | `printed_page_label` | `DEV-235` / `evidence_text` |
| `mom-jv2025:p020:b017:5f8de557` | `section_heading`, `quality_note`, `context_required` | `DEV-607` / `evidence_text` |
| `mom-lf2024-coverage-methodology:p003:b016:b0e602ee` | `section_heading` | `HO-002` / `evidence_text` |
| `mom-lf2025-survey-findings:p018:b000:7a395929` | `section_heading` | `DEV-032` / `evidence_text`<br>`DEV-618` / `evidence_text` |
| `mom-lf2025-survey-findings:p019:b002:8926e4a5` | `section_heading` | `DEV-616` / `evidence_text` |
| `mom-lf2025-survey-findings:p021:b000:61079f8a` | `section_heading` | `DEV-020` / `evidence_text`<br>`DEV-615` / `evidence_text` |
| `mom-lf2025-survey-findings:p033:b000:379f0248` | `section_heading` | `DEV-610` / `evidence_text`<br>`DEV-620` / `evidence_text`<br>`DEV-631` / `evidence_text` |
| `mom-lf2025-survey-findings:p034:b000:ccf78c77` | `section_heading` | `DEV-033` / `evidence_text`<br>`DEV-611` / `evidence_text` |
| `mom-lf2025-survey-findings:p035:b000:aa2ba4f1` | `section_heading` | `DEV-632` / `evidence_text` |
| `mom-lf2025-survey-findings:p035:b004:2c045bbf` | `section_heading`, `quality_note`, `context_required` | `DEV-612` / `evidence_text`<br>`DEV-632` / `evidence_text` |
| `mom-lf2025-survey-findings:p061:b000:8558b6a8` | `section_heading` | `DEV-623` / `evidence_text` |
| `mom-lf2025-survey-findings:p061:b004:c8c38bb8` | `section_heading` | `DEV-028` / `evidence_text` |
| `mom-lf2025-survey-findings:p078:b000:13df0bd0` | `section_heading` | `DEV-024` / `evidence_text` |
| `mom-wage-practices2024:p008:b016:051d0c3b` | `section_heading` | `DEV-621` / `evidence_text`<br>`DEV-626` / `context_only_evidence_text` |
| `mom-wage-practices2024:p009:b017:ea4b7ee5` | `section_heading` | `DEV-627` / `context_only_evidence_text` |
| `mom-wage-practices2024:p011:b004:c72670f0` | `section_heading` | `DEV-609` / `evidence_text` |

## Proposed unchanged-text ID remapping table (all sources)

Each candidate has the same source ID and full text SHA-256 as the old passage. Multiple candidates are explicitly listed; they are alternatives, not a forced many-to-one reassignment. All genuine citation targets remain individually addressable. This table includes non-gold IDs.

| Old ID | Proposed new ID(s), exact text unchanged |
|---|---|
| `mom-2023-q2-final:p045:b000:e1819cc2` | `mom-2023-q2-final:p005:b000:e1819cc2`<br>`mom-2023-q2-final:p008:b000:e1819cc2`<br>`mom-2023-q2-final:p009:b000:e1819cc2`<br>`mom-2023-q2-final:p010:b000:e1819cc2`<br>`mom-2023-q2-final:p011:b000:e1819cc2`<br>`mom-2023-q2-final:p012:b000:e1819cc2`<br>`mom-2023-q2-final:p013:b000:e1819cc2`<br>`mom-2023-q2-final:p014:b000:e1819cc2`<br>`mom-2023-q2-final:p015:b000:e1819cc2`<br>`mom-2023-q2-final:p016:b000:e1819cc2`<br>`mom-2023-q2-final:p017:b000:e1819cc2`<br>`mom-2023-q2-final:p018:b000:e1819cc2`<br>`mom-2023-q2-final:p019:b000:e1819cc2`<br>`mom-2023-q2-final:p020:b000:e1819cc2`<br>`mom-2023-q2-final:p021:b000:e1819cc2`<br>`mom-2023-q2-final:p022:b013:e1819cc2`<br>`mom-2023-q2-final:p023:b000:e1819cc2`<br>`mom-2023-q2-final:p024:b000:e1819cc2` |
| `mom-2023-q2-final:p046:b000:e1819cc2` | `mom-2023-q2-final:p005:b000:e1819cc2`<br>`mom-2023-q2-final:p008:b000:e1819cc2`<br>`mom-2023-q2-final:p009:b000:e1819cc2`<br>`mom-2023-q2-final:p010:b000:e1819cc2`<br>`mom-2023-q2-final:p011:b000:e1819cc2`<br>`mom-2023-q2-final:p012:b000:e1819cc2`<br>`mom-2023-q2-final:p013:b000:e1819cc2`<br>`mom-2023-q2-final:p014:b000:e1819cc2`<br>`mom-2023-q2-final:p015:b000:e1819cc2`<br>`mom-2023-q2-final:p016:b000:e1819cc2`<br>`mom-2023-q2-final:p017:b000:e1819cc2`<br>`mom-2023-q2-final:p018:b000:e1819cc2`<br>`mom-2023-q2-final:p019:b000:e1819cc2`<br>`mom-2023-q2-final:p020:b000:e1819cc2`<br>`mom-2023-q2-final:p021:b000:e1819cc2`<br>`mom-2023-q2-final:p022:b013:e1819cc2`<br>`mom-2023-q2-final:p023:b000:e1819cc2`<br>`mom-2023-q2-final:p024:b000:e1819cc2` |
| `mom-2023-q2-final:p047:b000:e1819cc2` | `mom-2023-q2-final:p005:b000:e1819cc2`<br>`mom-2023-q2-final:p008:b000:e1819cc2`<br>`mom-2023-q2-final:p009:b000:e1819cc2`<br>`mom-2023-q2-final:p010:b000:e1819cc2`<br>`mom-2023-q2-final:p011:b000:e1819cc2`<br>`mom-2023-q2-final:p012:b000:e1819cc2`<br>`mom-2023-q2-final:p013:b000:e1819cc2`<br>`mom-2023-q2-final:p014:b000:e1819cc2`<br>`mom-2023-q2-final:p015:b000:e1819cc2`<br>`mom-2023-q2-final:p016:b000:e1819cc2`<br>`mom-2023-q2-final:p017:b000:e1819cc2`<br>`mom-2023-q2-final:p018:b000:e1819cc2`<br>`mom-2023-q2-final:p019:b000:e1819cc2`<br>`mom-2023-q2-final:p020:b000:e1819cc2`<br>`mom-2023-q2-final:p021:b000:e1819cc2`<br>`mom-2023-q2-final:p022:b013:e1819cc2`<br>`mom-2023-q2-final:p023:b000:e1819cc2`<br>`mom-2023-q2-final:p024:b000:e1819cc2` |
| `mom-2023-q2-final:p048:b000:e1819cc2` | `mom-2023-q2-final:p005:b000:e1819cc2`<br>`mom-2023-q2-final:p008:b000:e1819cc2`<br>`mom-2023-q2-final:p009:b000:e1819cc2`<br>`mom-2023-q2-final:p010:b000:e1819cc2`<br>`mom-2023-q2-final:p011:b000:e1819cc2`<br>`mom-2023-q2-final:p012:b000:e1819cc2`<br>`mom-2023-q2-final:p013:b000:e1819cc2`<br>`mom-2023-q2-final:p014:b000:e1819cc2`<br>`mom-2023-q2-final:p015:b000:e1819cc2`<br>`mom-2023-q2-final:p016:b000:e1819cc2`<br>`mom-2023-q2-final:p017:b000:e1819cc2`<br>`mom-2023-q2-final:p018:b000:e1819cc2`<br>`mom-2023-q2-final:p019:b000:e1819cc2`<br>`mom-2023-q2-final:p020:b000:e1819cc2`<br>`mom-2023-q2-final:p021:b000:e1819cc2`<br>`mom-2023-q2-final:p022:b013:e1819cc2`<br>`mom-2023-q2-final:p023:b000:e1819cc2`<br>`mom-2023-q2-final:p024:b000:e1819cc2` |
| `mom-2023-q2-final:p049:b000:e1819cc2` | `mom-2023-q2-final:p005:b000:e1819cc2`<br>`mom-2023-q2-final:p008:b000:e1819cc2`<br>`mom-2023-q2-final:p009:b000:e1819cc2`<br>`mom-2023-q2-final:p010:b000:e1819cc2`<br>`mom-2023-q2-final:p011:b000:e1819cc2`<br>`mom-2023-q2-final:p012:b000:e1819cc2`<br>`mom-2023-q2-final:p013:b000:e1819cc2`<br>`mom-2023-q2-final:p014:b000:e1819cc2`<br>`mom-2023-q2-final:p015:b000:e1819cc2`<br>`mom-2023-q2-final:p016:b000:e1819cc2`<br>`mom-2023-q2-final:p017:b000:e1819cc2`<br>`mom-2023-q2-final:p018:b000:e1819cc2`<br>`mom-2023-q2-final:p019:b000:e1819cc2`<br>`mom-2023-q2-final:p020:b000:e1819cc2`<br>`mom-2023-q2-final:p021:b000:e1819cc2`<br>`mom-2023-q2-final:p022:b013:e1819cc2`<br>`mom-2023-q2-final:p023:b000:e1819cc2`<br>`mom-2023-q2-final:p024:b000:e1819cc2` |
| `mom-2023-q2-final:p050:b000:e1819cc2` | `mom-2023-q2-final:p005:b000:e1819cc2`<br>`mom-2023-q2-final:p008:b000:e1819cc2`<br>`mom-2023-q2-final:p009:b000:e1819cc2`<br>`mom-2023-q2-final:p010:b000:e1819cc2`<br>`mom-2023-q2-final:p011:b000:e1819cc2`<br>`mom-2023-q2-final:p012:b000:e1819cc2`<br>`mom-2023-q2-final:p013:b000:e1819cc2`<br>`mom-2023-q2-final:p014:b000:e1819cc2`<br>`mom-2023-q2-final:p015:b000:e1819cc2`<br>`mom-2023-q2-final:p016:b000:e1819cc2`<br>`mom-2023-q2-final:p017:b000:e1819cc2`<br>`mom-2023-q2-final:p018:b000:e1819cc2`<br>`mom-2023-q2-final:p019:b000:e1819cc2`<br>`mom-2023-q2-final:p020:b000:e1819cc2`<br>`mom-2023-q2-final:p021:b000:e1819cc2`<br>`mom-2023-q2-final:p022:b013:e1819cc2`<br>`mom-2023-q2-final:p023:b000:e1819cc2`<br>`mom-2023-q2-final:p024:b000:e1819cc2` |
| `mom-2023-q2-final:p051:b000:e1819cc2` | `mom-2023-q2-final:p005:b000:e1819cc2`<br>`mom-2023-q2-final:p008:b000:e1819cc2`<br>`mom-2023-q2-final:p009:b000:e1819cc2`<br>`mom-2023-q2-final:p010:b000:e1819cc2`<br>`mom-2023-q2-final:p011:b000:e1819cc2`<br>`mom-2023-q2-final:p012:b000:e1819cc2`<br>`mom-2023-q2-final:p013:b000:e1819cc2`<br>`mom-2023-q2-final:p014:b000:e1819cc2`<br>`mom-2023-q2-final:p015:b000:e1819cc2`<br>`mom-2023-q2-final:p016:b000:e1819cc2`<br>`mom-2023-q2-final:p017:b000:e1819cc2`<br>`mom-2023-q2-final:p018:b000:e1819cc2`<br>`mom-2023-q2-final:p019:b000:e1819cc2`<br>`mom-2023-q2-final:p020:b000:e1819cc2`<br>`mom-2023-q2-final:p021:b000:e1819cc2`<br>`mom-2023-q2-final:p022:b013:e1819cc2`<br>`mom-2023-q2-final:p023:b000:e1819cc2`<br>`mom-2023-q2-final:p024:b000:e1819cc2` |
| `mom-2023-q2-final:p052:b000:e1819cc2` | `mom-2023-q2-final:p005:b000:e1819cc2`<br>`mom-2023-q2-final:p008:b000:e1819cc2`<br>`mom-2023-q2-final:p009:b000:e1819cc2`<br>`mom-2023-q2-final:p010:b000:e1819cc2`<br>`mom-2023-q2-final:p011:b000:e1819cc2`<br>`mom-2023-q2-final:p012:b000:e1819cc2`<br>`mom-2023-q2-final:p013:b000:e1819cc2`<br>`mom-2023-q2-final:p014:b000:e1819cc2`<br>`mom-2023-q2-final:p015:b000:e1819cc2`<br>`mom-2023-q2-final:p016:b000:e1819cc2`<br>`mom-2023-q2-final:p017:b000:e1819cc2`<br>`mom-2023-q2-final:p018:b000:e1819cc2`<br>`mom-2023-q2-final:p019:b000:e1819cc2`<br>`mom-2023-q2-final:p020:b000:e1819cc2`<br>`mom-2023-q2-final:p021:b000:e1819cc2`<br>`mom-2023-q2-final:p022:b013:e1819cc2`<br>`mom-2023-q2-final:p023:b000:e1819cc2`<br>`mom-2023-q2-final:p024:b000:e1819cc2` |
| `mom-2023-q4-final:p026:b000:7e568e56` | `mom-2023-q4-final:p004:b003:7e568e56`<br>`mom-2023-q4-final:p005:b000:7e568e56`<br>`mom-2023-q4-final:p008:b000:7e568e56`<br>`mom-2023-q4-final:p009:b000:7e568e56`<br>`mom-2023-q4-final:p010:b000:7e568e56`<br>`mom-2023-q4-final:p011:b000:7e568e56`<br>`mom-2023-q4-final:p012:b000:7e568e56`<br>`mom-2023-q4-final:p013:b000:7e568e56`<br>`mom-2023-q4-final:p014:b000:7e568e56`<br>`mom-2023-q4-final:p015:b000:7e568e56`<br>`mom-2023-q4-final:p016:b000:7e568e56`<br>`mom-2023-q4-final:p017:b000:7e568e56`<br>`mom-2023-q4-final:p018:b000:7e568e56`<br>`mom-2023-q4-final:p019:b000:7e568e56`<br>`mom-2023-q4-final:p020:b000:7e568e56`<br>`mom-2023-q4-final:p021:b000:7e568e56`<br>`mom-2023-q4-final:p022:b000:7e568e56`<br>`mom-2023-q4-final:p023:b000:7e568e56`<br>`mom-2023-q4-final:p024:b000:7e568e56`<br>`mom-2023-q4-final:p025:b000:7e568e56`<br>`mom-2023-q4-final:p027:b000:7e568e56`<br>`mom-2023-q4-final:p028:b000:7e568e56`<br>`mom-2023-q4-final:p030:b000:7e568e56`<br>`mom-2023-q4-final:p031:b000:7e568e56`<br>`mom-2023-q4-final:p032:b009:7e568e56`<br>`mom-2023-q4-final:p033:b000:7e568e56`<br>`mom-2023-q4-final:p034:b000:7e568e56` |
| `mom-2023-q4-final:p029:b000:7e568e56` | `mom-2023-q4-final:p004:b003:7e568e56`<br>`mom-2023-q4-final:p005:b000:7e568e56`<br>`mom-2023-q4-final:p008:b000:7e568e56`<br>`mom-2023-q4-final:p009:b000:7e568e56`<br>`mom-2023-q4-final:p010:b000:7e568e56`<br>`mom-2023-q4-final:p011:b000:7e568e56`<br>`mom-2023-q4-final:p012:b000:7e568e56`<br>`mom-2023-q4-final:p013:b000:7e568e56`<br>`mom-2023-q4-final:p014:b000:7e568e56`<br>`mom-2023-q4-final:p015:b000:7e568e56`<br>`mom-2023-q4-final:p016:b000:7e568e56`<br>`mom-2023-q4-final:p017:b000:7e568e56`<br>`mom-2023-q4-final:p018:b000:7e568e56`<br>`mom-2023-q4-final:p019:b000:7e568e56`<br>`mom-2023-q4-final:p020:b000:7e568e56`<br>`mom-2023-q4-final:p021:b000:7e568e56`<br>`mom-2023-q4-final:p022:b000:7e568e56`<br>`mom-2023-q4-final:p023:b000:7e568e56`<br>`mom-2023-q4-final:p024:b000:7e568e56`<br>`mom-2023-q4-final:p025:b000:7e568e56`<br>`mom-2023-q4-final:p027:b000:7e568e56`<br>`mom-2023-q4-final:p028:b000:7e568e56`<br>`mom-2023-q4-final:p030:b000:7e568e56`<br>`mom-2023-q4-final:p031:b000:7e568e56`<br>`mom-2023-q4-final:p032:b009:7e568e56`<br>`mom-2023-q4-final:p033:b000:7e568e56`<br>`mom-2023-q4-final:p034:b000:7e568e56` |
| `mom-2023-q4-final:p058:b000:7e568e56` | `mom-2023-q4-final:p004:b003:7e568e56`<br>`mom-2023-q4-final:p005:b000:7e568e56`<br>`mom-2023-q4-final:p008:b000:7e568e56`<br>`mom-2023-q4-final:p009:b000:7e568e56`<br>`mom-2023-q4-final:p010:b000:7e568e56`<br>`mom-2023-q4-final:p011:b000:7e568e56`<br>`mom-2023-q4-final:p012:b000:7e568e56`<br>`mom-2023-q4-final:p013:b000:7e568e56`<br>`mom-2023-q4-final:p014:b000:7e568e56`<br>`mom-2023-q4-final:p015:b000:7e568e56`<br>`mom-2023-q4-final:p016:b000:7e568e56`<br>`mom-2023-q4-final:p017:b000:7e568e56`<br>`mom-2023-q4-final:p018:b000:7e568e56`<br>`mom-2023-q4-final:p019:b000:7e568e56`<br>`mom-2023-q4-final:p020:b000:7e568e56`<br>`mom-2023-q4-final:p021:b000:7e568e56`<br>`mom-2023-q4-final:p022:b000:7e568e56`<br>`mom-2023-q4-final:p023:b000:7e568e56`<br>`mom-2023-q4-final:p024:b000:7e568e56`<br>`mom-2023-q4-final:p025:b000:7e568e56`<br>`mom-2023-q4-final:p027:b000:7e568e56`<br>`mom-2023-q4-final:p028:b000:7e568e56`<br>`mom-2023-q4-final:p030:b000:7e568e56`<br>`mom-2023-q4-final:p031:b000:7e568e56`<br>`mom-2023-q4-final:p032:b009:7e568e56`<br>`mom-2023-q4-final:p033:b000:7e568e56`<br>`mom-2023-q4-final:p034:b000:7e568e56` |
| `mom-2023-q4-final:p059:b000:7e568e56` | `mom-2023-q4-final:p004:b003:7e568e56`<br>`mom-2023-q4-final:p005:b000:7e568e56`<br>`mom-2023-q4-final:p008:b000:7e568e56`<br>`mom-2023-q4-final:p009:b000:7e568e56`<br>`mom-2023-q4-final:p010:b000:7e568e56`<br>`mom-2023-q4-final:p011:b000:7e568e56`<br>`mom-2023-q4-final:p012:b000:7e568e56`<br>`mom-2023-q4-final:p013:b000:7e568e56`<br>`mom-2023-q4-final:p014:b000:7e568e56`<br>`mom-2023-q4-final:p015:b000:7e568e56`<br>`mom-2023-q4-final:p016:b000:7e568e56`<br>`mom-2023-q4-final:p017:b000:7e568e56`<br>`mom-2023-q4-final:p018:b000:7e568e56`<br>`mom-2023-q4-final:p019:b000:7e568e56`<br>`mom-2023-q4-final:p020:b000:7e568e56`<br>`mom-2023-q4-final:p021:b000:7e568e56`<br>`mom-2023-q4-final:p022:b000:7e568e56`<br>`mom-2023-q4-final:p023:b000:7e568e56`<br>`mom-2023-q4-final:p024:b000:7e568e56`<br>`mom-2023-q4-final:p025:b000:7e568e56`<br>`mom-2023-q4-final:p027:b000:7e568e56`<br>`mom-2023-q4-final:p028:b000:7e568e56`<br>`mom-2023-q4-final:p030:b000:7e568e56`<br>`mom-2023-q4-final:p031:b000:7e568e56`<br>`mom-2023-q4-final:p032:b009:7e568e56`<br>`mom-2023-q4-final:p033:b000:7e568e56`<br>`mom-2023-q4-final:p034:b000:7e568e56` |
| `mom-2023-q4-final:p060:b000:7e568e56` | `mom-2023-q4-final:p004:b003:7e568e56`<br>`mom-2023-q4-final:p005:b000:7e568e56`<br>`mom-2023-q4-final:p008:b000:7e568e56`<br>`mom-2023-q4-final:p009:b000:7e568e56`<br>`mom-2023-q4-final:p010:b000:7e568e56`<br>`mom-2023-q4-final:p011:b000:7e568e56`<br>`mom-2023-q4-final:p012:b000:7e568e56`<br>`mom-2023-q4-final:p013:b000:7e568e56`<br>`mom-2023-q4-final:p014:b000:7e568e56`<br>`mom-2023-q4-final:p015:b000:7e568e56`<br>`mom-2023-q4-final:p016:b000:7e568e56`<br>`mom-2023-q4-final:p017:b000:7e568e56`<br>`mom-2023-q4-final:p018:b000:7e568e56`<br>`mom-2023-q4-final:p019:b000:7e568e56`<br>`mom-2023-q4-final:p020:b000:7e568e56`<br>`mom-2023-q4-final:p021:b000:7e568e56`<br>`mom-2023-q4-final:p022:b000:7e568e56`<br>`mom-2023-q4-final:p023:b000:7e568e56`<br>`mom-2023-q4-final:p024:b000:7e568e56`<br>`mom-2023-q4-final:p025:b000:7e568e56`<br>`mom-2023-q4-final:p027:b000:7e568e56`<br>`mom-2023-q4-final:p028:b000:7e568e56`<br>`mom-2023-q4-final:p030:b000:7e568e56`<br>`mom-2023-q4-final:p031:b000:7e568e56`<br>`mom-2023-q4-final:p032:b009:7e568e56`<br>`mom-2023-q4-final:p033:b000:7e568e56`<br>`mom-2023-q4-final:p034:b000:7e568e56` |
| `mom-2023-q4-final:p061:b000:7e568e56` | `mom-2023-q4-final:p004:b003:7e568e56`<br>`mom-2023-q4-final:p005:b000:7e568e56`<br>`mom-2023-q4-final:p008:b000:7e568e56`<br>`mom-2023-q4-final:p009:b000:7e568e56`<br>`mom-2023-q4-final:p010:b000:7e568e56`<br>`mom-2023-q4-final:p011:b000:7e568e56`<br>`mom-2023-q4-final:p012:b000:7e568e56`<br>`mom-2023-q4-final:p013:b000:7e568e56`<br>`mom-2023-q4-final:p014:b000:7e568e56`<br>`mom-2023-q4-final:p015:b000:7e568e56`<br>`mom-2023-q4-final:p016:b000:7e568e56`<br>`mom-2023-q4-final:p017:b000:7e568e56`<br>`mom-2023-q4-final:p018:b000:7e568e56`<br>`mom-2023-q4-final:p019:b000:7e568e56`<br>`mom-2023-q4-final:p020:b000:7e568e56`<br>`mom-2023-q4-final:p021:b000:7e568e56`<br>`mom-2023-q4-final:p022:b000:7e568e56`<br>`mom-2023-q4-final:p023:b000:7e568e56`<br>`mom-2023-q4-final:p024:b000:7e568e56`<br>`mom-2023-q4-final:p025:b000:7e568e56`<br>`mom-2023-q4-final:p027:b000:7e568e56`<br>`mom-2023-q4-final:p028:b000:7e568e56`<br>`mom-2023-q4-final:p030:b000:7e568e56`<br>`mom-2023-q4-final:p031:b000:7e568e56`<br>`mom-2023-q4-final:p032:b009:7e568e56`<br>`mom-2023-q4-final:p033:b000:7e568e56`<br>`mom-2023-q4-final:p034:b000:7e568e56` |
| `mom-2023-q4-final:p062:b000:7e568e56` | `mom-2023-q4-final:p004:b003:7e568e56`<br>`mom-2023-q4-final:p005:b000:7e568e56`<br>`mom-2023-q4-final:p008:b000:7e568e56`<br>`mom-2023-q4-final:p009:b000:7e568e56`<br>`mom-2023-q4-final:p010:b000:7e568e56`<br>`mom-2023-q4-final:p011:b000:7e568e56`<br>`mom-2023-q4-final:p012:b000:7e568e56`<br>`mom-2023-q4-final:p013:b000:7e568e56`<br>`mom-2023-q4-final:p014:b000:7e568e56`<br>`mom-2023-q4-final:p015:b000:7e568e56`<br>`mom-2023-q4-final:p016:b000:7e568e56`<br>`mom-2023-q4-final:p017:b000:7e568e56`<br>`mom-2023-q4-final:p018:b000:7e568e56`<br>`mom-2023-q4-final:p019:b000:7e568e56`<br>`mom-2023-q4-final:p020:b000:7e568e56`<br>`mom-2023-q4-final:p021:b000:7e568e56`<br>`mom-2023-q4-final:p022:b000:7e568e56`<br>`mom-2023-q4-final:p023:b000:7e568e56`<br>`mom-2023-q4-final:p024:b000:7e568e56`<br>`mom-2023-q4-final:p025:b000:7e568e56`<br>`mom-2023-q4-final:p027:b000:7e568e56`<br>`mom-2023-q4-final:p028:b000:7e568e56`<br>`mom-2023-q4-final:p030:b000:7e568e56`<br>`mom-2023-q4-final:p031:b000:7e568e56`<br>`mom-2023-q4-final:p032:b009:7e568e56`<br>`mom-2023-q4-final:p033:b000:7e568e56`<br>`mom-2023-q4-final:p034:b000:7e568e56` |
| `mom-2023-q4-final:p063:b000:7e568e56` | `mom-2023-q4-final:p004:b003:7e568e56`<br>`mom-2023-q4-final:p005:b000:7e568e56`<br>`mom-2023-q4-final:p008:b000:7e568e56`<br>`mom-2023-q4-final:p009:b000:7e568e56`<br>`mom-2023-q4-final:p010:b000:7e568e56`<br>`mom-2023-q4-final:p011:b000:7e568e56`<br>`mom-2023-q4-final:p012:b000:7e568e56`<br>`mom-2023-q4-final:p013:b000:7e568e56`<br>`mom-2023-q4-final:p014:b000:7e568e56`<br>`mom-2023-q4-final:p015:b000:7e568e56`<br>`mom-2023-q4-final:p016:b000:7e568e56`<br>`mom-2023-q4-final:p017:b000:7e568e56`<br>`mom-2023-q4-final:p018:b000:7e568e56`<br>`mom-2023-q4-final:p019:b000:7e568e56`<br>`mom-2023-q4-final:p020:b000:7e568e56`<br>`mom-2023-q4-final:p021:b000:7e568e56`<br>`mom-2023-q4-final:p022:b000:7e568e56`<br>`mom-2023-q4-final:p023:b000:7e568e56`<br>`mom-2023-q4-final:p024:b000:7e568e56`<br>`mom-2023-q4-final:p025:b000:7e568e56`<br>`mom-2023-q4-final:p027:b000:7e568e56`<br>`mom-2023-q4-final:p028:b000:7e568e56`<br>`mom-2023-q4-final:p030:b000:7e568e56`<br>`mom-2023-q4-final:p031:b000:7e568e56`<br>`mom-2023-q4-final:p032:b009:7e568e56`<br>`mom-2023-q4-final:p033:b000:7e568e56`<br>`mom-2023-q4-final:p034:b000:7e568e56` |
| `mom-2023-q4-final:p064:b000:7e568e56` | `mom-2023-q4-final:p004:b003:7e568e56`<br>`mom-2023-q4-final:p005:b000:7e568e56`<br>`mom-2023-q4-final:p008:b000:7e568e56`<br>`mom-2023-q4-final:p009:b000:7e568e56`<br>`mom-2023-q4-final:p010:b000:7e568e56`<br>`mom-2023-q4-final:p011:b000:7e568e56`<br>`mom-2023-q4-final:p012:b000:7e568e56`<br>`mom-2023-q4-final:p013:b000:7e568e56`<br>`mom-2023-q4-final:p014:b000:7e568e56`<br>`mom-2023-q4-final:p015:b000:7e568e56`<br>`mom-2023-q4-final:p016:b000:7e568e56`<br>`mom-2023-q4-final:p017:b000:7e568e56`<br>`mom-2023-q4-final:p018:b000:7e568e56`<br>`mom-2023-q4-final:p019:b000:7e568e56`<br>`mom-2023-q4-final:p020:b000:7e568e56`<br>`mom-2023-q4-final:p021:b000:7e568e56`<br>`mom-2023-q4-final:p022:b000:7e568e56`<br>`mom-2023-q4-final:p023:b000:7e568e56`<br>`mom-2023-q4-final:p024:b000:7e568e56`<br>`mom-2023-q4-final:p025:b000:7e568e56`<br>`mom-2023-q4-final:p027:b000:7e568e56`<br>`mom-2023-q4-final:p028:b000:7e568e56`<br>`mom-2023-q4-final:p030:b000:7e568e56`<br>`mom-2023-q4-final:p031:b000:7e568e56`<br>`mom-2023-q4-final:p032:b009:7e568e56`<br>`mom-2023-q4-final:p033:b000:7e568e56`<br>`mom-2023-q4-final:p034:b000:7e568e56` |
| `mom-2023-q4-final:p065:b000:7e568e56` | `mom-2023-q4-final:p004:b003:7e568e56`<br>`mom-2023-q4-final:p005:b000:7e568e56`<br>`mom-2023-q4-final:p008:b000:7e568e56`<br>`mom-2023-q4-final:p009:b000:7e568e56`<br>`mom-2023-q4-final:p010:b000:7e568e56`<br>`mom-2023-q4-final:p011:b000:7e568e56`<br>`mom-2023-q4-final:p012:b000:7e568e56`<br>`mom-2023-q4-final:p013:b000:7e568e56`<br>`mom-2023-q4-final:p014:b000:7e568e56`<br>`mom-2023-q4-final:p015:b000:7e568e56`<br>`mom-2023-q4-final:p016:b000:7e568e56`<br>`mom-2023-q4-final:p017:b000:7e568e56`<br>`mom-2023-q4-final:p018:b000:7e568e56`<br>`mom-2023-q4-final:p019:b000:7e568e56`<br>`mom-2023-q4-final:p020:b000:7e568e56`<br>`mom-2023-q4-final:p021:b000:7e568e56`<br>`mom-2023-q4-final:p022:b000:7e568e56`<br>`mom-2023-q4-final:p023:b000:7e568e56`<br>`mom-2023-q4-final:p024:b000:7e568e56`<br>`mom-2023-q4-final:p025:b000:7e568e56`<br>`mom-2023-q4-final:p027:b000:7e568e56`<br>`mom-2023-q4-final:p028:b000:7e568e56`<br>`mom-2023-q4-final:p030:b000:7e568e56`<br>`mom-2023-q4-final:p031:b000:7e568e56`<br>`mom-2023-q4-final:p032:b009:7e568e56`<br>`mom-2023-q4-final:p033:b000:7e568e56`<br>`mom-2023-q4-final:p034:b000:7e568e56` |
| `mom-2024-q1-final-release:s01:i001:0ed1fc52` | `mom-2024-q1-final-release:s02:i001:0ed1fc52` |
| `mom-2024-q1-final-release:s01:i002:210461e2` | `mom-2024-q1-final-release:s02:i002:210461e2` |
| `mom-2024-q1-final-release:s01:i003:b463ca65` | `mom-2024-q1-final-release:s02:i003:b463ca65` |
| `mom-2024-q1-final-release:s01:i004:2b9332f8` | `mom-2024-q1-final-release:s02:i004:2b9332f8` |
| `mom-2024-q1-final-release:s01:i005:cf2313e2` | `mom-2024-q1-final-release:s03:i001:cf2313e2` |
| `mom-2024-q1-final-release:s01:i006:b940c78e` | `mom-2024-q1-final-release:s03:i002:b940c78e` |
| `mom-2024-q1-final-release:s01:i007:dd6f2d09` | `mom-2024-q1-final-release:s03:i003:dd6f2d09` |
| `mom-2024-q1-final-release:s01:i008:4ffbce39` | `mom-2024-q1-final-release:s03:i004:4ffbce39` |
| `mom-2024-q1-final-release:s01:i011:0bc09e03` | `mom-2024-q1-final-release:s04:i001:0bc09e03` |
| `mom-2024-q1-final-release:s01:i013:567c4460` | `mom-2024-q1-final-release:s05:i001:567c4460` |
| `mom-2024-q1-final-release:s01:i014:aa0c4b63` | `mom-2024-q1-final-release:s05:i002:aa0c4b63` |
| `mom-2024-q1-final-release:s01:i017:751527fa` | `mom-2024-q1-final-release:s06:i001:751527fa` |
| `mom-2024-q1-final-release:s01:i018:3f1ed54d` | `mom-2024-q1-final-release:s07:i001:3f1ed54d` |
| `mom-2024-q1-final-release:s01:i019:8eb5d4a5` | `mom-2024-q1-final-release:s07:i002:8eb5d4a5` |
| `mom-2024-q1-final-release:s01:i020:22b98af3` | `mom-2024-q1-final-release:s07:i003:22b98af3` |
| `mom-2024-q1-final-release:s01:i022:f921d431` | `mom-2024-q1-final-release:s07:i006:f921d431` |
| `mom-2024-q1-final-release:s01:i024:1569a498` | `mom-2024-q1-final-release:s07:i011:1569a498` |
| `mom-2024-q1-final-release:s01:i025:21edf0bf` | `mom-2024-q1-final-release:s07:i012:21edf0bf` |
| `mom-2024-q1-final-release:s01:i026:740662aa` | `mom-2024-q1-final-release:s08:i001:740662aa` |
| `mom-2024-q1-final-release:s02:i002:f537060b` | `mom-2024-q1-final-release:s08:i003:f537060b` |
| `mom-2024-q1-final-release:s02:i003:8e6e4b07` | `mom-2024-q1-final-release:s08:i004:8e6e4b07` |
| `mom-2024-q1-final-release:s02:i004:7b51c5b1` | `mom-2024-q1-final-release:s08:i005:7b51c5b1` |
| `mom-2024-q1-final-release:s02:i005:f40cf003` | `mom-2024-q1-final-release:s08:i006:f40cf003` |
| `mom-2024-q2-final:p015:b007:fab3b094` | `mom-2024-q2-final:p014:b006:fab3b094` |
| `mom-2024-q3-advance:s01:i001:0abb46e7` | `mom-2024-q3-advance:s02:i001:0abb46e7` |
| `mom-2024-q3-advance:s02:i001:adf6d818` | `mom-2024-q3-advance:s03:i001:adf6d818` |
| `mom-2024-q3-advance:s02:i002:70746417` | `mom-2024-q3-advance:s03:i002:70746417` |
| `mom-2024-q3-advance:s02:i003:5c71dccc` | `mom-2024-q3-advance:s03:i003:5c71dccc` |
| `mom-2024-q3-advance:s02:i004:bbeb3403` | `mom-2024-q3-advance:s03:i004:bbeb3403` |
| `mom-2024-q3-advance:s03:i001:8f613839` | `mom-2024-q3-advance:s04:i001:8f613839` |
| `mom-2024-q3-advance:s04:i001:af0ad030` | `mom-2024-q3-advance:s05:i001:af0ad030` |
| `mom-2024-q3-advance:s05:i001:6f5c6a06` | `mom-2024-q3-advance:s06:i001:6f5c6a06` |
| `mom-2024-q3-advance:s05:i002:175c680c` | `mom-2024-q3-advance:s06:i002:175c680c` |
| `mom-2024-q3-advance:s05:i003:be8417e0` | `mom-2024-q3-advance:s06:i003:be8417e0` |
| `mom-2024-q3-advance:s05:i004:9c975a79` | `mom-2024-q3-advance:s06:i004:9c975a79` |
| `mom-2024-q3-advance:s05:i005:ad270b6a` | `mom-2024-q3-advance:s06:i005:ad270b6a` |
| `mom-2024-q3-advance:s05:i006:026e2880` | `mom-2024-q3-advance:s06:i006:026e2880` |
| `mom-2024-q3-advance:s06:i001:4db42761` | `mom-2024-q3-advance:s07:i001:4db42761` |
| `mom-2024-q3-advance:s06:i002:12172e51` | `mom-2024-q3-advance:s07:i002:12172e51` |
| `mom-2024-q3-advance:s06:i003:2d978ea3` | `mom-2024-q3-advance:s07:i003:2d978ea3` |
| `mom-2024-q3-advance:s06:i004:b61db016` | `mom-2024-q3-advance:s07:i004:b61db016` |
| `mom-2024-q3-advance:s06:i005:1e115fec` | `mom-2024-q3-advance:s07:i005:1e115fec` |
| `mom-2024-q3-advance:s06:i006:4a27f455` | `mom-2024-q3-advance:s07:i006:4a27f455` |
| `mom-2024-q3-advance:s06:i007:c2b68cdc` | `mom-2024-q3-advance:s07:i007:c2b68cdc` |
| `mom-2024-q3-advance:s06:i008:ef3253c8` | `mom-2024-q3-advance:s07:i008:ef3253c8` |
| `mom-2024-q3-final-release:s01:i001:84ae72fe` | `mom-2024-q3-final-release:s02:i001:84ae72fe` |
| `mom-2024-q3-final-release:s01:i002:4a97a8f1` | `mom-2024-q3-final-release:s02:i002:4a97a8f1` |
| `mom-2024-q3-final-release:s01:i003:e7354cad` | `mom-2024-q3-final-release:s02:i003:e7354cad` |
| `mom-2024-q3-final-release:s01:i005:1ea23d96` | `mom-2024-q3-final-release:s04:i001:1ea23d96` |
| `mom-2024-q3-final-release:s01:i006:55c8bb6e` | `mom-2024-q3-final-release:s04:i002:55c8bb6e` |
| `mom-2024-q3-final-release:s01:i007:1ba5eedf` | `mom-2024-q3-final-release:s04:i003:1ba5eedf` |
| `mom-2024-q3-final-release:s01:i008:3d8541a4` | `mom-2024-q3-final-release:s04:i004:3d8541a4` |
| `mom-2024-q3-final-release:s01:i009:b479337c` | `mom-2024-q3-final-release:s04:i005:b479337c` |
| `mom-2024-q3-final-release:s01:i010:a3b96c55` | `mom-2024-q3-final-release:s04:i006:a3b96c55` |
| `mom-2024-q3-final-release:s01:i012:adea6048` | `mom-2024-q3-final-release:s05:i001:adea6048` |
| `mom-2024-q3-final-release:s01:i013:fe128a4d` | `mom-2024-q3-final-release:s05:i002:fe128a4d` |
| `mom-2024-q3-final-release:s01:i014:23a212b1` | `mom-2024-q3-final-release:s05:i003:23a212b1` |
| `mom-2024-q3-final-release:s01:i015:0204064e` | `mom-2024-q3-final-release:s05:i004:0204064e` |
| `mom-2024-q3-final-release:s01:i016:5de77f22` | `mom-2024-q3-final-release:s05:i005:5de77f22` |
| `mom-2024-q3-final-release:s01:i017:307edb1c` | `mom-2024-q3-final-release:s05:i006:307edb1c` |
| `mom-2024-q3-final-release:s01:i019:0d260897` | `mom-2024-q3-final-release:s06:i001:0d260897` |
| `mom-2024-q3-final-release:s01:i020:ba9118f5` | `mom-2024-q3-final-release:s06:i002:ba9118f5` |
| `mom-2024-q3-final-release:s01:i021:22450020` | `mom-2024-q3-final-release:s06:i003:22450020` |
| `mom-2024-q3-final-release:s01:i022:fb03537f` | `mom-2024-q3-final-release:s06:i004:fb03537f` |
| `mom-2024-q3-final-release:s01:i023:0d805a90` | `mom-2024-q3-final-release:s06:i007:0d805a90` |
| `mom-2024-q3-final-release:s01:i024:68d5b028` | `mom-2024-q3-final-release:s06:i008:68d5b028` |
| `mom-2024-q3-final-release:s01:i025:3d4d5b36` | `mom-2024-q3-final-release:s06:i009:3d4d5b36` |
| `mom-2024-q3-final-release:s01:i026:83e7d901` | `mom-2024-q3-final-release:s06:i010:83e7d901` |
| `mom-2024-q3-final:p053:b002:8b1bc8ad` | `mom-2024-q3-final:p053:b003:8b1bc8ad` |
| `mom-2024-q3-final:p053:b003:a9c69839` | `mom-2024-q3-final:p053:b005:a9c69839` |
| `mom-2024-q3-final:p053:b004:168424e6` | `mom-2024-q3-final:p053:b006:168424e6` |
| `mom-2024-q3-final:p053:b012:51d0c500` | `mom-2024-q3-final:p053:b014:51d0c500` |
| `mom-2024-q3-final:p053:b013:69a30f7c` | `mom-2024-q3-final:p053:b015:69a30f7c` |
| `mom-2024-q3-final:p053:b015:9f56bba7` | `mom-2024-q3-final:p053:b017:9f56bba7` |
| `mom-2024-q3-final:p053:b016:8fb1b301` | `mom-2024-q3-final:p053:b018:8fb1b301` |
| `mom-2024-q3-final:p053:b018:d9807ace` | `mom-2024-q3-final:p053:b020:d9807ace` |
| `mom-2024-q4-advance:s01:i001:cb718adf` | `mom-2024-q4-advance:s02:i001:cb718adf` |
| `mom-2024-q4-advance:s01:i002:2d0b4914` | `mom-2024-q4-advance:s02:i002:2d0b4914` |
| `mom-2024-q4-advance:s02:i001:f3672d90` | `mom-2024-q4-advance:s03:i001:f3672d90` |
| `mom-2024-q4-advance:s02:i002:58275552` | `mom-2024-q4-advance:s03:i002:58275552` |
| `mom-2024-q4-advance:s02:i003:3a92d162` | `mom-2024-q4-advance:s03:i003:3a92d162` |
| `mom-2024-q4-advance:s02:i004:a1e67819` | `mom-2024-q4-advance:s03:i004:a1e67819` |
| `mom-2024-q4-advance:s02:i005:b5f9ac5a` | `mom-2024-q4-advance:s03:i005:b5f9ac5a` |
| `mom-2024-q4-advance:s02:i006:bb023ba6` | `mom-2024-q4-advance:s03:i006:bb023ba6` |
| `mom-2024-q4-advance:s02:i007:7f9d1279` | `mom-2024-q4-advance:s03:i007:7f9d1279` |
| `mom-2024-q4-advance:s02:i008:97071852` | `mom-2024-q4-advance:s03:i008:97071852` |
| `mom-2024-q4-advance:s03:i001:5fd89c69` | `mom-2024-q4-advance:s04:i001:5fd89c69` |
| `mom-2024-q4-advance:s03:i002:03e9327d` | `mom-2024-q4-advance:s04:i002:03e9327d` |
| `mom-2024-q4-advance:s04:i001:3884d30d` | `mom-2024-q4-advance:s05:i001:3884d30d` |
| `mom-2024-q4-advance:s04:i002:ad98cd85` | `mom-2024-q4-advance:s05:i002:ad98cd85` |
| `mom-2024-q4-advance:s04:i003:54f45d1b` | `mom-2024-q4-advance:s05:i003:54f45d1b` |
| `mom-2024-q4-advance:s04:i004:0296b1b3` | `mom-2024-q4-advance:s05:i004:0296b1b3` |
| `mom-2024-q4-advance:s04:i005:6cd3e3c2` | `mom-2024-q4-advance:s05:i005:6cd3e3c2` |
| `mom-2024-q4-advance:s04:i006:e5f63d66` | `mom-2024-q4-advance:s05:i006:e5f63d66` |
| `mom-2024-q4-advance:s04:i007:21aa86d2` | `mom-2024-q4-advance:s05:i007:21aa86d2` |
| `mom-2024-q4-advance:s04:i008:9cc597a0` | `mom-2024-q4-advance:s05:i008:9cc597a0` |
| `mom-2024-q4-advance:s05:i001:35be08a9` | `mom-2024-q4-advance:s06:i001:35be08a9` |
| `mom-2024-q4-advance:s05:i002:ed73dd46` | `mom-2024-q4-advance:s06:i002:ed73dd46` |
| `mom-2024-q4-advance:s05:i003:29ec8c29` | `mom-2024-q4-advance:s06:i003:29ec8c29` |
| `mom-2024-q4-advance:s05:i004:dde57389` | `mom-2024-q4-advance:s06:i004:dde57389` |
| `mom-2024-q4-advance:s05:i005:b97bc31b` | `mom-2024-q4-advance:s06:i005:b97bc31b` |
| `mom-2024-q4-advance:s05:i006:08027fb5` | `mom-2024-q4-advance:s06:i006:08027fb5` |
| `mom-2024-q4-advance:s05:i007:42a52a45` | `mom-2024-q4-advance:s06:i007:42a52a45` |
| `mom-2024-q4-advance:s05:i008:ef3253c8` | `mom-2024-q4-advance:s06:i008:ef3253c8` |
| `mom-2024-q4-final-release:s01:i001:d48a54cb` | `mom-2024-q4-final-release:s02:i001:d48a54cb` |
| `mom-2024-q4-final-release:s01:i002:c9be34d2` | `mom-2024-q4-final-release:s02:i002:c9be34d2` |
| `mom-2024-q4-final-release:s01:i003:99d103c1` | `mom-2024-q4-final-release:s02:i003:99d103c1` |
| `mom-2024-q4-final-release:s01:i004:a19baa8b` | `mom-2024-q4-final-release:s02:i004:a19baa8b` |
| `mom-2024-q4-final-release:s01:i005:a05661f7` | `mom-2024-q4-final-release:s02:i005:a05661f7` |
| `mom-2024-q4-final-release:s01:i006:79ad7d42` | `mom-2024-q4-final-release:s02:i006:79ad7d42` |
| `mom-2024-q4-final-release:s01:i007:7b1cd77f` | `mom-2024-q4-final-release:s02:i007:7b1cd77f` |
| `mom-2024-q4-final-release:s01:i008:7990024f` | `mom-2024-q4-final-release:s02:i008:7990024f` |
| `mom-2024-q4-final-release:s02:i001:8dffa418` | `mom-2024-q4-final-release:s03:i001:8dffa418` |
| `mom-2024-q4-final-release:s02:i002:8ad1d756` | `mom-2024-q4-final-release:s03:i002:8ad1d756` |
| `mom-2024-q4-final-release:s02:i003:d7087611` | `mom-2024-q4-final-release:s03:i003:d7087611` |
| `mom-2024-q4-final-release:s02:i004:7ac8298c` | `mom-2024-q4-final-release:s03:i004:7ac8298c` |
| `mom-2024-q4-final-release:s02:i005:47677537` | `mom-2024-q4-final-release:s03:i005:47677537` |
| `mom-2024-q4-final-release:s02:i006:84708b24` | `mom-2024-q4-final-release:s03:i006:84708b24` |
| `mom-2024-q4-final-release:s03:i001:796888ef` | `mom-2024-q4-final-release:s04:i001:796888ef` |
| `mom-2024-q4-final-release:s04:i001:9214296d` | `mom-2024-q4-final-release:s05:i001:9214296d` |
| `mom-2024-q4-final-release:s04:i002:03ba8de5` | `mom-2024-q4-final-release:s05:i002:03ba8de5` |
| `mom-2024-q4-final-release:s04:i003:aaf756ca` | `mom-2024-q4-final-release:s05:i003:aaf756ca` |
| `mom-2024-q4-final-release:s04:i004:82d0c144` | `mom-2024-q4-final-release:s05:i004:82d0c144` |
| `mom-2024-q4-final-release:s04:i005:af2fa999` | `mom-2024-q4-final-release:s05:i005:af2fa999` |
| `mom-2024-q4-final-release:s04:i006:caf79e3a` | `mom-2024-q4-final-release:s05:i006:caf79e3a` |
| `mom-2024-q4-final-release:s04:i007:4854ae48` | `mom-2024-q4-final-release:s05:i007:4854ae48` |
| `mom-2024-q4-final-release:s04:i008:66d23318` | `mom-2024-q4-final-release:s05:i008:66d23318` |
| `mom-2024-q4-final-release:s04:i009:248959e2` | `mom-2024-q4-final-release:s05:i009:248959e2` |
| `mom-2024-q4-final-release:s05:i001:40742300` | `mom-2024-q4-final-release:s06:i001:40742300` |
| `mom-2024-q4-final-release:s05:i002:1b0cd288` | `mom-2024-q4-final-release:s06:i002:1b0cd288` |
| `mom-2024-q4-final-release:s05:i003:f1e8daab` | `mom-2024-q4-final-release:s06:i003:f1e8daab` |
| `mom-2024-q4-final-release:s05:i004:385888d0` | `mom-2024-q4-final-release:s06:i004:385888d0` |
| `mom-2024-q4-final-release:s05:i005:23e46b30` | `mom-2024-q4-final-release:s06:i005:23e46b30` |
| `mom-2025-q1-final-release:s01:i001:b0363360` | `mom-2025-q1-final-release:s02:i001:b0363360` |
| `mom-2025-q1-final-release:s01:i002:7172161f` | `mom-2025-q1-final-release:s02:i002:7172161f` |
| `mom-2025-q1-final-release:s01:i003:531b6fcf` | `mom-2025-q1-final-release:s02:i003:531b6fcf` |
| `mom-2025-q1-final-release:s01:i004:aa31236a` | `mom-2025-q1-final-release:s02:i004:aa31236a` |
| `mom-2025-q1-final-release:s01:i005:e7a4c903` | `mom-2025-q1-final-release:s02:i005:e7a4c903` |
| `mom-2025-q1-final-release:s01:i006:9cf7838a` | `mom-2025-q1-final-release:s02:i006:9cf7838a` |
| `mom-2025-q1-final-release:s02:i001:4033abe7` | `mom-2025-q1-final-release:s03:i001:4033abe7` |
| `mom-2025-q1-final-release:s02:i002:de8ee350` | `mom-2025-q1-final-release:s03:i002:de8ee350` |
| `mom-2025-q1-final-release:s02:i003:b0db67bc` | `mom-2025-q1-final-release:s03:i003:b0db67bc` |
| `mom-2025-q1-final-release:s03:i001:3c634d8f` | `mom-2025-q1-final-release:s04:i001:3c634d8f` |
| `mom-2025-q1-final-release:s03:i002:535dec1b` | `mom-2025-q1-final-release:s04:i002:535dec1b` |
| `mom-2025-q1-final-release:s03:i003:45372e18` | `mom-2025-q1-final-release:s04:i003:45372e18` |
| `mom-2025-q1-final-release:s03:i004:7e287385` | `mom-2025-q1-final-release:s04:i004:7e287385` |
| `mom-2025-q1-final-release:s03:i005:9dddef14` | `mom-2025-q1-final-release:s04:i005:9dddef14` |
| `mom-2025-q1-final-release:s04:i001:46ab034b` | `mom-2025-q1-final-release:s05:i001:46ab034b` |
| `mom-2025-q1-final-release:s04:i002:b6860fc7` | `mom-2025-q1-final-release:s05:i002:b6860fc7` |
| `mom-2025-q1-final-release:s04:i003:b968f24a` | `mom-2025-q1-final-release:s05:i003:b968f24a` |
| `mom-2025-q1-final-release:s04:i004:e97f529c` | `mom-2025-q1-final-release:s05:i004:e97f529c` |
| `mom-2025-q1-final-release:s04:i005:23e46b30` | `mom-2025-q1-final-release:s05:i005:23e46b30` |
| `mom-2025-q2-advance:s01:i001:194d014a` | `mom-2025-q2-advance:s02:i001:194d014a` |
| `mom-2025-q2-advance:s03:i001:1ef7e243` | `mom-2025-q2-advance:s04:i001:1ef7e243` |
| `mom-2025-q2-advance:s03:i002:6077110d` | `mom-2025-q2-advance:s04:i002:6077110d` |
| `mom-2025-q2-advance:s03:i003:6ab22584` | `mom-2025-q2-advance:s04:i003:6ab22584` |
| `mom-2025-q2-advance:s04:i001:2a1a9a05` | `mom-2025-q2-advance:s05:i001:2a1a9a05` |
| `mom-2025-q2-advance:s05:i001:1cd70d7f` | `mom-2025-q2-advance:s06:i001:1cd70d7f` |
| `mom-2025-q2-advance:s06:i001:cb4f8369` | `mom-2025-q2-advance:s07:i001:cb4f8369` |
| `mom-2025-q2-advance:s07:i001:2d7385b9` | `mom-2025-q2-advance:s08:i001:2d7385b9` |
| `mom-2025-q2-advance:s07:i002:90fae570` | `mom-2025-q2-advance:s08:i002:90fae570` |
| `mom-2025-q2-advance:s07:i003:be4e153c` | `mom-2025-q2-advance:s08:i003:be4e153c` |
| `mom-2025-q2-advance:s07:i004:4cdde7ff` | `mom-2025-q2-advance:s08:i004:4cdde7ff` |
| `mom-2025-q2-advance:s07:i005:841b4f25` | `mom-2025-q2-advance:s08:i005:841b4f25` |
| `mom-2025-q2-advance:s07:i006:a7701e82` | `mom-2025-q2-advance:s08:i006:a7701e82` |
| `mom-2025-q2-advance:s07:i007:bc7ea9f3` | `mom-2025-q2-advance:s08:i007:bc7ea9f3` |
| `mom-2025-q2-advance:s07:i008:4bf1179a` | `mom-2025-q2-advance:s08:i008:4bf1179a` |
| `mom-2025-q2-advance:s08:i001:bdccca48` | `mom-2025-q2-advance:s09:i001:bdccca48` |
| `mom-2025-q2-advance:s08:i002:39c84a0c` | `mom-2025-q2-advance:s09:i002:39c84a0c` |
| `mom-2025-q2-advance:s08:i003:166ae757` | `mom-2025-q2-advance:s09:i003:166ae757` |
| `mom-2025-q2-advance:s08:i004:0264f6ca` | `mom-2025-q2-advance:s09:i004:0264f6ca` |
| `mom-2025-q2-advance:s08:i005:38799fde` | `mom-2025-q2-advance:s09:i005:38799fde` |
| `mom-2025-q2-advance:s08:i006:d50343c8` | `mom-2025-q2-advance:s09:i006:d50343c8` |
| `mom-2025-q2-advance:s08:i007:23e46b30` | `mom-2025-q2-advance:s09:i007:23e46b30` |
| `mom-2025-q2-final-release:s01:i001:de757a34` | `mom-2025-q2-final-release:s02:i001:de757a34` |
| `mom-2025-q2-final-release:s01:i002:95b872e3` | `mom-2025-q2-final-release:s02:i002:95b872e3` |
| `mom-2025-q2-final-release:s01:i003:42d2954f` | `mom-2025-q2-final-release:s02:i003:42d2954f` |
| `mom-2025-q2-final-release:s01:i004:1b27cae6` | `mom-2025-q2-final-release:s02:i004:1b27cae6` |
| `mom-2025-q2-final-release:s01:i005:86179eaa` | `mom-2025-q2-final-release:s02:i005:86179eaa` |
| `mom-2025-q2-final-release:s02:i001:86ef1ddf` | `mom-2025-q2-final-release:s03:i001:86ef1ddf` |
| `mom-2025-q2-final-release:s02:i002:4fd235bc` | `mom-2025-q2-final-release:s03:i002:4fd235bc` |
| `mom-2025-q2-final-release:s02:i003:76081adb` | `mom-2025-q2-final-release:s03:i003:76081adb` |
| `mom-2025-q2-final-release:s03:i001:849f2b2f` | `mom-2025-q2-final-release:s04:i001:849f2b2f` |
| `mom-2025-q2-final-release:s03:i002:f2d74a39` | `mom-2025-q2-final-release:s04:i002:f2d74a39` |
| `mom-2025-q2-final-release:s03:i003:8d6625b8` | `mom-2025-q2-final-release:s04:i003:8d6625b8` |
| `mom-2025-q2-final-release:s03:i004:be3b472c` | `mom-2025-q2-final-release:s04:i004:be3b472c` |
| `mom-2025-q2-final-release:s03:i005:f355b509` | `mom-2025-q2-final-release:s04:i005:f355b509` |
| `mom-2025-q2-final-release:s03:i006:bb49c42f` | `mom-2025-q2-final-release:s04:i006:bb49c42f` |
| `mom-2025-q2-final-release:s03:i007:cc19e2c7` | `mom-2025-q2-final-release:s04:i007:cc19e2c7` |
| `mom-2025-q2-final-release:s03:i008:3f4ff8da` | `mom-2025-q2-final-release:s04:i008:3f4ff8da` |
| `mom-2025-q2-final-release:s03:i009:fd59d634` | `mom-2025-q2-final-release:s04:i009:fd59d634` |
| `mom-2025-q2-final-release:s04:i001:5fef2cbf` | `mom-2025-q2-final-release:s05:i001:5fef2cbf` |
| `mom-2025-q2-final-release:s04:i002:c365e8e7` | `mom-2025-q2-final-release:s05:i002:c365e8e7` |
| `mom-2025-q2-final-release:s04:i003:2dbb0760` | `mom-2025-q2-final-release:s05:i003:2dbb0760` |
| `mom-2025-q2-final-release:s04:i004:2e6a5f30` | `mom-2025-q2-final-release:s05:i004:2e6a5f30` |
| `mom-2025-q2-final-release:s04:i005:23e46b30` | `mom-2025-q2-final-release:s05:i005:23e46b30` |
| `mom-2025-q3-advance:s01:i001:2810fd24` | `mom-2025-q3-advance:s02:i001:2810fd24` |
| `mom-2025-q3-advance:s02:i001:2068cba6` | `mom-2025-q3-advance:s03:i001:2068cba6` |
| `mom-2025-q3-advance:s02:i002:6c4338fb` | `mom-2025-q3-advance:s03:i002:6c4338fb` |
| `mom-2025-q3-advance:s02:i003:8c8a9b26` | `mom-2025-q3-advance:s03:i003:8c8a9b26` |
| `mom-2025-q3-advance:s02:i004:bfea3fb7` | `mom-2025-q3-advance:s03:i004:bfea3fb7` |
| `mom-2025-q3-advance:s03:i001:ffc8da87` | `mom-2025-q3-advance:s04:i001:ffc8da87` |
| `mom-2025-q3-advance:s04:i001:224a41e2` | `mom-2025-q3-advance:s05:i001:224a41e2` |
| `mom-2025-q3-advance:s05:i001:fb30808d` | `mom-2025-q3-advance:s06:i001:fb30808d` |
| `mom-2025-q3-advance:s05:i002:ea571211` | `mom-2025-q3-advance:s06:i002:ea571211` |
| `mom-2025-q3-advance:s06:i001:1bf150a0` | `mom-2025-q3-advance:s07:i001:1bf150a0` |
| `mom-2025-q3-advance:s06:i002:296b3d98` | `mom-2025-q3-advance:s07:i002:296b3d98` |
| `mom-2025-q3-advance:s06:i003:27e315d8` | `mom-2025-q3-advance:s07:i003:27e315d8` |
| `mom-2025-q3-advance:s06:i004:eff36440` | `mom-2025-q3-advance:s07:i004:eff36440` |
| `mom-2025-q3-advance:s06:i005:026d9edb` | `mom-2025-q3-advance:s07:i005:026d9edb` |
| `mom-2025-q3-advance:s06:i006:2de396c1` | `mom-2025-q3-advance:s07:i006:2de396c1` |
| `mom-2025-q3-advance:s07:i001:bdccca48` | `mom-2025-q3-advance:s08:i001:bdccca48` |
| `mom-2025-q3-advance:s07:i002:39c84a0c` | `mom-2025-q3-advance:s08:i002:39c84a0c` |
| `mom-2025-q3-advance:s07:i003:a46bc2a7` | `mom-2025-q3-advance:s08:i003:a46bc2a7` |
| `mom-2025-q3-advance:s07:i004:0264f6ca` | `mom-2025-q3-advance:s08:i004:0264f6ca` |
| `mom-2025-q3-advance:s07:i005:793464e7` | `mom-2025-q3-advance:s08:i005:793464e7` |
| `mom-2025-q3-advance:s07:i006:23e46b30` | `mom-2025-q3-advance:s08:i006:23e46b30` |
| `mom-2025-q3-final:p046:b023:b01f9a31` | `mom-2025-q3-final:p045:b023:b01f9a31` |
| `mom-2025-q4-final-release:s01:i001:14231889` | `mom-2025-q4-final-release:s02:i001:14231889` |
| `mom-2025-q4-final-release:s01:i002:257c8baa` | `mom-2025-q4-final-release:s02:i002:257c8baa` |
| `mom-2025-q4-final-release:s01:i003:b24762ae` | `mom-2025-q4-final-release:s02:i003:b24762ae` |
| `mom-2025-q4-final-release:s01:i004:6b5d0787` | `mom-2025-q4-final-release:s02:i004:6b5d0787` |
| `mom-2025-q4-final-release:s01:i005:9425eacc` | `mom-2025-q4-final-release:s02:i005:9425eacc` |
| `mom-2025-q4-final-release:s02:i001:1fd60019` | `mom-2025-q4-final-release:s03:i001:1fd60019` |
| `mom-2025-q4-final-release:s02:i002:169be331` | `mom-2025-q4-final-release:s03:i002:169be331` |
| `mom-2025-q4-final-release:s03:i001:d57421a0` | `mom-2025-q4-final-release:s04:i001:d57421a0` |
| `mom-2025-q4-final-release:s03:i002:b13b5e5a` | `mom-2025-q4-final-release:s04:i002:b13b5e5a` |
| `mom-2025-q4-final-release:s03:i003:3b6301e7` | `mom-2025-q4-final-release:s04:i003:3b6301e7` |
| `mom-2025-q4-final-release:s03:i004:475b28ca` | `mom-2025-q4-final-release:s04:i004:475b28ca` |
| `mom-2025-q4-final-release:s03:i005:fa50f31a` | `mom-2025-q4-final-release:s04:i005:fa50f31a` |
| `mom-2025-q4-final-release:s04:i001:810821d0` | `mom-2025-q4-final-release:s05:i001:810821d0` |
| `mom-2025-q4-final-release:s04:i002:b6860fc7` | `mom-2025-q4-final-release:s05:i002:b6860fc7` |
| `mom-2025-q4-final-release:s04:i003:8a9f982a` | `mom-2025-q4-final-release:s05:i003:8a9f982a` |
| `mom-2025-q4-final-release:s04:i004:dbaaf819` | `mom-2025-q4-final-release:s05:i004:dbaaf819` |
| `mom-2025-q4-final-release:s04:i005:23e46b30` | `mom-2025-q4-final-release:s05:i005:23e46b30` |
| `mom-2025-q4-final:p043:b024:b01f9a31` | `mom-2025-q4-final:p044:b024:b01f9a31` |
| `mom-2026-q1-advance:s01:i001:9d4ca111` | `mom-2026-q1-advance:s02:i001:9d4ca111` |
| `mom-2026-q1-advance:s01:i003:3cd3fd75` | `mom-2026-q1-advance:s04:i001:3cd3fd75` |
| `mom-2026-q1-advance:s01:i004:d371c7f2` | `mom-2026-q1-advance:s04:i002:d371c7f2` |
| `mom-2026-q1-advance:s01:i006:8af92b1e` | `mom-2026-q1-advance:s05:i001:8af92b1e` |
| `mom-2026-q1-advance:s01:i007:09f4937c` | `mom-2026-q1-advance:s05:i002:09f4937c` |
| `mom-2026-q1-advance:s01:i008:937f6d9f` | `mom-2026-q1-advance:s05:i003:937f6d9f` |
| `mom-2026-q1-advance:s01:i009:76a4418c` | `mom-2026-q1-advance:s06:i001:76a4418c` |
| `mom-2026-q1-advance:s01:i010:ab80f61c` | `mom-2026-q1-advance:s07:i001:ab80f61c` |
| `mom-2026-q1-advance:s01:i011:c4fcd293` | `mom-2026-q1-advance:s07:i005:c4fcd293` |
| `mom-2026-q1-advance:s01:i012:a4d7fe30` | `mom-2026-q1-advance:s07:i006:a4d7fe30` |
| `mom-2026-q1-advance:s01:i013:71647d6a` | `mom-2026-q1-advance:s08:i001:71647d6a` |
| `mom-2026-q1-advance:s01:i014:4cf6ed14` | `mom-2026-q1-advance:s08:i002:4cf6ed14` |
| `mom-2026-q1-advance:s02:i002:d43d0b3b` | `mom-2026-q1-advance:s08:i004:d43d0b3b` |
| `mom-2026-q1-advance:s02:i003:ec57bcb1` | `mom-2026-q1-advance:s08:i005:ec57bcb1` |
| `mom-2026-q1-advance:s02:i004:8af6dfd4` | `mom-2026-q1-advance:s08:i006:8af6dfd4` |
| `mom-2026-q1-advance:s02:i005:04cfda13` | `mom-2026-q1-advance:s08:i007:04cfda13` |
| `mom-2026-q1-final-release:s01:i003:75b60f85` | `mom-2026-q1-final-release:s04:i005:75b60f85` |
| `mom-2026-q1-final-release:s02:i002:2dbb0760` | `mom-2026-q1-final-release:s05:i003:2dbb0760` |
| `mom-2026-q1-final-release:s02:i003:05566261` | `mom-2026-q1-final-release:s05:i004:05566261` |
| `mom-2026-q1-final-release:s02:i004:f449d527` | `mom-2026-q1-final-release:s05:i005:f449d527` |
| `mom-2026-q1-final:p041:b024:b01f9a31` | `mom-2026-q1-final:p040:b024:b01f9a31` |
| `mom-2026-q2-advance:s01:i001:a424084c` | `mom-2026-q2-advance:s02:i001:a424084c` |
| `mom-2026-q2-advance:s01:i003:d9fc23dd` | `mom-2026-q2-advance:s04:i001:d9fc23dd` |
| `mom-2026-q2-advance:s01:i004:d1aca6dd` | `mom-2026-q2-advance:s04:i002:d1aca6dd` |
| `mom-2026-q2-advance:s01:i006:389a7c6f` | `mom-2026-q2-advance:s05:i001:389a7c6f` |
| `mom-2026-q2-advance:s01:i008:86484167` | `mom-2026-q2-advance:s06:i001:86484167` |
| `mom-2026-q2-advance:s01:i009:ddaf1f87` | `mom-2026-q2-advance:s07:i001:ddaf1f87` |
| `mom-2026-q2-advance:s01:i010:bc79f6f4` | `mom-2026-q2-advance:s08:i001:bc79f6f4` |
| `mom-2026-q2-advance:s01:i011:477ccfdd` | `mom-2026-q2-advance:s08:i005:477ccfdd` |
| `mom-2026-q2-advance:s01:i012:350507f0` | `mom-2026-q2-advance:s08:i006:350507f0` |
| `mom-2026-q2-advance:s01:i013:71647d6a` | `mom-2026-q2-advance:s09:i001:71647d6a` |
| `mom-2026-q2-advance:s01:i014:4cf6ed14` | `mom-2026-q2-advance:s09:i002:4cf6ed14` |
| `mom-2026-q2-advance:s02:i002:4f170877` | `mom-2026-q2-advance:s09:i004:4f170877` |
| `mom-2026-q2-advance:s02:i003:8af6dfd4` | `mom-2026-q2-advance:s09:i005:8af6dfd4` |
| `mom-2026-q2-advance:s02:i004:b3e95f5a` | `mom-2026-q2-advance:s09:i006:b3e95f5a` |
| `mom-2026-q2-final-release:s01:i001:98b26ad8` | `mom-2026-q2-final-release:s02:i001:98b26ad8` |
| `mom-2026-q2-final-release:s01:i002:cf323120` | `mom-2026-q2-final-release:s02:i002:cf323120` |
| `mom-2026-q2-final-release:s01:i003:1d7fc2bc` | `mom-2026-q2-final-release:s02:i003:1d7fc2bc` |
| `mom-2026-q2-final-release:s01:i004:d20bfa82` | `mom-2026-q2-final-release:s02:i004:d20bfa82` |
| `mom-2026-q2-final-release:s01:i005:8b20c705` | `mom-2026-q2-final-release:s03:i001:8b20c705` |
| `mom-2026-q2-final-release:s01:i006:6a3e2ce4` | `mom-2026-q2-final-release:s04:i001:6a3e2ce4` |
| `mom-2026-q2-final-release:s01:i007:f07b514a` | `mom-2026-q2-final-release:s04:i002:f07b514a` |
| `mom-2026-q2-final-release:s01:i008:477ccfdd` | `mom-2026-q2-final-release:s04:i006:477ccfdd` |
| `mom-2026-q2-final-release:s01:i009:4ff37f3f` | `mom-2026-q2-final-release:s05:i001:4ff37f3f` |
| `mom-2026-q2-final-release:s02:i002:2dbb0760` | `mom-2026-q2-final-release:s05:i003:2dbb0760` |
| `mom-2026-q2-final-release:s02:i003:647bb511` | `mom-2026-q2-final-release:s05:i004:647bb511` |
| `mom-2026-q2-final:p041:b023:b01f9a31` | `mom-2026-q2-final:p040:b023:b01f9a31` |
| `mom-jv2025-release:s00:i004:4bad7291` | `mom-jv2025-release:s00:i001:4bad7291` |
| `mom-wage-practices2024-release:s00:i002:ef5b1a26` | `mom-wage-practices2024-release:s01:i001:ef5b1a26` |
| `mom-wage-practices2024-release:s01:i001:f863c61a` | `mom-wage-practices2024-release:s02:i001:f863c61a` |
| `mom-wage-practices2024-release:s01:i002:086e40e5` | `mom-wage-practices2024-release:s02:i002:086e40e5` |
| `mom-wage-practices2024-release:s01:i003:e9d5319e` | `mom-wage-practices2024-release:s02:i003:e9d5319e` |
| `mom-wage-practices2024-release:s01:i004:1c756eae` | `mom-wage-practices2024-release:s02:i004:1c756eae` |
| `mom-wage-practices2024-release:s02:i001:bb611f23` | `mom-wage-practices2024-release:s03:i001:bb611f23` |
| `mom-wage-practices2024-release:s02:i002:5aab18c2` | `mom-wage-practices2024-release:s03:i002:5aab18c2` |
| `mom-wage-practices2024-release:s03:i001:c68a2a82` | `mom-wage-practices2024-release:s04:i001:c68a2a82` |
| `mom-wage-practices2024-release:s03:i002:00d82a92` | `mom-wage-practices2024-release:s04:i002:00d82a92` |
| `mom-wage-practices2024-release:s04:i001:13fff465` | `mom-wage-practices2024-release:s05:i001:13fff465` |
| `mom-wage-practices2024-release:s04:i002:dbf95f59` | `mom-wage-practices2024-release:s05:i002:dbf95f59` |
| `mom-wage-practices2024-release:s04:i003:fcecf092` | `mom-wage-practices2024-release:s05:i003:fcecf092` |
| `mom-wage-practices2024-release:s05:i001:a54fc6e2` | `mom-wage-practices2024-release:s06:i001:a54fc6e2` |
| `mom-wage-practices2024-release:s06:i001:42c52a1d` | `mom-wage-practices2024-release:s07:i001:42c52a1d` |
| `mom-wage-practices2024-release:s06:i002:33af2caa` | `mom-wage-practices2024-release:s07:i002:33af2caa` |
| `mom-wage-practices2024-release:s06:i003:00245df5` | `mom-wage-practices2024-release:s07:i003:00245df5` |
| `mom-wage-practices2024-release:s06:i004:391f10b3` | `mom-wage-practices2024-release:s07:i004:391f10b3` |
| `mom-wage-practices2024-release:s06:i005:125d1e7e` | `mom-wage-practices2024-release:s07:i005:125d1e7e` |
| `mom-wage-practices2024-release:s06:i006:9021dc36` | `mom-wage-practices2024-release:s07:i006:9021dc36` |
| `mom-wage-practices2024-release:s06:i007:88cc27e8` | `mom-wage-practices2024-release:s07:i007:88cc27e8` |
| `mom-wage-practices2024-release:s06:i008:b8388004` | `mom-wage-practices2024-release:s07:i008:b8388004` |
| `mom-wage-practices2024-release:s06:i009:70e1a337` | `mom-wage-practices2024-release:s07:i009:70e1a337` |
| `mom-wage-practices2024-release:s06:i010:a3821d28` | `mom-wage-practices2024-release:s07:i010:a3821d28` |
| `mom-wage-practices2024-release:s06:i011:41cb7c65` | `mom-wage-practices2024-release:s07:i011:41cb7c65` |
| `mom-wage-practices2024-release:s06:i012:9ea08f2d` | `mom-wage-practices2024-release:s07:i012:9ea08f2d` |

## Packaging and limitations

- No `data/` files, PDFs, extracted publisher passages or model outputs are included in the commit. `data/processed/` and `data/export/` tracked contents did not change during this build. All corpus-derived JSONL remains local.
- Build regenerates four tracked local quality artifacts: `artifacts/data-quality/extraction_stats.json`, `quality-report.md`, `reconciliation.json` and `validation.json`. Generated results are preserved in gitignored `private/extraction-after-build/`; tracked artifacts are restored to their original frozen versions rather than publishing source rights-notice text or silently replacing historical evidence. The observed final results are recorded above.
- The baseline and rebuilt local corpus, plus generated quality evidence, remain available in this worktree. The main checkout and its frozen evaluation corpus remain untouched.
- Exact text deduplication does not identify near-duplicates. Cross-source/revision duplication is deliberately preserved; it must not be interpreted as independent corroboration. Heading and note-boundary rules are conservative layout heuristics, not semantic guarantees.
- No new retrieval/answer/agent benchmark was run. Existing frozen results are not transferable without explicit corpus/gold migration and a newly registered run. Owner approval is required before merge or any such run.

## Update, 1 Nov 2026 (parser `extract-0.3`, corpus v3.1, D-052)

The symbolic-text refinement of the garbled flag (statistical symbols no longer count towards the symbol ratio; starred coefficient rows count as tables) is applied. Of 286 `garbled` passages, 246 control-character cases stay `garbled`; the 40 false positives in the MTI feature article become 16 `ok` and 24 `table_unreliable`, plus 4 `ok` to `table_unreliable`. Passage ids outside that article are unchanged. Numbers: `experiments/corpus-snapshots/v3.1-diff.json`. The control-character statements above remain true.
