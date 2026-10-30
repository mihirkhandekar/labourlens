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
