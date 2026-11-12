# Requirements matrix

This table maps each requirement in the assessment PDF (Section 1 core requirements, demonstration scenarios and submission requirements, plus the Section 2 innovation assessment) to evidence in this repository. Last updated 4 November 2026.
`Done` means working evidence exists. The Limit column says what a reviewer should still know. The previous full matrix is kept as [detail](reference/requirements-matrix-detail.md). Dated decisions are in [decisions](decisions.md).

## Core requirements

| Requirement | Evidence | Status | Limit |
|---|---|---|---|
| 1 Problem framing, baseline, leakage-safe split | [Scope ADR](decisions/ADR-001-scope.md), [BM25 baseline](experiments/m2-bm25-baseline.md), [evaluation report](evaluation-report.md), [freeze](../experiments/heldout/FREEZE.md) | Done | AI-drafted gold signed off by one reviewer after the runs; original test questions share evidence with development |
| 2 Data preparation and EDA | [Data sheet](data-sheet.md), [quality report](../artifacts/data-quality/quality-report.md), [EDA findings](../artifacts/data-quality/eda-findings.md), [notebook](../notebooks/01_data_and_eda.ipynb) | Done | Source rights and dataset licences unverified; an outsider cannot rebuild the report corpus; a fresh data fetch fails the pinned contracts |
| 3 Retrieval-augmented generation | [Retrieval code](../src/labourlens/retrieval/), [hybrid study](experiments/m3-dense-hybrid.md), [retrieval study](experiments/m6-retrieval-improvements.md) | Done | Retrieval gains (strict hit@8) show no demonstrated gain in answers on the fresh 65 questions; report-only arithmetic is weak |
| 4 Models and controlled configurations | [Generation study](experiments/m3-answer-generation.md), [prompts](../prompts/), [prices](../specs/prices.yaml), [final mean](../experiments/eval/final-mean.json) | Done | Reruns are not bit-identical (no seeds set); the served system differs from the evaluated one |
| 5 Bounded agent with deterministic tools | [Agent code](../src/labourlens/agent/), [ADR-002](decisions/ADR-002-langgraph.md), [agent study](experiments/m4-agent.md), [fixed-pipeline comparison](../experiments/eval/agent-vs-fixed-pipeline.json) | Done | Gain over the fixed pipeline is on development questions only, from one fixed run; full-set runs call tools directly, not through MCP |
| 6 Evaluation and error analysis | [Gold v3.7](../experiments/gold/gold_v3.7.jsonl) (268 cases), [evaluation report](evaluation-report.md), [second judge](experiments/second-judge.md), [owner review](human-review/owner-review-final-summary.md) | Done | AI-drafted gold signed off by one reviewer after the runs; same-family judge, and the second-family check did not reproduce every gain |
| 7 Responsible AI, security, privacy | [Threat model](threat-model.md), [threat suite v2](experiments/threat-v2-results.md), [audit policy](audit-and-logging.md), [tests](../tests/test_security.py) | Done | Injection scanner is a heuristic (10/30 to 23/30 detected); the 36-case suite scored 35/36 with and without defences; guarded and naive v2 arms each failed 3 of 8 benign cases |
| 8 GenAI concepts and trade-offs | [Concepts](concepts.md), [architecture](architecture.md), [glossary](glossary.md), [deployment](deploy.md) | Done | Written explanation only; online monitoring is a plan, not built |
| 9 MCP server, client and comparison | [Server](../src/labourlens/mcp/server.py), [client](../src/labourlens/mcp/client.py), [transcript and direct comparison](mcp-demo-transcript.md), [tests](../tests/mcp/) | Done | The live app routes statistics lookup and annual averaging through MCP; the all-tools variant was tested and is not live |
| 10 Reproducibility and tests | [Reproduce](reproduce.md), [lockfile](../uv.lock), [env template](../.env.example), [tests](../tests/), `make verify` | Done | Offline checks only; corpus tests need the private corpus; a fresh data fetch fails the pinned contracts |

## Demonstration scenarios

| Scenario | Evidence | Status | Limit |
|---|---|---|---|
| 1 Factual answer with citations | [README sample queries](../README.md#sample-queries), [demo plan](demo-plan.md), deck slide "Agent Workbench" | Done | Live workbench needs an access code |
| 2 Structured and unstructured synthesis | [Agent tools](../src/labourlens/agent/tools.py), [evaluation report](evaluation-report.md) | Done | Report-only arithmetic is weak |
| 3 Deterministic calculation | [Agent tests](../tests/retrieval/test_agent.py), [agent tools](../src/labourlens/agent/tools.py) | Done | Calculation from report text was tested and not adopted |
| 4 Abstention or clarification | [Gold cases](../experiments/gold/gold_v3.7.jsonl), [evaluation report](evaluation-report.md) | Done | Reference answers were AI-drafted |
| 5 Conflicting sources | [Reconciliation](../artifacts/data-quality/reconciliation.json), [data sheet](data-sheet.md), deck slide "Understanding the Data" (Finding 3, advance and final figures differ) | Done | Gold conflict cases are AI-drafted |
| 6 Prompt-injection resistance | [Threat summary](../experiments/threats/SUMMARY.md), deck slide "Attacks and defences" | Done | Scanner heuristic; the 36-case suite cannot separate defended from naive |
| 7 Recovery from tool failure | [MCP fault transcript](mcp-demo-transcript.md), [tests](../tests/mcp/) | Done | Faults are injected, not observed in production |
| 8 Discover and invoke MCP, grounded answer | [Transcript](mcp-demo-transcript.md), [agent run](../artifacts/mcp-agent-demo.md) | Done | One recorded agent run, one question |
| 9 Reject invalid MCP input, handle failures | [MCP tests](../tests/mcp/), [transcript](mcp-demo-transcript.md) | Done | Fault cases are injected, not observed |
| 10 Ignore instructions in MCP output | [Hostile fixture](../src/labourlens/mcp/evil.py), [transcript](mcp-demo-transcript.md) | Done | Detection is partly heuristic |

## Submission and innovation

| Requirement | Evidence | Status | Limit |
|---|---|---|---|
| Source, prompts, config template, tests | [src](../src/labourlens/), [prompts](../prompts/), [.env.example](../.env.example), [tests](../tests/) | Done | Report text and raw answers are not in the repository |
| README | [README](../README.md) | Done | Setup checked offline only |
| Architecture diagram | [Architecture](architecture.md), [SVG](img/architecture.svg) | Done | Describes the evaluated design, plus served additions |
| Data sheet | [Data sheet](data-sheet.md) | Done | Source rights and dataset licences unverified; 23 document rights unresolved |
| Evaluation report | [Report](evaluation-report.md) | Done | No demonstrated gain on the fresh 65 questions; one reviewer |
| System card | [System card](system-card.md) | Done | Same limits as the evaluation report |
| 20-minute demo plan | [Demo plan](demo-plan.md), the `/deck` page | Done | Rehearsal and timing are not recorded here |
| Section 2 innovation assessment | [Innovation](innovation.md) (about 600 words) | Done | Page count not re-measured after the last edit |
