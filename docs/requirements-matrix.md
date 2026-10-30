# Requirement-to-evidence matrix (live)

Source of truth for requirements: the assessment PDF (page references in `docs/01_REQUIREMENTS_AND_SCOPE.md`). Status uses only: `done`, `partial`, `not started`. A row is `done` only when the evidence file exists and was produced by a command listed there. Updated at the end of M1 (30 Oct 2026).

| ID | Requirement | Status | Evidence (exists today) | Gap |
|---|---|---|---|---|
| R01 | Framing, assumptions, baseline, leakage-safe evaluation design | partial | `docs/decisions/ADR-001-scope.md`, `docs/decisions.md` | Hypotheses, baseline and dev/held-out split are designed at M2 and M6 |
| R02 | At least two source types, provenance, licences, schema, validation, two EDA findings | **partial, M1 evidence complete pending human review** | 17 datasets + 16 documents (`data/manifests/manifest.json`); licence per source (`docs/data-sheet.md`); 142 checks, 0 failed (`artifacts/data-quality/quality-report.md`); 3 findings with figures (`artifacts/data-quality/eda-findings.md`, `artifacts/figures/`); 51 tests (`artifacts/tests/pytest-m1.txt`) | Human spot-check sheets (`docs/human-review/`) not yet filled in by the owner |
| R03 | Parsing, chunking, indexing, two retrieval approaches, passage citations, abstention | partial | Parsing with locators and quality flags (`data/pdf_extract.py`, `html_extract.py`); 4 chunking variants, tokeniser, persisted BM25 index (`src/labourlens/retrieval/`); dev experiments E1 to E4 (`docs/experiments/m2-bm25-baseline.md`, `experiments/runs/`); 74 tests (`artifacts/tests/pytest-m2.txt`) | Held-out run (after owner review of gold); second retrieval approach (dense, M3); citations in answers and abstention (M3, M4) |
| R04 | LLM, two controlled configurations, structured output, cost and latency | partial | Answer layer with strict schema, verbatim-quote validator and repair (`src/labourlens/answer/`); 6-model comparison, oracle-evidence control, k sweep, all on dev with measured cost and latency (`docs/experiments/m3-answer-generation.md`); prices in `specs/prices.yaml` | Held-out run; judged groundedness and human review (M6) |
| R05 | One bounded agent with deterministic tools, limits, recovery | partial | LangGraph agent with 3 typed tools and the 7 ADR-002 nodes, bounds (2 rounds, 6 calls, 10 s), one retry, one repair, operational failures kept apart from missing evidence (`src/labourlens/agent/`); fault-injection tests; A1 dev experiment (`docs/experiments/m4-agent.md`); `get_series` can run over MCP | Held-out run; known gap: arithmetic on figures that appear only in report text |
| R06 | At least 30 evaluation cases, metrics, human review, error analysis | partial | 65 draft cases (34 dev, 31 held-out) validated by `labourlens gold-check` (`experiments/gold/draft_cases.jsonl`); retrieval metrics harness; first error analysis on dev; review sheet `docs/human-review/gold-review.md`; human feedback design (`docs/human-feedback-design.md`) | Owner review and freeze of gold; generation metrics and human review (M6) |
| R07 | Responsible-AI threat tests | partial | 36-case threat suite with deterministic pass criteria across 6 categories, run on 3 models plus a no-defence ablation (`experiments/threats/`, `src/labourlens/security/threat_suite.py`); guards, redaction, output scan (`src/labourlens/security/`, `src/labourlens/mcp/redact.py`); threat model (`docs/threat-model.md`) | Suite is small and not adaptive; docs and sign-off by owner; held-out threat cases not separated |
| R08 | AI concepts and trade-offs | partial | Private study note 01 (not published) | Remaining notes through M7 |
| R09 | MCP server (tool and resource), client demo, error behaviour | partial | Official-SDK server with 1 tool, 2 resources, 1 prompt (`src/labourlens/mcp/server.py`); allow-listed client with schema pre-validation, timeouts, size cap, quarantine (`client.py`); 22 protocol tests against real subprocesses and a hostile fixture; scripted demo with observed transcript and direct-vs-MCP comparison (`docs/mcp-demo-transcript.md`) | Owner to rehearse the demo; HTTP transport and authentication not built (stdio only, documented) |
| R10 | Reproducibility, pinned dependencies, tests, setup | partial | `pyproject.toml`, `uv.lock`, `.env.example`, `README.md`, tests; clean-room run result in `docs/progress.md` | Full-system clean run at M7 |

## Final artifacts (page 5 and 7)
| Artifact | Status |
|---|---|
| Source code, config template, README | partial (M1 code, README, `.env.example`) |
| Prompts | not started |
| Architecture diagram | not started |
| Data sheet | done for M1 (`docs/data-sheet.md`), human verification pending |
| Evaluation report | not started |
| System/model card | not started |
| Innovation assessment (1 to 2 pages) | not started |
| 20-minute demo plan | not started; interactive report plan in `docs/presentation-plan.md` |
