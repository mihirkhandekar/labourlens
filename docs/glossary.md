# LabourLens glossary

## How to read the ids

The documents use plain names ("the first run", "the 65 fresh questions", "filter then rerank"); the last column maps each to the internal id used in folders, files and commands.
A `D-0nn` id is an entry in the [decision log](decisions.md); every other id is an experiment, run, case or file name.

## Plain names and internal ids

| Plain name | What it is | Where to find it | Internal id |
|---|---|---|---|
| The final evaluation, first run | The first of two complete runs of the system on the development, original test and fresh questions, on document build v3.1 | [evaluation report](evaluation-report.md#headline-the-final-evaluation-two-runs-averaged); `experiments/eval/` | `FIN` (folders `agent-*-FIN-*`) |
| The final evaluation, second run | The pre-registered repeat of the first run; the headline is the mean of the two | [registration](experiments/fin2-replicate.md); [`final-mean.json`](../experiments/eval/final-mean.json) | `FIN2` (folders `agent-*-FIN2-*`) |
| The two-run mean | The average of the first and second run of the final evaluation; the headline | [`final-mean.json`](../experiments/eval/final-mean.json) | `scripts/final_mean.py` |
| The 237 development questions | Questions used while building the system | `experiments/gold/draft_cases.jsonl` | split `dev`, case ids `DEV-nnn` |
| The original 31 test questions | The first held-out set; shares evidence with development | `experiments/heldout/` | split `heldout`, case ids `HO-nnn` |
| The 65 fresh questions | A later set written on six sources no earlier case cites; reused for diagnostics and the second run | `experiments/gold/heldout_v2_v1.jsonl`; [registered result](experiments/m7-heldout-v2-result.md) | held-out v2, case ids `HO-V2-nnn` |
| Filter then rerank | Restrict passages by period and release, then let a model reorder them | [evaluation report](evaluation-report.md) | retrieval `r3` (`R3` in retrieval ladders) |
| Hybrid search | Keyword (BM25) plus embedding search, merged by rank fusion; the baseline | [evaluation report](evaluation-report.md) | `hybrid` (`R0` in retrieval ladders) |
| Period filter only; rerank only; widened filter | The other retrieval settings in the ladder | [evaluation report](evaluation-report.md) | `R1a`; `R2`; `r3w` |
| Baseline, prompt-change, filter-then-rerank, widened-filter and planner-prompt runs | The five first-build development runs | `experiments/eval/agent-dev-A*` | `A1`, `A2`, `A3`, `A4`, `A5` |
| Extraction-fix run | Development run on the corpus with the parsing corrections | [evaluation report](evaluation-report.md) | `X1` (`agent-dev-X1`) |
| Regression check | Development run of the served system on corpus v3, with the 14 runtime fixes | [regression report](../experiments/eval/agent-dev-X2-REPORT.md) | `X2` |
| Second tool set | Arithmetic on figures printed in reports; tested, not adopted | [design and plan](experiments/m7-tool-fix.md) | tool set v2, run `X3`, post-freeze diagnostic `V2post` |
| Post-freeze diagnostic | Re-run of the 65 fresh questions with the second tool set, after the freeze; optimistic by construction | [evaluation report](evaluation-report.md) | `V2post` |
| The 14 runtime fixes | Fixes from the end-to-end review | [list](experiments/m7-e2e-fixes.md) | `B1` to `B14` |
| Current-corpus retrieval re-run | The retrieval ladder on build v3.1, 128 development report questions | [summary](../experiments/runs/dev-R-V31/SUMMARY.md) | `dev-R-V31`, tag `V31` |
| Same-set retrieval comparison | Keyword against embeddings against hybrid on the same 128 questions | [summary](../experiments/runs/dev-R-V31-methods/SUMMARY.md) | `dev-R-V31-methods` |
| Served-chain check | The web app's full chain (small-talk, rewrite, scope check, agent with MCP) on 65 mixed cases | [registration](experiments/served-chain-eval.md); [all-tools variant, pre-declaration and result](experiments/served-chain-mcp-all.md) | `S65`, folders `served-dev-S65-*`, probes `SERVED-Pnn` |
| All-three-tools MCP variant | The served app with search, series lookup and calculation all over MCP; built and measured on one model, slower with no accuracy gain, not live (the live route sends only the statistics lookup) | [pre-declaration and result](experiments/served-chain-mcp-all.md) | `mcp_all`, `S65-mcpall`; live route `mcp_stats` |
| Statistics tool removed | An experiment-only route of the served chain: the planner can search reports and calculate changes but cannot look up statistics; used to measure what the statistics store adds. Accuracy 0.692 against 0.908 with the tool, on 65 questions, one run | [pre-registration and result](experiments/served-chain-no-stats.md) | `no-stats`, `S65-nostats-b` (first attempt `S65-nostats` was interrupted and not used) |
| Second-judge check | A second-family AI judge re-scoring one saved sample; not human review | [declaration](experiments/second-judge.md); [summary](../experiments/xjudge/sonnet55-FIN-s60-b-20261102/SUMMARY.md) | `sonnet55-FIN-s60-b-20261102` |
| Attack suite | 36 hand-written attack cases with deterministic checks | [threat model](threat-model.md) | `experiments/threats/`, case ids `T-Dnn`, `T-Inn` |
| First scorer; second scorer | The two scoring rules for the planted-false-figure attack; the second allows the planted figure inside a disclosed-conflict caveat and was written after outputs were seen | [rule](experiments/t-i06-scorer-v2-rule.md) | scorer `v1`; scorer `v2` |
| Second scanner version | The rewritten ingestion scanner (markup stripping, leetspeak decoding, two-fragment window), evaluated offline on 120 passages | [declaration](experiments/injection-scanner-v2.md); [threat model](threat-model.md) | scanner v2 |
| Planted-false-figure attack | The one attack not reliably stopped: a passage plants a wrong figure | [threat model](threat-model.md#t-i06-v2-diagnostics-and-fresh-2-nov-rerun-d-060-d-061) | case `T-I06` |
| The 31 Oct attack run on the fixed system | Attack suite after the end-to-end fixes | `experiments/threats/m7-e2efix-20261031/` | `m7-e2efix-20261031` |
| The 31 Oct post-fix attack run | Attack suite after the source-figure cross-check | `experiments/threats/m7-ti06-postfix-20261031/` | `m7-ti06-postfix-20261031` |
| The fresh 2 Nov attack rerun, and second-scorer rescoring | New generation, and rescoring of old outputs, with the second scorer | [rule](experiments/t-i06-scorer-v2-rule.md); `experiments/threats/ti06-v2-*` | `ti06-v2-fresh-20261102` and siblings |
| Document builds | Versions of the parsed corpus: v1 first experiments, v2 extraction fixes, v3 plus six labour-only sources, v3.1 current | [data sheet](data-sheet.md) | `extract-0.2`, `extract-0.3` |
| Gold versions | Versions of the reference-answer file; later ones change provenance, not labels | `experiments/gold/CHANGELOG.md` | v3.2 to v3.7 |
| Owner review decisions | The ten methodology and acceptance choices recorded in the review | [review records](human-review/README.md) | `J1` to `J10` |
| Requirement numbers | Rows of the assessment requirements matrix | [requirements matrix](requirements-matrix.md) | `R01` to `R10` |
| Milestone file names | Experiment write-ups named after the build milestone they belong to | `docs/experiments/` | `m2-` to `m7-` prefixes |
| Scope, LangGraph and structured-data decision records | Approved architecture decision records | `docs/decisions/` | `ADR-001`, `ADR-002`, `ADR-003` |

## Decision log ids

The decision log ([decisions.md](decisions.md)) numbers its entries `D-000` to `D-069`. Only the ones that public documents still need are listed.

| Plain name | Id |
|---|---|
| Domain, scope and LangGraph architecture | D-000 |
| Repository private then public; published and private documents | D-001, D-002, D-057 |
| Structured data expanded beyond the four approved datasets | D-003 |
| Raw dataset CSVs, documents, UI, storage, chunking | D-004 to D-015 |
| Experiment policy, gold-set authoring, model selection by experiment | D-016 to D-018, D-022 |
| Corpus expansion and its cap | D-019, D-020 |
| Hosted embeddings; answer format; abstention policy | D-021, D-024, D-026 |
| Agent design and its three tools; MCP server and threat controls | D-027, D-028 |
| Retrieval improvements and default retrieval | D-029, D-030 |
| Supported analysis period is a hard scope | D-031 |
| Planner prompt tested, not adopted | D-032 |
| Original test run, post-run gold adjudications and owner review | D-033 to D-036 |
| Extraction corrections; corpus v2 working corpus | D-037, D-041 |
| Source-figure conflict guard | D-038 |
| Fresh-question design, corpus v3 and acceptance rule | D-039, D-040, D-042 |
| End-to-end review fixes; regression check | D-043, D-044 |
| Fresh-question result | D-045 |
| Second tool set: plan and result | D-046, D-048 |
| Out-of-period policy | D-047 |
| Review wording | D-049 |
| Small-talk fast path; scope check; conversation context | D-050, D-051, D-054 |
| Corpus v3.1 | D-052 |
| MCP route for statistics (live); all three tools over MCP (built and measured, not live) | D-053, D-066 |
| Statistics-tool ablation (statistics tool removed) | D-069 |
| Fresh questions re-run on v3.1 | D-055 |
| The final evaluation headline | D-056 |
| Served-chain check; retrieval re-runs | D-058, D-059 |
| Second scorer for the planted-false-figure attack | D-060 |
| The headline becomes the mean of two runs | D-061 |
| All-three-tools MCP variant | The served app with search, series lookup and calculation all over MCP; built and measured on one model, slower with no accuracy gain, not live (the live route sends only the statistics lookup) | [pre-declaration and result](experiments/served-chain-mcp-all.md) | `mcp_all`, `S65-mcpall`; live route `mcp_stats` |
| Second-judge check | D-062 |
| Same-set retrieval comparison | D-063 |
| Audit fixes; scanner v2 | D-064, D-065 |

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

## Retrieval terms
- **Chunk:** a retrievable piece of a document, built from one or more extracted passages. It records which passages it contains.
- **BM25:** keyword scoring. A passage scores higher when it contains rare query words, repeated words help with diminishing returns (k1), and long passages are discounted (b).
- **k1, b:** BM25 tuning knobs. k1 controls how fast repeated words saturate; b controls how strongly length is penalised.
- **Stopword:** a very common word (the, of) removed before matching.
- **Stemming:** reducing words to a root (retrenched, retrenchment to retrench).
- **hit@k:** share of questions where at least one correct passage is in the top k results.
- **MRR (mean reciprocal rank):** average of 1/rank of the first correct result; 1 means always first.
- **Held-out set:** evaluation questions frozen before tuning, used once to report honest results.
- **Gold set:** questions with expected evidence and behaviour, labelled for evaluation.
- **MCP (Model Context Protocol):** an open protocol for an AI application's client to discover server capabilities, invoke schema-defined tools and read URI-addressed resources after initialization (protocol revision 2025-11-25, which this project negotiates; the 2026-07-28 revision replaces the handshake with per-request metadata and `server/discover`). Here: stdio by default, optional authenticated loopback HTTP, nine read-only tools, two resources (one URI template) and one prompt. The served web app routes the agent's `get_series` through it (D-053). Full-set FIN/FIN2 evaluations used direct statistics calls; D-058/D-061 measured the served route in one 65-case sample, with no observed loss against direct but no demonstrated gain or equivalence.
- **Tool vs resource vs prompt (MCP):** the difference is who controls use. A tool is model-controlled: the model-side client asks the server to run it with arguments. A resource is application-driven: read-only content addressed by URI, which the host application chooses to load. A prompt is user-controlled: a template a person picks. Here the agent uses one tool (`get_statistic`); the resources and the prompt are exercised by the demo and the workbench tab only.
- **Prompt injection:** text that tries to give the model instructions, either typed by the user (direct) or hidden in retrieved content or tool output (indirect).
- **Untrusted data:** anything not written by us (retrieved passages, tool output, server metadata). It is labelled as data and never treated as instructions.
- **Canary:** a unique marker string (`PWNED-7731`) an attack asks the model to output. Its presence in an answer body is a deterministic sign the attack worked.
- **Quarantine:** dropping a tool-result row that looks like an instruction, and reporting that, instead of passing it to the model.
- **Fail closed:** on a fault, refuse or report an operational failure rather than continue with partial or invented data.
- **Ablation:** switching defences off to measure what they contribute; here the `+naive` threat-suite runs.
- **Trust boundary:** a line across which data is not trusted: user input, retrieved text, MCP server output.
