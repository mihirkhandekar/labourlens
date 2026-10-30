# LabourLens — live progress and handoff

> **This is the first file any agent reads when resuming.** Update it at the end of every work session, every substep, and before any long-running command. Newest entry on top of the log. Never record a result that has no file or command behind it.

**Last updated:** 2026-10-30 (M1 implemented; awaiting owner gate review) · **Deadline:** Wed 4 Nov 2026, morning SGT

## Current state (one screen)

| Item | Value |
|---|---|
| Active milestone | **M1 — Government data ingestion and provenance** |
| Gate status | **M1 IMPLEMENTATION APPROVED 30 Oct 2026 (D-005).** Scope: ADR-001 + ADR-003 structured data, D-006 corpus, D-004 CSV snapshots committed to the private repo. M2+ is NOT approved. |
| Code written | M1 complete: `src/labourlens/**`, 51 tests pass, 142 build checks 0 failed |
| Data downloaded | See checklist; raw files under `data/raw/` (gitignored) |
| Next decision for owner | M1 gate review: fill `docs/human-review/*.md`, then approve M2 (BM25 baseline). Open proposals D-007, D-008, D-009, D-011 |
| Blockers | None. No API keys needed for M1. |
| Who is working | Nobody holds a lock. Repo: https://github.com/mihirkhandekar/labourlens (private, `master`) |

## Document map (public vs private)

| Location | Audience | Contents |
|---|---|---|
| `docs/` | **Published** with the submission | requirements, source catalog, ADRs, decisions, data sheet, evaluation report, system card, architecture, innovation, demo script |
| `docs/progress.md`, `docs/decisions.md`, `docs/glossary.md` | Published, but written as working logs | handoff, decision log, vocabulary |
| `study/` | **Private to owner. Gitignored.** | interview prep, why-we-chose-this, alternatives rejected, failure postmortems, Q&A rehearsal |
| `private/` | **Private to owner. Gitignored.** | scratch research, raw probe output, personal review notes, anything not meant for reviewers |
| `data/raw/` | Local only. Gitignored. | MOM PDFs and raw downloads |

Rule: if unsure whether something belongs in a published doc, put it in `private/` and ask the owner.

## Claiming work (multi-agent protocol)

1. Before starting, add a row to "Active claims" with your agent name, the substep ID, and the files you will touch.
2. Do not edit files claimed by another row. If you need one, add a note under "Handoff notes" and stop on that file.
3. When finished or stopping early, remove your claim, log what is done and what is not, and name the exact next command or file to open.
4. If a claim is older than one working session with no log entry, treat it as abandoned: read the last log entry, verify the repo state with `git status`, then re-claim.

### Active claims

| Agent | Substep | Files | Started (SGT) |
|---|---|---|---|

## Milestone checklist

Status values: `not started`, `in progress`, `done (evidence: path)`, `blocked (reason)`.

| ID | Substep | Status | Evidence |
|---|---|---|---|
| M1.0 | Repo hygiene: `.gitignore`, private/public doc split, handoff docs | done | evidence: `.gitignore`, this file, `docs/decisions.md` |
| M1.1 | Verify sources, rights, schemas; freeze manifest | done | evidence: `specs/sources.yaml`, `data/manifests/manifest.json` |
| M1.2 | Models, manifest, acquisition with throttle and hashes | done | evidence: `src/labourlens/data/acquire.py`, `raw_store.py`, `fetch.py`; 33 sources ok |
| M1.3 | Dataset normalizers, Parquet, DuckDB read layer | done | evidence: `data/processed/observations.parquet`, 10,896 rows |
| M1.4 | PDF and HTML passage extraction with quality flags | done | evidence: `artifacts/data-quality/extraction_stats.json` |
| M1.5 | Quality report, advance/final/dataset reconciliation | done | evidence: `artifacts/data-quality/quality-report.md`, `reconciliation.json` |
| M1.6 | Clean-room run, data sheet, study note, commit proposal | done except human review | evidence: `artifacts/tests/pytest-m1.txt`, `docs/data-sheet.md`, clean-room run below |

## Verified facts so far (planning session 1, probes run 2026-10-30)

Every row came from a live call; none is stored as a repo artifact yet. M1.1 must re-run these and save the outputs under `artifacts/data-quality/`.

- data.gov.sg metadata API works for all 4 approved datasets. A custom `User-Agent` is required: Python's default urllib agent gets HTTP 403.
- Download flow works on host `api-open.data.gov.sg`: `GET /v1/public/api/datasets/{id}/initiate-download`, then `/poll-download`. The `api-production` host returns 404 for these paths.
- Returned download URLs are signed S3 links containing `X-Amz-Security-Token`. **Strip the query string before logging or writing a manifest.**
- Quota: 5 requests/minute without an API key. HTTP 429 was observed on `datastore_search` after a burst.
- Resident unemployment: 138 rows, `period` as `YYYY-MM`, values are strings, `residential_status` always `resident`.
- Vacancy ratio and retrenchments: `quarter` already `YYYY-Qn`, 114 rows each, values are strings.
- Sector dataset: wide columns `20262Q`…; hierarchy only by leading whitespace in `DataSeries`. Its 2Q26 "Total Changes In Employment" is **14,700**, while MOM final reports **11,400** (excluding migrant domestic workers) and the advance release **10,700**. The cause of the 14,700 gap is **not verified**.
- All 4 report PDFs download (HTTP 200, `application/pdf`) and carry an all-rights-reserved MOM notice. Pages: 3Q25=64, 4Q25=64, 1Q26=59, 2Q26=59.
- One page of the 2Q26 PDF extracted with `pdftotext` as encoded garbage. Extraction needs a garble detector.
- MOM press-release rights: unresolved.
- data.gov.sg lists ~4,663 datasets; roughly 190 are MOM-managed (see `docs/decisions.md` D-003 for the shortlist).

## Open decisions

| ID | Question | Status |
|---|---|---|
| D-003 | Structured data scope: Tier 1 plus six features | **approved 30 Oct; ADR-003 written** |
| D-006 | Expand unstructured corpus (Labour Force 2025 methodology PDFs now; earlier advance/final pairs once URLs verified) | **approved 30 Oct** |
| D-007 | UI, deployment, authentication (M7) | proposal; no action until M7 gate |
| D-008 | Agent quality targets | proposal; refined at M4 |
| D-004 | Commit the raw dataset CSVs to the private repo | recommended yes; confirm with M1 approval |
| D-005 | Approve "Implement Milestone 1" | **awaiting owner** |

## Log (newest first)

### 2026-10-30 — planning session 2
- Owner approved D-003. Wrote `docs/decisions/ADR-003-structured-data-scope.md`. Added D-006, D-007, D-008 to `docs/decisions.md`.
- Probed more unstructured sources: `Labour Force in Singapore 2025` page (7 PDFs, verified); MTI Economic Survey page reachable but no PDF links found; MAS page in maintenance; earlier advance-release URLs not found without a browser. Nothing was downloaded to the repo.
- Read `kpi-dashboard-design`. Noted `design-taste-frontend` excludes dashboards, so it is not used for the workbench.
- Owner approved D-006. Added D-009 (RAG storage layers) and deployment notes to D-007. Still no code.
- **Next step revised:** D-005 (explicit "Implement Milestone 1" approval). M1.1 must also find exact URLs of earlier advance/final releases in a browser session and read each new document's rights notice.

### 2026-10-30 — planning session 1
- Read all project docs and the assessment PDF. Ran the live source probes above. No code written.
- Presented the M1 design. Owner chose: private repo shared with reviewers (D-001), split private/published docs (D-002), expand structured data scope (D-003, in discussion).
- Created `docs/decisions.md`, `docs/glossary.md`, this file; moved `docs/study/01_PREPARATION.md` to `study/`; updated `CLAUDE.md` with the handoff protocol.
- **Next step for whoever resumes:** get the owner's answer to D-003, then write `docs/decisions/ADR-003-structured-data-scope.md`, and wait for D-005 before any code.

## Handoff notes

(none)

- 2026-10-30: D-010 recorded (interactive report page). Added `labourlens export` (data/export/*.json, 7 files), fixed revisions summary print, eda+revisions run OK (3 figures, eda-findings.md, revisions.json baseline_only). `docs/presentation-plan.md` written. Remaining M1: tests (M1.6), spot-check sheets, data-sheet, study note, README/.env.example, clean-room run, commit proposal. Checklist table above is stale: M1.1-M1.5 implemented, build 142 checks/0 failed.

- 2026-10-30 (M1 close): Added tests (51 pass, `artifacts/tests/pytest-m1.txt`), review sheets (`labourlens review-sheets`; UNREVIEWED), data sheet, README, `.env.example`, requirements matrix, study note (private), D-011 human-feedback design. Re-fetched the 4 LF2025 PDFs to sync catalog rights (now 8 unresolved, all HTML releases). Clean-room run in /tmp copy of tracked files: `uv sync`, `fetch --kind documents`, `build` (142 checks, 0 failed), `pytest` (51 passed). NOT re-run in clean room: dataset `fetch` (throttled, about 4 min; datasets came from committed snapshots). Committed `7c23b3a` and pushed to the private GitHub repo. Next: owner review of `docs/human-review/`, then M2 approval. Claim released.
