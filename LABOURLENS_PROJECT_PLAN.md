# LabourLens — consolidated planning and architecture document

**Prepared:** 30 October 2026  
**Status:** Scope and LangGraph architecture approved; ingestion implementation awaiting explicit approval.  
**Usage:** For convenient reading and discussion. The individual docs in this pack are the working decision records; the original recruiter assignment PDF remains the definitive requirements source.

## Contents

1. Requirements and scope — `docs/01_REQUIREMENTS_AND_SCOPE.md`
2. Official source catalog — `docs/02_DATA_SOURCE_CATALOG.md`
3. Approved scope decision — `docs/decisions/ADR-001-scope.md`
4. Approved LangGraph decision — `docs/decisions/ADR-002-langgraph.md`
5. Milestone 1 detailed ingestion plan — `docs/03_MILESTONE_1_INGESTION_PLAN.md`
6. Milestone roadmap — `docs/04_ROADMAP.md`
7. Evidence and study strategy — `docs/05_EVIDENCE_AND_STUDY_PLAN.md`

---

# Section 1 — Requirements and scope

*Source within the planning pack: `docs/01_REQUIREMENTS_AND_SCOPE.md`*

# LabourLens — requirements, scope, and success criteria

**Status:** Planning baseline. Domain and LangGraph architecture approved; implementation of Milestone 1 not yet approved.  
**Source of truth:** `Tech Challenge - GenAI Engineer v1.0.pdf` (8 pages), supplied by the recruiter. If this PDF is absent, obtain it before implementation; this file is a summary, not an override.

## Product definition

LabourLens is a policy intelligence research assistant for Singapore labour-market analysts. It synthesizes official MOM labour-market reports with four official public statistical series. It answers factual and analytical questions with source-identifiable evidence, calculates numeric comparisons via deterministic tools, handles preliminary versus final releases, clearly states uncertainty, and demonstrates its performance using reproducible experiments.

**Approved answer scope:** 2024-Q1 through 2026-Q2, including comparative report material from MOM Q3/Q4 2025 and Q1/Q2 2026, plus Q2 2026 advance release. **Not in scope:** forecasts, causal attribution not established by source evidence, unrestricted live-web answering, personal job advice, private/non-public data.

**Success means:** requirements implemented and traceable; all mandatory demonstrations feasible; conclusions backed by verifiable passages/observations; actual metrics with honest error analysis; a reviewer can execute documented setup/test commands; creator can explain trade-offs and failures.

## Requirement-to-evidence traceability matrix (initial)

| ID | Assessment requirement (pages) | Intended implementation/evidence | Verification | Current status |
|---|---|---|---|---|
| R01 | Framing, assumptions, measurable success, baseline, leakage avoidance (p1) | Scope ADR, hypotheses, baseline plan, separate dev/held-out cases | Review scope and split procedure | Scope approved; design not tested |
| R02 | >=2 source types, provenance/licences/schema/cleaning, >=2 EDA insights (pp1-2) | Four official datasets + five official publications, source manifest, normalization, EDA figures | Data quality checks and manual sample review | Sources selected; ingestion pending |
| R03 | Ingestion + chunking/index/retrieval + >=2 approaches, citations and abstention (p2) | BM25, dense, hybrid retrieval; source-aware passage IDs; abstention | Recall@k/MRR + manual citation checks | Planned |
| R04 | LLM choice/settings, >=2 meaningful controlled configurations, structured validation, reproducible results (p2) | Fixed model/prompt, controlled retriever comparisons, typed answer schema | Versioned experiment outputs, token/latency/cost | Planned |
| R05 | Purposeful bounded agent/tools, deterministic arithmetic, transitions, limits, failure recovery (p2) | Approved single-agent LangGraph workflow and tools | State/trace/tool-retry tests | Architecture approved; unbuilt |
| R06 | >=30 cases; retrieval + generation evaluation; human sample review; errors, cost/latency (pp2-3) | Gold set with labels/evidence, metrics, human-review rubric, experiment report | Exact case count and stratified results | Planned |
| R07 | Prompt injection, malicious evidence, sensitive data, unsafe tools, privacy, permissions (p3) | Untrusted source boundaries, typed read-only tools, redacted traces, security fixtures | Adversarial/integration tests | Planned |
| R08 | LLM, embedding, prompts, evaluation, agents, MCP, production conceptual trade-offs (p3) | ADRs, study pack, concise engineering justifications | Interview rehearsal and code walkthrough | Ongoing learning plan |
| R09 | MCP server >=1 tool + >=1 resource, real client demo, schema/errors/timeouts, trust boundaries (pp4-5) | Official MCP SDK read-only statistics tool and source catalog | Protocol-level discovery, invoke, bad args, timeout, malicious content | Planned |
| R10 | Reproducibility, pinned dependencies, tests, optional API/containerization (p4) | uv lockfile, `.env.example`, deterministic snapshot manifests, pytest, one-command setup | Fresh checkout smoke tests | Planned |

**Evaluation rubric (page 6):** framing/data 10%; RAG/model design 20%; evaluation/error analysis 25%; agent/tools 10%; GenAI concepts/MCP 15%; security 10%; reproducibility/communication 10%. Evaluation plus RAG plus concepts/MCP = **60%**; avoid over-investing in frontend polish.

## Ten mandatory demonstration scenarios (pp4-5)

| Demo ID | Scenario | Planned demonstrable evidence |
|---|---|---|
| D1 | Factual answer with correct source passage | Correct statistic + passage/citation ID |
| D2 | Synthesis across structured and unstructured sources | Series plus MOM report cited analysis |
| D3 | Deterministic calculation with citations | Original observations, formula, result, provenance |
| D4 | Insufficient / ambiguous question | Clarification or abstention; no invented values |
| D5 | Conflicting sources | Advance vs final source chronology and explanation |
| D6 | Prompt injection resistance | Malicious retrieved content ignored as instructions |
| D7 | Retrieval/tool failure recovery | Controlled fault, retry trace, graceful outcome |
| D8 | Discover/invoke MCP capability | Real client/server protocol transcript + source-backed response |
| D9 | Invalid MCP args and timeout/unavailable/malformed response | Input rejection, bounded failure behavior |
| D10 | Ignore malicious MCP tool/resource instructions | Untrusted content isolated from tool-selection policies |

## Required final artifacts (page 5 and page 7)
- Repository/submission package with source, notebooks/prompts, config templates, focused tests.
- README with problem, setup, usage, sample queries, limits and responsible-use notes.
- Architecture diagram with data/retrieval/model/tools/evaluation/guardrails.
- Source data sheet (publisher, provenance, transformations, exclusions, quality issues).
- Evaluation report (dataset design, metrics, baseline, experiment table, results, error analysis, prioritized improvements).
- Short system/model card (intended uses, limitations, risks, mitigations).
- Separate **1–2-page innovation assessment** for secure government expansion, with two prioritized and measurable improvements.
- **20-minute live demo** plan and technical Q&A preparation. Video submission is not explicitly required in the supplied assessment.

## Target research question categories and evidence design
- Factual: exact rate or quarterly employment change, with definition, year/quarter and source.
- Numerical: differences in people, percentage-point shifts, percent change with explicit denominator.
- Multi-source: reconcile report narrative with structured observations (e.g., employment grew while retrenchments rose).
- Preliminary/final: explain Q2 2026 10,700 vs 11,400 total employment growth values, source dates, and revisions.
- Ambiguity: ask whether the question refers to residents, citizens or overall population; SA/NSA when relevant.
- Unsupported causal: refuse unsupported inference that AI caused a retrenchment trend.
- Injection: adversarial instructions in report passages and MCP resources must not override trusted instructions.

## Evaluation design commitments to establish before coding retrievers
- Reserve >=30 evaluation cases (e.g. 8 factual, 5 synthesis, 5 calculations, 4 ambiguous/unanswerable, 4 conflicting, 4 adversarial) and separate 12–15 development examples.
- Label gold source/passage IDs only after ingestion makes stable IDs available; keep preliminary questions/expected behavior in draft without pretending they are validated.
- A non-LLM/simple baseline must be explicit: BM25 with extractive answer/passages, not BM25 + LLM disguised as non-LLM.
- Compare controlled configurations; keep model/prompt, corpus snapshot and generation settings fixed when comparing retrievers.
- Evaluate retrieval (Recall@5, MRR@5, optional nDCG); answer correctness, groundedness, citation correctness, abstention, calculation and security behavior.
- Human-review sample must be actually reviewed by a human using documented criteria; do not fabricate review.
- Report latency and estimated cost alongside quality, stratified by case type; preserve every error category and negative result.

## Approval states
**Approved:** Singapore labour-market domain, 2024-Q1–2026-Q2, four statistical datasets, five MOM publications; LangGraph architecture and initial bounding behavior; high-quality but subordinate UI ambition.

**Not yet approved:** ingestion approach and source file distribution policy; parser implementation details; data schema; exact library versions; embedding/LLM selection; UI stack; specific evaluation judges; implementation of any milestone.


---

# Section 2 — Official source catalog

*Source within the planning pack: `docs/02_DATA_SOURCE_CATALOG.md`*

# Source catalog and initial verification notes

**Status:** planning evidence verified from publisher pages on 30 October 2026. **No dataset API extraction or PDF corpus ingestion has been executed in this planning pack.** These entries must be confirmed programmatically and captured in a machine-readable manifest during Milestone 1.

## Dataset inventory — approved structured sources

| ID | Publisher | Official data.gov.sg URL | Preliminary schema observations | Caveats / transformations |
|---|---|---|---|---|
| `resident_unemployment` | MOM | https://data.gov.sg/datasets/d_d1d755e060dd6b01a8024ba60b21b831/view | `period` (`YYYY-MM`, quarter-end month), `residential_status`, `seasonally_adj_unemp_rate`, `non_seasonally_adj_unemp_rate` | `2026-06` => `2026-Q2` while retaining source date; separate SA/NSA; population = residents; unit percent |
| `vacancy_unemployed_ratio` | MOM | https://data.gov.sg/datasets/d_80c0cf251ee9a26d240808297f52c820/view | `quarter`, `jv_to_ue` | Seasonally adjusted; unit ratio, NOT percentage; preserve exact series definition |
| `retrenchments` | MOM | https://data.gov.sg/datasets/d_000d49cda016c13522d7d5be6a050f59/view | `quarter`, `retrench` | Count values stored as TEXT; handle suppression/missing markers rather than coercing to 0 |
| `employment_by_sector` | SingStat (source MOM) | https://data.gov.sg/datasets/d_31dec7667bc2c6b945a262cd60958eaf/view | `DataSeries` plus one column per quarter, e.g. `20262Q`, `20261Q` | Wide-to-long unpivot; sector hierarchy and totals, SSIC footnotes, rounding and revisions; unit persons |

These publisher pages currently show data through Q2 2026. That is **source-page evidence**, not proof of success against the dataset API.

### Source links and methodological footnotes
- Resident unemployment: quarter-end `YYYY-MM` field and seasonally adjusted revision policy: https://data.gov.sg/datasets/d_d1d755e060dd6b01a8024ba60b21b831/view
- Vacancy ratio: seasonally adjusted, source survey coverage notes: https://data.gov.sg/datasets/d_80c0cf251ee9a26d240808297f52c820/view
- Retrenchments: source measure stored as text and definition of retrenchment: https://data.gov.sg/datasets/d_000d49cda016c13522d7d5be6a050f59/view
- Sector employment: wide layout, rounding and industry classifications: https://data.gov.sg/datasets/d_31dec7667bc2c6b945a262cd60958eaf/view

### Do not silently assume
- A release date of the dataset page equals the exact publication timestamp of each observation.
- All ten selected quarters have complete and comparable observations for all industries.
- The data.gov.sg UI's displayed row counts represent cleaned/usable data rows in the pipeline.
- `total employment`, `resident employment`, `employment level`, and `employment change by sector` are interchangeable.
- SA and NSA unemployment values can be compared without clear selection and labeling.
- Vacancy/unemployment *ratio* is a vacancy *rate*.
- A dash, suppression marker, `NA`, or blank is numeric zero.

## Publication inventory — approved unstructured sources

| Source ID | Official reference page / document | Release stage | Role |
|---|---|---|---|
| `mom-2025-q3-final` | https://stats.mom.gov.sg/Pages/Labour-Market-Report-3Q-2025.aspx | Final, 11 Dec 2025 | Earlier report language, methodologies and comparison context |
| `mom-2025-q4-final` | https://stats.mom.gov.sg/Pages/Labour-Market-Report-4Q-2025.aspx | Final, 20 Mar 2026 | End-2025 labour-market context |
| `mom-2026-q1-final` | https://stats.mom.gov.sg/Pages/Labour-Market-Report-1Q-2026.aspx | Final, 15 Jun 2026 | Before/after comparison with 2026 Q2 |
| `mom-2026-q2-final` | https://stats.mom.gov.sg/Pages/Labour-Market-Report-2Q-2026.aspx | Final, 21 Sep 2026 | Latest full report in approved answer scope |
| `mom-2026-q2-advance` | https://www.mom.gov.sg/newsroom/press-releases/2026/0731-labour-market-advance-release-2q-2026 | Advance, 31 Jul 2026 | A genuine preliminary-versus-final provenance exercise |

**Known primary source revision example:** Q2 2026 total employment increase was 10,700 in the advance release (31 Jul) and 11,400 in the final report (21 Sep). The correct behavior is to distinguish release stages and dates rather than label one as an unexplained contradiction.
- Advance official release: https://www.mom.gov.sg/newsroom/press-releases/2026/0731-labour-market-advance-release-2q-2026
- Final official release: https://www.mom.gov.sg/newsroom/press-releases/2026/0921-labour-market-report---second-quarter-2026

### Rights and redistribution — critical

**data.gov.sg data:** data.gov.sg identifies the four datasets under the Singapore Open Data Licence; that licence permits reuse and redistribution subject to attribution and other conditions. Use the actual licence and attribution notices, and do not imply governmental endorsement.
- Official licence: https://developers.data.gov.sg/open-data-licence
- API/website terms: https://data.gov.sg/privacy-and-terms

**MOM full report PDFs:** The Q3 2025 full PDF visibly contains a copyright notice stating that further reproduction requires permission and requests attribution to `MRSD, MOM`. Do **not** assume the Open Data Licence covering data.gov.sg applies to the PDFs. Check each report's rights/usage notice individually before any redistribution.
- Official Q3 2025 PDF for rights inspection: https://stats.mom.gov.sg/iMAS_PdfLibrary/mrsd-Labour-Market-Report-3Q-2025.pdf

**Default repository handling:**
- Keep acquired full PDF files and large text dumps local, gitignored, not bundled into a publicly shared GitHub repository.
- Commit source metadata/manifests, source URLs, parser code, small derived statistics where permitted, hashes, and a reproducible download procedure.
- Use short necessary quotations only if permitted; prefer your own summaries and links to the original source for public documentation.
- Clearly label local-only corpus access when evaluating fresh-clone reproducibility; provide public sample fixtures only when rights permit.

## API acquisition plan — verified documentation, not executed

data.gov.sg documents a whole-dataset flow:
1. Identify dataset ID from official URL.
2. Call documented `initiate-download` endpoint for CSV datasets.
3. Poll the documented `poll-download` endpoint for the download URL, observing its expected statuses and server guidance.
4. Download bytes, preserve as immutable raw file, verify content type, hash with SHA-256, record retrieval time UTC, and avoid committing source secrets.
5. If API fails or is rate-limited, offer a **clearly labelled manual official-site download fallback** with the same manifest requirements. Never pretend the API succeeded.

Official guide: https://guide.data.gov.sg/developer-guide/dataset-apis/download-dataset

Use real publisher URLs and verify final downloadable PDF links from the official pages; never guess PDF filenames without checking. The 2025 Q3 full PDF link above is verified; verify all others in the implementation gate.

## A source record should include
`source_id, source_type, title, publisher, source_url, download_url_if_verified, licence_name, licence_url, redistribution_policy, publication_date, retrieval_utc, reporting_period, release_stage, content_type, raw_filename, byte_count, sha256, source_revision_notes, access_method, retrieval_status`.

## What remains open
- Resolve and validate direct URLs for all report files; inspect their copyright notices.
- Test API response schemas and whether rate limits require credentials.
- Confirm full interval coverage 2024-Q1 through 2026-Q2 per metric/sector.
- Decide whether the Q2 advance is better ingested as HTML or full PDF and how page citations apply to each.
- Confirm raw-file storage/redistribution policy appropriate to interview repository visibility.
- Pin parser, dataframe, analytics and download tool versions after smoke testing.


---

# Section 3 — Approved scope decision

*Source within the planning pack: `docs/decisions/ADR-001-scope.md`*

# ADR-001 — LabourLens research scope

**Status:** APPROVED by project owner, 30 October 2026  
**Decision category:** Product/domain and evaluation boundaries

## Context
The GenAI Engineer technical challenge asks for an evidence-grounded policy research assistant using mixed-format data, numerical tools, cited synthesis, ambiguity and conflict handling, and experimental evaluation. It explicitly does not prioritize a heavy backend or polished frontend. The project needs a small, coherent real-world corpus suitable for a defensible 20-minute demonstration.

## Alternatives discussed
| Option | Benefits | Risks |
|---|---|---|
| Labour market intelligence | Official structured quarterly indicators and narrative reports; true publication revisions; useful calculations | Definition/seasonality and release-version mismatches |
| Housing affordability | Accessible datasets, clear visualizations | Confounding variables and heterogeneous transaction-level data |
| Cost of living / inflation | Time-series data, policy relevance | Index methodology, weights and causality complexities |

## Approved decision
- Product: **LabourLens — Singapore Labour Market Intelligence**.
- Intended users: policy researchers and labour-market analysts.
- Supported answer period: **2024 Q1 through 2026 Q2**, inclusive. Older values may exist in downloaded datasets; scope filters and corpus snapshot must control which observations are answerable.
- Four structured datasets: resident unemployment rate; vacancy-to-unemployed ratio; quarterly retrenchments; employment changes by sector.
- Five unstructured/publication sources: MOM full labour-market reports for 2025 Q3, 2025 Q4, 2026 Q1, 2026 Q2; and Q2 2026 advance release (PDF/HTML depending on verified access and reuse conditions).
- Question types: factual; numerical change; cross-source synthesis; preliminary/final revision; ambiguity/unanswerability; adversarial/injection.
- Explicit non-goals: forecasting, causal-policy-impact estimation without evidence, unrestricted internet research, individual job advice, production-scale identity infrastructure.
- Official-source evidence and licensing are mandatory; evaluate at least 30 held-out cases, with human review and real measured metrics.
- Visual ambition: sleek policy-research workbench with citations, provenance, interactive figures, execution evidence, and experiment comparison. UI polish must not compromise rubric-critical evaluation.

## Evidence and warnings
- Scope approval is **not** confirmation that every data source can be downloaded or parsed without issues.
- Data availability, quarter completeness, PDF publication links, publisher terms, and exact row schemas must be tested during ingestion. Distinguish planned facts from observed facts.
- Approved corpus does not imply a right to redistribute original MOM PDF report files in a public repository.

## Revisit criteria
Only revisit scope with the owner's approval if a core government dataset is inaccessible, rights prevent legitimate usage, or quality is insufficient for mandatory demonstrations. First try a transparent official-source alternative with similar definitions.


---

# Section 4 — Approved LangGraph decision

*Source within the planning pack: `docs/decisions/ADR-002-langgraph.md`*

# ADR-002 — LangGraph orchestration and evidence separation

**Status:** APPROVED by project owner, 30 October 2026  
**Decision category:** Research orchestration and system boundaries

## Decision summary
Use **LangGraph StateGraph** with one bounded, model-directed research agent and deterministic, typed, read-only evidence/calculation tools. Separate the structured statistical store from the unstructured document retrieval index. Keep retrieval, data access, MCP integration, evaluation and the UI behind testable interfaces.

## Architecture decisions approved
1. **One bounded researcher**, not a three-agent hierarchy. A graph may have multiple nodes; that does not make it multiple autonomous agents.
2. **Seven conceptual graph nodes:** `validate_question`, `plan_research`, `execute_tool`, `assess_evidence`, `generate_answer`, `validate_answer`, `finalize`. Conditional routing and recoverable error paths are allowed. Exact implementation is adjustable within these boundaries.
3. **Typed research state** holds request, current tool proposal, references to evidence, counts, errors, validation outcome and response. Do not store full PDF documents, large tables or hidden model reasoning in graph state.
4. **Five candidate tool contracts:** `search_reports`, `get_statistical_series`, `calculate_change`, `get_source_metadata`, `compare_publications`. Tools must validate input, be read-only (or pure calculations), respect the approved domain and return provenance. A specialized `compare_publications` helper may be omitted if it adds no reliability beyond the general metadata tool; discuss at its implementation gate.
5. **Model-controlled choices, deterministic execution:** model chooses eligible tools and proposes arguments; application validates allowed indicators, source IDs, types and periods; all arithmetic is deterministic. No arbitrary SQL, shell, unrestricted URLs, or direct access to secrets.
6. **Bounded execution starting parameters:** max 6 tool calls; max 2 evidence-gathering rounds; one retry for transient tool errors; one correction for malformed model/tool arguments; explicit response on exhaustion. These are initial defaults to measure and revise, not production guarantees.
7. **Failure distinction:** unsupported claim / missing evidence / ambiguous question are epistemic outcomes; unavailable external source or MCP server is an operational failure. Never represent an operational failure as absence of evidence.
8. **Observability:** record safe tool inputs/outputs, timestamps, evidence IDs, state transitions, retries, errors and time/cost metrics; do not reveal private chain-of-thought. UI can stream task-status events.
9. **Persistence:** prefer a local SQLite checkpointer if the pinned LangGraph version and tests support it; memory-only is acceptable during unit tests. Avoid unnecessary long-term memory or production database infrastructure.
10. **MCP:** expose one read-only statistics tool and one source-catalog resource via a small server, and prove real capability discovery, successful invocation, invalid-argument rejection and timeout/malicious-output handling. Keep a direct-function integration for comparison. Do not confuse MCP-shaped Python methods with actual MCP protocol calls.
11. **Retrieval experiment design:** BM25 non-LLM baseline, dense vector retrieval, hybrid (e.g. reciprocal rank fusion) and, if time permits, section-aware chunking comparison. Do not assert superiority until measurements exist.
12. **UI:** modern research workbench; exact UI stack remains a separate decision gate. No generic chat-only demonstration.

## Alternatives considered
| Option | Benefit | Why not selected |
|---|---|---|
| Direct custom tool loop | Smallest dependencies, demonstrates primitives | More manual state/retry/trace wiring; graph state is relevant to assessment |
| OpenAI Agents SDK | Fast agent setup, tools/tracing/MCP support | StateGraph better foregrounds explicit execution/routing/recovery for this specific demonstration |
| LangGraph with many autonomous agents | Separate specialized roles | Unnecessary complexity, coordination overhead, extra cost, less controlled evaluation |

## Core data/agent boundary (conceptual)
`source acquisition -> immutable raw snapshots -> validated statistical facts and source passages -> retrieval/statistical tools -> bounded LangGraph research -> grounded structured response -> citation/claim checks -> experiment and trace records`

## Risks and mitigations
- Graph complexity outruns schedule -> keep nodes and tool contracts minimal; test each tool independently.
- Tool loops -> enforce state counters and graph recursion backstop separately (recursion counts graph steps, not tools).
- Unstable checkpoints -> use testable pinned version or downgrade to in-memory within approved gate.
- Citation ID exists but doesn't support claim -> separately score semantic support and human review.
- Tool/LLM content injection -> isolate retrieved/source text as untrusted data; never treat it as system instructions.

## Approval boundary
**Architecture approved; coding NOT approved yet.** The next decision is the detailed ingestion/provenance milestone. The agent must present trade-offs and obtain explicit owner approval before writing application implementation.

## Relevant documentation
- LangGraph overview: https://docs.langchain.com/oss/python/langgraph/overview
- LangGraph persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph streaming: https://docs.langchain.com/oss/python/langgraph/streaming
- GenAI assessment PDF is the source of truth for the rubric and mandatory demonstrations.


---

# Section 5 — Milestone 1 detailed ingestion plan

*Source within the planning pack: `docs/03_MILESTONE_1_INGESTION_PLAN.md`*

# Milestone 1 — Government data ingestion and provenance

**Status: PROPOSAL — HUMAN APPROVAL REQUIRED BEFORE CODING.**  
**Goal:** build a small, reproducible, legally considerate pipeline that acquires real government data, retains original bytes locally, normalizes official statistical observations, extracts citable report passages, tracks source revisions and produces audit-ready quality evidence.

## 1. Why ingestion is the first coding milestone

The RAG search index, statistical tools, answer citations, and evaluation gold labels all depend on stable identifiers and trustworthy source metadata. If data ingestion is weak, an apparently good LLM can still mix resident and overall unemployment, seasonally adjusted and raw rates, or preliminary and final figures. This milestone does **not** implement agents, LLM calls, retrieval indexes, MCP, or UI.

### Primary deliverables
1. Official-source acquisition pathway for each of four approved datasets and five approved reports, with honest API/manual fallback and a rights-aware raw-file handling policy.
2. Machine-readable source manifest and an immutable local raw snapshot with SHA-256 hashes (where licensed/access permitted).
3. Typed long-form statistical observation table, with population/adjustment/unit/source/revision metadata and validated quarter handling.
4. PDF/HTML extraction into auditable passages with stable IDs, real page numbers for PDF content, and publication/source metadata.
5. Data-quality reports, reproducibility instructions, unit/integration tests, and a small manually checked citation/observation sample.
6. An interview/study note explaining the data choices, pitfalls, source reliability, and rejected alternatives.

## 2. Decision A — Acquisition strategy

| Option | How | Advantages | Problems | Recommendation |
|---|---|---|---|---|
| A1. Manual downloads | Download CSV/PDF via official sites and store locally | Quick, easy to inspect; survives API quirks | Harder to reproduce automatically; human mistakes | Fallback |
| A2. API/live downloads | Use documented data.gov.sg endpoints and official document URLs on each run | Repeatable, potentially fresh | Network, rate limits, revision drift, changed upstream content | Not alone |
| **A3. Verified acquisition + immutable snapshot** | Fetch through official API and verified URLs, hash originals, pin manifest, allow explicitly labelled manual fallback | Best mix of reproducibility and real-world engineering | Slightly more metadata/build work | **Preferred** |

### Proposed flow (to be implemented after approval)
- Identify verified official source ID and URL from manifest.
- For data.gov.sg CSV, follow official `initiate-download` then `poll-download` documented endpoints; honor response codes/rate limits and use a bounded retry policy.
- For MOM report, follow the verified official page to the actual PDF link or ingest the official advance-release HTML when more faithful. Never guess a download URL.
- Validate media type and file signature, size cap, non-empty content, HTTP status, source host allow-list, and sha256 of exact downloaded bytes.
- Store local immutable raw bytes in versioned snapshot paths. **Do not check restricted report PDFs into public GitHub.**
- Record retrieval UTC timestamp, publisher publication date, reporting period, rights, hash, byte length, source URL, and parser version.
- Normalized output is derived from one exact snapshot ID; changes create a new snapshot, not a silent overwrite.

**Open item:** choose whether the public repository includes allowed dataset CSV snapshots or only scripts + hashes. Rights for report PDFs must be evaluated separately. Recommended: commit small structured snapshots only when terms allow, but never raw report PDFs by default.

## 3. Decision B — Dataframe and analytical store

| Option | Benefits | Costs | Recommendation |
|---|---|---|---|
| Pandas + CSV only | Few dependencies, familiar | Repeated parsing, weak persistent analytical queries | Useful interim baseline |
| SQLite normalized records | Portable/inspectable, relational | Less convenient for analytical table operations | Credible alternative |
| **Pandas -> Parquet -> DuckDB** | Good cleaning + typed snapshots + analytical SQL; local and testable | Adds `pyarrow`/DuckDB | **Preferred** |
| PostgreSQL | Strong production database | DevOps overhead unrelated to rubric | Defer |

Do **not** let the agent produce arbitrary SQL. Later statistical tools should accept typed indicator/time/dimension inputs, and application code should query the validated store.

## 4. Decision C — PDF/HTML extraction

| Option | Benefits | Risks | Recommendation |
|---|---|---|---|
| Plain PyMuPDF page text | Very fast, page-aware | Reading order, columns and tables may be scrambled | Baseline extractor |
| **PyMuPDF block/coordinate + section-aware extraction** | Preserves positions and page metadata; better citations | Custom parsing logic; need manual verification | **Preferred** |
| pdfplumber selective table extraction | Additional table inspection capabilities | Another parser dependency; inconsistent on complex PDFs | Fallback on named problem pages |
| LLM/OCR-first extraction | Can handle difficult layouts | Extra costs, potential hallucinated text, weak reproducibility | Only controlled exceptional cases |
| Official HTML as document source | Clearer text and direct URL | Lacks PDF page references; summary may omit full methodology | Useful for Q2 advance/revision evidence |

Use PyMuPDF to retain physical PDF page index (1-based) plus printed page label if discernible, section heading, block order/coordinates, text and extraction warnings. The `page.get_text()` API does not guarantee natural reading order, and table recovery needs validation. Inspect a deliberate sample of pages containing prose, multicolumn sections, tables and footnotes. If a report is not extractable faithfully, mark the passage unsuitable for high-stakes numerical answers and rely on structured series for calculations.

Rights-sensitive default: acquired full PDFs remain local and ignored from Git. If source document cannot be legally redistributed, source manifests and link-backed citations can still be public, while any extracted passages in the repository must be limited to what reuse permits. Do not silently make a public corpus dump.

## 5. Canonical data contract — proposed

### 5.1 `SourceManifestEntry`
| Field | Meaning |
|---|---|
| `source_id` | Stable identifier (`mom-2026-q2-final`) |
| `source_type` | `dataset_csv`, `report_pdf`, `release_html` |
| `publisher`, `title`, `canonical_url` | Official provenance |
| `retrieval_url` | Actual verified download URL if distinct |
| `publication_date`, `retrieval_utc` | Published vs fetched times |
| `reporting_period_start/end` | Coverage of the source |
| `release_stage` | `advance`, `final`, `revised`, `not_applicable` |
| `licence_id`, `licence_url`, `redistribution_status` | Rights decisions and unknowns |
| `snapshot_id`, `sha256`, `byte_count`, `mime_type` | Immutable raw-file identity |
| `access_method`, `retrieval_status`, `parser_version` | Reproduction and troubleshooting |
| `notes` | Definitions, warnings, manual fallback reason |

### 5.2 `StatisticalObservation`
| Field | Why needed |
|---|---|
| `observation_id` | Stable, content/version-aware reference for citations |
| `source_id`, `snapshot_id`, `source_row_or_cell` | Lineage back to the original table |
| `indicator_id` | Canonical measure (`resident_unemployment_rate`, `retrenchments`, etc.) |
| `period` | Canonical `YYYY-QN` |
| `period_start`, `period_end` | Date bounds, not just a label |
| `value` | Validated numeric value; nullable only with a reason |
| `unit` | `percent`, `people`, `ratio`, `percentage_points` (the latter mainly for derived results) |
| `population` | `resident`, `overall`, `citizen`, `not_applicable` |
| `adjustment` | `seasonally_adjusted`, `not_adjusted`, `not_applicable` |
| `sector_id`, `sector_label` | Preserve sector hierarchy if applicable |
| `release_stage`, `revision_tag` | Preliminary/final/revised status |
| `raw_value`, `missing_reason`, `transformation_version` | Cleaning audit trail |

### 5.3 `DocumentPassage`
`passage_id, source_id, snapshot_id, original_url, document_title, publication_date, release_stage, page_number_pdf_1_based_or_null, printed_page_label_or_null, section_heading, block_positions_if_available, text, extraction_method, extraction_quality_flag, source_span_or_locator, parser_version, text_sha256`

**Stable ID rule:** derive IDs deterministically from source snapshot + passage position/section + parser version. IDs may legitimately change when the source or parser changes, but no silent changes in an evaluation snapshot.

## 6. Normalization per approved dataset

| Dataset | Conversion | Key validation questions |
|---|---|---|
| Resident unemployment | Map quarter-end `YYYY-MM` to `YYYY-QN`; emit separate observations per adjustment series | Month must be 03,06,09,12; `resident` definition retained; percent vs pp |
| Vacancy/unemployment ratio | Parse `YYYY-QN` and numeric ratio | Do not convert ratio `1.48` to `1.48%`; SA status retained |
| Retrenchments | Parse `retrench` textual numbers with strict patterns and explicit missing tokens | `N/A`, `-`, suppressed or invalid text never converted to 0 |
| Employment by sector | Melt wide quarter columns into long observations, preserve source series hierarchy | Don't double-count aggregate and sub-sector rows; check signs, unit, notes on rounded totals and revisions |

### Time range and semantic integrity
- Restrict **supported answers** to 2024-Q1–2026-Q2 (10 quarters).
- The raw source files may include earlier history; do not delete it without a documented reason, but apply scope filters for questions and evaluation.
- When comparing values, require matching indicator, unit, population, seasonality, and compatible reporting period. The tool should reject mismatches.
- Example: Q2 2026 advance total employment increase of 10,700 and final increase of 11,400 must remain two distinct source-attributed observations or release facts, not collapse into one unversioned value.

## 7. Quality checks and review

### Automated checks (required)
- All nine approved source IDs represented in catalog with retrieval status and official URL.
- Every successfully retrieved source file has a non-empty byte count, UTC acquisition timestamp, a SHA-256 digest and declared MIME type.
- Idempotency: rerunning against a pinned snapshot yields identical normalized outputs and stable observation/passage IDs.
- No duplicates for canonical composite keys within a snapshot unless they represent an explicitly different release/population/adjustment.
- All usable observations parse into valid quarter/number/unit; errors quarantined with raw cell and reason, never swallowed.
- Quarter-end `YYYY-MM` normalization tests for Mar/Jun/Sep/Dec and invalid month rejection.
- Null/suppression and non-numeric retrenchment marker tests.
- Employment sector wide-to-long conversion with aggregate/hierarchy handling, including rounding tolerance in totals.
- PDF/HTML passage non-emptiness, source ID, stable ID, and real document locator; flagged extraction anomalies.
- No secrets or copyrighted full reports committed; check `.gitignore`/public package contents.

### Manual cross-checks (real human review needed)
- Spot-check at least 2 observations per statistical dataset (8 total) against official source values.
- Review at least 2 passages per report (10 total), including one table/footnote/multicolumn example, verifying the extracted ordering and page or HTML locator.
- Verify the source-revision example against the original advance and final official releases.
- Record who reviewed, date, original source link, observed result and any discrepancy; do not report agent-generated reviews as human validation.

### Proposed acceptance criteria
1. A fresh user can follow documented acquisition and normalization steps without hidden manual edits; when copyright prevents redistributing raw PDFs, the instructions explicitly acquire them from the official sites.
2. The four dataset adapters produce typed observations or a clearly reported failure; all five reports yield verifiable citable source units or clearly flagged limitations (PDF or HTML as justified).
3. A provenance record connects each normalized observation and report passage to the exact source file, URL and immutable snapshot.
4. Quality test suite passes with actual command/test output captured; errors are visible, not hidden.
5. A single deterministic data inspection/demo prints sample validated observation IDs and passage IDs, and verifies the preliminary/final distinction (not an LLM answer).
6. Data sheet and decision record state licensing, exclusions, missingness and transformations.

## 8. Suggested project components AFTER approval (not implemented by this document)

```text
src/labourlens/data/
    catalog.py              # fixed source IDs and approved URLs
    acquire.py              # official dataset/document downloads
    raw_store.py            # hash/version snapshots
    normalize.py            # indicator-specific adapters
    models.py               # typed source/observation/passage structures
    pdf_extract.py          # layout-aware PDF extraction and warnings
    validate.py             # invariant checks and quality report
    build.py                # orchestrated, repeatable ingestion pipeline

data/                       # actual raw sources handled according to rights
    raw/                    # usually gitignored
    processed/              # Parquet or equivalent; licence-aware
    manifests/

tests/data/
    test_periods.py
    test_normalizers.py
    test_provenance.py
    test_pdf_extract.py
    test_rights_packaging.py

docs/data-sheet.md
artifacts/data-quality/       # actual generated validation summaries
study/01-data-ingestion.md
```

## 9. Proposed implementation sequence after Milestone 1 approval

**M1.1** Verify API, direct report file URLs, PDF rights, and schemas. Produce actual source inventory. Stop if publisher access/terms differ materially from the plan.  
**M1.2** Implement approved manifest/typed schemas and acquisition with hashes, retries, immutable filenames, clear download errors. Test against one small dataset.  
**M1.3** Implement each dataset normalizer, tests and quarter/adjustment/unit checks. Build Parquet snapshot if chosen.  
**M1.4** Extract report text with physical page mapping and HTML locators. Run manual checks on difficult layouts before accepting passages as evidence.  
**M1.5** Build reproducible data-quality report; audit source revisions/licences; document observed errors.  
**M1.6** Run a clean-room setup/ingestion smoke test where feasible; capture commands, outputs, hashes and quality metrics. Document limitations and prepare a Git commit for owner review.

## 10. What should NOT happen during M1
- No LangGraph nodes, model calls, vector embeddings, BM25 index, MCP server, Next.js UI, dataset-only fake analytics, or evaluation scores presented as real.
- No unverified PDF URLs, invented citations, arbitrary web scraping, full report redistribution, hardcoded statistics as the whole data pipeline, or silent fallback to synthetic data.
- No claims that all data have been cleaned or manually reviewed without real artifacts to support them.

## 11. Decision gate for the owner

**Recommended bundle to approve:**
- **Acquisition:** official API + verified download URLs + immutable hashes + licensed/manual fallback.
- **Structured data:** Pandas normalization -> Parquet -> DuckDB for later typed queries.
- **Documents:** PyMuPDF text blocks and page/section locators; use HTML for advance release as needed; explicitly quarantine low-confidence PDF tables.
- **Rights:** keep full MOM PDFs local and out of public Git; publish manifests, fetch scripts and links with attribution; evaluate small derived text excerpt redistribution carefully.
- **Validation:** strict schemas, revision awareness, no null-to-zero conversions, manual sample checks, reproducibility test.

Ask the user to approve this package or request a change. **Do not start coding unless the user authorizes “Implement Milestone 1” (or equivalent).**


---

# Section 6 — Milestone roadmap

*Source within the planning pack: `docs/04_ROADMAP.md`*

# LabourLens — roadmap, approval gates, and contingency plan

**Deadline:** Wednesday, 4 November 2026, morning Singapore time. **Planning date:** Friday, 30 October 2026. Prioritize an explainable and testable working core; do not cut required evidence artifacts silently.

## Phase summary

| Milestone | Objective | Gate before work | Main exit evidence |
|---|---|---|---|
| M0 — Scope and architecture | Select domain, source scope and orchestration boundaries | **APPROVED** | ADR-001 and ADR-002 |
| M1 — Government ingestion and provenance | 4 official statistical datasets + 5 official publications, normalized observations/passages | **PENDING APPROVAL** | Frozen source manifest, hashes, parser/validation tests, quality report, data sheet |
| M2 — Evidence retrieval baseline | Page/section aware passages, BM25 non-LLM baseline; begin gold evidence labelling | Discuss chunking/keyword libraries and gold labelling; approve | Baseline queries, ranked passage IDs, Recall@k and errors |
| M3 — RAG experiments | Embeddings, dense/hybrid retrieval, one LLM and structured cited answers | Discuss models, chunking, fusion and prompt constraints; approve | Controlled configs and results; citations, abstentions; cost/latency |
| M4 — LangGraph research tools | One bounded model-directed workflow using deterministic statistical tools | Discuss final tool schemas, evidence budget, errors; approve | Observable state transitions, safe failures, calculation + source proof |
| M5 — MCP + responsible AI | Read-only MCP tool/resource, real protocol client, threat and fault tests | Discuss SDK, transport, boundaries and tests; approve | MCP transcripts, bad arguments, timeout, malicious resource handling |
| M6 — Evaluation and error analysis | >=30 held-out cases, stratified scores, human review, failure diagnosis | Approve evaluation rubric/judge methodology and holdout policy | Full raw run logs, human review sheet, evaluation report |
| M7 — Presentable demo and submission | Sleek thin UI, reproducible setup, required writing and rehearsal | Approve minimal UI stack and scope; approve submission audit | App/demo, README, diagram, system card, innovation report, clean-room verification |

**Critical dependency:** Design evaluation labels and baseline tasks during M1/M2; do not defer all evaluation design until M6. Build automated verification incrementally. MCP and evaluation can be developed in parallel only if they do not compete for shared files or break reproducibility.

## Work allocation guidance
- **Friday 30 Oct:** M1 core source pipeline, report extraction/rights checks, source-data contract; seed evaluation question design.
- **Saturday 31 Oct:** M2 BM25 baseline, evidence labels; M3 first retrieval/LLM path.
- **Sunday 1 Nov:** M3 experiments, M4 LangGraph read-only research flow and arithmetic tools.
- **Monday 2 Nov:** M5 MCP and security failures; M6 run evaluation; begin human review.
- **Tuesday 3 Nov:** Analyze errors, create docs and clean-room install/test; implement thin presentable UI if core is stable; rehearse a demo.
- **Wednesday 4 Nov (morning):** Submit verified repository/package before recruiter's requested deadline.

These are **working priorities**, not guarantees. Do not defer correctness, security or required artifacts to the last evening.

## Milestone approval protocol
Each gate produces a short decision memo:
1. Current milestone purpose; exact requirements/demo IDs.
2. Two or three feasible approaches including a minimal one.
3. Pros/cons, correctness and evaluation impact, complexity and time risks, fallback.
4. Recommended design and key schema/contracts.
5. Precise implementation tasks and acceptance criteria.
6. What files and real evidence will exist upon completion.
7. User authorization request: **implement / revise / defer**.

Once approved, Claude may perform implementation and tests **within the approved milestone**, then stops before the next milestone. Architecture changes, new services, scope expansion and source replacements need fresh approval.

## Minimum demonstration storyline (must be tested, not staged as successful without results)
- Q2 2026 factual official statistic, with exact source locator.
- Cross-source labour analysis with two indicators and MOM's narrative caveat.
- Q1 to Q2 retrenchment change with deterministic arithmetic and inputs.
- Advance Q2 employment +10,700 vs final +11,400 with publication dates.
- One ambiguous/unsupported causal question that correctly abstains.
- One malicious retrieved document or MCP resource ignored as instructions.
- One transient failure recovery and a separate explicit failure case.
- MCP list tools/resources -> invoke tool -> reject invalid request -> timeout handling.
- Retrieval baseline vs improved method with measured quality, latency and cost.

## Scope-control rules
- No user accounts or authentication in the prototype; discuss role-aware authorization in the innovation report and implement read-only boundaries in tools.
- No multi-agent system unless experiments demonstrate it is needed and owner approves.
- No forecasting, unsupported causal inference, scraped blogs or synthetic statistics masquerading as official sources.
- No elaborate cloud/Kubernetes/vector database setup. Local reproducibility is the default.
- A polished UI is welcome **after** core retrieval and evaluation can be demonstrated. Build just: ask, inspect evidence, view charts/traces, compare experiments, inspect sources.

## Failure contingencies
| Blocker | Approved fallback to propose (do not silently enact beyond scope) | Evidence required |
|---|---|---|
| data.gov.sg API unavailable/rate-limited | Manually download official CSV, document access method and sha256, normalize the same way | Official URL, timestamp, hash, reproducible directions |
| MOM PDF download unsuitable/copyright restrictions | Keep local-only PDF; use publisher's official HTML release/summary with explicit locator and limitations | Rights note, link, affected source and evaluation boundary |
| PDF tables malformed | Use structured official CSV for numeric truth; mark PDF table extraction unreliable | Examples, test failure, validation flag |
| Embedding model too slow | Use BM25 and a smaller local model or hosted embedding after owner discussion | Measured speed/quality impact |
| Hosted LLM unavailable | Preserve deterministic baseline and explicit service-unavailable result; don't fabricate LLM evaluation | Logs, reason, incomplete checklist |
| MCP remote transport unstable | Local stdio client/server protocol demonstration using pinned SDK | Actual protocol transcript incl. failure tests |
| UI behind schedule | Minimal but clean Streamlit/NiceGUI or CLI with polished evaluation report; owner approves trade-off | Working core and recorded artifact gaps |
| Incomplete human review | Human review a feasible documented sample, explicitly state size; do not attribute AI review to human | Completed reviewer rows and rubric |

## Final public repository checklist (not met yet)
- [ ] No real credentials, private documents, or copyrighted full-report PDFs in public Git.
- [ ] Setup and CLI/API commands tested from fresh checkout.
- [ ] Data acquisition documented with official source links, licence and reproducibility constraints.
- [ ] Full required assessment matrix has implementation/test/demo evidence.
- [ ] >=30 genuine labelled evaluation cases and measured results; no holdout leakage.
- [ ] Baseline and controlled experiments have versioned configs and raw outputs.
- [ ] Human review was actually performed; unsupported claims corrected.
- [ ] Agent state/trace, tool retries, guardrails and MCP protocol evidence exist.
- [ ] Architecture diagram, data sheet, eval report, model/system card, innovation note and README.
- [ ] Demonstration script rehearsed and failure scenario can be reproduced.
- [ ] Author can answer major design questions without reading generated notes verbatim.


---

# Section 7 — Evidence and study strategy

*Source within the planning pack: `docs/05_EVIDENCE_AND_STUDY_PLAN.md`*

# Evidence ledger, evaluation design and interview learning plan

**Status:** planned process. No ingestion, tests, benchmarks or human reviews have yet been executed in this planning bundle. Never fill the following templates with invented pass/fail results.

## Purpose
The take-home should produce a system **and** a defensible engineering story: hypotheses, choices, failed alternatives, source facts, observed metrics and repeatable demonstrations. Maintain separate public submission artifacts and private learning notes.

## Evidence ledger — record after each authorized milestone

| Evidence type | Required details | Proposed durable location |
|---|---|---|
| Source provenance | Official URL, publisher, licence, publication/retrieval dates, version, hash, rights | `data/manifests/`, `docs/data-sheet.md` |
| Transform/quality | Raw column/row lineage, missing/invalid counts, schema drift, normalization version, source spot checks | `artifacts/data-quality/` |
| Code change | Commit ID, short diff summary, what changed and why, linked tests | `docs/progress.md`, `docs/decisions/` |
| Experiment configuration | Corpus snapshot ID, embedding model, retrieval top-k/fusion, prompt/model IDs, generation options, dependencies | `experiments/configs/` |
| Retrieval evaluation | Case ID, expected evidence, returned IDs and rank, Recall@k/MRR, errors | `experiments/runs/<run_id>/retrieval.*` |
| Generation evaluation | Raw answer, citations, gold answer/behavior, schema/result validation, groundedness review | `experiments/runs/<run_id>/answers.*` |
| Operational metrics | Tokens, provider/model, per-call duration, retries, estimated USD/SGD cost and assumptions, tool success/failures | `experiments/runs/<run_id>/telemetry.*` |
| Safety and MCP | Malicious input fixture, tool/resource payload, rejected arg, expected vs observed outcome, protocol traces | `tests/security/`, `artifacts/mcp/` |
| Human review | Reviewer role/name initials, date, rubric, cases reviewed, per-dimension rating, rationale | `experiments/human_review/` |
| Reproducibility | Command, environment (redacted), version hashes, start time, output/log path, exit code, clean-room steps | `artifacts/verification/` |

**Rule:** measured or verified outcomes require supporting files and exact command or review record. Hypotheses and illustrative figures must be marked as such. Avoid publishing personal identifiers, sensitive environment paths, secrets, or full copyrighted report text in traces.

## Evaluation split / anti-leakage rules
- Draft >=12–15 **development** cases for iterative debugging and >=30 **held-out** cases for final comparison; stratify by factual, synthesis, calculation, ambiguous/unanswerable, conflicting, adversarial.
- Seed questions from domain questions and direct verified sources; label correct observation/passage IDs after stable ingestion ID assignment.
- Assign `case_id`, source snapshot, approved gold evidence, required facts/calc, expected answer behavior and case-type label. Maintain a small rubric for allowable paraphrases.
- Store a hash or immutable version of held-out labels before using them for final benchmark. Do not edit holdout to rescue a poor score.
- Compare B0 non-LLM BM25 extractive baseline, E1 BM25 + fixed LLM, E2 dense + fixed LLM, E3 hybrid + fixed LLM; optional E4 changes only chunking. All other experimental factors held constant for each controlled comparison.
- Report retrieval Recall@5/MRR@5, accuracy by type, groundedness/citation correctness, numeric precision, abstention reliability, latency, costs and errors. If a metric cannot be measured rigorously, label it exploratory.
- Use deterministic grading for exact quantities/schema/citation existence; human-review actual supporting passages for semantic correctness. LLM judge is a supplement with fixed prompt/model, not a substitute for human review.

## Study material after each milestone
Every `study/<milestone>.md` should contain:
1. **In plain English:** What we built, why it exists and what assessment requirement it addresses.
2. **Technical mechanism:** Data flow and critical contracts, illustrated by real inputs/outputs.
3. **Rejected options:** 2–3 alternatives and meaningful pros/cons.
4. **Why our choice:** Practical trade-off based on observed project needs; clearly note any untested assumption.
5. **How we know it works:** Real tests, metrics, manual review and known limitations with file references.
6. **Failure cases:** At least one genuine example (without sanitizing errors away).
7. **Interview preparation:** Five probable questions, concise defensible answer, one deeper follow-up.
8. **Where to inspect code:** Entry points/modules/files and the exact command to reproduce demonstration.
9. **Self-test:** A short quiz; explain the difference between a source fact, model claim and interpretation.

## Suggested study headings
- `study/01-data-ingestion.md`: sourcing, provenance, revisions, licensing, quarter normalization, seasonality.
- `study/02-retrieval-baselines.md`: BM25, chunks, relevancy labels, Recall@5, MRR.
- `study/03-hybrid-rag.md`: embeddings, vector similarity, RRF, context and citation support.
- `study/04-langgraph.md`: state graph, model-directed tools, bounded execution, deterministic arithmetic, retries.
- `study/05-mcp-and-security.md`: host/client/server, tool/resource, schemas, untrusted content, prompt injection.
- `study/06-evaluation.md`: experimental controls, leakage, judge bias, confidence, errors, cost/latency.
- `study/07-production.md`: drift, data versioning, access control, observability, secure government considerations.
- `study/demo-qa.md`: critical design decisions and challenge questions with real project answers.

## 20-minute live demonstration — target outline
- Minutes 0–3: users, problem, approved domain, real official-source architecture.
- Minutes 3–7: factual answer + multi-source synthesis + original source locator.
- Minutes 7–10: deterministic calculation and revised preliminary/final conflict.
- Minutes 10–13: unanswerable and injection case; show trustworthy failure behavior.
- Minutes 13–17: held-out evaluation, baseline vs selected configuration, quality/latency/cost, errors.
- Minutes 17–19: MCP discovery/invocation and failure-handling demo.
- Minute 19–20: limitations, production controls and top two next experiments.

Bring local/replayable **actual** recorded execution traces for reliability, but label replay vs live; demonstrate one live request if reliable. The brief specifies a live 20-minute demonstration and subsequent questions; it does not explicitly mandate a submitted recording.

## Interview questions to practice from Milestone 1 onward
1. Why is a published statistical figure not enough without definition, unit and release date?
2. Why can a quarter be encoded as a month, and how do you prevent bad conversions?
3. What is the difference between immutable snapshot reproducibility and data freshness?
4. Why should PDF table extraction not be used as the sole source for calculations?
5. How do you know advance and final figures represent a revision, not different underlying indicators?
6. How does your pipeline distinguish a missing value from a true zero?
7. What exactly is published under each source's usage licence? Can you commit reports to GitHub?
8. What changes would permission-aware retrieval require in a government environment?
9. What would happen if a data.gov.sg schema changes tomorrow?
10. What exactly did you personally validate, rather than only ask an AI model to verify?


---
