> **Historical planning document (30 Oct 2026), written before implementation.** Statements such as "not yet approved" or "not executed" describe that date, not the current state. Current status is in [`docs/progress.md`](../../progress.md), decisions in [`docs/decisions.md`](../../decisions.md) and requirements evidence in [`docs/requirements-matrix.md`](../../requirements-matrix.md).

# LabourLens presentation plan: interactive report page

**Status:** PLAN. Decision D-010 (owner, 30 Oct 2026): the presentation is an **interactive, report-style web page** that reviewers can explore and click through themselves, in addition to the 20-minute live demo. Stack and hosting are decided at the M7 gate. Only the data export (M1) exists today.

## Audience and purpose
Reviewers of the GenAI Engineer assessment. They should be able to (a) follow the story in five minutes unaided, (b) open any number and see where it came from, (c) inspect evaluation results and failures, and (d) see the system's honest limits. Every figure traces to a validated observation, every claim to a file.

## Design principles
- A report you can explore: scroll narrative, clickable charts, evidence drawer, filters. Not a chat clone and not a slide deck in a browser.
- Dashboards follow `kpi-dashboard-design`: 5 to 7 headline KPIs, context on every number (previous quarter, year ago, unit), consistent colour meaning, drill-down to source, methodology visible, no 3D, responsive.
- Truthful before pretty: uncertainty, missing ('-') cells, unverified definitions and unresolved rights are shown, not hidden.
- Accessible: AA contrast, keyboard operable, reduced motion respected.
- One colour per concept, shared by every chart (blue = unemployment/final, red = retrenchment, teal = vacancy/dataset), as in `artifacts/figures/`.

## Page structure
| Section | Visitor can | Evidence | Milestone |
|---|---|---|---|
| 1. Question and scope | Read problem, users, scope (2024-Q1 to 2026-Q2), exclusions | ADR-001 | M7 |
| 2. The data | KPI strip; click a KPI for series, definition, source, snapshot hash | `data/export/kpis.json`, `series.json`, `sources.json` | data M1, UI M7 |
| 3. Three numbers, one quarter | Toggle advance / final / dataset totals; read why they differ | `reconciliation.json` | data M1, UI M7 |
| 4. Retrenchment deep-dive | Filter by industry level; '-' shown as gap, not zero | `retrenchments_by_industry.json` | data M1, UI M7 |
| 5. Ask the assistant | Sample questions; answer, citations, evidence drawer, tool timeline, **feedback controls** (see `docs/human-feedback-design.md`) | M3 to M5 | M7 |
| 6. How it was tested (incl. human review results and agreement) | Baseline vs improved retrieval; per-case results | M6 artifacts | M7 |
| 7. Failure gallery | Injection, abstention, tool failure, MCP errors, real transcripts | M4, M5 | M7 |
| 8. Data sheet and limits | Sources, rights per source, quality checks | `docs/data-sheet.md`, `quality.json` | data M1, UI M7 |
| 9. Where next | Innovation write-up | `docs/innovation.md` | M7 |

## Rights constraints
MOM reports are all-rights-reserved (D-001). The page shows numbers, short citations, locators and links to originals, never copied report text. Any hosted copy is private (D-007).

## What M1 delivers
- `data/export/*.json`: KPI cards, series, industry and sector tables, reconciliation, sources with rights status, quality summary. Each figure has an `observation_id` for the provenance drawer.
- `artifacts/figures/*.png`: presentation-grade static charts for the talk and README.
- `artifacts/data-quality/`: quality report and findings.
Regenerate: `uv run labourlens build && uv run labourlens export`.

## Open decisions (M7 gate)
1. Frontend stack and chart library.
2. Hosting and access control (D-007).
3. Whether to also export a static PDF/slide version for offline use.
