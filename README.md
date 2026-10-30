# LabourLens

**Singapore labour-market intelligence for policy researchers.** An evidence-grounded research assistant built on official MOM and SingStat data. Every number traces to a published source; every claim is meant to carry a citation or an honest "not enough evidence".

> **Status (30 Oct 2026): Milestone 1 of 7 complete pending owner review: data ingestion and provenance.** Retrieval, the LLM, the LangGraph agent, MCP server and UI are not built yet. See `docs/progress.md` for exact state and `docs/04_ROADMAP.md` for the plan.

## What exists today
| | |
|---|---|
| 17 official datasets | fetched, snapshotted, hashed, normalised into 10,896 observations (880 in the 2024-Q1 to 2026-Q2 answer scope) |
| 16 MOM documents | fetched locally and parsed into page-located passages (not redistributed; see rights below) |
| Quality | 142 automated checks, 0 failed; 3 documented warnings (`artifacts/data-quality/quality-report.md`) |
| Tests | 51 passing (`artifacts/tests/pytest-m1.txt`) |
| Findings | 3 exploratory findings with figures (`artifacts/data-quality/eda-findings.md`) |
| Human review | sheets prepared, **not yet reviewed** (`docs/human-review/`) |

![Vacancies per unemployed person](artifacts/figures/fig1_vacancy_vs_unemployment.png)
![Three employment-change numbers](artifacts/figures/fig3_employment_change_reconciliation.png)

## Run it
Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). No API keys are needed for M1.
```bash
uv sync
uv pip install -e .
uv run labourlens fetch            # datasets via data.gov.sg (throttled, about 4 min) + MOM documents
uv run labourlens build            # normalise, extract, validate; writes data/processed and artifacts/data-quality
uv run labourlens eda              # figures and findings
uv run labourlens export           # presentation-ready JSON in data/export/
uv run labourlens trace <id>       # provenance for any observation_id or passage_id
uv run pytest
```
Committed dataset snapshots in `data/snapshots/` let `build` run without `fetch` for the statistical data; MOM documents must be fetched locally.

## Where to look
| Need | File |
|---|---|
| Sources, provenance, caveats | `docs/data-sheet.md` |
| Decisions and alternatives | `docs/decisions.md`, `docs/decisions/` |
| Live progress and handoff state | `docs/progress.md` |
| Presentation (interactive report) plan | `docs/presentation-plan.md` |
| Human feedback design | `docs/human-feedback-design.md` |
| Term definitions | `docs/glossary.md` |

## Rights and attribution
Statistical datasets: contains information from data.gov.sg datasets published by MOM and SingStat, accessed 2026-10-30, under the [Singapore Open Data Licence v1.0](https://developers.data.gov.sg/open-data-licence). Not endorsed by any agency. MOM reports carry an all-rights-reserved notice; this repository does not contain them or extracted text from them, only ids, hashes, locators and links. Rights for the MOM press-release pages are unresolved and handled the same way.
