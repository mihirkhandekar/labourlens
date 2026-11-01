# Practical GenAI concepts in LabourLens

This note explains design trade-offs, not production certification. Implementation references: [architecture](architecture.md), [decisions](decisions.md), [evaluation](evaluation-report.md) and [MCP transcript](mcp-demo-transcript.md).

## Tokens, context and generation

Tokens are model-specific pieces of text, not words. A context window bounds the combined instructions, question, evidence and generated response. More evidence consumes input tokens, increases cost and can distract the model; truncation may remove the decisive passage. LabourLens retrieves a bounded evidence set rather than sending whole reports. Its approximately 200-word chunks are a retrieval setting, not a 200-token guarantee. Usage records measure actual tokens; configured completion limits bound output length.

Temperature and top-p change sampling diversity; low temperature does not guarantee correct or repeatable facts. The model wrapper uses provider-default sampling where controls are unset, not an asserted zero-temperature setting. Structured generation constrains shape, not truth. Hosted model identifiers and provider behavior may drift, so retain prompts, settings and evidence snapshots alongside results.

## Retrieval, chunks and ranking

An embedding maps text into a vector: similar meaning should produce nearby vectors. Dot product depends on vector direction and magnitude; cosine similarity divides by both vector lengths. LabourLens normalizes vectors, making dot product equivalent to cosine similarity. This enables semantic retrieval, but cannot guarantee exact figures, dates or definitions.

Chunking trades context against specificity. Tiny PDF blocks lose surrounding meaning; large chunks dilute matches and spend more context tokens. The `merge200` configuration combines adjacent good passages while retaining source passage IDs and page locators. Tables and garbled extraction need separate handling; an embedding cannot repair incorrect extraction.

BM25 is the lexical, non-LLM baseline. Dense retrieval can find paraphrases. Hybrid retrieval uses reciprocal rank fusion (RRF): add contributions based on each candidate's rank rather than comparing incompatible raw score scales. Metadata filtering narrows periods and release stages. R3 then reranks the candidate pool with an LLM. Reranking costs another model call and cannot recover an absent candidate; hard filters can exclude a later report restating an earlier period. Inspect candidate recall before blaming answer generation. Wrong evidence is a retrieval error; misusing sufficient evidence is a generation error.

## Prompt and context engineering

Instruction hierarchy separates application rules from user requests and untrusted evidence. A report passage or MCP response is data, never authority to change tools or disclose secrets. LabourLens labels evidence, constrains planner choices, validates arguments and checks outputs; delimiters alone do not defeat injection. The planner does not receive passage text. The answer model receives selected evidence with labels and provenance, not unrestricted documents.

Few-shot examples demonstrate desired behavior but consume tokens and can bias answers toward their patterns. JSON schemas enforce allowed fields and types more reliably than examples; neither proves claim support. Versioned prompts plus deterministic citation and status checks allow controlled comparisons. Quote containment is weaker than semantic entailment.

Prompt caching can reuse a stable instruction prefix, reducing repeated input processing where the provider supports it. It is distinct from cached embeddings, saved answers and judge results. Do not claim measured prompt-cache savings without usage evidence. Cache keys must bind relevant model/prompt/evidence inputs; stale judge judgments can invalidate an otherwise reproducible evaluation.

## Evaluation and oversight

Offline evaluation scores saved cases under fixed configurations; development cases guide changes and held-out cases estimate generalisation without tuning. Online evaluation studies real usage, feedback and failures after release. Feedback is not automatically a gold label or an experiment. Protect questions and separate operational monitoring from assessment scores.

Deterministic checks cover status, evidence IDs, schemas and calculations. LLM judges estimate semantic support but can share the generating model's biases, miss subtle numerical errors and favor fluent answers. Report denominators, strata, cost, latency and uncertainty, not only aggregate accuracy. Human review must check apparently successful answers as well as failures and calibrate the rubric. LabourLens has prepared sheets; AI review is not completed human review. A confidence interval does not correct biased labels or test leakage.

## Agents, workflows and MCP

A workflow fixes execution steps; an agent makes bounded choices within them. LabourLens uses one StateGraph workflow with a model-directed planner and three typed read-only tools. State tracks counters and evidence references; in-memory checkpoints are not durable user memory. Deterministic code performs changes. Idempotent read-only calls permit bounded retries, but deadlines do not necessarily cancel underlying work. Distinguish operational failure from insufficient evidence. No consequential write tool exists; adding one would require explicit authorization and approval design.

The MCP host is the AI application; its client manages a connection to a server exposing capabilities. Lifecycle (protocol revision 2025-11-25, the one this project negotiates; the 2026-07-28 revision replaces the handshake with per-request metadata and `server/discover`): connect, initialize/negotiate, discover tools/resources/prompts, invoke or read, validate results, close. The client records the protocol version and server capabilities that were actually negotiated, and lists resources or prompts only if the server declared them. This server exposes nine tools, two resources (one URI template) and one prompt over stdio, with optional authenticated loopback HTTP. Resources carry catalogue metadata, not MOM passages. Discovery and schemas do not make a server trustworthy; allow-lists, quarantine, deadlines and secret isolation remain necessary. Direct calls are simpler within one process; MCP adds interoperability and a process boundary with connection/validation overhead. The served app pays it for `get_series` (median 22.7 ms against 4.4 ms per call, about 1.9 s once at startup); the accuracy evaluations used direct calls.

## Production decisions still requiring evidence

Track configuration and corpus versions, failures, evidence IDs, token usage, p95 latency and estimated cost without exposing secrets or restricted text. Budget admission and rate limits bound demand, not provider billing. Model routing could reserve expensive reranking for difficult cases, but needs a quality/cost comparison before adoption. Canary questions, drift alerts and human-reviewed release gates are proposals, not deployed monitoring. A fallback must disclose its provenance and must not disguise an outage as “no evidence.”
