> **Historical process record (30 Oct 2026).** The kick-off prompt given to the coding agent at the start of the project. Status statements in it describe that date. Current state: [`docs/progress.md`](../progress.md).
>
> Packaging note (2 Nov 2026): the planning documents named below are kept locally, not in the repository. Their path mentions are historical plain text, not public links.

# Kickoff prompt for Claude Code — LabourLens (copy everything below this line)

You are my senior AI engineering partner and technical mentor for **LabourLens**, a take-home GenAI Engineer assessment. I will use AI-assisted coding but must understand, test, present and defend every decision.

**FIRST: READ THE EXISTING PROJECT DOCUMENTS AND THE ORIGINAL ASSIGNMENT PDF.**
- `CLAUDE.md` (binding collaboration/quality instructions)
- `docs/archive/planning/01_REQUIREMENTS_AND_SCOPE.md`
- `docs/archive/planning/02_DATA_SOURCE_CATALOG.md`
- `docs/archive/planning/03_MILESTONE_1_INGESTION_PLAN.md`
- `docs/archive/planning/04_ROADMAP.md`
- `docs/archive/planning/05_EVIDENCE_AND_STUDY_PLAN.md`
- `docs/decisions/ADR-001-scope.md`
- `docs/decisions/ADR-002-langgraph.md`
- `Tech Challenge - GenAI Engineer v1.0.pdf` (or the file under `reference/` — locate it before assuming its contents)

If the original assignment PDF is absent, tell me exactly which document you need. Do not pretend you read it. The original brief supersedes the derived planning docs.

## Current decisions — ALREADY APPROVED, do not reopen without a real blocker
- Product: **LabourLens — Singapore Labour Market Intelligence**, intended for policy researchers.
- Supported analysis period: **2024-Q1 through 2026-Q2**.
- **Four structured official datasets:** quarterly resident unemployment, quarterly vacancies-to-unemployed ratio, quarterly retrenchments, and employment changes by sector (official URLs in source catalog).
- **Five official MOM documents:** full reports for 2025 Q3, 2025 Q4, 2026 Q1, 2026 Q2, plus Q2 2026 advance release.
- Key use cases: factual research, deterministic calculations, multi-source synthesis, preliminary/final revisions, ambiguity/unanswerable questions, malicious-source/prompt injection cases.
- **Architecture APPROVED:** one bounded research agent using LangGraph `StateGraph`, typed state, a small registry of validated read-only/research tools, deterministic arithmetic, citations, bounded retries/steps, observability, real MCP tool/resource, reproducible comparisons between baseline and improved retrieval. The separate ADR defines the proposal and initial limits.
- Desired UX: professional, modern and sleek policy intelligence workbench (evidence, charts, provenance, trace and evaluations). UI stack and implementation are **not yet approved**; rubric-critical evidence comes first.
- Original GenAI Engineer brief requires >=30 representative evaluation cases, experimental comparison, human review, security/MCP failure demonstrations, data sheet, eval report, model/system card, and 1–2-page innovation assessment.
- Deadline is **Wednesday, 4 November 2026, morning Singapore time**.

**Current phase: Milestone 1 PLANNING / DECISION GATE. There is NO permission to implement application code yet.** Preparing this documentation is not approval to install packages, write source files, ingest entire datasets, scaffold a frontend, invoke paid LLMs, or begin downstream milestones.

## Task for this session — do a decision-ready review of Milestone 1 ONLY
Milestone 1 is official government data ingestion, immutable provenance, schema-aware normalization, report passage extraction and data-quality evidence. You may inspect project files, consult publisher docs, inspect official dataset metadata/API schemas and small samples if that can be done safely without creating application artifacts. Do not fetch full corpora or create/modify implementation code. Clearly say what you really inspected or tested.

1. **Validate the nine-source inventory.** Confirm each official publisher/source URL; verify the most suitable published CSV/API download method for each dataset and real link to each report PDF or official HTML; document source date, schema, cadence, coverage, and rights. Verify each fact against authoritative current sources. Note failures and unresolved rights distinctly. Remember: the official PDF copyright notice is not necessarily governed by the data.gov.sg open-data licence.
2. **Compare acquisition options:** manual source download vs always-live API vs versioned official downloads + immutable snapshots. Assess freshness, reproducibility, terms, complexity, errors and fallback. Recommend an approach.
3. **Compare structured processing:** Pandas-only CSV vs SQLite vs Pandas -> Parquet -> DuckDB. Show proposed normalized observation schema and how you'll handle seasonally adjusted vs raw rates, `YYYY-MM` quarter-end dates, retrenchment text values, wide sector table, source revisions, missing values, units and sectors. Don't assume publisher column labels without checking.
4. **Compare report extraction:** basic PyMuPDF vs block/position+section aware PyMuPDF vs selective table fallback, and PDF vs official HTML for the advance release. Explain what might fail in multi-column documents, tables/footnotes, page citation mapping and licensing. Propose an extraction-quality/manual spot-check rubric.
5. **Provenance design:** propose the exact manifest, `StatisticalObservation` and `DocumentPassage` schemas, deterministic IDs, hash strategy, raw-file gitignore/right-to-redistribute policy, versioning and refresh behavior. Show one example record clearly labelled illustrative and grounded only in verified source metadata.
6. **Testing and acceptance:** propose actual tests for each adapter and source, at least 8 manual statistical spot checks and 10 manually checked passage examples, plus idempotency, malformed input, sector hierarchy, licence packaging and Q2 2026 advance/final reconciliation. State how to run checks and save raw test outputs. Do not claim tests passed until they ran.
7. **Deliverable plan:** list exact files/modules/scripts to create AFTER approval; show a 5–6 substep execution plan with order, verification and stopping criteria. Clearly separate what is in M1 from BM25, LLM, LangGraph, MCP and UI work that come later.
8. **Study and interview preparation:** propose a concise study note for this milestone (provenance vs lineage, revision management, reproducibility, seasonality, PDF pitfalls, source rights), at least 5 questions likely to be asked, and what actual evidence will substantiate our answers.
9. **Challenge assumptions critically.** Flag data semantics, ambiguous definition differences, copyright/reuse questions, dependent libraries and deadline risks; offer proportionate fallback choices.

## Reply format
1. Briefly state what you inspected and which choices are already fixed.
2. Present one **decision matrix** comparing the ingestion/normalization/document strategies with trade-offs, then your recommended combination.
3. Present the **proposed data contracts** and validation/error policies.
4. Present the milestone substeps, files, acceptance checks, evidence outputs, and known unknowns.
5. Identify **one concrete approval decision** needed from me. Finish with **STOP — awaiting Milestone 1 implementation approval**.

## Strict rules
- Do not re-plan the already-approved project domain or replace LangGraph without discussing a true blocker.
- Do not write or modify application source files, install dependencies, ingest complete datasets or proceed to subsequent milestones until I explicitly authorize Milestone 1 implementation.
- Do not turn planning into indefinite debate. Use concrete alternatives, state your recommendation and seek approval.
- Do not make up download success, test results, retrieved PDF pages, evaluation scores, costs, citations or reviewer approvals.
- Do not put full proprietary/copyright-restricted MOM PDF reports or extensive reproductions into a public GitHub submission; preserve source links, rights and reproducible local retrieval.
- Preserve real model/tool outputs and evaluation artifacts after implementation; never use fabricated results in slides or the UI.
- I want a clean, modern, demonstration-ready interface later, but first a scientifically defensible project with reliable evidence.
- After I approve implementation, work only on M1, independently test each substep, report actual commands and outputs, produce M1's data sheet/quality report/study notes, and STOP for M2 discussion.
