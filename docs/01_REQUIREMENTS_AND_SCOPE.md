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
