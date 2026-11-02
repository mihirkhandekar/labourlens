# AI-assisted development

## What AI did and what the owner owns

LabourLens was built with Claude Code and AI review passes: agents drafted implementation, experiments, reference labels and documents under a written collaboration contract. The owner remains responsible for the submission. Recorded owner approvals and inputs are not the same as agent recommendations, and AI review is not human review. The intended sequence was explore, compare, recommend, discuss, approve, implement, verify, document; the deviations below mean this is a contract, not evidence that it was always followed. Sources: `CLAUDE.md`, [decision log](decisions.md), [review inventory](human-review/review-inventory.md).

There are **403 recorded confirmations/sign-offs**, across 268 gold questions, 65 fresh questions, 40 saved answers and 30 source checks, not 403 independent verifications. The recorded confirmations were fast; the detailed timing audit is kept locally, not in the repository. The interface's `owner_manual` label records input, not reading or cognition. Stronger human evidence is the first pack's 17 answer verdicts, J1–J10 and three gold cards, plus written policy decisions. Public evidence: [final owner summary](human-review/owner-review-final-summary.md), `experiments/gold/gold_v3.7-final-provenance.json`.

## Recorded decision gates

Dates and approvals below are those attributed in repository records, not independently authenticated transcripts. Agents prepared alternatives and recommendations; this was not human-only preparation. Evidence: [decision log](decisions.md), [ADRs](decisions/), [signed freeze](../experiments/heldout-v2/FREEZE.md).

Historical progress logs, planning drafts, repository/submission/fresh-clone audits, the owner-review guide and detailed numbers audit are kept locally, not in the repository. Path mentions below identify those working records, not downloadable public evidence. They were public until this packaging change and remain in Git history. The public [demo plan](demo-plan.md) replaces the full rehearsal script, retained only in local study notes. [D-067](decisions.md#d-067---public-deliverables-and-local-working-material-owner-decision-2-nov-2026) records the boundary; this document is the canonical AI-development account, replacing the removed agent-logs pointer.

| Date, 2026 | Recorded owner contribution | Record |
|---|---|---|
| 30 Oct | Domain, answer period and bounded LangGraph architecture | ADR-001, ADR-002, D-000 |
| 30 Oct | Private visibility and source-text boundary; structured expansion and M1 implementation | D-001–D-006; D-005 records “I approve” |
| 30 Oct | M2 start, chunking, experiment protocol, AI-drafted/owner-reviewed gold and expansion cap | D-012–D-020; `docs/archive/progress-log.md` |
| 30 Oct | Hosted embeddings and passage processing acceptance, answer format, abstention, tools, MCP and hard period scope | D-021–D-031; D-022 is owner risk acceptance, not publisher permission |
| 31 Oct | Run original held-out before human review, then approve five held-out case corrections and DEV-018 after outcomes | D-033–D-036; `experiments/gold/CHANGELOG.md` |
| 31 Oct | Extraction fixes, conflict guard, fresh-source design and labour-only expansion | D-037–D-040 |
| 31 Oct, 13:19:56.904 UTC | Sign unchanged 65-case v2 gold: 59 own inputs, six agreements with AI | `experiments/heldout-v2/FREEZE.md`; signing metadata is not rewritten by later redo |
| 31 Oct / 1 Nov | J1–J10, extraction-limit acceptance and final recorded confirmations | `docs/human-review/owner-review-summary.md`, `owner-review-final-summary.md` |
| 1 Nov | Retain four change-clicks without applying them under period policy | D-047; `experiments/gold/gold_v3.7-review-log.jsonl` |
| 1–2 Nov | Final reruns, default and mean-of-two reporting; amendment before replicate scoring, though generation was underway | D-055, D-056, D-061; `docs/experiments/fin2-replicate.md` |
| 2 Nov | Public repository visibility, preserving the private-content boundary | D-057; visibility is not legal clearance |
| 2 Nov | Served-chain/retrieval/scorer measurements and second-family judge, including continuation amendment | D-058–D-062; `docs/experiments/second-judge.md` |
| 2 Nov | Submission audit fixes and truthful control/disclosure wording | D-064 |

Configuration selection was **not universally human-only**. D-030 records an assistant-selected default with owner confirmation pending; later D-056/D-061 choices do not retrospectively approve it. D-007 has no single approval recorded, and later assistant decisions under D-016 are delegated discretion, not newly inferred owner gates. Evidence: `docs/decisions.md`, introductory provenance note and D-007/D-016/D-030/D-056/D-061.

## Evidenced development roles

Names below identify logged roles or output artefacts, not independently proven people, model identities or per-commit authorship. The running product is one bounded research agent, not this development roster: [ADR-002](decisions/ADR-002-langgraph.md), `src/labourlens/agent/graph.py`.

| Role evidenced in the record | Assignment/output | Evidence path |
|---|---|---|
| Coding agent, Claude Code | Implementation, experiments and documents | `CLAUDE.md`; `docs/archive/progress-log.md` |
| Gold drafting; GoldFixer | Initial reference questions; hard-period gold corrections | `docs/archive/progress-log.md`; D-017 |
| ReviewGoldBase/A/B/C, Review2B, ReviewV3 | Successive gold pre-reviews | `experiments/gold/ai-review/`, `ai-review-2/`, `ai-review-3/` |
| ReviewSpotPassage, ReviewSpotStats, ReviewSpotMeta | Source sample pre-reviews and cross-check | `docs/human-review/ai-pre-review-passage-spot-check.md`, `ai-pre-review-statistical-spot-check.md`, `ai-verification-of-pre-reviews.md` |
| Blind source, gold and answer reviewers; AI adjudicator | Defects, disagreements and non-blind adjudication | `docs/human-review/independent-ai-review-m1.md`, `ai-adjudication.md`; `experiments/human-review-sample/` |
| Extraction-fixes worker; SourceScout; HeldoutDesign | Parser repair, source scouting, fresh-source design | `docs/experiments/m7-extraction-fixes.md`, `m7-corpus-v3-runbook.md`; `docs/archive/progress-log-2.md` |
| Five e2e reviewers; EvalFix/DataFix/DocsFix attributions | Data, runtime, evaluation, security and deliverables; repairs | `docs/human-review/e2e-review-summary.md`; `docs/experiments/m7-e2e-fixes.md`, `m7-eval-fixes.md` |
| Held-out-v2 A/B/C; PendA/PendB; review-pack builder role | Blind pre-freeze/queue passes and review UI/imports | `docs/human-review/heldout-v2-ai-review-summary.md`, `owner-review-final-summary.md`; `src/labourlens/review/` |
| UI/deck role, DeckReport, DocsPass; site reviewer; audit agents | Presentation/report integration and read-only audits | `docs/archive/progress-log-2.md`; `docs/process/repository-audit.md`; site scratch record remains private |
| XJudge | Second-family judge integration and continuation checks | `docs/experiments/second-judge.md`; `docs/archive/progress-log-2.md` |

Earlier blind reviewers were one model family: withholding previous opinions does not create independent human evidence. The adjudicator saw earlier reviews and was not blind. The later Anthropic judge is a different-family AI sensitivity check, not a human panel. Evidence: `docs/human-review/ai-adjudication.md`, `heldout-v2-ai-review-summary.md`, `docs/experiments/second-judge.md`.

## Controls: enforcement and limits

| Control | Enforced behaviour and remaining boundary | Source |
|---|---|---|
| Review exports | Strict types, known IDs, source-input hashes and AI-basis consistency reject malformed, stale and inconsistent exports. A schema-valid manual change to verdict, name or timestamp is not authenticated; hashes identify supplied bytes, not human authorship or reading. | `src/labourlens/review/pending.py`, `heldout_v2.py`; `tests/test_pending_review.py`, `tests/test_heldout_v2_review.py` |
| Freeze | `v2-run` requires a signed marker and matching gold hash. It does not recheck corpus, prompt, price or guard environment at execution; direct `agent-exp` bypasses this wrapper. Approval compares available file hashes anywhere in freeze text and can omit absent inputs. Operators must still verify runtime identity. | `src/labourlens/review/heldout_v2.py`; `experiments/heldout-v2/FREEZE.md` |
| Results | Archival gold hashes are checked; `agent-exp` requires explicit force for an existing ID. Audit-fix overwrite guards are described below, not retroactively attributed to earlier runs. Gold/run mismatch checks require an explicit override. Hashes do not establish gold correctness. | `src/labourlens/agent/experiments.py`; `evaluation/harness.py`, `paired.py`, `retrieval/experiments.py`, `retrieval/experiments_dense.py`; `tests/evaluation/test_guards.py` |
| Cache | Judge fingerprints include question, expected facts/behaviour, answer/evidence and judge prompt/model. Historical embedding/rerank cache gaps are separately disclosed. | `src/labourlens/evaluation/harness.py`; `tests/evaluation/test_integrity.py`; `docs/experiments/retrieval-v31-rerun.md` |
| Manifest | Sorted serialisation is centralised, but there is no lock, compare-and-swap or atomic replace. Single-writer operation is policy, not mutual exclusion. | `src/labourlens/data/raw_store.py`; historical e2e data P2-2 |
| Rights scan | Exact-word overlap against local passages, with numeric, suffix, size and 21 allowlist exclusions. Without corpus it says NOT CHECKED and normally exits zero, including fresh-clone CI. Not permission, a history scan or complete copyright enforcement. | `src/labourlens/data/rights_scan.py`; `specs/rights-scan-allowlist.txt`; [data-sheet section 9](data-sheet.md#9-open-licence-items-and-what-the-rights-scan-covers) |
| Experiments and threats | D-016 one-factor-at-a-time is policy, not a general automatic validator; X2 is multi-factor regression. Poison-delivery checks and exercised-only denominators are code-backed; the repeated 36-case suite is not adaptive security validation. | `docs/decisions.md`, D-016/D-044; `src/labourlens/security/threat_suite.py`; `tests/test_security.py` |
| Engineering | Locked install, offline/corpus test split, docs checks and secret-path/history checks exist. A fresh-clone scan cannot certify absent source text; CI configuration is not an observed CI result. | `Makefile`, `.github/workflows/ci.yml`, `tests/README.md`; dated clone evidence kept locally, not in the repository |

## Verification loops and current dispositions

These are recorded outcomes, not new model runs or independent human judgements. Evidence paths distinguish finding, repair and measurement.

| Loop or mistake | What changed | Current disposition / limit |
|---|---|---|
| PDF/unit audit | Fixed vacancy units and extraction faults; evidence-ID migration recorded | X1 did not demonstrate answer-quality improvement; table semantics remain limited. `docs/experiments/m7-extraction-fixes.md`, `docs/human-review/ai-adjudication.md` |
| Gold/answer review | Five held-out case corrections plus DEV-018 approved after outcomes; old versions retained | Cannot restore untouched confirmatory labels. Original test shares evidence with development; v2 uses fresh sources but later repeats reuse known cases. `experiments/gold/CHANGELOG.md`, `docs/evaluation-report.md` |
| Answer adjudication | Reconciled conflicting AI opinions against source evidence | Two passes used A1 versus A3 answers: no identical answer objects across six shared IDs, so cross-ID agreement is not inter-rater reliability. Consensus did not itself implement fixes. `docs/human-review/ai-adjudication.md` |
| Five e2e areas | Fixed citation projection, provider-shape errors, deadline, feedback ownership, audit identity, gold checks and p95 | Fetch lock, planner-failure design, cross-check recall, whole-claim rewrite and lenient calculation scoring remain deferred/disclosed. [Historical ledger with later dispositions](human-review/e2e-review-summary.md), `docs/experiments/m7-e2e-fixes.md`, `m7-eval-fixes.md` |
| Poison/scorer failures | Repaired six attacks that never reached evidence; kept original v1 scoring and declared v2 before fresh generation | Old 36/36 is invalid injection evidence. Fresh 2 Nov arms all 35/36; T-I06 unstable. `docs/threat-model.md`, D-030/D-060/D-061 |
| Numbers and repeatability | Corrected status-only metric wording and rapid-confirmation claims; mean of two runs rather than best run | No demonstrated test-set rerank gain; two runs do not estimate variance. `docs/human-review/numbers-audit.md`, `experiments/eval/final-mean.json` |
| Second-family judging | Saved-answer sample and explicit omitted pairs | Support gains remain judge-dependent; 117 valid pairs, not all planned pairs or independent truth. `docs/experiments/second-judge.md`, D-062 |
| Tool set v2 | Built deterministic report-value arithmetic, tested declared criteria | Failed development adoption criteria, not adopted; reused-v2 gain is optimistic diagnostic. `docs/experiments/m7-tool-fix.md`, D-048 |
| Rights and secrets | Shortened rights-bearing committed text after scoring; recorded reviewer-session `.env` exposure | 35 files no longer byte-exact; history retains pre-truncation text. No proof of rotation. Three assumed-licence datasets still have derived rows committed. `experiments/rights-truncation-sidecar.json`, `docs/data-sheet.md`, `docs/human-review/e2e-review-security-deploy.md` |
| Submission audit | Corrected current-versus-history claims, guaranteed demo slots and generated owner-review wording; tightened output/lifecycle controls | Late safeguards do not govern earlier runs retrospectively or remove rights, leakage, anchoring and scorer limits. D-064; `src/labourlens/review/pack.py` |

## Reproduction and ownership

Use `make verify` for the supported offline workflow; corpus-dependent work has separate prerequisites in [reproduction](reproduce.md) and `tests/README.md`. Saved command outcomes are dated in the fresh-clone working record, kept locally, not in the repository; they are not a timeless test total. Private report text, raw answers and caches are not supplied by package installation. The repository does not prove interview rehearsal, completion of tutoring or owner understanding: the author must still explain an answer end-to-end, one metric and one meaningful failure. Evidence: [demo plan](demo-plan.md), [requirements matrix](requirements-matrix.md), `docs/process/START_HERE_PROMPT.md`.

## How I would run this differently next time

These are proposed lessons, not claims of work already performed.

1. I would reserve evidence-disjoint questions and review a feasible smaller sample before the first run, rather than repair overlap and labels afterwards. Basis: D-033–D-036; `experiments/heldout-v2/evidence-audit.json`; timing audit section 3.
2. I would record approval or delegated discretion immediately, rather than let assistant selections look like owner decisions. Basis: D-007/D-030 and the decision-log provenance note.
3. I would require new output destinations across generation, scoring and paired analysis from the start, and check named runtime fingerprints immediately before execution. Basis: `src/labourlens/evaluation/`, `review/heldout_v2.py`; D-064 guards are late fixes.
4. I would test scorers, cache identity and attack delivery before paid runs, keeping later scoring changes as new diagnostics. Basis: `tests/evaluation/test_integrity.py`, D-030/D-060, `docs/experiments/retrieval-v31-rerun.md`.
5. I would call rapid confirmation sign-off, hide AI suggestions for a smaller genuine human assessment, and document what was inspected. Basis: `docs/human-review/numbers-audit.md`, `owner-review-final-summary.md`.
6. I would scan rights-bearing text earlier, minimise reviewer access to secrets and generate review-state summaries from one source. Basis: `experiments/rights-truncation-sidecar.json`, `docs/human-review/e2e-review-security-deploy.md`, `docs/process/repository-audit.md`.
