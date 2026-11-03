# Architecture detail and history

[Back to the architecture](../architecture.md). This reference retains the implementation detail and historical records moved from the main document on 3 November 2026. The main document describes the current design. Corpus and deployment statements below are dated records, not evidence that a local build was deployed. Decision IDs refer to the [decision log](../decisions.md).

## 1. Overview

LabourLens answers questions from Singapore policy researchers about labour-market statistics and MOM reports. The supported period is 2020-Q1 to 2026-Q2 (D-077, 3 Nov 2026; it was 2024-Q1 to 2026-Q2 for the scope decision record, `docs/decisions/ADR-001-scope.md`, and for every evaluated run). Statistics cover the whole window; since corpus v4 (D-080) quarterly report passages do too, starting with 1Q 2020.

Two kinds of source feed the system.

- **Structured data.** Quarterly datasets from data.gov.sg, published by MOM and SingStat. They are fetched as immutable snapshots, normalised into one observation table and checked by data contracts (structured-data decision record).
- **Reports.** MOM labour-market reports and advance releases. They are parsed into passages with page or section locators. The PDFs are all-rights-reserved, so they and their text stay out of Git.

One bounded LangGraph agent chooses among four read-only tools in the served app: `search_reports` retrieves report chunks, `get_series` returns structured statistical observations, `calculate_change` performs deterministic arithmetic, and `annual_average` computes the simple mean of four quarterly percentage rates. `get_series` maps to MCP server tool `get_statistic`; `annual_average` also crosses MCP. Report search and `calculate_change` stay in process. Search is not run before the agent. The planner sees the question and a catalogue, never passage text. The served planner uses native OpenAI function calling; historical evaluated runs retain the structured-output planner and three-tool base set as library defaults. A deterministic validator checks every answer. Answer statuses are answered, abstained, clarify or refused.

The README (`README.md`) states the current data counts. The data sheet (`docs/data-sheet.md`) records sources, licences and checks.

**Historical served versus evaluated comparison.** The measured served chain added a small-talk fast path, scope check, conversation rewriting and statistics-only MCP lookup to the evaluated core; report search and change calculation remained in process. Final-evaluation entry points (`run_agent`, `agent-exp`, `threat-test`) bypassed the web stages and MCP. The earlier all-three-tools MCP variant was measured on `gpt-6-luna` only (65 cases, one run): accuracy 0.877 against 0.908, not a demonstrated difference, median 14.3 s against 12.4 s, p95 51.4 s against 34.7 s. It was slower without demonstrated gain and is not live. The second model stopped at 17 of 65 at the owner's request and was not rerun ([result](../experiments/served-chain-mcp-all.md#deviations-and-result-recorded-2-november-2026-after-the-run)). The earlier standalone scope check diverted 0 of 333 gold/fresh questions and 1 of 36 threats, catching 30 of 30 off-topic messages (`experiments/triage/triage-v1-luna/metrics.json`). These historical measurements do not evaluate the current four-tool set, prompt versions or context repair.

**Conversation context.** In the served app only, a rewrite stage (`agent/contextualise.py`, current prompt `contextualise_v3`) sits ahead of scope checking. The browser sends at most three earlier turns; the server supplies today's Singapore date. Earlier resolved questions and bounded series/period answer context support a standalone follow-up question and contextual triage, with history treated as untrusted data. Failures fail open to the original message; the audit records original and resolved text, with "Read as: ..." shown when they differ. Small talk is decided on the original message without history. Final-evaluation runs and `threat-test` bypass this stage. The historical 65-case served-chain check used earlier prompts: context was 5/6 for the primary model and 6/6 for the second. Those results do not evaluate the current context repair or measure browser admission.

**Current served changes (3 November 2026, D-083 to D-086, unevaluated).** The served prompt set is `planner_v7`, `answer_v9`, `triage_v4` and `contextualise_v3`. Context assembly carries earlier resolved questions and bounded answer-context series/period metadata into rewriting and triage, framed as untrusted data; failures still fail open. Reasons questions request report search and attribute only publisher-stated drivers, not inferred causes. Answers distinguish unavailable observations from unavailable method or commentary. `annual_average` accepts percentage-rate series only, requires four non-null quarters within the supported window and one consistent series, and rounds a Decimal mean to two places with `ROUND_HALF_UP`. Missing quarters return `not_found` with the missing list, never a partial average; mixed series return `invalid_arguments`. C-labelled calculation evidence records input observation IDs and the method `simple mean of four quarterly rates`. This is not an official published annual rate. No new end-to-end evaluation was run; the measurements below describe the earlier three-tool configuration.

**Corpus versions.** Four corpus states exist. **v1** (13,484 passages) is what every registered held-out and development experiment (the five first-build development runs and the filter-then-rerank and hybrid-search runs on the original 31 test questions) ran on. **v2** (`extract-0.2`, the extraction-fix decision: 15,915 passages, 1,732 `merge200` chunks, 43,662 observations) was used for the extraction-fix run and the first post-fix planted-false-figure attack run. **v3** (v2 plus six labour-only sources): 85 sources (36 datasets, 49 documents), 52,020 observations (4,300 were in the 2024-Q1 to 2026-Q2 answer scope used by every measured run; 11,228 are in the 2020-Q1 to 2026-Q2 scope now served), 16,419 passages, 1,847 chunks, 276 build checks (269 pass, 7 warn at the time; the 3 Nov 2026 rebuild reports 276 checks, 0 failed). Three measured evaluations exist on v3, all on 31 Oct 2026: the regression check, the 31 Oct fixed-system attack run (`docs/experiments/m7-e2e-fixes.md`) and the 65 fresh questions, the first evaluation on evidence-disjoint sources (`docs/experiments/m7-heldout-v2-result.md`). Serving: until the v4 files are shipped the live site serves corpus v3.1 (16,419 passages, 1,847 chunks); `/healthz` shows the commit and the corpus fingerprint (content fingerprint `242e2b284fbc` for v3.1, last checked on 1 Nov 2026).

**v3.1** (`extract-0.3`) is the last evaluated build: same sources, passages and chunk count as v3, with 40 MTI passages relabelled by a refined garbled-text rule; current-corpus evidence includes the final evaluation's two runs, the current-corpus retrieval re-run, the served-chain sample and the fresh 2 Nov attack rerun, beside the earlier re-run of the 65 fresh questions on v3.1.

**v4** (D-080, 3 Nov 2026) is the current local build and the one to be served: v3.1 plus 57 documents (2020 to 2022 quarterly reports, advance and final releases, and 2020 to 2023 job-vacancy, wage-practice and labour-force publications), giving 142 sources (36 datasets, 106 documents), 29,760 passages and 3,632 `merge200` chunks; observations are unchanged at 52,020. The 49 earlier passage files, their passage ids and chunks are byte-identical. It is not evaluated: gold and every frozen result were measured on v3.1. 1,285 chunks need dense vectors before the live container (which never embeds at startup) can start on it (`docs/deploy.md`, `docs/data-sheet.md` section 7a).

The v2 extraction rebuild was byte-identical across two offline builds. PDF parsing uses page-local layout headings, control detection, footer provenance and explicit context-required fragments; HTML parsing stays article-bounded. Context deduplication is limited to identical normalised text within one source snapshot. Gold v3.6 migrates evidence IDs only. The premerge code tag is `corpus-v1-frozen`; private premerge stores are retained separately. Dense embeddings are content- and model-keyed, so unchanged inputs reuse cached vectors even when passage IDs move. See `docs/experiments/m7-corpus-v2-runbook.md` and `docs/experiments/m7-corpus-v3-runbook.md`.

## 3. Data flow from ingestion to cited answer

1. **Fetch.** `src/labourlens/data/fetch.py` and `acquire.py` download each source named in `specs/sources.yaml` and `specs/sources.d/`. `raw_store.py` writes the file under a snapshot id with its SHA-256 hash. Dataset snapshots are committed in `data/snapshots/`. MOM files go to `data/raw/`, which is gitignored.
2. **Normalise.** `data/normalize.py` reads each dataset using its spec in `specs/datasets/*.yaml` and writes one long table, `data/processed/observations.parquet`. Every row keeps indicator, population, seasonal adjustment, unit, release stage and an observation id that leads back to the raw cell (`labourlens trace <id>`).
3. **Validate.** `data/validate.py` runs the data contracts and writes `artifacts/data-quality/quality-report.md`. A dataset that fails its contract is dropped and reported.
4. **Extract.** `pdf_extract.py` and `html_extract.py` split reports into passages. Each passage has an id, a page or section locator and a quality flag. Output is `data/passages/*.jsonl`.
5. **Chunk and index.** `retrieval/chunk.py` merges adjacent `ok` passages within one source and section into `merge200` chunks, targeting about 200 words with up to 40 words of whole-passage overlap. Corpus v4 has 29,760 passages and 3,632 chunks (v3.1, the evaluated build: 16,419 and 1,847). BM25 and text-embedding-3-large vectors index the same chunks. The embedding cache is local and content-keyed; per-build index and corpus metadata identify which chunks the cache represents. `labourlens embed-corpus` fills the missing vectors (dry run by default; `--yes` makes the paid call).
6. **Plan.** The planner receives the question and dataset catalogue, never passage text. It chooses among four fixed tools when served, or the historical three-tool base set under frozen evaluated configuration. It does not retrieve before the loop. Native function calling uses strict schemas, `tool_choice` auto and up to three parallel calls per round; no tool call means finish. Tool messages are untrusted summaries without passage text. Malformed, unknown, wrongly typed or duplicate calls become `invalid_arguments` errors and count against the call budget. Structured-output mode remains the library default and was used by every evaluated run.
7. **Execute tools inside the loop.** `search_reports` returns hybrid-retrieved, filtered and reranked chunks. `get_series` returns validated observations. `calculate_change` computes Decimal changes from returned rows. The served set adds `annual_average`, a simple mean of four non-null quarterly percentage rates from one series. Lookup and annual averaging cross MCP; search and change calculation stay in process. The historical, non-live all-three-tools variant routed its then-current three tools over MCP. No historical comparison evaluates annual averaging. In the served app, tool calls within a round run in parallel, a short-lived cache keyed to the corpus reuses repeated searches, and at most 20 report passages reach the answer prompt per run (D-083 to D-091, unevaluated).
8. **Answer.** `answer/context.py` renders items and notes into the prompt. The model returns a structured answer with claim-level citations, each with a verbatim quote (`answer/schema.py`).
9. **Validate.** `answer/validate.py` rejects an answer when a cited label is not in the context, a quote is not verbatim in the cited item, a quote exceeds 40 words, a flagged item is cited or the status contradicts the content. One repair attempt follows. Numbers in a claim that do not appear in the cited text are reported as ungrounded. Served answers must paraphrase publisher text; when a quote overlaps the source too closely the repair step runs once, and if it still overlaps the clause is dropped with a copyright note (D-090).
10. **Finalize.** The output guard in `security/guards.py` blocks answers that contain a known secret or system-prompt text. The page shows the answer, the evidence behind each citation and the tool timeline.

### Browser pages and public API

`GET /` serves `web/index.html` for the report/presentation; `GET /workbench` and `GET /workbench.html` both serve `web/workbench.html`. These static pages are public even when live research is disabled. All use the same security-header middleware, self-hosted assets and CSP (`script-src 'self'; style-src 'self'`); opening a page does not invoke research.

The workbench uses the existing authenticated `POST /api/ask`, session/status and feedback endpoints, not a new retrieval or audit endpoint. Its public result projects observation values and definition fields (`unit`, `indicator_id`, `population`, `adjustment`, `dimension`, `period`, plus available `missing_reason` and `source_locator`) only from stored observation records. Non-finite observation values become `null`. Optional `usage.prompt_tokens` and `usage.completion_tokens` come from recorded usage, not estimates. Calculation cards identify derived evidence as `calculated`, omit the dataset publication date and use input labels/periods only when present in deterministic calculation text; their source URL still identifies the underlying dataset. Calculation values/units are not guessed. Report text remains limited to bounded, verified cited quotes; full passages, hidden reasoning and private audit records are not exposed.

**Streaming (D-079).** `POST /api/ask/stream` sits next to the unchanged `POST /api/ask` and returns server-sent events: `status` (accepted, contextualise, triage, planning, answering, validating), `tool` (started with tool and arguments; finished with the trace item), `trace` (allow-listed trace items), then exactly one `result` event whose data is the `/api/ask` response body, or one `error` event. No model tokens are streamed: answer text appears only in the `result` event, after deterministic validation. The route has the same session, origin check, rate limits, daily budget reservation, concurrency slot, request-size limit and CSP as `/api/ask`; refusals are ordinary HTTP errors before the stream opens. A keepalive comment is sent every 10 s, and the app sends `X-Accel-Buffering: no`. The graph has an optional `on_event` observer (a no-op by default). The browser client uses `fetch` with a `ReadableStream` (`EventSource` cannot POST) and falls back to `/api/ask` when streaming is unsupported or fails before the first event. A reverse proxy must not buffer this route (`docs/deploy.md`).


## 4. The agent graph

Built in `src/labourlens/agent/graph.py` with LangGraph `StateGraph` (LangGraph decision record). There is one agent with seven nodes.

| Node | Work |
|---|---|
| `validate_question` | Rejects an empty question or one over 1,000 characters. Records heuristic injection flags. |
| `plan_research` | Planner model proposes up to three tool calls, or decides to finish (native function calling when served; structured JSON plan in the evaluated mode). |
| `execute_tool` | Runs each call in a worker thread with a timeout. |
| `assess_evidence` | Counts passages, observations and calculations. Reports an operational failure if every tool call failed. Annotates conflicts between a passage figure and the validated dataset value for the same indicator and period (`answer/crosscheck.py`). |
| `generate_answer` | Answer model writes the structured answer from the evidence. |
| `validate_answer` | Runs the checks in section 3, step 9, and enforces the source-conflict cross-check: a used conflicting level is replaced by the dataset figure with both citations and a caveat. Closed grammar of phrasings; advance and preliminary vintages are preserved. |
| `finalize` | Applies the output guard and sets the outcome. |

Bounds, all constants or fields in `graph.py`:

| Bound | Value |
|---|---|
| Evidence-gathering rounds | 2 |
| Tool calls per run | 6, at most 3 per round |
| Time per tool call | 10 s; 25 s for `search_reports` in the served app, with one retry after a timeout (D-091) |
| Retry for a transient tool failure | 1 |
| Retry for malformed planner output | 1 (structured-output mode only; in function-calling mode a malformed call is an `invalid_arguments` tool error that counts against the call budget) |
| Repair of an invalid answer | 1 |
| Graph recursion backstop | 40 |
| Question length | 1,000 characters |

Graph state holds counters, decisions and the activity trace. Evidence text sits in a per-run registry, not in graph state (LangGraph decision record, item 3). Checkpointing is in memory only.

Outcomes are `answered`, `abstained`, `clarify`, `refused`, `invalid`, `rejected_input`, `blocked_output` and `operational_failure`. A tool outage, a timeout or a planner outage ends in `operational_failure`. It is never reported as missing evidence. Tests for these paths are in `tests/retrieval/test_agent.py`.

## 5. MCP trust boundary

The server is `src/labourlens/mcp/server.py`, built on the official `mcp` SDK. Its default statistics profile now offers ten read-only tools, including `annual_average`, two resources (`labourlens://sources` and `labourlens://source/{id}`) and one prompt. The recorded MCP measurements used nine tools before annual averaging was added. It serves statistics and catalogue metadata, not MOM text by default. The optional `--agent-tools` profile additionally registers report search, change calculation, report-text calculation and corpus description, loads the report corpus and serves passages as untrusted data. The default transport is stdio. An optional loopback HTTP transport with a bearer token is in `mcp/http_server.py`; the Compose sidecar never gets the agent profile.

The client is `src/labourlens/mcp/client.py`. It treats the server as untrusted: allow-listed launch, minimal subprocess environment, name/version checks, tool allow-list, input schemas, deadlines, response-size caps, typed tool-result validation and instruction-like-content quarantine. `mcp/redact.py` redacts secrets. The diagram names controls, not proof that every hostile paraphrase is detected; the saved transcript includes a heuristic miss. Resource handling must be assessed separately from tool-result screening. See `docs/threat-model.md`.

The served web app uses `Shared.stats_backend`, a `SyncStatsBackend`, with `mcp_stats` as the default: `get_series` maps to MCP `get_statistic` and `annual_average` also crosses MCP; search and change calculation remain in process. `LABOURLENS_TOOL_TRANSPORT` selects `direct`, `mcp_stats` or the non-live `mcp_all` variant; `LABOURLENS_MCP=false` selects direct. The historical `mcp_all` comparison routed all three then-current agent tools to one local stdio server started with `--agent-tools`. That profile serves report passages, with truthful `text_served_by_this_server` metadata. The API key remains in the app: the query embedding travels as base64 float32, the server filters and fuses rankings into a 30-chunk pool, and the app reranks. Cached chunk vectors prevent server embedding calls; server calculations recompute from its own table or passages. MCP traces carry `transport: "mcp"` on success and failure. Timeouts, crashes and malformed replies produce typed errors or operational failures, never missing evidence or silent in-process fallback (one reconnect, one transient retry). Historical final-evaluation entry points ran direct. The historical statistics-only served-chain sample (51 development questions plus 14 probes, one run) scored 90.8% for both models, with no observed loss against direct/web-on, not independent evidence. The historical all-tools sample scored 0.877 against 0.908 on `gpt-6-luna`, median 14.3 s against 12.4 s, p95 51.4 s against 34.7 s; not a demonstrated accuracy difference and no gain, so not live. The second model stopped at 17 of 65 at the owner's request and was not rerun ([result](../experiments/served-chain-mcp-all.md#deviations-and-result-recorded-2-november-2026-after-the-run)). The 2 November transcript records real scripted calls and a direct-versus-MCP comparison (median 36.1 ms against 4.5 ms, 1.84 s one-off connect). None of those measurements evaluates annual averaging or current prompt/context changes.

`src/labourlens/mcp/evil.py` is a test fixture. It is a deliberately hostile server and is never on the allow-list.

## 6. Audit log

`src/labourlens/audit/log.py` appends run records to `data/audit/runs-YYYY-MM-DD.jsonl`, feedback to `feedback.jsonl`, and administrative/rejection events to `events-YYYY-MM-DD.jsonl`. With trace saving enabled, `data/runs/agent/<run_id>.json` also contains the detailed run: evidence ids, hashes and the answer's cited quotes. Full retrieved evidence text is stored only when the debug flag `LABOURLENS_DEBUG_EVIDENCE=true` is set. The web runner currently enables trace saving (`src/labourlens/report/app.py`). Those local files are not safe public presentation artifacts; redaction does not confer MOM redistribution rights or anonymise user questions.

A record holds the run id, channel, salted hashes of session and client, the redacted question, model and prompt versions, git commit, data manifest hash, outcome, tool calls with outcomes, guard events, data-quality notes, evidence and cited ids, token usage, cost and latency. Secrets are redacted before every write. Raw IP addresses are not stored. A write failure never breaks a request.

Commands: `uv run labourlens audit-report`, `audit-show <run_id>` and `audit-prune --days N`. Field-level detail is in `docs/audit-and-logging.md`. The `data/audit/` directory is local and not published.

The evaluation branch consumes saved runs rather than changing live answers. The 237 development questions support configuration selection; the original and fresh test questions must not tune prompts or labels. Deterministic scoring checks behavior, evidence IDs and numbers; the LLM judge estimates semantic support and reference-fact coverage. Neither substitutes for the prepared human review sheets. No completed human review or test-question outcome is asserted by this diagram.

## 7. Module map

| Area | Path | Purpose |
|---|---|---|
| CLI | `src/labourlens/cli.py` | All commands: fetch, build, eda, export, serve, agent-exp, threat-test, eval, audit-* |
| Paths and models | `src/labourlens/paths.py`, `models.py` | Directory layout, shared record types |
| Source specs | `specs/sources.yaml`, `specs/sources.d/`, `specs/datasets/` | What to fetch and how each dataset is read |
| Prices | `specs/prices.yaml`, `src/labourlens/prices.py` | Model price table used for cost per case |
| Acquisition | `src/labourlens/data/fetch.py`, `acquire.py`, `raw_store.py`, `catalog.py` | Download, hash and catalogue sources |
| Normalisation | `src/labourlens/data/normalize.py`, `validate.py`, `build.py` | Observation table and data contracts |
| Report parsing | `src/labourlens/data/pdf_extract.py`, `html_extract.py` | Passages with locators |
| Analytics | `src/labourlens/data/reconcile.py`, `derived.py`, `revisions.py`, `eda.py`, `export.py`, `trace.py`, `review.py` | Advance-versus-final reconciliation, derived checks, revision tracker, figures, provenance, review sheets |
| Retrieval | `src/labourlens/retrieval/chunk.py`, `tokenize.py`, `bm25_index.py`, `dense.py`, `runtime.py` | Chunking, BM25, dense and hybrid search |
| Retrieval evaluation | `src/labourlens/retrieval/gold.py`, `evaluate.py`, `experiments.py`, `experiments_dense.py` | Gold-set validator, retrieval metrics, experiment runners |
| Answers | `src/labourlens/answer/schema.py`, `context.py`, `llm.py`, `pipeline.py`, `validate.py`, `experiments.py` | Answer schema, prompt context, model client, validator |
| Agent | `src/labourlens/agent/graph.py`, `tools.py`, `experiments.py` | LangGraph graph, tools, experiment runner; `search_reports` defaults to filter then rerank: quarter and release filter on both candidate lists, then a top-30 LLM rerank; hybrid search (earlier default) and widened filter then rerank (widening when the filtered pool is small) remain selectable; search traces/audit and run usage include rerank metadata/cost |
| MCP | `src/labourlens/mcp/server.py`, `analysis.py`, `models.py`, `client.py`, `http_server.py`, `redact.py`, `demo.py`, `evil.py` | Server, client, real-call fixed-order recording, hostile fixture |
| Security | `src/labourlens/security/guards.py`, `threat_suite.py` | Injection and output guards, adversarial suite |
| Evaluation | `src/labourlens/evaluation/harness.py` | Metrics from saved raw runs |
| Audit | `src/labourlens/audit/log.py` | Run, feedback and event logs |
| Web | `src/labourlens/report/app.py`, `serve.py`, `build.py`, `audit.py`; `web/index.html`, `web/workbench.html`, `web/static/` | FastAPI server and report builder; report/presentation page plus a separate research workbench, self-hosted fonts and no inline script or style |
| Prompts | Historical versioned prompts and matching `_user.md` templates remain untouched; served set: `planner_v7`, `answer_v9`, `triage_v4`, `contextualise_v3` (D-083 to D-086) | Frozen runs retain their pinned prompt hashes; the current served set has not been re-evaluated |
| Tests | `tests/data/`, `tests/retrieval/`, `tests/mcp/`, `tests/web/`, `tests/test_security.py`, `tests/test_audit_and_notes.py` | Unit, integration, protocol and adversarial tests |
| Gold set | `experiments/gold/draft_cases.jsonl`, `CHANGELOG.md`, `ai-review/`, `ai-review-2/` | Evaluation cases and their review history |
| Experiments | `experiments/eval/`, `experiments/runs/`, `experiments/threats/`, `docs/experiments/` | Raw and summarised experiment outputs |

## 8. Key design decisions

| Decision | Reason | Logged in the [decision log](../decisions.md) as |
|---|---|---|
| MOM PDFs and their text stay out of Git | The notices reserve all rights. | Repository and rights |
| Report page as the presentation | Reviewers can open any number and its source. | Report page |
| Passages as JSONL, indexes on disk, no database server | The corpus is small and the files are easy to audit. | Document storage |
| BM25 index persisted with a corpus hash that fails on mismatch | A stale index must not serve old text. | Persisted index |
| Chunks of about 200 words from adjacent good passages | The median passage is too short to retrieve on its own. | Chunking |
| Compare options under a fixed harness and report null results | Choices should rest on measurements. | Experiment policy |
| Gold cases labelled at passage and observation level | Every chunking variant can be scored. | Gold-set authoring |
| Hosted OpenAI embeddings and models, chosen by experiment | Candidates are compared on our own cases and costs. | Embeddings and model selection |
| Claim-level citations with verbatim quotes | A reviewer can check each claim against its quote. | Answer format |
| Prefer declining to a wrong answer | A wrong figure does more harm in policy work than a decline. | Abstention policy |
| One bounded agent, three typed tools when evaluated (four when served), enum-constrained planner | Fewer moving parts and a measurable failure surface. | LangGraph and agent design |
| Code computes every difference and percentage | The model is not trusted with arithmetic. | Agent design |
| Planner never sees passage text | Injected text cannot steer tool choice. | Agent design; MCP and threat controls |
| Operational failures end the run and are never "no data" | A tool outage must not look like an absence of evidence. | LangGraph; MCP and threat controls |
| MCP server with ten read-only tools and a screening client | The server is treated as untrusted even when local; historical measurements used nine tools. | MCP and threat controls |
| Served app routes `get_series` and `annual_average` through MCP; search and change calculation stay in process | The agent has four tools, not the server's full catalogue. The historical all-three-tools variant was slower without demonstrated accuracy gain and is not live. Annual-average routing has not been re-evaluated. | MCP and threat controls; the MCP route; historical served-chain check |
| Structured data scope of 36 datasets through a spec-driven adapter (33 until corpus v3) | One adapter and a spec per dataset keep the cost of each addition low. | Structured-data scope; corpus expansion |
| Labels follow what the evidence supports | One rule makes abstain, refuse and answer cases consistent. | `experiments/gold/CHANGELOG.md`, section v3 |
