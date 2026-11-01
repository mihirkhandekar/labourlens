# Repository audit (read-only, 1 Nov 2026)

Audit of the repository at commit `1f8226b` (`master`), run on 1 Nov 2026. Nothing was changed except the creation of this file. No model, embedding or judge call and no network call was made.

Principle applied: remove noise, never remove honesty. Nothing below proposes altering a published number, a frozen result, a gold file, a hash or an experiment record.

## 0. Headline

| Question | Answer | Evidence |
|---|---|---|
| Any secret ever committed? | **No.** | `gitleaks git` over 90 commits: 73 hits, all in `data/manifests/manifest_history.jsonl`, all false positives (data.gov.sg dataset identifiers matched as "generic API key"). History search for `sk-`, `ghp_`, `github_pat_`, `PRIVATE KEY`, `AKIA`, `xox` finds only test fixtures (`sk-abcd...` strings) and a template placeholder. `.env` was never tracked (only `.env.example` and `deploy/.env.example`, with empty values). The two live access codes and the DigitalOcean host were searched for in history and the tree (values read locally, never printed): 0 matches. No public IPv4 address is present; only `172.30.0.x` (Docker network) and RFC 5737 documentation addresses. |
| Any MOM/MTI file, raw model output or the assessment PDF ever committed? | **No.** | `git log --all --name-only` shows no `*.pdf`, `data/raw`, `data/passages`, `data/index`, `data/runs`, `private/`, `study/`. Raw model outputs live in gitignored `data/runs/`; committed `experiments/runs` and `experiments/eval` hold scores, metrics and judge notes only (D-001, D-004). |
| `rights-scan` | 0 hits, 16 allowlist globs. **But** it only compares against the gitignored `data/passages/`; in a fresh clone it prints "skipped" and exits 0 (finding B6). |
| Tests | `782 passed, 56 deselected, 5 warnings in 65.34s` (`uv run pytest -q -m 'not corpus' -p no:cacheprovider`, observed by the audit). 56 corpus-marked tests are deselected. |
| Working tree | Clean at audit end except untracked `artifacts/screenshots/` (7 MB, not covered by `.gitignore`). The 41 uncommitted modifications seen at the start were committed as `1f8226b` by the owner during the audit; findings below were re-checked against it. |
| BLOCKERs | 7 (B1 to B7). All are fixable without touching frozen artefacts. |

Not checked (needs the owner): the contents of the live site; the GitHub repository settings (environment protection on `production`); whether the owner is content for the name "Mihir Khandekar" and the git author email to appear in a shared repository.

## 1A. Inventory and classification

Classes: **Ship** (core deliverable), **Ship, reorganise**, **Private** (gitignored or moved to `private/`), **Delete** (obsolete), **Question** (owner decides). Tracked file count: 911.

| Path | Files | Class | Notes |
|---|---|---|---|
| `README.md` | 1 | Ship, rewrite as entry point | Accurate but dense: result rows of 80 to 120 words; says current gold is v3.6 at line 103 while elsewhere v3.7. |
| `CLAUDE.md` | 1 | Ship (decision D1 below) | The collaboration contract is the evidence of method. Contains a stale "PLANNING ONLY / no implementation approved" status block; update the status block, keep the contract. |
| `START_HERE_PROMPT.md`, `LABOURLENS_PROJECT_PLAN.md` (58 KB) | 2 | Ship, reorganise into `docs/process/` | Kick-off prompt and original plan show the method. Plan is long; keep with a banner "initial plan, superseded by decisions.md". Question D1. |
| `Tech Challenge - GenAI Engineer v1.0.pdf` | 1 local | Private (already gitignored) | Remove from any export; never commit. |
| `private/` (286 MB), `study/` (60 KB) | local | Private (already gitignored, never in history) | Keep local. |
| `.env` | local | Private (gitignored) | Contains only a provider key. Never printed. |
| `.env.example`, `deploy/.env.example`, `deploy/mcp.env.example` | 3 | Ship | Empty values. |
| `docs/` core: `architecture`, `data-sheet`, `evaluation-report`, `system-card`, `innovation`, `demo-script`, `requirements-matrix`, `threat-model`, `glossary`, `decisions.md`, `decisions/ADR-001..003`, `deploy`, `mcp-demo-transcript`, `concepts`, `audit-and-logging`, `adding-sources`, `data-processing-log` | ~20 | Ship (edit for staleness) | See findings S-series. |
| `docs/progress.md` | 1 | Ship, reorganise | 291 lines of multi-agent working log ("the parent", agent names). Keep a short current-state page; move the log to `docs/archive/progress-log.md` or `private/`. Question D2. |
| `docs/01..05_*.md`, `presentation-plan.md` | 6 | Ship, reorganise into `docs/archive/planning/` | Written before implementation; read as current status. |
| `docs/human-feedback-design.md`, `docs/storage.md` | 2 | Delete or merge | Say "nothing built" for things that now exist. Merge a short section into `audit-and-logging.md` and `data-sheet.md`; git history keeps the originals. |
| `docs/security-review-web.md` | 1 | Ship (dated) | Cites "164 passed" and CLAUDE.md. Date it. |
| `docs/experiments/` | 16 | Ship | Experiment records. Add an index. |
| `docs/human-review/` | 24 | Ship, reorganise | Proposed layout in section 1A-2. |
| `experiments/runs`, `eval` | 349 | Ship (frozen) | Scores, metrics, reports. Not model transcripts. 7.7 MB + 4.3 MB. |
| `experiments/gold` | 33 | Ship (frozen) | Includes `archive/` (v3.2 to v3.5, 1.5 MB, hash-pinned) and `ai-review*/`. Keep; optionally note which archived versions are referenced. |
| `experiments/threats`, `heldout`, `heldout-v2`, `human-review-sample`, `corpus-snapshots`, `tool-fix`, `rights-truncation-sidecar.json` | ~60 | Ship (frozen) | `heldout-v2/evidence-audit.json` is 1.4 MB, mostly a period listing. |
| `data/manifests`, `data/snapshots` (66), `data/export`, `data/processed` | ~90 | Ship (see B7 and S-data findings) | Open Data Licence CSVs and metadata; three datasets under assumed licence are excluded as raw CSV but included as derived rows. |
| `prompts/*.md` (21) | 21 | Ship | Runtime prompts, hashed into experiment records. |
| `prompts/meta/` (3) | 3 | Question D1 | The two meta prompts are the owner's own tutor and submission-audit prompts. Reads professionally. Keep only if the owner wants them visible; they are not read by the application. |
| `specs/` (42) | 42 | Ship | Includes `rights-scan-allowlist.txt` (reviewed in 1B-R). |
| `src/labourlens` (77), `tests` (52), `scripts` (3), `deploy` (6), `Dockerfile`, `.github/workflows/deploy.yml` | | Ship | Code is clean of TODO/FIXME, commented-out code and stubs. Lint findings in 1B-C. |
| `web/` (86) | 86 | Ship | `web/static/data/report.json` (1.8 MB) is generated by `labourlens build-report` and tracked on purpose. Fonts carry OFL licence text. |
| `artifacts/figures` (3 PNG), `artifacts/data-quality` (11), `artifacts/tests` (8) | 22 | Ship | `artifacts/tests/pytest-m1.txt` and `pytest-m2.txt` contain a local absolute path (S-path). Do not edit if cited as evidence; see finding N3. |
| `artifacts/screenshots/` (untracked), `screenshots-*/` (ignored) | 41 + many | Private | Add `artifacts/screenshots/` to `.gitignore`. Screenshots may show source passages. |
| `.DS_Store`, `.pytest_cache`, `.ruff_cache`, `__pycache__`, `.venv` | local | Private (already ignored) | None tracked. |
| `uv.lock`, `pyproject.toml` | 2 | Ship | No `.python-version`, no ruff config, no Makefile. |

### 1A-2. `docs/human-review/` classification

| File(s) | Class |
|---|---|
| `owner-review-final-summary.md`, `review-inventory.md` | Ship. Change the second-person register ("your review") to "the owner". |
| `owner-review-summary.md` (31 Oct, 125 cards), `ai-pre-review-*-spot-check.md`, `ai-verification-of-pre-reviews.md`, `ai-adjudication.md`, `independent-ai-review-m1.md`, `independent-ai-review-m1-2.md`, `heldout-v2-ai-review-summary.md` | Ship, reorganise into `ai-review/` and `owner-review/`, each with a dated "state as of" header. |
| `e2e-review-summary.md` and the five area reports | Ship, reorganise into `e2e-review/`. `e2e-review-security-deploy.md` needs a rewrite first (B4). |
| `passage-spot-check.md`, `statistical-spot-check.md`, `gold-review.md` (3,075 lines) | Ship with a banner, or Question D3. Headers say "unreviewed" or "45/268" (B2). |
| `OWNER-REVIEW-GUIDE.md`, `HELDOUT-V2-REVIEW.md` | Private. Operator manuals for the owner's local review pack. |
| `copy-audit.md`, `deck-copy-review.md`, `site-artifact-review.md` | Private. Copy-editing history, quotes superseded wording ("45 of 268"). |
| Delete | Nothing. |

## 1B. Red-flag scan

Severity: BLOCKER, SHOULD, NICE. "Action" never alters frozen artefacts.

### Blockers

| ID | Path | Problem | Action |
|---|---|---|---|
| B1 | repo root | No `LICENSE`. Reuse terms of the code are undefined; data (Open Data Licence), fonts (OFL) and MOM/MTI material carry other terms and nothing says so at the top level. | Owner decision D4. Add `LICENSE` (or an explicit "all rights reserved, shared for review" notice) and a README licence and attribution section. |
| B2 | `docs/human-review/gold-review.md:3` (and `tests/retrieval/test_gold_review.py:53,69`), `passage-spot-check.md:1,3`, `statistical-spot-check.md:1,3`, `web/static/data/report.json` (one string) | States "45/268 owner-reviewed", "(UNREVIEWED)", "not yet reviewed by a human". The owner has since decided all 403 items. The reader sees the reverse of the record. | Add a dated banner to each sheet pointing to `owner-review-final-summary.md`; find the string's source in `report/build.py`, correct it and run `labourlens build-report` (changes `report.json` only; no number or score changes). Update the test pin with the file header, not by weakening it. |
| B3 | `web/static/presentation/ch5-evaluation.js:271` | Says no held-out or evidence-disjoint evaluation exists on corpus v3. Held-out v2 exists (README, D-045). Other occurrences (`ch8-limits.js`, `ch-work.js`) were fixed in `1f8226b`; this one remains. | Reword to "development only; held-out v2 is reported separately". |
| B4 | `docs/human-review/e2e-review-security-deploy.md:1,29,78,87` | Raw agent reply saved verbatim: "I could not write ... paste it into that file". | Rewrite as a plain report (the findings are in `e2e-review-summary.md`). |
| B5 | `docs/demo-script.md:17,84`; `requirements-matrix.md:51`; `progress.md:16` | Agent working note in a published file ("TO BE RECORDED"). Scenario 8 (MCP-backed agent answer) has no recorded artefact (`artifacts/mcp-agent-demo.md` does not exist). | Either record it (needs a paid call; not in this task) or state plainly "not recorded; shown to the tool result only" in the script and the matrix. |
| B6 | `src/labourlens/data/rights_scan.py:114-116`; README | In a fresh clone `rights-scan` has no corpus to compare against, prints "skipped" and exits 0. Reviewers will see a green check that proves nothing. The output "0 hit(s) in 0 file(s)" is also unclear. | Print `NOT CHECKED: data/passages absent` and add `--require-corpus` (non-zero exit); document that the real scan runs only on the owner's machine with the private corpus, and what CI does instead (tracked-file leak guard plus gitleaks). This changes tooling, not results. |
| B7 | `data/processed/observations.parquet` (tracked, hash pinned in `experiments/heldout-v2/FREEZE.md`); `docs/data-sheet.md:14,38,68-69` | 8,358 derived rows come from three datasets whose licence is "assumed open, not verified" (`unit_labour_cost_index_quarterly`, `value_added_per_worker_quarterly`, `avg_weekly_paid_hours_quarterly`). Raw CSVs are gitignored; the derived rows are committed, and the data sheet says "local-only" without saying so. | Preferred: verify the licence on each dataset page (read-only web read) and record it. Otherwise state the commitment plainly in the data sheet. Dropping rows would change a pinned hash and is not recommended. |

### Should fix

| ID | Path | Problem | Action |
|---|---|---|---|
| S1 | `README.md:15-22` | Results table is correct (checked against `heldout-v2/paired.json` and the gold changelog) but cells run 80 to 120 words. | One row per question, at most 30 words; caveats stay in `evaluation-report.md`. |
| S2 | `README.md:103` | "current gold file is v3.6". Elsewhere v3.7 (provenance only, labels equal to v3.6). | Reword, citing the changelog. |
| S3 | `docs/requirements-matrix.md:3,5,13-17,32-36,67` | Dated 31 Oct but cites 1 Nov items; narrates "this refresh did not run tests"; headline rows present v3.5 as current; innovation doc claimed "about 830 words" but is 1,071 words (`wc -w`). | Re-date, order headline rows by current state, label v3.5 as historical, fix or trim the innovation doc. |
| S4 | `docs/progress.md:13,242,252,288,291` | "Existing checks are historical" (no single current test count); stale next-step blocks from 30 Oct; local path to the access-codes file (path only, no codes); "login not yet verified" contradicts README. | Short current-state page; move the log (D2). Record one dated test line: 782 passed, 56 deselected. |
| S5 | `docs/decisions.md` (574 lines) | D-003 to D-006 filed under "In discussion/Awaiting"; D-004, D-007, D-008, D-009, D-011 still `PROPOSAL`; D-046 title not marked superseded by D-048; no approver on D-029, D-032, D-041 to D-046, D-048. | Add an index by status; add "approved by owner on <date>, evidence <path>" where the record shows it (for example the held-out v2 signed block in `FREEZE.md:85-91`), and "assistant under D-016, owner may overturn" where it does not. Never invent an approval. |
| S6 | `docs/storage.md:12-15`, `human-feedback-design.md:1-4`, `presentation-plan.md:3`, `docs/01..05_*.md` | "Not built" for things that exist. | Merge or archive (1A). |
| S7 | `docs/evaluation-report.md` (531 lines), `system-card.md`, `architecture.md`, `data-sheet.md`, `innovation.md` | The "three corpus states" paragraph and the v3.2 to v3.5 sensitivity numbers repeat in about six files. | Single home in the evaluation report; others link. Do not change numbers. |
| S8 | `docs/human-review/*` (`e2e-review-deliverables.md:57,66`, `e2e-review-evaluation.md:9`, `docs/progress.md:155,156,280`, `decisions.md:298`) | 31 Oct counts ("45", "125 cards") shown without a state-as-of header; `progress.md:280` bolds "independent human review". | Add "state as of 31 Oct" headers; bracket or delete "independent". |
| S9 | `experiments/gold/gold_v3.7-review-log.jsonl` | 265 unique cases against 268 gold cases; three decided in earlier exports. The final summary does not say so. | One sentence in the summary and `experiments/gold/CHANGELOG.md`. The log file is not touched. |
| S10 | `experiments/gold/CHANGELOG.md:1` | Title "(AI pre-review fixes)"; the v3.7 heading says the owner reviewed "cases never reviewed before". | Retitle, reword the heading. Hash entries untouched; CHANGELOG is hash-referenced in places, so confirm first that no pinned hash covers it. |
| S11 | `data/snapshots/*/*.metadata.json` (32 files) | `contactEmails` fields hold four named MOM officers' work addresses and one generic address, published by data.gov.sg under the Open Data Licence. Personal data under PDPA in a shared repository. | Record a decision (kept as published provenance) or redact in the metadata only. Check first that no hash covers the metadata bytes (CSV hashes are separate). Owner decision D5. |
| S12 | `specs/rights-scan-allowlist.txt` | Whole-directory globs (`data/snapshots/*`, `data/manifests/*`, `specs/*`, `data/export/*.json`, `experiments/gold/archive/*`) mean those paths are never scanned. With the allowlist disabled, 113 tracked files hit. Longest runs outside CSVs: 18 words (publisher copyright notice), 16 (a document title), 78 (dataset definitions, Open Data Licence text). The `heldout_v2_v1.jsonl` entry says "locator headings" but contains one 7-word run that is a statistic phrase. | Keep the entries; state in the data sheet that allowlisted paths are not scanned; correct the reason text of the `heldout_v2_v1.jsonl` and `gold/archive/*` entries. Line-by-line review is in the table in section 1B-R. |
| S13 | `experiments/rights-truncation-sidecar.json` | Over-long runs in committed judge and review outputs were cut to six words after scoring. The sidecar records counts, so files are no longer byte-exact to the run. | Disclose in the evaluation report limitations. Already recorded in the sidecar; make it visible. |
| S14 | `.github/workflows/deploy.yml` | Only workflow; triggers on push to `master` and `workflow_dispatch`. No PR trigger, no lint, no rights/secret scan. `--deselect` of one test is redundant (module already carries the `corpus` marker) and its comment is stale. `workflow_dispatch` can deploy from any ref unless the `production` environment restricts branches. | Add `ci.yml` (tests, ruff, leak guard, gitleaks); fix the comment; add a branch guard. |
| S15 | `tests/conftest.py:12-47` | `CORPUS_TESTS` and `INDEPENDENT_MCP` are name lists; a renamed test silently changes class. | Mark explicitly with `@pytest.mark.corpus`. |
| S16 | `tests/web/test_deck.py:78-100,130-150,175-189` | Pins deck wording and style: banned CSS words, dash style, slide-count range, the strings "403", "One reviewer", "OWNER TO CONFIRM", the owner's name, absence of `favicon.svg`. Project rule: delete tests that pin wording. | Delete those assertions; keep route, CSP, no-inline-script tests. |
| S17 | `tests/test_review_pack.py:154-160,321,429`; `tests/test_pending_review.py:368,370` | Exact summary phrases and a changelog table row pinned. | Keep privacy negatives; delete wording positives or assert on structured fields. |
| S18 | `src/`, `tests/` | No ruff or type-check config. Ruff F-rules: 21 unused imports, 23 redefinitions (shadowed `settings` fixture), 5 unused locals (`harness.py:177`, `experiments_rerank.py:217,247`, `review/pending.py:415`). | Add `[tool.ruff]` with F, E9 and I; fix the F findings only. Do not enable stylistic rules that would reformat the repo. |
| S19 | `.gitignore` | `artifacts/screenshots/` not ignored (untracked, 7 MB); `artifacts/screenshots-pending/` listed twice. | Fix. |
| S20 | `docs/human-review/e2e-review-deliverables.md`, `site-artifact-review.md` | Link to local-only screenshot folders. | Mark "local only" or drop; if pictures help, commit three to five hand-checked images under `docs/img/`. |
| S21 | `web/static/presentation/slides.js:133`, `docs/security-review-web.md:42` | Cite `CLAUDE.md` as if a source. | Cite ADR-001 or the rights rule instead. |
| S22 | no `SECURITY.md`, no `.pre-commit-config.yaml`, no `Makefile`, no `.python-version`, no `tests/README.md`, no `docs/README.md`, no `docs/reproduce.md` | Harness items missing at audit time. | Added later (harness). |
| S23 | Architecture diagram | One mermaid block in `docs/architecture.md`, no rendered image. Graphviz `dot` is installed; `mmdc` is not (node and npx are present, but installing Mermaid CLI needs the network). | Render with `dot` from a DOT source kept next to the mermaid, or keep mermaid only and say so. Owner decision D6. |
| S24 | `docs/deploy.md:123` | A v1 corpus verification (13,484 passages) next to the v3 deployment claim. | Prefix "historical, 30 Oct". |

### Nice to have

| ID | Path | Note |
|---|---|---|
| N1 | `README.md`, `innovation.md`, `slides.js` | Mixed voice ("I would not call it", "the owner decided"); some American spellings in `requirements-matrix.md` (9), `architecture.md` (4), `concepts.md` (4); some may be identifiers. |
| N2 | `docs/human-review/owner-review-summary.md` | Correctly bannered as superseded; retitle "31 Oct export (superseded)". |
| N3 | `artifacts/tests/pytest-m1.txt`, `pytest-m2.txt` | Contain `/Users/<name>/...` paths. They are recorded evidence of old runs; leave unchanged and say so in a one-line index, or accept. |
| N4 | `deck.html` and presentation footer | Open Data Licence attribution is in the app footer and README, not in the deck. Add one line. |
| N5 | `experiments/gold/independent-ai-review*.md` vs `experiments/human-review-sample/independent-ai-review*.md` | Same file names, different documents. Cross-link or rename on move. |
| N6 | `experiments/heldout-v2/FREEZE.md:31` | Draft gate text superseded by the signed block at line 85. Add a one-line "superseded" note (FREEZE.md is hash-referenced? confirm before touching). |
| N7 | `deploy/docker-compose.yml:18,83` | Default image path contains the GitHub username; overridable. Acceptable. |
| N8 | Docker base images | Pinned by tag, not digest (declared in the Dockerfile). |
| N9 | `tests/` frozen-count pins (`test_gold_review.py:52,82,83`, `test_integrity.py:137`, `test_revisions_reconcile.py:45-47`) | These guard frozen artefacts; label them as such in a docstring. Keep. |

### 1B-R. Rights allowlist, line by line

| Entry | Verdict |
|---|---|
| `data/snapshots/*` | Justified: open-licence CSVs and metadata. Note S11 (emails). |
| `data/manifests/*` | Justified: publisher notice recorded verbatim (18 words, legal text). |
| `specs/*` | Justified for titles and dataset definitions; broad. Disclose that it is not scanned. |
| `data/export/*.json` | Justified: titles, locators, legal notices (longest 16 words). |
| `artifacts/data-quality/reconciliation.json` | Justified: locators. |
| `experiments/heldout-v2/evidence-audit-v3.json` | Justified: document titles. |
| `experiments/gold/draft_cases.jsonl`, `archive/*`, `heldout_v2_draft.jsonl`, `gold_v3.7.jsonl`, `gold_v3.7-review-log.jsonl`, `docs/human-review/gold-review.md` | Justified as hash-pinned frozen files with headings and category names (longest 10 words). Reason text should say "pinned, never rewritten". |
| `experiments/gold/heldout_v2_v1.jsonl` | **Reason inaccurate**: one 7-word run is a statistic phrase, not a heading. Frozen and signed, so keep, correct the reason, and record the exception in the data sheet. |
| `experiments/eval/agent-dev-A1/...cases.jsonl`, `agent-dev-X3/...cases.jsonl`, `...judgements.json` | Justified: one section heading echoed in frozen output. |

The scan also skips binaries (Parquet, PNG) and files above 5 MB, and matches exact words only (no paraphrase detection). The data sheet should say so.

### 1B-O. Other red-flag checks

| Check | Result |
|---|---|
| Local absolute paths | `/Users/<name>` in `artifacts/tests/pytest-m1.txt`, `pytest-m2.txt` (4 lines) and `docs/human-review/OWNER-REVIEW-GUIDE.md:99` (moves private). None in code. |
| Personal data | Owner name and GitHub username throughout (intended: byline, GHCR default, review provenance); git author email is a personal Gmail address in all 90 commits; MOM officer emails (S11). |
| Unprofessional or chat text | B4, `docs/progress.md` agent chatter (S4), `demo-script.md` (B5). No profanity or jokes found by the scouts. No emojis in README or docs. |
| TODO, FIXME, XXX, stubs | None in code or docs, except documented "top follow-up (not done)" statements in `decisions.md:498` and `progress.md:143`, which are honest open items and stay. Scaffold words ("MVP", "foundation") were not used to hide unfinished work. |
| Bloat | Largest tracked: `report.json` 1.8 MB, `observations.parquet` 1.5 MB, `evidence-audit.json` 1.4 MB, gold files about 370 KB each. Tracked binaries: 3 PNG figures, 3 Parquet files, 2 woff2 fonts. No `.DS_Store`, `__pycache__`, `.env`. Nothing to remove for size. |
| Commit history | 90 commits, one author, 30 Oct to 1 Nov. Messages name milestone or decision IDs. Weak ones: ten "Rebuild report page data" commits (generated output, harmless). Large mixed commits: `d894dae` (129 files, 102,731 lines), `c297146` (172 files), `a774b15`, `7c23b3a`. No commit adds then removes a sensitive file. History is acceptable; rewriting is not recommended (it would invalidate recorded commit references such as `89c51d7` and tag `corpus-v1-frozen`). |
| Branches | `master`, `extraction-fixes` (local and remote); tag `corpus-v1-frozen` referenced by D-037. Keep. |
| Claims of human or independent review | None found where AI review is labelled human (`README.md:22,156`, `evaluation-report.md:198,278`, `system-card.md:3`, `innovation.md:23`, D-047 state the limits). Stale 45 and 125 counts remain (B2, S8). |
| Where approval gates are missing | S5. The record shows no approver on D-029, D-032, D-041 to D-046, D-048. |
| Tests needing private data | 56 tests carry the `corpus` marker. Fresh-clone simulation (tracked files copied to a temp dir, no `.git`): one failure (`test_integrity.py::test_provenance_fingerprints`, `git_head` is `None`; attributed to the missing `.git`, not confirmed in a true clone) and one skip (`test_runtime_fixes.py:231`). To be settled by the fresh-clone check. |

## 1C. Standard-repo checklist

| Item | Status |
|---|---|
| README as entry point | Exists; needs a short top summary, a "what you can and cannot run without the private corpus" box, a repo map, licence and attribution, and the demo URL without access codes. |
| `uv.lock`, Python pin | `uv.lock` present; `requires-python = ">=3.12,<3.13"`; no `.python-version`. |
| Single entry point (`make ...`) | Missing. |
| `.env.example` documented | Present and commented; every variable has a comment. |
| Formatter, linter, type check | None configured (ruff available offline via `uvx`, 0.16.1; its defaults report 431 findings, so a scoped config is required). |
| Pre-commit | Missing. `gitleaks` 8.30.1 and `dot` are installed locally; `detect-secrets`, `pre-commit` and `mmdc` are not. |
| CI | Deploy-only workflow (S14). |
| `SECURITY.md`, `LICENSE`, `tests/README.md`, `docs/README.md`, `docs/reproduce.md` | All missing. |
| Gitleaks config | Needed: an allowlist for the 73 dataset-identifier false positives in `data/manifests/manifest_history.jsonl`. |
| Relative links | 163 Markdown files: 0 broken relative links, and 0 that resolve only to untracked local files. External links not checked (no network). |

### Required assessment deliverables

Derived from `docs/requirements-matrix.md` (18 R-rows) and the repository. The assessment PDF is not in the repository and was not re-read in this audit; the owner should compare against the PDF.

| Deliverable | Evidence file | Status |
|---|---|---|
| Source code | `src/labourlens/`, `tests/` | Present |
| Prompts | `prompts/*.md` (runtime) | Present; `prompts/meta/` optional (D1) |
| Configuration template | `.env.example`, `specs/` | Present |
| README | `README.md` | Present; rewrite planned |
| Architecture diagram | `docs/architecture.md` (mermaid) | Present as mermaid only; no rendered image (S23) |
| Data sheet | `docs/data-sheet.md` | Present; add open licence items and derived-row statement (B7) |
| Evaluation report | `docs/evaluation-report.md` | Present |
| System/model card | `docs/system-card.md` | Present |
| Innovation assessment, 1 to 2 pages | `docs/innovation.md` | Present, 1,071 words; trim or confirm page count |
| 20-minute demo plan | `docs/demo-script.md` | Present; scenario 8 not recorded (B5) |
| MCP server and client demo | `src/labourlens/mcp/`, `docs/mcp-demo-transcript.md` | Present |
| Threat tests | `docs/threat-model.md`, `experiments/threats/` | Present (T-I06 not shown stable; disclosed) |
| Requirements traceability | `docs/requirements-matrix.md` | Present; stale ordering (S3) |
| Fresh-clone proof | none | Missing at audit time |

Open licence items to state in one place (currently spread across `data-sheet.md` lines 14, 72, 85, 128-129): three assumed-open datasets (B7); no dataset page was read for the licence label on the 33 "verified" datasets; 22 MOM HTML releases with unresolved rights; the MTI 2026-Q2 feature PDF notice not read; two MOM PDFs "to re-confirm on the file"; no repository licence (B1).

## 2. Outcome (1 Nov 2026)

The findings above were worked through on the `repo-cleanup` branch. Decisions taken by the owner at the time:

| Topic | Decision |
|---|---|
| Agent instruction file and initial plan | `CLAUDE.md` kept; kick-off prompt and plan moved to `docs/process/` with a historical banner; the author's own meta prompts kept local and gitignored |
| `progress.md` | Short current-state page kept; older log moved verbatim to `docs/archive/progress-log.md` |
| Blank review sheets | Kept, with a banner pointing at the final owner review |
| Licence | All rights reserved, shared for review (`LICENSE`) |
| Officer email addresses in dataset metadata | Redacted in the committed metadata files (no hash covers them) |
| Architecture diagram | Graphviz SVG committed beside the Mermaid block |
| Live demonstration URL | Included, without access codes |
| Author name and email in history | Accepted; history not rewritten |
| Demo scenario 8 | Recorded: `artifacts/mcp-agent-demo.md` |

Status of the blockers, with evidence, is in [`../fresh-clone-check.md`](../fresh-clone-check.md) and the commit log. No frozen result, gold file, hash or experiment record was changed.
