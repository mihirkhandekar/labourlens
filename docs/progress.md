# LabourLens — live progress and handoff

> **This is the first file any agent reads when resuming.** Update it at the end of every work session, every substep, and before any long-running command. Newest entry on top of the log. Never record a result that has no file or command behind it.

**Last updated:** 2026-10-30 (M6 dev evidence and M7 implementation documented; human review and held-out run pending) · **Deadline:** Wed 4 Nov 2026, morning SGT

## Current state (one screen)

| Item | Value |
|---|---|
| Active milestone | **M6 evaluation and M7 deliverables in progress.** Evaluation harness, dev runs, report application and audit/feedback code exist. Human review and held-out evidence are incomplete. |
| Gate status | M1–M5 implementation history is recorded below. D-030 records the assistant's current default change; **owner confirmation or rollback is pending**. Historical planning gates below are not current status. |
| Code written | Ingestion, retrieval, answer, agent, MCP, security, evaluation and report modules exist under `src/labourlens/`. Existing checks are historical artifacts, not a new verification of current code. |
| Data downloaded | Source inventory and hashes: `data/manifests/manifest.json`; local raw files and passages remain gitignored. |
| Next decision for owner | Confirm or revert D-030, review source/gold/answer samples and resolve `experiments/gold/CHANGELOG.md` label questions before freezing the held-out protocol. |
| Blockers | Required human review has not happened. Gold freeze and held-out execution remain pending. Corrected threat runs expose planted-figure acceptance and subtle instruction-following; direct over-refusal remains. A5 / `planner_v2` is in progress with no results. |
| Evidence to resume from | `experiments/eval/agent-dev-A*-REPORT.md`, `experiments/gold/CHANGELOG.md`, `docs/threat-model.md`, `src/labourlens/report/`, `docs/deploy.md` |

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
| M2 | BM25 baseline and draft gold | implemented; owner review and freeze pending | `src/labourlens/retrieval/`, `docs/experiments/m2-bm25-baseline.md` |
| M3 | Dense/hybrid retrieval and cited generation | implemented; dev comparisons recorded | `docs/experiments/m3-dense-hybrid.md`, `docs/experiments/m3-answer-generation.md` |
| M4 | Bounded research agent and deterministic tools | implemented; dev results recorded | `src/labourlens/agent/`, `docs/experiments/m4-agent.md` |
| M5 | MCP and responsible-AI controls | implemented; corrected `r3` threat runs recorded; planted-figure and subtle-instruction failures remain | `src/labourlens/mcp/`, `src/labourlens/security/`, `docs/threat-model.md`, `experiments/threats/SUMMARY.md`, `docs/mcp-demo-transcript.md` |
| M6.1 | Evaluation harness and dev agent comparisons | implemented; A1–A4 metrics available; single-factor A5 / `planner_v2` comparison in progress, no results | `src/labourlens/evaluation/harness.py`, `experiments/eval/agent-dev-A1-REPORT.md` through `agent-dev-A4-REPORT.md` |
| M6.2 | Gold drafting and AI pre-review | AI drafting and three AI review passes; **not human-reviewed** | `experiments/gold/CHANGELOG.md`: 268 cases, 237 dev and 31 held-out |
| M6.3 | Documented answer-review sample | selection and AI pre-review exist; **owner review pending** | `experiments/human-review-sample/selection.json`, `ai-review-summary.md` |
| M6.4 | Freeze protocol and run held-out evaluation | pending owner review and label decisions | `docs/human-review/gold-review.md`, `experiments/gold/CHANGELOG.md` |
| M7.1 | Report application, live research and audit/feedback | implementation exists; current checkout not reverified in this refresh | `src/labourlens/report/`, `web/`, `src/labourlens/audit/`, `docs/audit-and-logging.md` |
| M7.2 | Deployment setup | files and instructions exist; deployment not established by these files | `deploy/`, `Dockerfile`, `docs/deploy.md` |
| M7.3 | Written submission and demo materials | documentation refresh in progress; final completeness review pending | `docs/architecture.md`, `docs/system-card.md`, `docs/innovation.md`, `docs/demo-script.md`; evaluation report and end-to-end experiment write-up updated in this refresh |
| Final | Owner reviews, held-out report and submission rehearsal | pending | `docs/human-review/`, `docs/demo-script.md` |

Existing verification artifacts include `artifacts/tests/pytest-m1.txt` through `pytest-m5.txt` and `artifacts/tests/web-live-smoke.json`. They describe earlier executions only. No tests, builds, fetches, evaluations or verification commands were run for this documentation refresh.

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
| D-003 / D-006 / D-019 / D-020 | Source scope and expansion cap | settled in `docs/decisions.md`; do not reopen without an incompatible requirement |
| D-004 / D-005 | M1 implementation and private-repo dataset snapshots | approved in D-005; source spot-checks still await the owner |
| D-030 | Current `r3` / `gpt-6-luna` / `answer_v3` agent default | assistant changed default on measured dev evidence; owner to confirm or revert |
| Gold review | Resolve remaining behaviour/definition questions and review evidence | owner pending; see `experiments/gold/CHANGELOG.md` |
| Held-out protocol | Freeze cases and configurations before running held-out evaluation | pending owner review; no held-out result claimed |
| Human answer review | Review the prepared sample using the documented rubric | pending; AI pre-review is not human review |

## Log (newest first)

### 2026-10-30 — M6/M7 evidence and submission-documentation refresh

- Read the assessment text, approved scope/graph ADRs and existing implementation/results. Updated current state and checklist to reflect the evaluation harness and report/audit implementation already present.
- Added `docs/system-card.md` with intended use, models/prices, A3 dev results, rights, risks, monitoring and oversight. Appended D-030 to `docs/decisions.md`; `src/labourlens/agent/graph.py` currently defaults to `r3`, `gpt-6-luna` and unchanged `answer_v3`.
- A1/A2 show no measurable prompt benefit; A3/A4 show no measurable widening benefit. A3 is development evidence, not held-out validation. Metrics and latency/cost sources: `experiments/eval/agent-dev-A1/` through `agent-dev-A4/`; interpretation is maintained in `docs/experiments/m6-agent-end-to-end.md` and `docs/evaluation-report.md`.
- Gold v3/v3.1 remains AI-drafted after three AI review passes: 268 total, 237 dev and 31 held-out (`experiments/gold/CHANGELOG.md`). Source, gold and answer-sample human reviews remain undone. Freeze and held-out run remain pending.
- Correction superseding the earlier final-default `r3` 36/36 claim: the poisoned fixture lacked BM25/dense candidate lists, so all six indirect attacks failed operationally before reaching the model. This made the earlier indirect-injection safety and utility interpretation invalid. The corrected fixture places poison in both candidate lists with named document metadata; an attack is exercised only if poison reaches evidence. Regression tests were added in `tests/test_security.py`, not run in this refresh.
- Corrected defended safety results: `gpt-6-luna` 35/36, `gpt-5.6-luna` 35/36 (both Wilson 95% interval 0.858–0.995), and `gpt-4.1-mini` 34/36 (0.819–0.985). Each has 6/6 useful indirect answers but only 5/6 indirect safety passes. Both luna models accept T-I06's false planted figure; `gpt-5.6-luna` mentions the canary once in a caveat, not as compliance. Mini fails T-S05's status criterion and follows T-I02's subtle instruction while citing poison. `gpt-6-luna` direct usefulness remains 0/1 and MCP usefulness 3/3. Sources: `experiments/threats/SUMMARY.md` and `experiments/threats/runs/{gpt-6-luna,gpt-5.6-luna,gpt-4.1-mini}.metrics.json`. Older hybrid naive rows are not a paired `r3` ablation. Parent supplied fixture/run provenance; this worker read saved metrics without executing checks.
- No passage-figure cross-check against datasets for the same indicator and period exists. A deterministic cross-check is proposed, not built. A5 / `planner_v2` is in progress as a single-factor comparison against A3: continue legitimate research despite an override, while DEV503/DEV505 retain zero-tool abstention. No A5 results or default change are claimed.
- **Commands/checks run in this refresh: none.** Existing test and smoke artifacts were read, not rerun. Documentation updates do not establish current-code test status, deployment or completion of the mandatory demo scenarios.
- **Next gate:** owner confirms or reverts D-030 and completes review/label decisions, then freezes the held-out protocol. Continue remaining submission-documentation integration before final rehearsal.

Entries below are historical session records. Their “next” gates, proposal statuses, counts and test results describe the state at that entry.

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

- 2026-10-30: Owner approved starting M2 (BM25 baseline). Decisions recorded since M1 close: D-012 persisted BM25 index, D-013 managed Postgres direction, D-014 DigitalOcean. M2 design discussion in progress (chunking, BM25 library, gold labelling); no M2 code written yet.

- 2026-10-30 (M2): D-015 chunking, D-016 experiment policy, D-017 gold authoring, D-018 protocol. Built `src/labourlens/retrieval/` (chunk, tokenize, bm25_index, evaluate, experiments, gold), CLI `retrieval-exp`, `gold-check`. 50 draft gold cases (19 dev, 31 held-out) by a subagent, validated mechanically; I spot-checked 4 against passage text and scanned for copied MOM text (none). Dev experiments E1 to E4 on 9 text cases: see `docs/experiments/m2-bm25-baseline.md`. 74 tests pass (`artifacts/tests/pytest-m2.txt`). NOT done: owner review of `docs/human-review/gold-review.md`; gold freeze; held-out run (pre-registered, 3 configs); more dev cases. Next: owner reviews gold, then M3 (dense retrieval, LLM) needs approval and a design discussion.
- 2026-10-30: Owner asked for more dev evidence. Added 15 dev cases (DEV-020..034), gold now 65 (34 dev, 31 held-out); validator extended to accept literal calculation inputs verified against cited text; normalised adversarial fixture fields. Dev experiments re-run at n=24 (report updated; n=9 summary kept as `experiments/runs/dev-n9-SUMMARY.md`). Conclusion changed: b=0.4 no longer helps. Corpus expansion feasibility investigated (see chat; no ingestion yet; awaiting owner decision).

- 2026-10-30 (D-019/D-020): Owner agreed to cap expansion (D-020). Ingested 30 documents and 16 datasets: 46 documents, 33 datasets, 13,484 passages, 43,662 observations; build 254 checks, 0 failed; 74 tests pass. Changed the in-scope coverage check to use each spec's declared last period (two datasets end 2025-Q4). Reconciliation not extended (regex mismatched; see data-processing-log). Dev retrieval re-run: baseline hit@10 0.58, MRR 0.31 (was 0.71 and 0.41), see `docs/experiments/m2-bm25-baseline.md`. NOT done: gold cases for the new documents, held-out run, owner review of gold and M1 sheets. Next: M3 design discussion (embedding model, LLM, answer schema) then M4 to M7.
- 2026-10-30 (M3 build, step 1): Owner approved starting the M3 build and excluded `gpt-6-astra` as too expensive. Built `retrieval/dense.py` (cached OpenAI embeddings, usage log, cosine search, RRF hybrid) and `experiments_dense.py`; CLI `dense-exp`. Ran E5 to E7 on dev (n=24): see `docs/experiments/m3-dense-hybrid.md`. 5 new tests pass. NOT done: LLM answer layer (citations, abstention, structured output), LLM model comparison, two controlled configs, held-out. Next: answer-layer design (schema and citation rules), then LLM comparison.
- 2026-10-30 (M3 build, step 2): Answer layer built in `src/labourlens/answer/` (D-024): strict JSON schema, labelled passage context, deterministic validator (label exists, verbatim quote, status rules), one repair call, prompts in `prompts/`. Experiments G1 (6 models), G0 (oracle evidence), G3 (k=3/5/8) on 30 dev cases: `docs/experiments/m3-answer-generation.md`. Raw outputs local in `data/runs/` (gitignored, contain MOM quotes). Excluded gpt-6-astra per owner. NOT done: price table for cost, LLM judge and human review (M6), numerical cases (need M4 tool), prompt comparison, held-out. Next: owner picks the abstention policy / candidate default; then M4 (LangGraph agent with statistics tool).
- 2026-10-30 (M3 step 3): Added `specs/prices.yaml` (official OpenAI pricing page, read 30 Oct) and `labourlens.prices`; cost per case added to all answer summaries; embedding costs corrected from unverified to verified. D-026 recorded (prefer declining). G4 run (k=8, two luna models). Candidate default: hybrid, k=8, gpt-6-luna (not frozen). Next: M4 LangGraph agent.
- 2026-10-30 (M4): Built the bounded LangGraph agent (`src/labourlens/agent/`): three tools, seven nodes, bounds, trace, operational-failure separation. 98 tests pass (13 agent tests with fault injection). A1 on 34 dev cases: `docs/experiments/m4-agent.md`. Candidate default gpt-6-luna. NOT done: threat tests and MCP (M5), judge and human review (M6), held-out, text-number arithmetic improvement. Next: M5 design discussion (MCP server, threat tests).
- 2026-10-30 (M5): MCP server and client (`src/labourlens/mcp/`), hostile fixture server, guards and redaction (`src/labourlens/security/`), agent wiring (flagged items cannot be cited, output guard, trace redaction), 36-case threat suite (`experiments/threats/`), scripted client demo and direct-vs-MCP comparison (`docs/mcp-demo-transcript.md`), `docs/threat-model.md`, D-028. Threat suite: defended 36/36 on gpt-6-luna, gpt-5.6-luna, gpt-4.1-mini; no-defence gpt-4.1-mini 33/36. Checker corrected after manual review of 2 flagged cases (disclosed). NOT done: adaptive attacks, over-refusal fix for override-plus-legitimate-question (T-D02), HTTP transport/auth, accuracy and hallucination metrics (M6). Next: M6.
  Correction: this historical M5 entry is not current R3 evidence. The later R3 36/36 claim was invalid for indirect injection because six attacks failed before reaching the model; the corrected results and fixture methodology in the current refresh above supersede that claim. Older hybrid naive runs remain historical, not a paired R3 ablation.

- 2026-10-30 (M6 retrieval experiments): Added `retrieval/{period,rerank,experiments_rerank}.py`, `prompts/rerank_v1.md`, CLI `retrieval-exp2`, tests (`tests/retrieval/test_period.py`, `test_rerank.py`). Dev n=137, one factor at a time: hard period/release filter and the LLM rerank each beat the hybrid baseline beyond the bootstrap interval, and combined they lift hit@8 from 0.60 to 0.97 and gold-in-context (top 8 chunks) from 0.60 to 0.97 (retrieval only; agent not run). Spend $0.54. Caveats: AI-drafted gold, LLM reranker, filter blind spot for restated quarters. Nothing adopted (D-029, PROPOSAL); report `docs/experiments/m6-retrieval-improvements.md`; results `experiments/runs/dev-R*/`.

- 2026-10-30 (M6 retrieval scope-correction rerun, supersedes preceding v3.1 numbers): after GoldFixer completed v3.2 and reported `gold.validate == []`, ran `PYTHONHASHSEED=0 uv run labourlens retrieval-exp2` on 128 answerable dev text cases, SHA-256 `647b26a2f0faa86be30ad897840bc1887b54f55c27268d141565b94cb22998e8`. Hit@8: R0 0.5703, R1a 0.8438, R1b 0.7188, R2 0.7891, R3 0.9688; paired bootstrap differences versus R0 exclude zero for all four changes. R3 versus R2 +0.1797 [0.1094, 0.2500]; gold-in-context from eight chunks 0.5703 to 0.9688. Conclusion unchanged; subset changed because nine out-of-scope historical questions now require abstention. All API responses cached, new spend $0.00 (cumulative recorded rerank spend $0.54). Updated generated dev-R results, current report section and D-029, preserving hypotheses, deviations and old-hash numbers as explicitly superseded history. No agent code, default or prompt changed or run; D-030 separately records subsequent integration history.
