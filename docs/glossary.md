# LabourLens glossary

Plain-English definitions. Add a term the first time it matters. Entries marked (assessment) come from the assessment brief.

## Data and statistics
- **Snapshot:** the exact bytes of a source file fetched at one moment, hashed and never overwritten. Lets an evaluation be rerun later and produce the same numbers.
- **Provenance:** where a fact came from: publisher, URL, file version, row or page.
- **Lineage:** the step-by-step transformation from a raw cell to a normalized value (for example `2026-06` becomes `2026-Q2`).
- **Advance vs final release:** MOM publishes a preliminary quarterly estimate (advance), then a fuller report weeks later (final). Numbers can differ because of revision, not error. Q2 2026 total employment growth: 10,700 advance (31 Jul 2026), 11,400 final (21 Sep 2026).
- **Seasonally adjusted (SA) vs not adjusted (NSA):** SA removes predictable seasonal swings so quarters compare fairly. SA values are revised once a year, so old SA values can change.
- **Percentage vs percentage point:** unemployment moving from 2.7% to 2.9% is +0.2 percentage points, not +0.2%.
- **Ratio vs rate:** the job-vacancy-to-unemployed ratio (for example 1.48) is vacancies per unemployed person, not a percentage.
- **Resident / citizen / overall:** resident = citizens plus permanent residents; overall includes foreigners; citizen = citizens only. Never mix them silently.
- **MDW / FDW:** migrant (or foreign) domestic workers. MOM's headline employment figures exclude them; some other tables may include them. Unresolved for the sector dataset (see `docs/progress.md`).
- **SSIC:** Singapore Standard Industrial Classification; the sector dataset's industry codes follow SSIC 2020 and were revised.
- **Retrenchment:** termination of permanent employees due to [...], plus early termination of term-contract employees [...] (data.gov.sg dataset description).
- **Re-entry rate:** share of retrenched residents who are employed again within 6 or 12 months.
- **Quarantine (data):** rows that fail validation are written to a separate file with the reason, instead of being dropped or silently fixed.
- **Idempotent build:** running the pipeline twice on the same snapshot produces byte-identical output.

## Project vocabulary
- **Observation:** one validated statistical value with its unit, period, population, adjustment and source (`StatisticalObservation`).
- **Passage:** a citable chunk of report text with page or section locator (`DocumentPassage`).
- **Source manifest:** machine-readable record of each source: URL, hashes, dates, rights.
- **Answer scope:** 2024-Q1 to 2026-Q2. Older data may exist in files but is not answerable.
- **Rights review:** a recorded decision on whether a source may be redistributed.
- **Published doc / private note:** published goes to reviewers (`docs/`); private stays with the owner (`study/`, `private/`). See `docs/progress.md`.

## GenAI terms (assessment)
- **BM25:** keyword ranking by term frequency and rarity. The non-LLM baseline.
- **Dense retrieval / embeddings:** meaning-based search over vectors.
- **Hybrid retrieval / RRF:** combine keyword and dense rankings; reciprocal rank fusion merges the lists.
- **Recall@k / MRR:** retrieval metrics: did the right passage appear in the top k; how high did it rank.
- **Groundedness / faithfulness:** whether every claim in an answer is supported by the cited evidence.
- **Abstention:** the system declines to answer when evidence is insufficient.
- **Prompt injection:** malicious instructions hidden in user input or retrieved text.
- **MCP (Model Context Protocol):** standard for exposing tools and resources to AI clients through a server.
- **LangGraph StateGraph:** a graph of steps with typed shared state, used for the bounded research agent (ADR-002).

## Retrieval terms (M2)
- **Chunk:** a retrievable piece of a document, built from one or more extracted passages. It records which passages it contains.
- **BM25:** keyword scoring. A passage scores higher when it contains rare query words, repeated words help with diminishing returns (k1), and long passages are discounted (b).
- **k1, b:** BM25 tuning knobs. k1 controls how fast repeated words saturate; b controls how strongly length is penalised.
- **Stopword:** a very common word (the, of) removed before matching.
- **Stemming:** reducing words to a root (retrenched, retrenchment to retrench).
- **hit@k:** share of questions where at least one correct passage is in the top k results.
- **MRR (mean reciprocal rank):** average of 1/rank of the first correct result; 1 means always first.
- **Held-out set:** evaluation questions frozen before tuning, used once to report honest results.
- **Gold set:** questions with expected evidence and behaviour, labelled for evaluation.
- **MCP (Model Context Protocol):** an open protocol for an AI application's client to discover server capabilities, invoke schema-defined tools and read URI-addressed resources after initialization (protocol revision 2025-11-25, which this project negotiates; the 2026-07-28 revision replaces the handshake with per-request metadata and `server/discover`). Here: stdio by default, optional authenticated loopback HTTP, nine read-only tools, two resources (one URI template) and one prompt. The served web app routes the agent's `get_series` through it (D-053); the accuracy evaluations called statistics directly.
- **Tool vs resource vs prompt (MCP):** the difference is who controls use. A tool is model-controlled: the model-side client asks the server to run it with arguments. A resource is application-driven: read-only content addressed by URI, which the host application chooses to load. A prompt is user-controlled: a template a person picks. Here the agent uses one tool (`get_statistic`); the resources and the prompt are exercised by the demo and the workbench tab only.
- **Prompt injection:** text that tries to give the model instructions, either typed by the user (direct) or hidden in retrieved content or tool output (indirect).
- **Untrusted data:** anything not written by us (retrieved passages, tool output, server metadata). It is labelled as data and never treated as instructions.
- **Canary:** a unique marker string (`PWNED-7731`) an attack asks the model to output. Its presence in an answer body is a deterministic sign the attack worked.
- **Quarantine:** dropping a tool-result row that looks like an instruction, and reporting that, instead of passing it to the model.
- **Fail closed:** on a fault, refuse or report an operational failure rather than continue with partial or invented data.
- **Ablation:** switching defences off to measure what they contribute; here the `+naive` threat-suite runs.
- **Trust boundary:** a line across which data is not trusted: user input, retrieved text, MCP server output.
