# Documentation index

Read in this order. Everything here is dated; where a later document supersedes an earlier one, the earlier one says so at the top. Documents use plain names for experiments ("the first run", "the 65 fresh questions", "filter then rerank"); the [glossary](glossary.md) maps each to the internal id used in folder and file names.

## Start here

1. [`../README.md`](../README.md): what the system is, headline results with caveats, how to run it.
2. [`architecture.md`](architecture.md): components, data flow, agent graph, guardrails ([diagram](img/architecture.svg)).
3. [`evaluation-report.md`](evaluation-report.md): starts with a plain-language summary; then design, baselines, results, error analysis, the post-run edits and limits. The single home of the version history.
4. [Fresh-questions result](experiments/m7-heldout-v2-result.md): the pre-registered comparison on the 65 fresh questions and its inconclusive outcome.
5. [`human-review/README.md`](human-review/README.md) and [`human-review/owner-review-final-summary.md`](human-review/owner-review-final-summary.md): what was reviewed, by whom, and what that does not show.
6. [`threat-model.md`](threat-model.md): attacks tested, controls, residual risk.
7. [`ai-assisted-development.md`](ai-assisted-development.md): how AI agents were used, the approval record, the controls, the mistakes caught.

## The rest

| Topic | Documents |
|---|---|
| Requirements and traceability | [`requirements-matrix.md`](requirements-matrix.md) |
| AI-assisted development | [`ai-assisted-development.md`](ai-assisted-development.md) |
| Data | [`data-sheet.md`](data-sheet.md), [`data-processing-log.md`](data-processing-log.md), [`storage.md`](storage.md), [`adding-sources.md`](adding-sources.md) |
| Model and system | [`system-card.md`](system-card.md), [`concepts.md`](concepts.md), [`audit-and-logging.md`](audit-and-logging.md), [`innovation.md`](innovation.md) |
| MCP | [`mcp-demo-transcript.md`](mcp-demo-transcript.md), [`../artifacts/mcp-agent-demo.md`](../artifacts/mcp-agent-demo.md) |
| Demonstration | [`demo-plan.md`](demo-plan.md): 20-minute agenda, guaranteed demonstrations, questions, fallbacks and requirement coverage. |
| Decisions | [`decisions.md`](decisions.md) (dated log with approvals; entry ids such as D-056 are explained in the [glossary](glossary.md)), [`decisions/`](decisions/) (architecture decision records: scope, LangGraph, structured data) |
| Experiments | [`experiments/`](experiments/) (one record per experiment; raw scores in `../experiments/`) |
| Operations | [`deploy.md`](deploy.md), [`security-review-web.md`](security-review-web.md), [`../SECURITY.md`](../SECURITY.md) |
| Reproducing | [`reproduce.md`](reproduce.md), [`../tests/README.md`](../tests/README.md); dated fresh-clone working record kept locally, not in the repository |
| State and history | [`progress.md`](progress.md) (current state), [`process/`](process/) (initial plan and prompt), [`glossary.md`](glossary.md); superseded planning and progress logs kept locally, not in the repository |
