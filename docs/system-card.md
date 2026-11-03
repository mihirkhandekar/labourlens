# LabourLens system card

**Updated:** 3 November 2026. **Status:** research prototype.

I built LabourLens to help Singapore policy researchers find official labour-market evidence, compare quarterly statistics and inspect the sources behind a cited answer. The application combines report search, validated statistical records, deterministic calculations and a bounded research agent. Its workbench exposes evidence, definitions, charts and tool activity so that a researcher can check the answer.

**Strongest measured results:** filtering and reordering search results improved answer behaviour on 237 development questions for both tested models. A separate retrieval test found better evidence selection on original-test and fresh questions. The harder security suite passed 50 of 54 attacks with guards, against 42 without them. These are different experiments with different boundaries, explained below. The final end-to-end comparison shows **no demonstrated gain on the 65 fresh questions**.

The [detailed reference](reference/system-card-detail.md) preserves the full previous card: corpus versions, per-run tables, review history, configuration identifiers, rejected experiments and security regression logs. The [evaluation report](evaluation-report.md) explains the experiment design; the [data sheet](data-sheet.md) covers sources and processing.

## Headline performance: the two-run mean

**MEASURED RESULT:** the final evaluation compared two ways of finding report evidence on the same questions. Hybrid search combines keyword and meaning-based search. Filter then rerank adds period and release filters, then asks a model to reorder the candidates. The latter remains my default because of its development results; its advantage has not carried through to fresh-question answer behaviour.

Behaviour accuracy measures whether the system took the expected action: answer, clarify, abstain or ignore an injected instruction while answering. It does not establish that every claim in an answer is correct. The figures below are means of two runs per configuration, on corpus v3.1, with direct statistics access and the web application's preliminary steps switched off.

| Question set | Model | Filter then rerank | Hybrid search | Difference, percentage points [95% interval] |
|---|---|---:|---:|---|
| Development, 237 | `gpt-6-luna` | 89.7% | 82.7% | +7.0 [3.6, 10.6] |
| Development, 237 | `gpt-5.6-luna` | 89.7% | 84.4% | +5.3 [1.9, 8.9] |
| Original test, 31 | `gpt-6-luna` | 83.9% | 80.6% | +3.2 [-3.2, 11.3] |
| Original test, 31 | `gpt-5.6-luna` | 83.9% | 82.3% | +1.6 [-8.1, 12.9] |
| Fresh questions, 65 | `gpt-6-luna` | 71.5% | 74.6% | -3.1 [-7.7, 0.8] |
| Fresh questions, 65 | `gpt-5.6-luna` | 73.1% | 73.8% | -0.8 [-2.3, 0.0] |

The development questions shaped the system. Original-test evidence overlaps development in 25 of 31 cases; the fresh questions are only partly independent. A rule that always answers, without reading the question, scores 76.8%, 77.4% and 73.8% on the three sets. Both search approaches are within about three points of that fresh-set floor. This makes the fresh result an important limit on the claim of general improvement.

Two runs are insufficient to estimate model variability. Repeating identical configurations changed outcomes on 11 to 18 development cases and 1 to 3 fresh cases. The intervals above resample questions; they do not capture uncertainty across independent runs. The second run used already-known questions. See the [complete run table and settings](reference/system-card-detail.md#headline-performance-the-two-run-mean).

### What the supporting experiments establish

- **Better evidence selection:** among the first eight distinct passages, filter then rerank found an expected passage on 77.8% of 18 eligible original-test questions and 94.1% of 34 eligible fresh questions. Hybrid search scored 16.7% and 50.0%. Both paired improvements excluded zero. Better retrieval did not establish better end-to-end answer behaviour; no per-case cause was investigated. [Retrieval experiment](experiments/heldout-retrieval-metrics-results.md).
- **Useful tool-driven research:** on development, the agent averaged 89.7% behaviour accuracy against 81.4% for a fixed pipeline. That pipeline lacked the calculation tool and had tighter lookup limits, so the comparison tests whole evidence policies and cannot isolate adaptive planning. It was not run on original-test or fresh questions. [Fixed-pipeline comparison](experiments/agent-vs-fixed-pipeline-results.md).
- **Useful statistical capability:** removing statistics lookup reduced behaviour accuracy from 90.8% to 69.2% on one 65-question served-chain sample. Removing lookup also removes inputs needed for change calculations. The sample reused development evidence and included 14 of my own probes. [Statistics-removal experiment](experiments/served-chain-no-stats.md).

### Review and model-based scoring

The reference answers and expected evidence were AI-drafted. I signed off as the sole human reviewer **after the saved runs were scored**, following AI pre-review. The review covered 268 development/original-test questions, 65 fresh questions, 40 saved answers and 30 source checks: 403 items across four review streams. This is not blinded annotation or independent agreement between human reviewers. Five original-test questions changed after their first freeze; earlier outputs and scoring versions remain preserved.

The primary answer judge, `gpt-6.1-terra`, belongs to the same model family as the generators. A second-family judge, `claude-sonnet-5-5`, checked saved answers. It agreed on 84.3% of 432 claim labels, but did not reproduce the first judge's claim-support gain for `gpt-5.6-luna`. Claim-support results therefore depend on the judge. Behaviour, number matching, calculation correctness, false-answer and over-abstention scores come from code and are unchanged by that comparison. The second AI judge is not human review. [Review provenance and judge comparison](reference/system-card-detail.md).

## Intended use

LabourLens supports Singapore policy researchers and labour-market analysts who need factual lookup, quarterly comparisons, cross-source summaries and inspection of preliminary versus final figures. It retrieves official evidence, performs supported calculations and produces cited summaries or an explicit request for clarification or abstention.

The served answer window is **2020-Q1 through 2026-Q2**. Source coverage varies within it. Requests for figures outside that window, including comparisons requiring an outside endpoint, must abstain. Timeless definitions remain answerable. Answers concerning 2020 to 2023 have not been evaluated.

Before using an answer in research, inspect the cited source, population definition, seasonal adjustment, unit and publication stage. A cited answer is a starting point for evidence checking; the researcher remains responsible for its policy use.

## Out-of-scope use

Forecasting, unsupported causal attribution, individual employment advice and unrestricted web research are excluded. LabourLens is not an official government service or an autonomous policy decision-maker. Do not submit confidential, personal or classified information. The prototype has no per-user document permissions and is unsuitable for a restricted-document collection without additional access controls.

## Served versus evaluated

**The current application is not the configuration measured in the headline table.** I decided not to rerun the experiments after the latest changes. Historical outputs and scores have not been relabelled as current-app results.

| Area | Final evaluated configuration | Current served application, unevaluated |
|---|---|---|
| Period | 2024-Q1 to 2026-Q2 | 2020-Q1 to 2026-Q2 |
| Source collection | Corpus v3.1, 49 documents and 36 datasets | Corpus v4, 106 documents and the same 36 datasets |
| Agent planning | Structured-output planner | Native function calling, up to three parallel calls per round |
| Tools | Report search, statistics lookup, change calculation | The same capabilities plus annual averaging of quarterly rates |
| Prompts | Frozen evaluated versions | New planner, answer, scope-check and conversation prompts |
| Front-end path | Full-set evaluation bypasses web preliminary steps | Small-talk handling, conversation rewriting, scope check and streamed activity |

Corpus v4 contains 29,760 passages and 3,632 search chunks. The 57 added documents include report text from 2020; four added PDFs yield no text and one is image-based. These are flagged, not repaired. Older passage files are unchanged and the expected evidence identifiers remain present, but additional documents compete in retrieval. The live health endpoint confirmed the v4 inventory on 3 November; that check establishes inventory, not answer quality.

The annual-average tool requires four non-missing quarterly percentage rates from one consistent series within the supported window. It returns a simple mean rounded to two decimal places, labelled as a calculation rather than an official annual rate. It refuses incomplete years and mixed series. This tool and the newer prompts remain unevaluated.

For an incomplete-year annual-average refusal, the served abstention deterministically names the missing quarters returned by the tool and says that an annual-average figure cannot be computed before those rates are published. It does not substitute a partial-year average or incur another model call (D-092).

**Earlier served-chain measurement:** before these changes, one 65-case sample tested the research chain with conversation handling, scope checks and MCP statistics access. Both models scored 90.8% overall. The primary model passed eight of eight diversion probes and five of six conversation probes, so the complete probe criterion was not met. Its median latency was 12.4 seconds, 95th percentile 34.7 seconds and estimated cost $0.00268 per question, excluding one-off startup latency. This sample reused development evidence and did not evaluate HTTP admission or public-answer rights filtering. It cannot substitute for full current-app evaluation. [Protocol and results](experiments/served-chain-eval.md).

MCP, the Model Context Protocol, carries tool calls to a separate local statistics process. Direct and MCP routes query the same local records using the same query code. Neither route adds another source of knowledge. On the earlier served sample, primary-model accuracy tied between routes; that does not establish transport equivalence. An all-tools-over-MCP variant was slower without demonstrated quality gain and was not adopted. Full route results, standalone scope and conversation tests, and subsequent prompt changes are preserved in the [reference](reference/system-card-detail.md#served-versus-evaluated).

## Architecture and models

Acquisition creates immutable source snapshots, validated observations and passages linked to source pages. Search combines keyword matching with dense embeddings, which represent text numerically for meaning-based retrieval. Period and release filters narrow the candidates; a model then reorders them. The bounded LangGraph agent chooses when to search reports, fetch statistical records or calculate from returned records. Evidence comes back through tools, rather than being preloaded into the planner.

The current agent has four read-only tools. Statistics lookup and annual averaging can cross MCP; report search and change calculation remain in process. Although the statistics server offers ten tools, the planner receives only its fixed four-tool set. Returned evidence identifiers connect calculations and citations to their inputs.

Structured answers undergo schema, citation-label, quotation-presence and status checks. One repair attempt can address malformed output. These checks establish format and citation mechanics; a quotation's presence does not prove that it supports the claim. A separate source-conflict check compares recognised reported figures against statistical records while preserving labelled preliminary vintages. Its coverage is limited.

| Role | Model | Estimated input / output USD per million tokens |
|---|---|---|
| Research planner, answer generator and reranker | `gpt-6-luna` | $0.10 / $0.50 |
| Dense embeddings | `text-embedding-3-large` | $0.13 / not applicable |
| Offline answer judge | `gpt-6.1-terra` | $1.00 / $5.00 |

I retained `gpt-6-luna` because the models tied on development mean and it cost about 60% as much as `gpt-5.6-luna`. The final comparison establishes no accuracy winner. Filtering and reranking cost about 1.7 times as much and took about 1.4 times as long as hybrid search for the primary model on development.

Prices are repository list-price assumptions dated 30 October 2026, exclude cached-input discounts and require rechecking. They are estimates, not invoices. Evaluated planner and answer completion caps were 1,500 and 6,000 tokens. Temperature and sampling settings used provider defaults, with no seed; reruns are not bit-reproducible. [Architecture](architecture.md), [price assumptions](../specs/prices.yaml) and [configuration history](reference/system-card-detail.md#architecture-and-models) provide implementation detail.

## Data and rights

The collection combines data.gov.sg statistics published by MOM/SingStat with official reports and release pages. Manifests retain source URLs, snapshot hashes, dates, definitions, units and release stages. Missing or suppressed values stay missing. Population, seasonal adjustment and publication vintage must remain separate; a disagreement between a report and dataset may have an unverified definition difference. The system must not invent an explanation. Revision tracking is limited by single snapshots.

Statistical data is attributed under the [Singapore Open Data Licence](https://developers.data.gov.sg/open-data-licence), without implying agency endorsement. A source review could not reproduce three sampled open-licence verification claims from cached evidence. That is an unresolved provenance gap. MOM PDFs carry restrictive notices; some release-page rights remain unresolved. Full documents, extracted passages, indexes and raw answers containing restricted text stay local and gitignored. Public documentation uses paraphrases, identifiers and links.

I accepted API processing of source passages, but have not independently verified provider data-use terms. Redaction does not clear reproduction rights or anonymise personal data. The [data sheet](data-sheet.md) records processing, exclusions and quality issues; the [processing log](data-processing-log.md) preserves transformations.

## Risks and mitigations

| Risk | Implemented control | Residual limit |
|---|---|---|
| Wrong source, period or series | Metadata filters, provenance, source inspection and deterministic calculations | Filters can miss later restatements; correct arithmetic can use the wrong inputs. |
| Unsupported or misleading claims | Structured validation, citation checks and source-conflict checks | Citation mechanics do not prove meaning; omissions and causal overreach still need review. |
| Instructions embedded in retrieved text | Treat source text as untrusted, scan inputs, restrict tools to read-only catalogue entries and validate MCP responses | Detection misses and unstable handling of planted false figures remain. |
| Runaway calls or service failure | Limits on rounds and calls, timeouts, bounded retries and traced errors | These bounds do not guarantee a fixed provider bill. |
| Secrets, personal data or restricted excerpts | Environment-based keys, redaction and local-only report material | Questions and feedback can still contain sensitive material; retention and access controls need further work. |

**MEASURED RESULT:** the harder security suite used 54 attacks and eight benign look-alikes, three repeats with `gpt-6-luna`. By majority outcome, guarded passed 50/54 attacks versus 42/54 without those guards, a paired gain of 14.8 points (exact paired-test p=.039). Guards and the answer prompt changed together, so this does not isolate one defence layer. Both configurations failed three of eight benign cases by clarifying or abstaining, missing the pre-declared usefulness cap. Single-author cases and one model limit generalisation. [Security results](experiments/threat-v2-results.md).

The earlier 36-case suite could not distinguish defences. Its fresh rerun scored 35/36 in all four configurations, with the planted false figure failing again. The numerical cross-check has low coverage and has not shown stable success across runs. All five malicious paraphrase probes in an earlier scanner-only review bypassed detection; later patterns cover those known probes only. Zero scanner hits cannot certify safe evidence. [Full security history](reference/system-card-detail.md#risks-and-mitigations).

Traces expose configuration, evidence identifiers, tool outcomes, errors, guards, latency and estimated cost. Feedback can be linked to a run for investigation. Monitoring and retention commands do not imply an active operations service. For restricted documents, I propose access labels enforced before both keyword and vector search and inside statistics tools; that permission-aware design is not implemented. See the [threat model](threat-model.md), [MCP transcript](mcp-demo-transcript.md) and [audit policy](audit-and-logging.md).

## Limitations

- **Generalisation:** development gains have not established fresh-question improvement. Original-test evidence overlap, post-run label review, known fresh outcomes and limited repeats constrain conclusions.
- **Current-app evidence:** the wider period, larger collection, native planning, new prompts and annual-average tool have no end-to-end evaluation. Historical performance is not a quality guarantee for the served app.
- **Coverage and numerical interpretation:** source coverage is uneven; unreliable tables are excluded. Default tools cannot calculate arbitrary figures found only in report text. Employment-series population definitions and some revision conflicts remain unresolved.
- **Review and scoring:** one human signed off after AI pre-review and saved runs. The main judge shares the generators' model family; claim-support results changed with a second-family judge.
- **Operational readiness:** this is a research prototype. Rights, provider terms, explicit retention and restricted-document access remain open. Accepted extraction gaps are still gaps. Proposed production architecture and improvement plans are not deployed controls.

The next useful evidence is a fresh, reviewed evaluation of the exact served configuration, with targeted checks on the new period, calculations and conversation path. Until then, use LabourLens with source inspection and human judgement. The [evaluation report](evaluation-report.md) records the ordered improvement plan; the [detailed reference](reference/system-card-detail.md) retains every historical result and qualification removed from this shorter card.
