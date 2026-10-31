# Prompt 2: prepare the repository for submission and sharing

Paste everything below the line into a fresh Claude Code session started in the repository root. It audits the repository and produces a clean, standard, reviewer-friendly submission, with the AI-assisted development process visible and honest.

---

You are preparing the **LabourLens** repository to be submitted to, and read by, interviewers for a GenAI Engineer role. They will clone it, read the README, skim the docs, run a few commands, and judge engineering quality, scientific honesty and how systematically AI coding agents were used. Your job is to make the repository something I am proud to share, without hiding anything that matters.

## The principle that governs every decision

**Remove noise, never remove honesty.**
- Remove: secrets, private notes, scratch files, duplicated or superseded drafts, raw model outputs, anything with rights problems, stale statements, broken links, confusing structure, and internal chatter that adds nothing for a reviewer.
- Keep and present clearly: limitations, negative results, disclosed post-run edits, the fact that the gold set is mostly AI-drafted with partial owner review, the fact that AI review is not human review, unresolved licence items, and the open issues list. A reviewer who finds a hidden weakness will distrust everything. A reviewer who finds a weakness already stated, measured and explained will trust the rest.
- Never rewrite published numbers to look better. Never alter frozen results, gold files, hashes, or experiment records. Never delete a negative result. If something is embarrassing but true, move it to the right place and describe it plainly.

## Ground rules

1. **Plan first, then ask, then act.** Phase 1 is read-only. Produce the audit and a change plan, then stop and wait for my approval. Do not delete or move anything before I approve the plan. Do not rewrite git history, force-push, or delete branches without explicit approval. Prefer producing a clean export (a new directory or a `submission` branch) over destructive edits to `master`.
2. **Rights (D-001, D-004).** MOM and MTI documents, extracted text, raw model outputs and the assessment PDF must not be in the shared repository. No quote over six consecutive words from MOM or MTI in any committed file. Run `uv run labourlens rights-scan` before and after; it must report zero hits. The allowlist (`specs/rights-scan-allowlist.txt`) is reviewed line by line and each entry justified.
3. **Secrets.** Search the working tree and the full git history for keys, tokens, passwords, access codes, private hostnames or IPs that should not be public (`git log --all -p -S` for patterns such as `sk-`, `OPENAI`, `ghp_`, `BEGIN .* PRIVATE KEY`, the deploy access codes, the Droplet IP, `.env`). If anything was ever committed, tell me, and recommend history rewriting or a fresh-history export for me to approve. Never print a secret value.
4. **No paid calls** (no model runs, no embeddings, no judge). No network calls except documented reads.
5. **Tests must stay green** and nothing may be weakened to get green. Run `uv run pytest -q -m 'not corpus'` and, where `data/` exists, the corpus tests.
6. Keep British English, a plain register and no marketing language. No emojis in docs.

## Phase 1: audit (read-only). Produce `docs/submission-audit.md` as a table of findings, each with path, problem, severity (BLOCKER / SHOULD / NICE) and a proposed action.

### 1A. Inventory and classification
List every tracked file and directory (`git ls-files`, plus untracked and ignored files that exist locally). Classify each as **Ship** (core deliverable), **Ship, reorganise**, **Keep private** (gitignored or moved out), **Delete** (obsolete), or **Question** (I must decide). Cover at least: `START_HERE_PROMPT.md`, `LABOURLENS_PROJECT_PLAN.md`, `CLAUDE.md`, `Tech Challenge - GenAI Engineer v1.0.pdf`, `private/`, `study/`, `artifacts/` (including screenshots), `experiments/` (runs, eval, gold, threats, heldout, heldout-v2, human-review-sample), `docs/human-review/` (AI reviews, adjudications, e2e reviews, copy-audit), `data/` (what is tracked: manifests, snapshots, export, processed), `prompts/` (runtime prompts versus `prompts/meta/`), `scripts/`, `deploy/`, `.github/`.

### 1B. Red-flag scan (things a reviewer would read negatively)
Check and report each:
- Secrets, keys, IPs, access codes, personal data, local absolute paths (`/Users/...`), usernames, emails, machine names in committed files and in git history.
- Raw model transcripts or prompts that read as unprofessional, jokes, profanity, frustrated or adversarial chat, or text that looks like an unreviewed AI dump.
- Dead code, commented-out blocks, `TODO`/`FIXME`/`XXX`, placeholders such as `<<E2E-PENDING>>`, stubs, mocks presented as real, scaffolding words ("MVP", "v1", "foundation", "follow-up") used to hide unfinished work.
- Stale or contradictory claims across README, docs and the website (numbers, corpus versions, gold versions, "not built" for things that exist, "open" for things closed).
- Oversized or generated files that bloat the repository, binary blobs, duplicated data, build outputs, `__pycache__`, `.DS_Store`, large screenshots.
- Unclear licensing of the repository itself (no LICENSE), of the fonts (see `web/static/fonts/LICENSES.md`), and of data (Singapore Open Data Licence attribution; MOM and MTI terms). Check that attribution lines exist where required.
- Commit history hygiene: messages that are noise, giant mixed commits, commits that add and later remove sensitive files.
- Tests that pin wording or incidental behaviour (the project's rule is to delete them), flaky tests, tests that need the private corpus without a skip marker.
- Anything that suggests the AI did the thinking unsupervised. Look for places where the record should show human decisions (approval gates, owner reviews) and does not.
- Anything claiming human review, independent review, or verification that was not done.

### 1C. Standard-repo checklist (report what exists, what is missing)
- `README.md` as a true entry point: what it is, a three-line summary of results with honest caveats, quick start that works from a fresh clone **without** the private corpus, what a grader can and cannot run, repository map, links to the deliverables, licence and data attribution, live-demo URL if it should be shared (and access-code handling: never publish the codes).
- Reproducibility: pinned dependencies (`uv.lock`), Python version file, a single `make`/`just`/script entry point (`make setup`, `make test`, `make demo`, `make eval-offline`, `make lint`), a fresh-clone test run recorded as evidence, `.env.example` with every variable documented, no hidden manual steps.
- Quality gates: formatter and linter config (ruff), type check if used, pre-commit config, CI workflow that runs tests, the rights scan and a secrets scan, `CONTRIBUTING`-style notes only if useful, `SECURITY.md` with how the repo handles secrets and untrusted text.
- Required assessment deliverables mapped to files: source, prompts, configuration template, README, architecture diagram (a rendered image as well as mermaid), data sheet, evaluation report, system/model card, a separate 1 to 2 page innovation assessment, 20-minute demo plan. Build a table "PDF requirement, evidence file, status" from `docs/requirements-matrix.md` and verify each link resolves.
- Docs structure: an index (`docs/README.md`) that tells a reviewer in what order to read; ADRs; decision log; experiment records; limitations; glossary. Remove duplication.

## Phase 2: the AI-assisted development story (design the evidence, do not fabricate it)

The interviewers want to see that I used AI agents **systematically and with control**, not by pasting prompts. Plan, and after approval create, a `docs/ai-assisted-development.md` (and link it from the README) that is strictly factual and built from the repository record:

1. **Operating model**: the collaboration contract in `CLAUDE.md` (explore, compare, recommend, discuss, approve, implement, verify, document), the human approval gates (list the actual gates and dates from `docs/decisions.md` and `docs/progress.md`), and what stayed human-only (scope, ADR approval, rights decisions, owner review of gold, sign-off of the held-out freeze).
2. **Agent roster and roles**: which sub-agents were used (extraction, evaluation reports, reviewers, adversarial reviewers, source scouting, UI/presentation, review-pack builder, etc.), what each was given, what it returned. Derive from `git log`, `docs/progress.md` and the agent outputs recorded in the repo. Do not invent agents.
3. **Controls that made agent work trustworthy**: single-writer manifest, frozen results, one-factor-at-a-time rule (D-016), pre-registered held-out protocol and freeze file, hash checks between gold and runs, rights scan, threat suite, deterministic scorers, strict export schemas that reject hand-edited reviews, and the rule that AI review is never labelled human review.
4. **Independent verification loops**: independent PDF audits, e2e reviews (five areas), blind multi-reviewer AI reviews, what each found, what was fixed, and what was disputed or deferred. Link to `docs/human-review/e2e-review-summary.md`.
5. **Mistakes the process caught** (honest list from the decision log: post-run gold edits disclosed, held-out overlap, stale docs, scorer brittleness, quote leakage) and what changed afterwards.
6. **The harness** (see Phase 3) described in a few lines so the reader sees the engineering around the agents, not only the output.

Include a short, honest "How I would run this differently next time" section.

Also decide with me whether to include the agent-instruction file (`CLAUDE.md`), the planning prompts (`START_HERE_PROMPT.md`, `LABOURLENS_PROJECT_PLAN.md`) and `prompts/meta/` as visible evidence of method (my default recommendation: keep `CLAUDE.md` and a cleaned-up `docs/process/` showing the contract and gates; keep `prompts/meta/` only if it reads professionally; remove the assessment PDF).

## Phase 3: engineering harness a reviewer expects to see

Propose and, after approval, add only what is small, real and verified. Do not add decoration.

- `Makefile` (or `justfile`) with targets: `setup`, `lint`, `format`, `test`, `test-corpus`, `rights-scan`, `secrets-scan`, `docs-check` (link and anchor check), `report` (rebuild `report.json`), `serve`, `verify` (everything that runs offline from a fresh clone), `clean`.
- `.pre-commit-config.yaml` (ruff, rights-scan, a secrets scanner such as `gitleaks` or `detect-secrets`, trailing whitespace) and a CI job running `make verify`.
- A `tests/README.md` explaining markers (`corpus`, offline) and what is skipped when the private data is absent.
- `docs/reproduce.md`: exact commands from a fresh clone to each key artifact, which steps need the private corpus or an API key, expected outputs and approximate cost, and how to verify hashes.
- A fresh-clone proof: `git clone` into a temporary directory, run `make setup && make verify`, and record the exact output summary in `docs/progress.md` (or `docs/fresh-clone-check.md`).
- Architecture diagram rendered to SVG or PNG and committed (check a renderer is available; if not, say so and keep mermaid).

## Phase 4: execute (only after I approve the plan)

Work in this order, committing in small, well-named commits (`docs: …`, `chore: …`, `build: …`) on a new branch `submission-prep`; never on `master` directly:

1. Safety: secrets and rights fixes first. If history contains a secret or rights-problem file, stop and present options (history rewrite vs fresh-history export) and wait.
2. Remove or relocate noise per the approved plan (use `git mv`, keep history; move private material under gitignored `private/`).
3. Fix stale and contradictory claims. Check every number against its artifact. Run `uv run labourlens build-report` after any change that feeds the website, then the web tests.
4. Add the harness (Phase 3) and the AI-assisted development doc (Phase 2).
5. Rewrite README as the entry point. Add `docs/README.md` index, LICENSE (ask me which), attribution and the data licence statements.
6. Fresh-clone verification, then the final audit (re-run Phase 1B scans; all BLOCKERs closed).
7. Produce `SUBMISSION.md` at the repository root: what to read first (five links), how to run it (three commands), what is and is not reproducible without the private corpus, the live-demo URL (no access codes in the file; I will send them separately), and the honest limitations list in ten lines.

## Final report

End with: the list of BLOCKERs found and how each was closed; the exact commands you ran with their pass/fail output; the remaining SHOULD/NICE items; what you removed and where it went; the diff summary of the branch; anything that needs my decision (licence choice, history rewrite, live-site access codes, whether to keep specific files); and a confirmation that no published number, frozen experiment, gold file or hash was altered. Then stop. I will review the branch before it is merged or shared.

Start with Phase 1 now. Do not change any file until I approve the plan.
