# How AI agents were used in this project

A factual account, built from the repository record (`CLAUDE.md`, `docs/decisions.md`, `docs/progress.md`, `docs/archive/progress-log.md`, `docs/human-review/`, `experiments/`). Where the record is silent, this page says so instead of filling the gap.

**In one paragraph.** The code, experiments and documents were written with a coding agent (Claude Code) working under a written contract. The agent proposed; the owner decided at named gates. Evaluation ran under pre-declared rules with frozen results, hash checks and deterministic scorers. Other AI agents reviewed the work, blind where stated, and were labelled as AI. One human, the owner, reviewed the gold labels and sources after the saved runs were scored. That review is one person's and is not independent evidence.

## 1. Operating model

`CLAUDE.md` is the agent's standing instruction. Its core is a sequence the agent may not skip: explore, compare, recommend, discuss, approve, implement, verify, document. At each decision the agent presents two to four options (including a plain baseline), states trade-offs and one recommendation, then stops for the owner. Other binding rules:

- Mark every statement as REQUIREMENT, VERIFIED FACT, ASSUMPTION, PROPOSAL, DECISION or MEASURED RESULT; never fabricate an experiment result, citation or cost.
- Work within an approved phase; do not widen scope, change key dependencies or start the next phase without approval.
- Resumability: any agent may be interrupted, so state lives in files (`docs/progress.md` first), with claims, handoff notes and a log updated at each substep.
- Published (`docs/`) versus private (`study/`, `private/`, gitignored).
- Numerical answers come from deterministic calculation on validated records, not from the model.

### Human approval gates in the record

From `docs/decisions.md`, `docs/progress.md` and the freeze file. The quoted words are the owner's replies as recorded there.

| Date (2026) | Gate | Record |
|---|---|---|
| 30 Oct | Domain, scope, single bounded LangGraph agent (ADR-001, ADR-002); private repository; published/private split (D-001, D-002) | `docs/decisions.md` |
| 30 Oct | Structured-data expansion ("Okay agreed", D-003); implement Milestone 1 ("I approve", D-005); corpus expansion ("Yes I approve", D-006, D-019, D-020) | `docs/decisions.md` |
| 30 Oct | Report page, BM25 persistence, managed Postgres direction, DigitalOcean, chunking, experiment policy, gold authoring (D-010, D-012 to D-017) | `docs/decisions.md` |
| 30 Oct | Hosted embeddings, model chosen by experiment (D-021, D-022); answer format, abstention policy, three tools, MCP scope (D-024, D-026 to D-028); supported period as a hard scope (D-031) | `docs/decisions.md` |
| 31 Oct | Post-run label corrections, each approved before it was applied: HO-029 ("Okay", D-034), three more ("Yes", D-035), HO-022 and DEV-018 ("Yes I confirm", D-036) | `docs/decisions.md`, `experiments/gold/CHANGELOG.md` |
| 31 Oct | Adopt the extraction fixes (D-037); source-conflict guard, held-out v2 design, labour-only sources (D-038 to D-040) | `docs/decisions.md` |
| 31 Oct, 13:19 UTC | Held-out v2 freeze signed: 65 cases approved unchanged, 59 by the owner's own click and 6 by agreeing with an AI suggestion | `experiments/heldout-v2/FREEZE.md` |
| 1 Nov | Final owner review: 403 items decided by own click (268 gold cases, 65 held-out v2 cases, 40 saved answers, 30 source checks); source-check acceptance with disclosed extraction gaps | `docs/human-review/owner-review-final-summary.md` |
| 1 Nov | Policy for out-of-period questions; four owner "change" clicks recorded and not applied (D-047) | `docs/decisions.md` |

Decisions from D-041 onward that name no approver (corpus v2 as working corpus, end-to-end fixes, X2, tool set v2 and its rejection) are marked in the log as assistant decisions within the experiment protocol (D-016), open to reversal. D-030 (default retrieval configuration) has no recorded owner confirmation. This is stated at the top of the decision log.

### What stayed human-only

Scope and ADR approval; rights decisions (D-001, D-004: what may be committed, no MOM or MTI text); the review of gold labels and source checks; the signature on the held-out v2 freeze; the choice to treat the extraction gaps as accepted limits (J10); the decision not to apply the four D-047 clicks; and the decision to adopt or reject a configuration (the agent measured, the owner decided).

## 2. Agents and roles

Only roles that the record names. The commit log (90 commits on `master`, 30 Oct to 1 Nov) does not label which agent wrote which commit, so code-writing roles cannot be itemised beyond "the coding agent".

| Role | Used for | Evidence |
|---|---|---|
| Coding agent (Claude Code) | Ingestion, retrieval, agent, MCP, evaluation, web app, documents, under `CLAUDE.md` | `CLAUDE.md`, the whole log |
| Gold-drafting sub-agent | First 50 gold cases at M2 | `docs/archive/progress-log.md` |
| AI pre-reviewers of gold (ReviewGoldBase, A, B, C; Review2B; ReviewV3) | Review draft labels before the owner saw them | `experiments/gold/ai-review*/` |
| AI pre-reviewers of source checks (ReviewSpotPassage, ReviewSpotStats, ReviewSpotMeta) | Pre-review of the 30 source checks | `docs/human-review/ai-pre-review-*`, `ai-verification-of-pre-reviews.md` |
| Blind independent reviewers | Saved answers, gold and M1 sources, with no earlier opinion shown | `docs/human-review/independent-ai-review-m1*.md`, `experiments/human-review-sample/independent-ai-review*.md`, `experiments/gold/independent-ai-review*.md` |
| AI adjudicator | Third pass over disagreements; not blind | `docs/human-review/ai-adjudication.md` |
| Five end-to-end reviewers | Data, runtime and answer path, evaluation, security and deployment, deliverables | `docs/human-review/e2e-review-summary.md` |
| Held-out v2 reviewers A, B, C | Review of the 65-case draft before the owner | `docs/human-review/heldout-v2-ai-review-summary.md` |
| Fresh blind queue reviewers (two per case) | Cards the owner had not yet decided | `owner-review-final-summary.md`, `review-inventory.md` |
| Site-artefact reviewer | Review of the report site and deck copy (the record is kept privately) | `docs/human-review/review-inventory.md` |
| Read-only audit agents (four) | The repository audit that preceded this tidy-up | `docs/process/repository-audit.md` |

The reviewers are one model family, so agreement among them is not independent evidence, and none of this is human review. Each file says so at the top.

## 3. Controls that made agent work checkable

| Control | What it does | Where |
|---|---|---|
| One-factor-at-a-time rule (D-016) | An experiment changes one thing; combined changes are labelled as regression checks, not ablations (X2 is labelled so) | `docs/decisions.md` D-016, D-044 |
| Pre-registered held-out protocol and freeze files | Gold, rule, code and data hashes fixed before the run; the held-out v2 rule was revised once, before any run (D-042) | `experiments/heldout/`, `experiments/heldout-v2/FREEZE.md` |
| Hash checks between gold and runs | `eval` and `paired` refuse a gold file whose SHA-256 differs from the one recorded with the run unless an explicit flag is passed | `src/labourlens/evaluation/` |
| Frozen results | Old gold versions archived byte for byte; `agent-exp` refuses to overwrite an existing experiment without `--force` | `experiments/gold/archive/`, `src/labourlens/agent/experiments.py` |
| Deterministic scorers | Calculation, citation, status and number checks do not use a model; the LLM judge covers support and fact coverage only and is reported separately | `src/labourlens/evaluation/` |
| Manifest written by one code path | All source records and hashes come from `raw_store`; there is no lock against two writers (e2e finding P2-2, deferred) | `src/labourlens/data/raw_store.py` |
| Rights scan | Fails if a tracked file repeats more than six consecutive words of local MOM or MTI text; needs the private corpus | `uv run labourlens rights-scan` |
| Threat suite | 36 hand-written adversarial cases with a no-defence baseline | `experiments/threats/`, `docs/threat-model.md` |
| Strict review export schema | The importer validates the owner's export and rejects hand-edited or incomplete files; gold is never edited by the importer (it writes a new version) | `src/labourlens/review/` |
| AI is never labelled human | Review files carry their reviewer type; summaries count owner clicks, agreements with AI and AI passes separately | `docs/human-review/` |

## 4. Independent verification loops

- **Independent PDF audits** of extraction (second blind source review, extraction boundary): found extraction errors and a vacancy-unit error in industry and occupation series; fixed, corpus v2 built (D-037). Re-measured: no measurable change in dev accuracy (0.886 versus 0.903).
- **Blind multi-reviewer AI reviews of gold:** led to the post-run label corrections D-034 and D-035; D-036 followed the owner's per-card review. Each is disclosed with its sensitivity analysis (`experiments/gold/CHANGELOG.md`, `docs/evaluation-report.md`).
- **Five end-to-end reviews (31 Oct 2026):** 0 P0 and 4 to 7 P1 findings per technical area, 3 P0 in the deliverables review. Statuses: [`e2e-review-summary.md`](human-review/e2e-review-summary.md). Fixed examples: validated citations dropped in the web result, no model deadline, a stale data sheet, `agent-exp` able to overwrite frozen runs, `paired` ignoring the gold hash, a p95 computed one rank low. Narrowed: fabricated numbers passing as answered (wider soft check, not a hard error, because that needs a development re-run). Deferred with reasons: for example round-two planner failure discarding evidence, near-zero recall of the cross-check, the fetch writer lock. Disputed: some findings were narrowed after checking against the code.
- **Owner review (1 Nov 2026):** all 403 items, one reviewer, after the saved runs were scored; gold v3.7 records it as provenance fields only. A comparison of the judge with the owner's 40 answer verdicts is in `docs/human-review/judge-vs-owner.md`.

## 5. Mistakes the process caught

| What went wrong | How it was found | What changed |
|---|---|---|
| Gold labels were edited after a held-out run (HO-029, three more, HO-022 and DEV-018) | Blind AI review, then owner review | Each edit approved, versioned (v3.3 to v3.5), the run re-scored beside the original, all versions kept; the held-out result is reported as not demonstrated |
| Held-out set shared evidence with development (25 of 31 cases) | Evidence audit | Held-out v2: 65 cases on six new sources no earlier case cites, pre-registered rule, separate result; still not pooled |
| The first indirect-injection threat result (R3 36/36) was invalid: the poisoned fixture omitted candidate lists, so six attacks never reached the model | Review of the threat fixture | Fixture corrected, rerun, earlier result marked invalid, and a rule that an attack counts only if the poison reached the evidence |
| Stale scoring caches and a calculation parsing bug briefly gave a wrong calculation score (8.3% transient) | Re-derivation in e2e review | Input-fingerprinted caches; corrected calculation score 75.0% [58.3%, 91.7%] stated beside the superseded figure |
| T-I06 (a planted false figure) fails or passes depending on run and an exact-string scorer | Final-code threat run | The strict result is kept, the refined scorer is labelled post hoc, the scorer was not changed after the failure; reported as not shown stable |
| Review wording drifted across documents (45 reviewed, 125 cards, 403) and planning drafts read as current status | e2e deliverables review and the repository audit | Banners, one summary of record, archive folder; `docs/process/repository-audit.md` lists what was changed |
| Quoted source text ended up in judge notes and review outputs | Rights scan | Over-long runs cut to six words after scoring; counts in `experiments/rights-truncation-sidecar.json`; those files are no longer byte-identical to the run |
| Tool set v2 (arithmetic on report figures) did not help | Its adoption criteria were declared before the run | Not adopted (D-048); the large gain on the held-out v2 questions is labelled a post-freeze diagnostic, optimistic by construction |
| An AI reviewer's search printed the contents of the local `.env` into its own session output | Its own report | Nothing committed; the report notes the exposure and that the key should be rotated if that transcript is retained |

## 6. The engineering around the agents

`make verify` (lint, 782 offline tests, docs link and anchor check, rights scan, secret scan) runs from a fresh clone without the private corpus, an API key or a paid call. CI runs it on every pull request, with gitleaks over the full history. Hashes of frozen gold and data files are checked by tests and by `eval`. `docs/reproduce.md` lists each artefact, what it needs and what it costs; `tests/README.md` says what is skipped without private data. Fresh-clone evidence: [`fresh-clone-check.md`](fresh-clone-check.md).

## 7. How I would run this differently next time

1. **Build the disjoint held-out set first.** The original held-out set shared evidence with development, so its result could not support a generalisation claim; held-out v2 repaired that later, at the cost of a second round.
2. **Record each approval when it happens.** Several decisions after D-040 carry no approver line. A one-line "approved by" entry at the time costs nothing and removes the doubt.
3. **Fix scorers before running, including the tricky strings.** The T-I06 scorer's exact-string check and the refined scorer written afterwards are the weakest part of the threat evidence.
4. **Review the labels before the runs, not after.** The owner review happened after the saved runs were scored, so it cannot be blind to model output and no label change could be applied cleanly.
5. **Generate review-state wording from one file.** The same facts (how many items, by whom) were retyped in many documents and drifted.
6. **Keep fewer long documents.** The evaluation report, system card and README repeat the same version history; one home and links would have been easier to keep true.
7. **Check rights on every committed text file from the first commit,** not by a scan added late; the truncation of judge notes after scoring is a cost of starting late.
