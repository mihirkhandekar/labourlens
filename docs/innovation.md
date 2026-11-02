# Innovation assessment

LabourLens researches public Singapore labour statistics and reports for Q1 2024 to Q2 2026. Analysts inspect citations, records and tool calls before using an answer.

**Abstract.** Period filters and reranking select passages; typed read-only tools retrieve series and calculate changes. I measured retrieval, answer behaviour, runtime and attack responses. The next priorities are report-table arithmetic and independent evaluation.

## Current approach

- Numbers come from validated tables or deterministic code; claims cite passages or records.
- Period and release filters precede reranking; preliminary and final releases stay labelled.
- A bounded agent uses typed read-only tools, including an MCP statistics server.
- Evaluation uses fixed reference sets, retained negative results and an attack suite.

## Retrieval and answer quality

Hit@8 was 0.969 [0.938, 0.992] for filter then rerank versus 0.539 [0.453, 0.625] for hybrid (128 development text questions; [retrieval](experiments/retrieval-v31-rerun.md)). `gpt-6-luna` behaviour accuracy was 0.897 versus 0.827 (237 development questions, two-run means); difference +0.070 [0.036, 0.106] ([evaluation](evaluation-report.md)). Historical fresh-set numerical accuracy was 0.214 (3/14); the tool extension failed its criteria ([tools](experiments/m7-tool-fix.md)).

**Proposal:** verify report-table cells, units, population and row/column lineage before calculation; exclude `table_unreliable` cells. Test period restatements. Add series, quarters and languages behind provenance and quality gates.

## Drift detection

**Proposal:** gate releases on schema, period and revision checks; rerun evaluation after every corpus, prompt or model change. Keep rollback versions, pin model versions, alert on provider changes and probe embedding drift.

Track hit rate, abstention, citation validity, grounded numbers, latency and cost daily, plus minimised, pseudonymised logs by question family. Set alert thresholds from an approved baseline; detect a seeded regression within one cycle. None of this runs today ([system card](system-card.md)).

## Provenance, explainability and review

Citations, observation lineage, abstention reasons, conflict flags, an evidence drawer and tool traces support inspection. Thumbs and comments link to the run; nothing consumes them ([audit](audit-and-logging.md)).

**Proposal:** add table-row locators, side-by-side sources and review indicators. Several analysts label before AI suggestions, adjudicate and measure agreement; extend second-family judging.

**Feedback loop proposal:** thumbs are triage, not labels. Review every thumbs-down and a sample of thumbs-up; label evidence, number, period/population, abstention or style failures. Before fixing a confirmed failure, write a test with expected evidence for the next fresh set. Pick one lever (filter/rerank, table extraction, planner prompt, validator or corpus gap); tune on development, report on fresh questions. Track weekly votes and abstention by family. Do not fine-tune on votes, trust unreviewed votes or use thumbs-up answers as prompts; that leaks tests and rewards fluent errors. Pseudonymise comments; limit retention.

## Security, privacy and third-party risk

Tools are bounded and read-only; retrieved text is isolated; MCP responses are validated. Scanner detections rose 10/30 to 23/30 with benign flags unchanged at 9/30 ([scanner](experiments/injection-scanner-v2.md)). Fresh attacks scored 35/36 ([threats](experiments/t-i06-scorer-v2-rule.md)).

**Proposal:** clear licences and publisher agreements; replace shared codes with government SSO and source roles; approve residency, private endpoints, retention and audit access. Review provider terms; keep a tested vendor exit plan. On provider failure return unavailable, never an unvalidated fallback. Test a stronger injection classifier on independent paraphrases; keep server allow-lists and red-team reviews.

## Latency and cost

Filter then rerank on development: median 14.35 s (mean of runs), p95 35.4 and 34.1 s, $0.002845 per question. All-tools MCP scored 0.877 (57/65) versus 0.908 (59/65) for statistics-only, median 14.3 versus 12.4 s, p95 51.4 versus 34.7 s; it was rejected ([comparison](experiments/served-chain-mcp-all.md)).

**Proposal:** test revision-keyed caches, filter-only routing and smaller triage/rerank models; add token and cost budgets, p95 alerts and provider caps. Target p95 below 40 s and mean cost below $0.005, with no regression in citations, numbers or abstention.

## Priorities and measurement

1. **Report-table arithmetic.** Pre-register one change; regress on the 14 known cases, then confirm on new blind questions. Threshold: accuracy at least 0.50, no rise in false-answer rate, unchanged citation checks.
2. **Independent review.** Three analysts label a stratified blind set before AI suggestions, then adjudicate; never tune on it. Threshold: Fleiss' kappa at least 0.70; 95% accuracy interval width at most 0.10.

## Limitations and threats to validity

Development shaped the design; original-test evidence overlaps and fresh-test outcomes are known. Neither final test demonstrates a gain. Gold was AI-drafted and reviewed by one person; the main judge is same-family. Two runs do not estimate variance. Citations check mechanics; arithmetic can use wrong inputs. Scanner and attack results establish no general defence. Full comparisons exclude web-only steps and MCP. Costs are list-price estimates. Government readiness is untested.

## Mocked or unverified components and their production replacements

No live capability is mocked; hostile-server fixtures are synthetic tests. Shared codes need approved SSO; the external model route needs approved private endpoints; report rights, some licences and the employment population basis need publisher agreements and validated definitions.
