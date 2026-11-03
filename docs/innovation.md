# Innovation assessment

LabourLens researches public Singapore labour statistics and reports for Q1 2024 to Q2 2026. Analysts inspect citations, records and tool calls before using an answer.

**Abstract.** Period filters and reranking select passages; typed read-only tools retrieve series and calculate changes. I measured retrieval, answer behaviour, runtime and attack responses. The next priorities are report-table arithmetic and independent evaluation.

## Current approach

- Numbers come from validated tables or deterministic code; claims cite passages or records.
- Period and release filters precede reranking; preliminary and final releases stay labelled.
- A bounded agent uses typed read-only tools, including an MCP statistics server.
- Evaluation uses fixed reference sets, retained negative results and an attack suite.

## Retrieval and answer quality

Development chunk hit@8 was .969 for filter then rerank versus .539 for hybrid (n=128; [retrieval](experiments/retrieval-v31-rerun.md)). [Original/fresh diagnostics](../experiments/eval/heldout-retrieval-20261103-paid/metrics.json) give strict passage hit@8 .778/.941 versus .167/.500 (n=18/34), without demonstrated end-to-end accuracy gain or per-case cause investigation. `gpt-6-luna` development behaviour was .897 versus hybrid .827, two-run means. Against one fixed pipeline run (.814), the agent mean .897 demonstrates a development advantage, confounded by arithmetic access and tool policy; it does not transfer to either test set ([comparison](../experiments/eval/agent-vs-fixed-pipeline.json)). Historical fresh numerical accuracy was 3/14; the tool extension failed ([tools](experiments/m7-tool-fix.md)).

**Proposal:** verify report-table cells, units, population and row/column lineage before calculation; exclude `table_unreliable` cells. Add series, quarters and languages behind provenance and quality gates.

## Drift detection

**Proposal:** gate releases on schema, period and revision checks; rerun evaluation after every corpus, prompt or model change. Keep rollback versions, pin model versions, alert on provider changes and probe embedding drift.

Track hit rate, abstention, citation validity, grounded numbers, latency and cost daily, plus minimised, pseudonymised logs by question family. Set alert thresholds from an approved baseline. None of this runs today ([system card](system-card.md)).

## Provenance, explainability and review

Citations, observation lineage, abstention reasons, conflict flags, an evidence drawer and tool traces support inspection. Thumbs and comments link to the run; nothing consumes them ([audit](audit-and-logging.md)).

**Proposal:** add table-row locators, side-by-side sources and review indicators. Several analysts label before AI suggestions, adjudicate and measure agreement; extend second-family judging.

**Feedback loop proposal:** thumbs are triage, not labels. Review every thumbs-down and a sample of thumbs-up, label the failure type (evidence, number, period, abstention, style) and write a test with expected evidence before fixing. Tune on development; report on fresh questions. Do not fine-tune on votes or reuse thumbs-up answers as prompts: that leaks tests and rewards fluent errors. Pseudonymise comments; limit retention.

## Security, privacy and third-party risk

Tools are bounded and read-only; MCP responses are validated. Scanner detections rose 10/30 to 23/30, benign flags unchanged at 9/30 ([scanner](experiments/injection-scanner-v2.md)). V1 fresh attacks remain 35/36. [V2](experiments/threat-v2-results.md), `gpt-6-luna`, three repeats: guarded/naive majority passes 50/54 versus 42/54 (p=.03857). Guards and answer prompt change together; both fail three of eight benign cases. No individual-layer or general safety claim follows.

**Proposal:** clear licences and publisher agreements; replace shared codes with government SSO and source roles. **Permission-aware retrieval:** the corpus is public and has no per-user permissions today; for restricted sources, label each document and chunk and pre-filter by label in BM25, vector search and the statistics tools, so restricted text never reaches the model. Also approve residency, private endpoints, retention and audit access. Review provider terms; keep a tested vendor exit plan. On provider failure return unavailable, never an unvalidated fallback. Test a stronger injection classifier; keep server allow-lists and red-team reviews.

## Latency and cost

Development median latency was 14.35 s, p95 35.4/34.1 s, cost $0.002845/question. All-tools MCP scored 57/65 versus statistics-only 59/65, p95 51.4 versus 34.7 s; it was rejected ([comparison](experiments/served-chain-mcp-all.md)). Removing statistics scored .692 versus .908, partly because calculation loses its input; MCP versus direct tied without establishing equivalence ([ablation](experiments/served-chain-no-stats.md)).

**Proposal:** test revision-keyed caches, filter-only routing and smaller triage/rerank models; add token and cost budgets, p95 alerts and provider caps. Target p95 below 40 s and mean cost below $0.005, with no regression in citations, numbers or abstention.

## Priorities and measurement

1. **Report-table arithmetic.** Pre-register one change; regress on the 14 known cases, then confirm on new blind questions. Threshold: accuracy at least 0.50, no rise in false-answer rate, unchanged citation checks.
2. **Independent review.** Three analysts label a stratified blind set before AI suggestions, then adjudicate; never tune on it. Threshold: Fleiss' kappa at least 0.70; 95% accuracy interval width at most 0.10.

## Limitations and threats to validity

Development shaped design; original-test evidence overlaps and fresh outcomes are known. Neither final test demonstrates an answer gain. Gold was AI-drafted, reviewed by one person; the main judge is same-family. One fixed run and two agent runs do not establish stability. Citations check mechanics; arithmetic can use wrong inputs. Attacks establish no general defence. Full comparisons exclude web/MCP. Government readiness is untested.

## Mocked or unverified components and their production replacements

No live capability is mocked; hostile-server fixtures are synthetic tests. Shared codes need approved SSO; the external model route needs approved private endpoints; report rights, some licences and the employment population basis need publisher agreements and validated definitions.
