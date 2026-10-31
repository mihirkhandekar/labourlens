# M7 — Candidate untouched sources for held-out v2 (design A)

**31 October 2026. Research only. Nothing was fetched into the repo, no build/index/fetch was run, `data/` and the live `specs/` are untouched.** Live checks (HTTP status, page counts, copyright notices, advance-versus-final figures) used throwaway files under `/tmp`. Proposed registrations: `specs/sources-heldout-v2.proposed.yaml` (not loaded by the catalog).

## 1. What the corpus already holds (VERIFIED FACT, `data/manifests/manifest.json`)

79 sources: 46 documents and 33 data.gov.sg datasets.

| Group | Source ids | Publication dates |
|---|---|---|
| MOM Labour Market Reports, final | `mom-2023-q1-final` … `mom-2026-q2-final` (14) | 2023-06-15 … 2026-09-21 |
| MOM Labour Market Advance Releases | `mom-2024-q1-advance` … `mom-2026-q2-advance` (10) | 2024-04-30 … 2026-07-31 |
| MOM quarterly press-release pages | `mom-2024-q1-final-release` … `mom-2026-q2-final-release` (10) | 2024-06-20 … 2026-09-21 |
| Labour Force in Singapore 2024 and 2025 | `mom-lf2024-*`, `mom-lf2025-*` (4 PDFs each: highlights, findings, coverage, copyright) | 2025-01-27 (2024); 2025 date null in manifest |
| Job Vacancies 2025 | `mom-jv2025`, `mom-jv2025-release` | 2026-03-20 |
| Report on Wage Practices 2024 | `mom-wage-practices2024`, `-release` | 2025-05-28 |
| MOM/SingStat datasets (33) | resident/overall/citizen unemployment, unemployed counts, job vacancy (count, rate, industry, occupation), recruitment, resignation, retrenchment (total, permanent, term, industry, occupation), re-entry 6m/12m, short work-week/temporary layoff, vacancy-to-unemployed ratio, employment change by sector | lastUpdated 2026-03-23 … 2026-10-12 |

Gaps that matter: no MTI publication of any kind; no wage-practices or lower-wage report for 2025; no job-vacancy report for 2024; no productivity, unit-labour-cost or hours datasets; no labour-force advance release.

## 2. Candidates (all URLs fetched with HTTP 200 and the expected type on 31 Oct 2026)

Independence ratings: **High** = different publisher or period and no figure restated in an existing document; **Medium** = same publisher/series family, partly restated figures; **Low** = same headline figures as an existing document.

| # | Candidate (exact title) | Publisher | Published | Stage | URL (type, size) | Periods | Rights / reuse (short) | Independence | Families supported |
|---|---|---|---|---|---|---|---|---|---|
| A1 | Economic Survey of Singapore Third Quarter 2025 | MTI | 2025-11-21 | final | `https://isomer-user-content.by.gov.sg/1004/f69fdd39-f0fa-44c5-8992-21b7969721f2/FullReport_3Q25.pdf` (PDF, 1,976,303 B, 52 p) | 2025-Q3 | all rights reserved (notice read) | **High** except the labour chapter, whose employment/retrenchment/unemployment figures mirror MOM advance releases already in corpus | factual, numeric, synthesis, revision, ambiguity |
| A2 | Singapore's GDP Grew by 2.9 Per Cent in Third Quarter of 2025 | MTI | 2025-10-14 | advance | `…/580d3146-fff0-49c3-bb1e-99c4043ec5ba/AdvEst_3Q25.pdf` (PDF, 239,071 B, 3 p) | 2025-Q3 | no notice in file; unresolved | High | revision (pair with A1), factual |
| A3 | Economic Survey of Singapore First Quarter 2026 | MTI | 2026-05-25 | final | `…/cbda13af-78fe-408d-91fa-21f50825cdb5/FullReport_1Q26.pdf` (PDF, 1,958,773 B, 48 p) | 2026-Q1 | all rights reserved | High (labour caveat as A1) | as A1 |
| A4 | Singapore's GDP Grew by 4.6 Per Cent in the First Quarter of 2026 | MTI | 2026-04-14 | advance | `…/3f06d523-2358-4aa9-8dda-61b856e28ab7/AdvEst_1Q26.pdf` (PDF, 236,881 B, 3 p) | 2026-Q1 | unresolved | High | revision, factual |
| A5 | Economic Survey of Singapore Second Quarter 2026 | MTI | 2026-08-11 | final | `…/e3064836-fb6a-4992-a2ee-5944212ab150/FullReport_2Q26.pdf` (PDF, 3,080,933 B, 74 p) | 2026-Q2 | all rights reserved | High (labour caveat) | as A1 |
| A6 | Singapore's GDP Grew by 5.7 Per Cent in the Second Quarter of 2026 | MTI | 2026-07-14 | advance | `…/947e4586-629d-4a60-85ed-82b5cac906df/AdvEst_2Q26.pdf` (PDF, 233,852 B, 3 p) | 2026-Q2 | unresolved | High | revision, factual |
| A7 | Economic Survey of Singapore Second Quarter 2025 | MTI | 2025-08-12 | final | `…/8616f189-94c0-4f2a-81ec-a7cb224e9d9e/FullReport_2Q25.pdf` (PDF, 2,137,931 B, 54 p) | 2025-Q2 | all rights reserved | High | as A1 |
| A8 | Singapore's GDP Grew by 4.3 Per Cent in the Second Quarter of 2025 | MTI | 2025-07-14 | advance | `…/0480616c-653c-44e0-aa76-e8f8f08387aa/AdvEst_2Q25.pdf` (PDF, 300,681 B, 3 p) | 2025-Q2 | unresolved | High | revision, factual |
| A9 | Economic Survey of Singapore 2025 (+ advance `AdvEst_4Q25.pdf`, 271,812 B) | MTI | 2026-02-10 (adv. 2026-01-02) | final / advance | `…/16f78938-9d69-4df0-87a2-c6e6b0376da6/FullReport_AES2025.pdf` (PDF, 4,032,115 B, 98 p); advance `…/77e15989-8ca5-436d-8499-b9b0fbe746aa/AdvEst_4Q25.pdf` | 2025-Q4 and full year 2025 | all rights reserved / unresolved | High | as A1; full-year annual figures |
| A10 | Economic Survey of Singapore Q1 2024, Q2 2024, Q3 2024, 2024 annual, Q1 2025 (five full reports, each with an advance release) | MTI | 2024-05-23 … 2025-05-22 | final / advance | page URL pattern `https://www.mti.gov.sg/resources/economic-survey-of-singapore/economic-survey-of-singapore-and-feature-articles/economic-survey-of-singapore-<first|second|third>-quarter-<yyyy>` (PDF links enumerated in the page HTML; all HTTP 200) | 2024-Q1 … 2025-Q1 | all rights reserved / unresolved | High | extra capacity if more pairs are wanted |
| B1 | Report on Wage Practices 2025 | MOM MRSD | 2026-05-28 | annual | `https://stats.mom.gov.sg/iMAS_PdfLibrary/mrsd-report-on-wage-practices-2025.pdf` (PDF, 783,470 B, 32 p); press page `https://www.mom.gov.sg/newsroom/press-releases/2026/0528-report-on-wage-practices-2025` (HTML, 58,831 B) | 2025 | all rights reserved (notice read); HTML rights unresolved | **Medium** (the 2024 edition is in corpus; prior-year comparatives may repeat) | factual, numeric, synthesis, ambiguity |
| B2 | Wage Adjustments and Adoption of NWC Guidelines for Lower-Wage Employees 2025 | MOM MRSD | Oct 2026 (PDF creation 2026-10-23; confirm on newsroom) | annual | `https://stats.mom.gov.sg/iMAS_PdfLibrary/mrsd-Wage-Adjustments-and-Adoption-of-NWC-Guidelines-for-Lower-Wage-Employees-2025.pdf` (PDF, 545,460 B, 18 p) | 2025 (plus 2026 expectations) | all rights reserved (notice read) | **High** (new report, no existing counterpart; shares the wage survey with B1) | factual, numeric, ambiguity (forecast-adjacent expectations) |
| B3 | Job Vacancies 2024 | MOM MRSD | 2025-03-28 (press page); PDF dated March 2025 | annual | `https://stats.mom.gov.sg/iMAS_PdfLibrary/mrsd_JV2024.pdf` (PDF, 1,755,189 B, 29 p); `https://www.mom.gov.sg/newsroom/press-releases/2025/0328-job-vacancies-2024` (HTML, 63,477 B) | 2024 | all rights reserved (notice read) | **Medium**: `mom-jv2025` restates 2024 comparatives (one figure, the PMET share for 2024, confirmed identical) | factual, numeric, revision (2024 as originally published versus as later restated) |
| B4 | Labour Force in Singapore Advance Release 2025 | MOM MRSD | 2025-11-28 | advance | `https://stats.mom.gov.sg/iMAS_PdfLibrary/mrsd-labour-force-in-singapore-advance-release-2025.pdf` (PDF, 5,191,739 B, 76 p); press page `…/2025/1128-labour-force-in-singapore-advance-release-2025` | June 2025 reference | all rights reserved (notice read) | **Low**: spot-checked headline figures (participation, PMET share, income growth) match the final report already in corpus | consistency only; not a true revision pair |
| B5 | Labour Force in Singapore Advance Release 2024 | MOM MRSD | 2024-11-28 | advance | `https://stats.mom.gov.sg/iMAS_PdfLibrary/mrsd-labour-force-in-singapore-advance-release-2024.pdf` (PDF, 5,045,222 B) | June 2024 reference | presumed as B4; not read | Low (same reason as B4) | as B4 |
| B6 | National Wages Council 2025/2026 Guidelines | MOM / NWC | 2025-11-11 | n/a | `https://www.mom.gov.sg/-/media/mom/documents/press-releases/2025/nwc-guidelines-11nov25.pdf` (PDF, 566,015 B) | wage year Dec 2025 – Nov 2026 | not read; unresolved | High | factual, ambiguity (advice/forecast refusals) |
| C1 | Measuring Firm-Level Artificial Intelligence Use and its Effects on Firm Performance and Employment in Singapore (feature article) | MTI | 2026-08-11 | n/a | `…/dfc3009e-5a9c-4d2c-9fdd-49e63d2c4aad/FA_2Q26.pdf` (PDF) | 2026-Q2 publication; analysis years not verified | unresolved (sibling report is all rights reserved) | High | ambiguity / causal overreach, factual |
| C2 | Impact of the 2022 Increases in Retirement and Re-employment Ages on the Employment Outcomes of Senior Workers (feature article) | MTI | 2025-08-12 | n/a | `…/c297ad39-b7a5-49cd-b57e-a9b3ec632b04/FA_2Q25.pdf` (PDF) | analysis years not verified | unresolved | High | causal-inference limits, factual |
| D1 | Unit Labour Cost Index (2015 = 100), Quarterly (`d_f9fc9b5420d96bcab45bc31eeb8ae3c3`) | SingStat | updated 2026-08-11 | dataset | data.gov.sg (CSV, 25,043 B, 26 series, 1980-Q1 … 2026-Q2) | in scope 2024-Q1 … 2026-Q2 | Open Data Licence presumed (see §5) | High (not derived from any ingested table) | numeric, synthesis with A-set productivity/cost text |
| D2 | Value Added Per Worker In Chained (2015) Dollars, By Industry (SSIC 2020), Quarterly (`d_fa4dcbefadf3e93e99c7d88de0f53406`) | SingStat (+MOM) | 2026-08-11 | dataset | CSV 31,803 B, 24 series, 1991-Q1 … 2026-Q2 | as D1 | as D1 | High | numeric, synthesis |
| D3 | Average Weekly Total Paid Hours Worked Per Employee - Quarterly (`d_aebf156556c15c9c312ff23d24bf7278`) | MOM | 2026-09-22 | dataset | CSV 1,489 B, 114 rows, 1998-Q1 … 2026-Q2 | as D1 | as D1 | High | numeric, ambiguity (one series, no hours-by-sector) |
| D4 | Resident Labour Force Participation Rate (Total) (`d_69cfdab122e09ce1cb0fc1b6e314cab7`) and Employment Rate of Residents Aged 25 to 64 (`d_f50492fe89a0c3a522bf9c04ce3e6380`) | MOM | 2026-03-23 | dataset | CSV; annual to 2025, June reference | 2024, 2025 only | as D1 | Low-Medium (same Comprehensive Labour Force Survey as the 2025 report in corpus) | numeric only; annual cadence does not fit the quarterly adapters |
| D5 | Gross Domestic Product In Chained (2015) Dollars, By Industry (SSIC 2020), Seasonally Adjusted, Annualised Growth Rate, Quarter On Quarter (`d_cced7916e9d4a432236691c43d3fa048`) | SingStat | 2026-08-11 | dataset | CSV 26,663 B, 29 series, 1975-Q2 … 2026-Q2 | as D1 | as D1 | High | revision (current vintage versus advance/final text). **Not recommended**: the series contains extreme historical values (maximum above 95,000), so a plausible-range check would need an arbitrary bound |

Rejected, with reason: (a) **Total Wage (Nominal) Changes by Industry** (`d_e5848828d6a14d35a8b7eea7e15a149e`) and other annual MOM wage tables end at 2024 and are annual, so the adapters cannot take them and the 2025 report B1 has no dataset twin (this gap is itself a useful abstention fact); (b) **Average Monthly Nominal Earnings Per Employee, Annual** (SingStat, 2 rows) is annual; (c) **SingStat Unemployment Rate (End Of Period), Quarterly** duplicates MOM series already ingested; (d) MOM **Key Indicators / Dashboard** HTML pages for each quarter repeat Labour Market Report figures (Low independence); (e) **Occupational Wages 2025 / Gross Monthly Income 2025** table pages are HTML tables without the text passages the research families need; (f) **Labour Force in Singapore 2023** has subject period June 2023, outside Q1 2024–Q2 2026.

## 3. Verified revision evidence (advance GDP versus final Economic Survey)

**VERIFIED FACT (read in the PDFs):** the MTI advance press release and the later survey disagree on year-on-year GDP growth for the same quarter in every pair read:

| Quarter | Advance (press release) | Economic Survey (final) |
|---|---:|---:|
| 2025-Q2 | 4.3% | 4.4% |
| 2025-Q3 | 2.9% | 4.2% |
| 2026-Q1 | 4.6% | 6.0% |
| 2026-Q2 | 5.7% | 5.9% |

All ten pairs 1Q24 … 2Q26 exist and download (HTTP 200); only the four above were compared. This gives genuine, publisher-labelled advance/final pairs that no gold case, dev run or tuning step has touched. **Caveat for the owner:** the revised quantity is GDP, not a labour statistic. The labour-market chapter of each survey restates MOM figures that corpus documents already carry (for example the 2026-Q2 employment gain excluding migrant domestic workers equals the figure in the MOM advance release held in corpus), so labour-specific revision questions drawn from MTI are **not** independent. Either accept GDP revision as the revision family for this domain or fall back to the weaker MOM-based pairs (B3, B4), see §4.

**MEASURED RESULT / honesty note on B4:** the Labour Force in Singapore Advance Release 2025 and the final 2025 report give the same headline numbers in the three places spot-checked, so it is not a revision pair; use only for "do the two releases agree" consistency cases, and only if the owner accepts a touched counterpart.

## 4. Recommendation: 12 sources for ingestion

**Core set (6 PDFs in 3 advance/final pairs + 3 further PDFs + 3 datasets = 12 sources).** Source ids are those proposed in the YAML.

| Role | Source ids | Why |
|---|---|---|
| Revision pairs, 3 | `mti-2025-q3-advance`/`-final`, `mti-2026-q1-advance`/`-final`, `mti-2026-q2-advance`/`-final` | Largest and smallest revisions (2.9→4.2, 4.6→6.0, 5.7→5.9); three quarters; no overlap with existing gold; also supply productivity, cost, wage and labour text for factual and synthesis cases |
| Wage text + numbers | `mom-wage-practices2025`, `mom-nwc-lower-wage2025` | New year, new report; wage questions cannot be answered from any dataset in corpus (a deliberate abstention source); `mom-wage-practices2024` is in corpus, so cross-year comparison is possible without sharing 2025 facts |
| Causal-limits text | `mti-2026-q2-feature-ai-employment` | AI and employment evidence; natural for causal-overreach and "does the evidence show X caused Y" cases |
| Numbers, 3 | `unit_labour_cost_index_quarterly`, `value_added_per_worker_quarterly`, `avg_weekly_paid_hours_quarterly` | Quarterly series untouched by dev or held-out; checkable against the survey text (cross-source synthesis); deterministic comparison tool applies |

Optional additions, in priority order: A7/A8 (2025-Q2 pair, a fourth pair), B3 (Job Vacancies 2024, only if the owner accepts a half-touched source and wants a MOM-only revision case), C2, B6 (NWC guidelines, for forecast-refusal cases), A9, B4/B5 (consistency only).

**Family coverage with the core set (capacity estimate, not an authored count):**

| Family | Target n | Supply from core set |
|---|---:|---|
| factual_lookup | 12 | Plenty: five long PDFs (48 to 74 pages for the surveys) plus two wage reports |
| numerical_comparison | 12 | Three datasets; 10 in-scope quarters each, two-series comparisons with hierarchy rows |
| cross_source_synthesis | 10 | Survey productivity and cost text versus D1/D2; wage-report statements versus survey wage chapter |
| revision_conflict | 8 | **3 answerable advance/final pairs** (target needs at least 2 for 4 answerable cases; 6 to 8 cases available, plus abstention variants) |
| ambiguity_insufficient_causal | 10 | Feature article; absent 2025 wage dataset; survey caveat footnotes on preliminary data |
| adversarial | 8 | Authored over any passage; no new source needed |

This supports 60 cases (the design-A strata) with at least 8 non-answer/injection cases. Minimum viable subset: the three revision pairs (6 PDFs) plus `mom-wage-practices2025`, `mom-nwc-lower-wage2025` and the three datasets (11 sources); dropping the feature article loses roughly half of the causal-overreach supply and would need C2 or B6 as a substitute.

### Fetch and registration (exact steps; single writer after the evaluation job ends)

1. Edit `src/labourlens/data/acquire.py`: add `"isomer-user-content.by.gov.sg"` to `ALLOWED_HOSTS` (MTI PDFs are served only from that host; no redirect occurs, direct HTTP 200). `stats.mom.gov.sg`, `www.mom.gov.sg` and `data.gov.sg` hosts are already allowed.
2. `cp` the `documents:` and `datasets:` lists of `specs/sources-heldout-v2.proposed.yaml` into `specs/sources.d/heldout-v2-expansion.yaml`; split `dataset_adapter_specs` into `specs/datasets/<source_id>.yaml` (three files). The catalog rejects duplicate ids, none collide.
3. Fetch:
   ```
   uv run labourlens fetch --kind documents --only mti-2025-q3-advance mti-2025-q3-final mti-2026-q1-advance mti-2026-q1-final mti-2026-q2-advance mti-2026-q2-final mom-wage-practices2025 mom-nwc-lower-wage2025 mti-2026-q2-feature-ai-employment
   uv run labourlens fetch --kind datasets --only unit_labour_cost_index_quarterly value_added_per_worker_quarterly avg_weekly_paid_hours_quarterly
   ```
   Dataset downloads are throttled at 13 s per request by the existing fetcher (expect a few minutes). Both commands save the manifest after every source.
4. `uv run labourlens build`, then the usual index and cache steps. New text raises the corpus fingerprint; embedding cost for the new chunks is not estimated here (no tokenisation was run).
5. Before authoring, run `uv run labourlens trace` or open one extracted MTI passage file to confirm the two-column layout of the surveys extracted cleanly (the plain-text layout of A1–A6 interleaves columns; MOM reports were not affected). If extraction is poor, budget an extraction fix before authoring, not after.
6. Record each source in `docs/data-sheet.md` and `docs/decisions.md` (new decision), with the licence note, then freeze the corpus fingerprint **before** authoring blind cases.

**Facts the parent must account for in code and gold:**
- `src/labourlens/agent/tools.py:25` (`RELEASE_ID`) and `src/labourlens/data/reconcile.py:25-28` key release/vintage logic to `mom-YYYY-qN-advance|final*` ids. The MTI pairs use `mti-…` ids by design so they are not misread as MOM releases, **which means the agent has no deterministic vintage tool for them**; revision cases on MTI pairs are answered from retrieved passages only. Gold labels must say so. If you prefer tool support, extending `RELEASE_ID` is a code change that touches evaluated code and invalidates the "same code for every arm" rule unless made before freezing.
- `src/labourlens/data/validate.py` accepts a wrong first period only for `employment_change_by_sector`; the proposed specs set exact first periods. The sector-wide hierarchy sum check is hard-wired to that one source and does not apply to the new tables.
- No test in `tests/` hard-codes 46 documents, 33 datasets or 79 sources (grep found none), but `docs/data-sheet.md` and `docs/requirements-matrix.md` state those counts.

## 5. Rights, robots and risks (per D-001 / D-004)

- **All-rights-reserved PDFs** (A1, A3, A5, A7, A9, B1–B5): same position as the existing MOM reports. Passages stay in the gitignored `data/raw/` and `data/passages/`; the public repo carries ids, hashes, locators and links only. This applies to the MTI surveys, whose notice (quoted in the YAML in six words or fewer plus a paraphrase) restricts reproduction without permission.
- **Unresolved** (MTI advance press-release PDFs, MTI feature articles, MOM press pages, NWC guidelines): no notice found or not read. Record as `unresolved`, local-only. Public accessibility is not permission.
- **Datasets D1–D3:** the existing fetcher stamps every data.gov.sg dataset with the Singapore Open Data Licence. The metadata API returns no per-dataset licence field, so [INFERENCE] that these three carry the same licence as the 33 existing datasets; confirm on each dataset page before committing a snapshot (D-004 commits raw CSVs only for verified open-licence data). If confirmation fails, mark `local_only`.
- **Robots and terms:** `www.mom.gov.sg/robots.txt` allows all agents except a short list of non-content paths; `stats.mom.gov.sg/robots.txt` returns a one-line sitemap pointer with no disallow rule; `www.mti.gov.sg` redirects (301) to `www.meti.gov.sg` (the site now names itself the Ministry of Energy, Trade and Industry), whose robots file allows everything except `/search`; the MTI PDF host `isomer-user-content.by.gov.sg` publishes no robots file (access-denied response). The fetcher sends a research User-Agent, throttles data.gov.sg and fetches a handful of files, well inside any reasonable crawl limit. MOM and METI terms-of-use pages read on 31 Oct state no reuse licence for publication text (METI's page says nothing on reuse). [INFERENCE] none permits redistribution.
- **Publisher naming:** PDFs from August 2026 still say "Ministry of Trade and Industry"; the live site says "Ministry of Energy, Trade and Industry". The YAML uses the name printed on each document; the canonical page URL host will redirect.
- **Evaluation-integrity risks:** (1) A-set labour figures repeat MOM advance figures already in corpus; cases built only on those would be shared-fact, not disjoint. Author labour cases from the new wage reports, ULC/VA datasets and the GDP/productivity chapters instead, and run the group-exclusion check in `experiments/heldout-v2/evidence-audit.json` terms for semantic duplicates. (2) The datasets are current-vintage, the surveys preliminary: a dataset value may legitimately differ from survey text, so gold must name the vintage. (3) GDP revision is a domain stretch (see §3). (4) B2's publication date is inferred from PDF metadata; verify before using it in a time-scoped gold case. (5) I did not read B6, C1, C2 beyond title and URL; capacity claims for them are inference.
- **Not done here:** no extraction smoke test, no licence confirmation on dataset pages, no human review.

## 6. Counts

- Corpus today: 79 sources (46 documents, 33 datasets).
- Candidates evaluated: 23 table rows in §2 (A1–A10, B1–B6, C1–C2, D1–D5; A10 stands for five further survey/advance pairs), of which **12 recommended** (9 documents, 3 datasets), the rest optional or rejected as marked.
- Untouched-by-gold substantive documents among the 12: all 9 (none is in corpus, so none can be cited in dev or held-out v1 gold). Independence caveat: the labour chapter of the six MTI survey/advance files and the wage-survey overlap between B1 and B2.
- Revision pairs: 3 core, 7 more available; 0 untouched MOM-only labour pairs exist.

## 7. Open decision for the owner

Accept advance-versus-final **GDP** revisions (MTI) as the "source revisions" family for a labour-market held-out set, or require labour-only revisions (which only B3/B4 offer, both partly touched and weak)? Everything else in §4 follows from that choice.
