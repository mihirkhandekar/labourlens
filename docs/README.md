# Documentation index

Read in this order. Everything here is dated; where a later document supersedes an earlier one, the earlier one says so at the top.

## Start here

1. [`../README.md`](../README.md): what the system is, headline results with caveats, how to run it.
2. [`architecture.md`](architecture.md): components, data flow, agent graph, guardrails ([diagram](img/architecture.svg)).
3. [`evaluation-report.md`](evaluation-report.md): design, baselines, results, error analysis, the post-run edits and limits. The single home of the version history.
4. [`experiments/m7-heldout-v2-result.md`](experiments/m7-heldout-v2-result.md): the pre-registered held-out comparison and its inconclusive outcome.
5. [`human-review/README.md`](human-review/README.md) and [`human-review/owner-review-final-summary.md`](human-review/owner-review-final-summary.md): what was reviewed, by whom, and what that does not show.
6. [`threat-model.md`](threat-model.md): attacks tested, controls, residual risk.
7. [`agent-logs.md`](agent-logs.md): how AI agents were used, the approval record, the controls, the mistakes caught.

## The rest

| Topic | Documents |
|---|---|
| Requirements and traceability | [`requirements-matrix.md`](requirements-matrix.md) |
| AI-assisted development | [`ai-assisted-development.md`](ai-assisted-development.md), [`agent-logs.md`](agent-logs.md) |
| Data | [`data-sheet.md`](data-sheet.md), [`data-processing-log.md`](data-processing-log.md), [`storage.md`](storage.md), [`adding-sources.md`](adding-sources.md) |
| Model and system | [`system-card.md`](system-card.md), [`concepts.md`](concepts.md), [`audit-and-logging.md`](audit-and-logging.md), [`innovation.md`](innovation.md) |
| MCP | [`mcp-demo-transcript.md`](mcp-demo-transcript.md), [`../artifacts/mcp-agent-demo.md`](../artifacts/mcp-agent-demo.md) |
| Demonstration | [`demo-script.md`](demo-script.md): 28 main slides, 42 total; Summary on slide 28, appendix index on 29, references A to M. Current-build detail remains on slide 11. |
| Decisions | [`decisions.md`](decisions.md) (log, with approvals), [`decisions/`](decisions/) (ADR-001 scope, ADR-002 LangGraph, ADR-003 structured data) |
| Experiments | [`experiments/`](experiments/) (one record per experiment; raw scores in `../experiments/`) |
| Operations | [`deploy.md`](deploy.md), [`security-review-web.md`](security-review-web.md), [`../SECURITY.md`](../SECURITY.md) |
| Reproducing | [`reproduce.md`](reproduce.md), [`fresh-clone-check.md`](fresh-clone-check.md), [`../tests/README.md`](../tests/README.md) |
| State and history | [`progress.md`](progress.md) (current state), [`archive/progress-log.md`](archive/progress-log.md), [`archive/planning/`](archive/planning/) (pre-implementation drafts), [`process/`](process/) (initial plan and prompt, repository audit), [`glossary.md`](glossary.md) |
