# Requirement-to-evidence matrix (live)

Source of truth for requirements: the assessment PDF (page references in `docs/01_REQUIREMENTS_AND_SCOPE.md`). Status uses only: `done`, `partial`, `not started`. A row is `done` only when the evidence file exists and was produced by a command listed there. Updated at the end of M1 (30 Oct 2026).

| ID | Requirement | Status | Evidence (exists today) | Gap |
|---|---|---|---|---|
| R01 | Framing, assumptions, baseline, leakage-safe evaluation design | partial | `docs/decisions/ADR-001-scope.md`, `docs/decisions.md` | Hypotheses, baseline and dev/held-out split are designed at M2 and M6 |
| R02 | At least two source types, provenance, licences, schema, validation, two EDA findings | **partial, M1 evidence complete pending human review** | 17 datasets + 16 documents (`data/manifests/manifest.json`); licence per source (`docs/data-sheet.md`); 142 checks, 0 failed (`artifacts/data-quality/quality-report.md`); 3 findings with figures (`artifacts/data-quality/eda-findings.md`, `artifacts/figures/`); 51 tests (`artifacts/tests/pytest-m1.txt`) | Human spot-check sheets (`docs/human-review/`) not yet filled in by the owner |
| R03 | Parsing, chunking, indexing, two retrieval approaches, passage citations, abstention | partial | Parsing and passage extraction with locators and quality flags (`src/labourlens/data/pdf_extract.py`, `html_extract.py`; 889 to 1,063 passages per report) | Chunking, indexes, retrievers, citations, abstention: M2 to M4 |
| R04 | LLM, two controlled configurations, structured output, cost and latency | not started | | M3 |
| R05 | One bounded agent with deterministic tools, limits, recovery | not started | ADR-002 (design only) | M4 |
| R06 | At least 30 evaluation cases, metrics, human review, error analysis | not started | Human review sheet format prepared; human feedback design (`docs/human-feedback-design.md`) | M6 |
| R07 | Responsible-AI threat tests | not started | Rights and trust-boundary rules in `CLAUDE.md` | M5 |
| R08 | AI concepts and trade-offs | partial | Private study note 01 (not published) | Remaining notes through M7 |
| R09 | MCP server (tool and resource), client demo, error behaviour | not started | | M5 |
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
