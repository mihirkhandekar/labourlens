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
