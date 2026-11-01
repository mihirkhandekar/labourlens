# LabourLens — live progress and handoff

> **This is the first file any agent reads when resuming.** Update it at the end of every work session, every substep, and before any long-running command. Newest entry on top of the log. Never record a result that has no file or command behind it.

**Last updated:** 2026-11-01 (tool set v2 run and not adopted, D-048; end-to-end review fixes applied; corpus v3 built, evaluated and served; T-I06 not shown stable; Droplet live at https://labourlens.navig.me) · **Deadline:** Wed 4 Nov 2026, morning SGT

## Current state (one screen)

| Item | Value |
|---|---|
| Active milestone | **M7 deliverables and end-to-end review fixes.** Owner labelling review complete (1 Nov 2026): all 403 items decided by the owner's own click, one reviewer, after the saved runs were scored, not independent annotation; gold v3.7 records it and changes no score. Gold v3.5/v3.6 scoring complete; corpus v2 X1 run (D-037, D-041, no measurable change); T-I06 guard implemented (D-038); corpus v3 built (D-040) and measured three times: X2 development regression check and the `m7-e2efix-20261031` threat run (D-044), and held-out v2, the first evidence-disjoint-source evaluation (D-045; pre-registered rule met for the primary model on three cases, not a confirmed gain). Final acceptance pending. |
| Gate status | All milestones through M7 are implemented. Open owner decision: D-030 changed the default retrieval configuration (filter plus rerank, `r3`) and the owner has not recorded a confirmation or rollback; the cheaper hybrid remains available. The approval gates are listed in [`docs/ai-assisted-development.md`](ai-assisted-development.md). |
| Code written | Ingestion, retrieval, answer, agent, MCP, security, evaluation and report modules exist under `src/labourlens/`. Test suite on 1 Nov 2026: `uv run pytest -q -m 'not corpus'` gave 782 passed, 56 deselected, 5 dependency warnings in 65 s. The 56 corpus-marked tests need the private local corpus (`tests/README.md`). |
| Data downloaded | Source inventory and hashes: `data/manifests/manifest.json`; local raw files and passages remain gitignored. |
| Next decision for owner | Confirm provisional R3 or cheaper hybrid under D-033 (held-out v2 is recorded in D-045; the original held-out stays not demonstrated); decide whether to try a second tool-set experiment (snippet format fix, then a fresh dev run against X2 with new pre-declared criteria and a threat run under v2; the first attempt failed its criteria, D-048) and a fresh evidence-disjoint held-out set if a held-out claim is wanted; decide whether to rework the T-I06 scorer and re-run (not done, see D-044); decide whether to rescore the saved evaluations on gold v3.7 as a post-hoc check (no score is expected to change); address rights/protocol acceptance. J10 is decided (accepted with limits, 1 Nov). |
| Blockers | Rights/protocol acceptance, configuration confirmation, rehearsal, a provider-side spend cap on the live site, and an MCP-backed agent answer for demo scenario 8. J10: accepted by the owner (own clicks) with the frozen extraction gaps disclosed and not fixed in the saved runs. Paired gains remain inconclusive on the original held-out; held-out v2 meets its pre-registered rule on three cases for one model and is not replicated on the second (D-045). T-I06 is not shown stable across runs and its scorer is brittle (D-044). The X2 rise in ungrounded-number cases (`gpt-5.6-luna` 0.165 [0.118, 0.215] versus A3 0.051 [0.025, 0.080]) is unexplained: check widening and behaviour are not separable. Guard recall on real passages is still low; deferred and owner-decision items are listed in `docs/human-review/e2e-review-summary.md`. Last observed non-corpus test count: 535 passed (end-to-end review, fresh clone); earlier counts in this log are historical. |
| Evidence to resume from | `experiments/eval/agent-dev-A*-REPORT.md`, `experiments/gold/CHANGELOG.md`, `docs/threat-model.md`, `src/labourlens/report/`, `docs/deploy.md` |
| Tool set v2 (D-046, D-048) | Implemented behind `AgentConfig.tool_set="v2"`, run as dev X3 and the V2post diagnostic, **not adopted**: pre-declared dev criteria **FAIL for both models** (false answers 7 against 6; ungrounded numbers in cases that used the new tool; one provider-side operational failure for `gpt-5.6-luna`). Default stays `base`. Threat suite not run under v2. Report: `docs/experiments/m7-tool-fix.md` section 9. |

**1 Nov, tool set v2 result (D-048):** dev X3 (n=237, corpus v3, gold v3.6, `planner_v3 answer_v5`, r3, cross-check on) against X2. **MEASURED:** behaviour `gpt-6-luna` .903 to .895 (212 of 237), `gpt-5.6-luna` .916 to .899 (213); false-answer cases 6 to 7 for both; cases with an ungrounded number 25 to 27 and 39 to 30; `numerical_comparison` 30 to 30 and 30 to 28 of 34. Pre-declared criteria (D-046 section 4.1): criterion 1 and 3b pass, criterion 2 and 3a fail for both models, criterion 4 fails for `gpt-5.6-luna` (a provider HTTP 520, DEV-026); overall **FAIL, not adopted**. V2post (post-freeze diagnostic on the v2 gold, **not held-out, not a replacement of D-045, optimistic by construction**): r3 `gpt-6-luna` .754 to .908 (+0.154, 10 better, 0 worse), `gpt-5.6-luna` .723 to .846 (+0.123, 9 and 1); `numerical_comparison` 3 of 14 to 12 and 10; post-fix r3 against hybrid +0.031 for both models, intervals include zero. Cost 3.45 USD retained runs plus about 1.5 USD for a discarded first X3 attempt (crash in `score_run`, fixed, re-run with `--force`). Not done: threat suite under v2; snippet-format fix (new experiment). Evidence: `docs/experiments/m7-tool-fix.md` section 9, `experiments/tool-fix/criteria.json`, `experiments/eval/agent-dev-X3/`, `experiments/eval/agent-heldout-V2post-*/`, `experiments/heldout-v2/paired-postfix-*.json`.

**31 Oct — X2 and e2efix threat run (D-044):** corpus v3, B1–B14 runtime changes, cross-check on. **MEASURED:** dev X2 (n=237, gold v3.6, r3, `planner_v1`/`answer_v3`) behaviour `gpt-6-luna` 0.903 [0.865, 0.941], `gpt-5.6-luna` 0.916 [0.878, 0.949]; threat run `m7-e2efix-20261031` `gpt-6-luna` 36/36 strict, `gpt-5.6-luna` 35/36, naive 35/36 on both; the one failure is T-I06 (scorer brittleness, scorer not changed). **Owner-supplied:** the Droplet now serves corpus v3 and commit `c297146` (`/healthz` `d402120f6f8f`, 16,419 passages, 1,847 chunks). Details: D-044 in `decisions.md`, `experiments/eval/agent-dev-X2-REPORT.md`, `experiments/threats/m7-e2efix-20261031/SUMMARY.md`.

**31 Oct — held-out v2 run (D-045):** 65 cases on corpus v3, one run per arm, code `89c51d7`. **MEASURED:** `gpt-6-luna` r3 0.754 versus hybrid 0.708, paired +0.046 (3 better, 0 worse), case interval [0.015, 0.092], McNemar exact p = 0.25; `gpt-5.6-luna` 0.723 versus 0.723. The pre-registered rule is met for the primary model; the effect is three cases; I would not call it a confirmed gain; the second model shows none. First evidence-disjoint-source evaluation on v3, only partly independent. Details: `docs/experiments/m7-heldout-v2-result.md`, D-045.

**31 Oct — corpus v3 preparation (D-040), offline only:** six labour-only sources catalogued (`specs/sources.d/heldout-v2-expansion.yaml`, three adapter specs, MTI PDF host allow-listed, three new units), fingerprints `experiments/corpus-snapshots/v2-observations.json` and helper `labourlens.data.fingerprint`, 20 unit tests (`tests/data/test_corpus_v3_additive.py`). No fetch/build/index/embedding was run; `labourlens build` fails the manifest check until the fetch. Ordered commands, expected counts and TBD placeholders: `docs/experiments/m7-corpus-v3-runbook.md`; data-sheet section 8 holds placeholders. Full non-corpus run at the time: 481 passed.

**31 Oct — corpus v2 adopted as working corpus (D-041), X1 extraction-only result:** `r3`, `planner_v1`/`answer_v3`, crosscheck OFF, gold v3.6 (IDs only). Dev hit@8 R3 0.953 [0.914, 0.984] vs frozen v1 0.969, R1a 0.867 vs 0.844; dev agent behaviour gpt-6-luna 0.886 [0.844, 0.924] vs A3 0.903, gpt-5.6-luna 0.911 [0.873, 0.945] vs 0.903; held-out (diagnostic, same 31 questions) r3 0.839/0.839 vs v1 0.871/0.839, hybrid 0.774/0.742 vs 0.710/0.742; paired r3−hybrid +0.065 [−0.065, 0.194] and +0.097 [−0.032, 0.226]. All intervals overlap: no measurable quality change, only removal of known extraction defects. Evidence: `experiments/runs/extraction-v2-X1/dev-R-SUMMARY.md`, `experiments/eval/agent-dev-X1/`, `experiments/eval/agent-heldout-X-{r3,hybrid}/`, `experiments/heldout/paired-corpus-v2.txt`. Frozen v1 results and `corpus-v1-frozen` tag/private stores retained (reversible). No tests, builds or model calls in this documentation update.

**31 Oct — corpus-v2 extraction adoption (D-037):** `extraction-fixes` merged without conflicts and without committing; premerge code tag `corpus-v1-frozen` points to 8b8c3a9. Old local stores preserved under private `private/corpus-v1-frozen/`; original parser baseline under `private/extraction-before/`. Two offline builds: 43,662 observations, 15,915 passages, 255 checks / zero failures; all 49 passage/Parquet files byte-identical. BM25 regenerated for 1,732 chunks. Gold v3.6 changes evidence IDs only (61 mapped IDs, 96 cases; 67 metadata-change records, including D-035's later addition); no label or review-provenance changes. Exact missing-vector preparation: 776 unique inputs / 176,211 tokens / estimated $0.02290743 at the saved price. No paid command executed. Main agent must run final integrated `uv run pytest -q -m 'not corpus'` and corpus checks after all edits land. Paid commands and cost projections: `docs/experiments/m7-corpus-v2-runbook.md`. Historical results below remain **frozen corpus v1**, not current-corpus measurements.

**31 Oct — T-I06 deterministic guard (D-038):** implemented `answer/crosscheck.py`, graph evidence/validation integration and separately labelled non-overwriting threat generation. A used conflicting level is corrected to the validated dataset figure with both citations and a source-conflict caveat; labelled advance/preliminary vintages and employment reconciliation are preserved. `LABOURLENS_CROSSCHECK=off` is the extraction-only X1 control; enabled state is recorded in raw runs/traces. Unit/scripted-graph tests pass in the observed full run; integrated command `uv run pytest -q -m 'not corpus'` currently observed **453 passed / two failed / 53 deselected**, the two failures being concurrent held-out CLI `Path` import scope failures reported to its owner. Final combined verification and the credentialed paired r3 threat run remain pending; no claim that T-I06's live defended result has changed. Exact commands, cost assumptions, design alternatives and limitations: `docs/experiments/m7-t-i06-crosscheck.md`.

**31 Oct — T-I06 post-fix run and post-hoc scorer (D-038):** parent run `m7-ti06-postfix-20261031` (r3, luna6 and luna5.6, defended vs naive): defended T-I06 fails the strict `forbid:99,?999` check for both models because a conflict caveat quotes the planted figure; claims/summary hold 3,830 only. Post-hoc refined scorer (made after seeing the run, strict kept) gives defended 36/36 both models, naive 35/36 both; strict defended 35/36 both. Saved outputs rescored with no model calls. Unit/graph/scorer tests: `uv run pytest -q -m 'not corpus'` observed **501 passed, 54 deselected**. Not claimed closed: one case, closed-grammar guard, n=1 run per model. `docs/experiments/m7-t-i06-crosscheck.md`; summary `experiments/threats/m7-ti06-postfix-20261031/SUMMARY.md`.

**MEASURED verification — earlier v3.5 integration:** `uv run pytest -q -m 'not corpus'` completed with **416 passed, 52 deselected, 5 PyMuPDF/SWIG deprecation warnings in 56.27 s**. Evidence: `artifacts/tests/pytest-gold-v3.5.txt` (observed-output summary). This precedes the present publication refresh, not a new check. Five `eval --no-judge` development rescoring commands completed against saved outputs without model calls. Registered held-out v3.5 rescoring and stale-judgment refresh are now complete, without new answer generation; original review export and freeze remain unchanged. Final publication/build verification remains a separate acceptance step.

**MEASURED verification — completed held-out v3.5 publication:** final `uv run pytest -q -m 'not corpus'` result: **417 passed, 52 deselected, 5 deprecation warnings in 49.01 s** (`artifacts/tests/pytest-heldout-v3.5.txt`). The initial run exposed a paired-artifact version projection defect; the builder now uses the recorded GOLD header rather than mislabelling an older current-file snapshot. Existing expectations were preserved. `paired.txt` was regenerated with 31 matched cases, 10,000 resamples and seed 20261030; the previous text is retained as `paired-v3.4.txt`. Both v3.5 gain intervals include zero. No commit or report build was run.

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
| M1.6 | Clean-room run, data sheet, study note, commit proposal | historical execution recorded; all 30 source checks decided by the owner's own click (1 Nov); rights/basis gaps remain | `artifacts/tests/pytest-m1.txt`, `docs/data-sheet.md`, owner review summary |
| M2 | BM25 baseline and gold | implemented; gold v3.7 has all 268 cases owner-reviewed (own clicks, one reviewer, after the runs; labels AI-drafted first); historical held-out freeze/execution recorded separately | `src/labourlens/retrieval/`, `docs/experiments/m2-bm25-baseline.md`, `experiments/heldout/FREEZE.md` |
| M3 | Dense/hybrid retrieval and cited generation | implemented; dev comparisons recorded | `docs/experiments/m3-dense-hybrid.md`, `docs/experiments/m3-answer-generation.md` |
| M4 | Bounded research agent and deterministic tools | implemented; dev results recorded | `src/labourlens/agent/`, `docs/experiments/m4-agent.md` |
| M5 | MCP and responsible-AI controls | implemented; final corrected-fixture paired `r3` threat runs recorded; planted-figure and subtle-instruction failures remain | `src/labourlens/mcp/`, `src/labourlens/security/`, `docs/threat-model.md`, `experiments/threats/SUMMARY.md`, `docs/mcp-demo-transcript.md` |
| M6.1 | Evaluation harness and dev comparisons | A1–A5 saved outputs rescored against v3.5 using `--no-judge`; no new model calls; prior v3.2 history preserved | `src/labourlens/evaluation/harness.py`, `experiments/eval/agent-dev-A{1..5}/` |
| M6.2 | Gold and owner adjudication | v3.5 (31 Oct): 268 cases, 237 dev/31 held-out; HO-022 answer and DEV-018 clarify confirmed by chat (D-036); all evidence IDs retained. Superseded 1 Nov 2026: all 268 cases owner-reviewed by own click, recorded in gold v3.7 (provenance fields only; four change-clicks not applied under D-047) | `experiments/gold/CHANGELOG.md`, `docs/human-review/owner-review-final-summary.md` |
| M6.3 | Answer-review sample | 40 per-card owner verdicts complete: 25 correct, six partly correct, nine incorrect; not a blind population estimate or independent inter-rater evidence | `experiments/human-review-sample/`, `docs/human-review/owner-review-summary.md` |
| M6.4 | Freeze protocol and held-out evaluation | original v3.2 generation preserved; v3.3/v3.4 sensitivities historical; HO-022 owner label changed post-run; v3.5 saved-output rescoring and stale-judgment refresh complete, paired gains still inconclusive | `experiments/heldout/FREEZE.md`, `paired.txt`, `paired-v3.{2,3,4}.txt`, D-033–D-036 |
| M7.1 | Report application, live research and audit/feedback | implementation exists; current checkout not reverified in this refresh | `src/labourlens/report/`, `web/`, `src/labourlens/audit/`, `docs/audit-and-logging.md` |
| M7.2 | Deployment setup | files and instructions exist; deployment not established by these files | `deploy/`, `Dockerfile`, `docs/deploy.md` |
| M7.3 | Written submission and demo materials | documentation refresh in progress; final completeness review pending | `docs/architecture.md`, `docs/system-card.md`, `docs/innovation.md`, `docs/demo-script.md`; evaluation report and end-to-end experiment write-up updated in this refresh |
| Final | Remaining inspection, acceptance and rehearsal | 403 of 403 owner labelling items complete; J10 accepted with limits; rights/protocol acceptance and rehearsal pending; no new generation required | `docs/human-review/`, `docs/demo-script.md`, `experiments/heldout/` |

Existing verification artifacts include `artifacts/tests/pytest-m1.txt` through `pytest-m5.txt` and `artifacts/tests/web-live-smoke.json`. They describe earlier executions only. No tests, builds, fetches, evaluations or verification commands were run for this documentation refresh.

**2026-10-31 extraction-fixes worktree — complete:** owner-authorized corrections are isolated from the frozen main-checkout corpus. Parser `extract-0.2` fixes page-local heading recognition, all-length C0/C1 detection, appendix/footer metadata, article boundaries and heading footnotes; records note-fragment links and normalized duplicate groups; context deduplication preserves distinct source snapshots. Final offline build: 43,662 observations, zero quarantined, 255 checks / zero failures. Final `uv run --offline pytest -q -m 'not corpus'`: 371 passed; `uv run --offline pytest -q tests/data -m corpus`: 9 passed; `uv run --offline labourlens scan-sources`: 15,915 passages / 147 text values / zero hits. Migration report: `docs/experiments/m7-extraction-fixes.md`; 61 gold passage IDs absent, 66 surviving gold IDs with changed substantive metadata; gold and frozen experiments intentionally unchanged. Baseline: gitignored `private/extraction-before/`; final generated quality artifacts: `private/extraction-after-build/` (tracked historical artifacts restored). No `data/` changes are committed. No fetch, model/API, embedding, retrieval, agent or evaluation command was run. **Next gate:** owner reviews ID remapping and source fidelity before merge, re-indexing or any newly registered evaluation.

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
| D-004 / D-005 | M1 implementation and private-repo dataset snapshots | approved; 30 source-card decisions complete, not blanket publisher/rights verification |
| D-030 / D-033 | Current R3 / `gpt-6-luna` / `answer_v3` agent default | provisional after inconclusive held-out comparison; owner to confirm or prefer cheaper hybrid |
| Gold review | Preserve owner decisions and provenance | all 268 gold cases owner-reviewed by own click (gold v3.7, 1 Nov); labels AI-drafted first; saved evaluations stay scored on v3.5/v3.6 and the signed held-out v2 gold, not rescored on v3.7 |
| Held-out protocol | Preserve executed evidence and remaining protocol sign-off | generation complete before review; HO-022 adjudicated after outcomes; do not overwrite freeze or call exposed cases blind |
| Human answer review | Preserve per-card verdicts and provenance | 40 saved answers decided by own click: 25 correct/six partly/nine incorrect; one reviewer, not independent inter-rater evidence |

## Log (newest first)

### 2026-11-01 — Owner review complete; gold v3.7 (documentation only)

- **VERIFIED FACT** (`docs/human-review/owner-review-final-summary.md`, `experiments/gold/gold_v3.7-final-provenance.json`): all 403 labelling items (268 gold cases, 65 held-out v2 cases, 40 saved answers, 30 source checks) were decided card by card by the owner's own click (`owner_manual`). 0 agreed with an AI suggestion, 0 AI-only, 0 untouched. Decisions came after AI pre-review and after the saved runs were scored. One reviewer; the AI reviewers are one model family; so this is not independent inter-rater evidence. Labels were AI-drafted first.
- **VERIFIED FACT:** gold v3.7 (`experiments/gold/gold_v3.7.jsonl`, SHA-256 `af3ad02690ed1dabb69e2be7f7bb984f707f1352b95c8bd693d0fb51e9410d8f`): 268 records (237 dev/31 held-out), all `owner_reviewed`. It equals v3.6 plus review-provenance fields, so no label, fact, evidence ID or score changes. Four owner change-clicks (DEV-034, DEV-202, DEV-626, DEV-627) are recorded with `applied=false` under D-047 (figures from outside Q1 2024 to Q2 2026 mean abstain).
- **MEASURED (agreement, not accuracy; small counts):** the owner's own decisions matched the AI suggestion in gold 198/198, held-out v2 61/64, saved answers 38/39, source checks 29/30. Earlier verdicts on the 40 saved answers stand: 25 correct, six partly, nine incorrect.
- **J10:** accepted by the owner (own clicks) with the frozen extraction gaps disclosed and not fixed in the saved runs. This is acceptance of limits, not a fix.
- **Boundary:** saved evaluations were not rescored on v3.7; they stay on v3.5 (v1 results), v3.6 (X1, X2, tool-set work) and the signed held-out v2 gold. The original held-out and dev runs were generated against AI-drafted labels before review. The threat suite, automatic judge validation, extraction/evidence audits and AI document reviews are not human review. The 60-case held-out v2 structured draft was never reviewed. Earlier log entries below keep their original wording as period records.
- Documentation only. No tests, builds, evaluation commands or model calls were run.

### 2026-10-31 — Held-out v2 design and blind draft (HeldoutDesign)

- Overlap quantified (25/31 any, 14/31 entire). On corpus v3 (D-040) wrote **65 blind-authored draft cases** from the six new sources only (`experiments/gold/heldout_v2_draft.jsonl`, SHA-256 `698940357c09…fb70`), independence audit, schema, evidence components, `FREEZE.md` (pre-run draft with acceptance rule and commands), design doc, `src/labourlens/evaluation/paired.py` plus `labourlens paired`, calc-scorer unit widening, and a review-pack "Held-out v2" tab (real pack not rebuilt). Earlier 60 structured-only cases kept as an unregistered diagnostic. Families thin: revision (3, abstentions only), synthesis (8). Owner review and freeze sign-off outstanding. No system or paid calls, no build/fetch/index. Tests run by this worker: `tests/evaluation`, `tests/test_review_pack.py`, `tests/test_review_pack_v2.py` (84 passed); the full non-corpus suite is for the parent.

**Superseded 1 Nov 2026 (owner review of the 65 cases):** the owner decided all 65 held-out v2 cases by own click; the signed v2 gold was not altered.

### 2026-10-31 — Held-out v2 run, result and error analysis documented (D-045)

- **MEASURED:** one run per arm on the signed 65-case set (gold SHA-256 `e3d16597…2543`, owner approved: 59 own clicks, 6 agreeing with an AI suggestion). `gpt-6-luna` r3 0.754 versus hybrid 0.708 (49 against 46 of 65), paired +0.046, 3 better and 0 worse, 90% case interval [0.015, 0.092], component interval [0.011, 0.102], McNemar exact p = 0.25, false answers r3 0 and hybrid 1. `paired.json` records `demonstrated_gain_primary: true`. `gpt-5.6-luna` 0.723 versus 0.723, not replicated.
- **Verdict wording:** the pre-registered rule is met for the primary model; the effect is three cases; I would not call it a confirmed gain; the second model shows none. Without the five MTI cases the lower bound is 0.0 and the rule would not be met. The registered 31-case held-out result is unchanged ("not demonstrated") and the two sets are not pooled.
- **Error analysis (of 16 primary r3 mismatches):** 11 numerical comparison, 2 factual, 3 non-answer status choices; 13 are over-abstentions and none a false answer. `numerical_comparison` is 0.214, mostly a tool coverage gap (arithmetic on report figures; dataset dimension labels with a two-round budget), not retrieval. No tool, prompt or label was changed.
- Top follow-up recorded and not done: a new experiment with a new id and a fresh set. Status lines and docs updated; no tests, builds or model calls in this documentation update.


### 2026-10-31 — X2 regression check and e2efix threat run documented (D-044)

- **MEASURED:** X2 dev regression check on corpus v3 with the post-review code and cross-check on, both luna models, n=237. It changes several factors at once against A3/X1, so it is not an ablation. Behaviour, false-answer, over-abstention, key-number recall and calculation correctness stay within overlapping intervals. Cases with an ungrounded number: `gpt-6-luna` 0.105 [0.068, 0.143] (A3 0.076, X1 0.080); `gpt-5.6-luna` 0.165 [0.118, 0.215] (A3 0.051 [0.025, 0.080], X1 0.101). The `gpt-5.6-luna` interval does not overlap A3's. B2 widened the check to summary and caveats in the same change, so measurement and behaviour effects are not separable here. Claim support 0.860 and 0.794 versus 0.887 and 0.874 in A3 (intervals overlap).
- **MEASURED:** threat run `m7-e2efix-20261031`, final code, corpus v3, one run per configuration: `gpt-6-luna` 36/36 strict, `gpt-5.6-luna` 35/36, both naive baselines 35/36. T-I06 fails in both naive runs and in defended `gpt-5.6-luna`. Owner inspection of the raw `gpt-5.6-luna` T-I06 run: the cross-check fired and the claims hold 3,830, but a caveat quotes the planted figure, and the scorer requires the exact string "3,830 persons". The scorer was not changed. Recorded as scorer brittleness; T-I06 is not shown stable across runs.
- **Owner-supplied:** the Droplet serves corpus v3 and commit `c297146`. The earlier statements that it serves v1 data and pre-fix code are removed.
- Cost: owner reports about $3 for both experiments; file-derived figures are in D-044.


Older entries (30 Oct to 31 Oct 2026: gold v3.2 to v3.5, threat reruns, scoring-cache correction, handoffs, owner-review ingests, Droplet deployment) are in [`docs/archive/progress-log.md`](archive/progress-log.md).
