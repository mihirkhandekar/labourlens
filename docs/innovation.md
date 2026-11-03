# Innovation assessment

LabourLens is a research prototype for Singapore labour-market analysts. It answers questions with public statistics and MOM reports from Q1 2020 to Q2 2026. Answers include source citations; statistical changes are calculated in code.

## Current approach

Statistics are stored with their measure, unit, period, population, release and source. Reports become searchable passages; uncertain tables are flagged rather than guessed. I compared keyword search, meaning search and hybrid retrieval, then added period/release filters and reranking. A bounded agent can search reports, retrieve statistics through an MCP server and calculate changes from returned rows. Answers use a fixed schema. Code checks citation labels, quotations, numbers and answer status, but cannot establish that a quote supports a claim.

I also compared the agent with a fixed workflow, screened model candidates, tested report-table arithmetic, compared direct and MCP routes, and ran synthetic security tests. The report-table extension failed its pre-set criteria and was not adopted.

## Retrieval and answer quality

On the same 128 development report questions, filter-then-rerank raised relevant-passage hit@8 from 54% to 97% ([retrieval experiment](experiments/retrieval-v31-rerun.md)). This is a passage-retrieval result, not answer accuracy. Full-system comparisons showed a development gain but no demonstrated gain on the original or fresh test set ([evaluation report](evaluation-report.md)). The original shares evidence with development; fresh questions have since been reused.

The agent beat one fixed policy on development questions only. There is no test-set comparison ([experiment](experiments/agent-vs-fixed-pipeline-results.md)). The current calculator accepts validated statistic rows. Report-table arithmetic needs reliable cell and row/column checks before another attempt ([rejected extension](experiments/m7-tool-fix.md)).

## Drift detection

Versioned snapshots and provenance make rebuilds traceable. Source acquisition and rebuilds still require an operator; scheduled refresh, drift alerts and rollback are not implemented. The expanded corpus and newer served planner have not been re-evaluated.

**Proposal:** fetch approved sources on a schedule into immutable snapshots. Check schema, coverage, revisions and rights before promotion. Record the last successful fetch, alert on missed freshness targets, and label the previous approved snapshot stale until an update passes validation. Retain the prior version for rollback. Add government sources through the same definitions, rights review and evaluation process. Extend to new topics only after a separate scope decision.

## Provenance, explainability and review

The workbench shows source links, cited passages, answer status and tool activity. Feedback is stored with its run but does not change the system. Citation checks verify that labels and quotations came from supplied evidence, not that the claim follows from them.

**Proposal:** have at least three analysts label a blind set before AI suggestions, then adjudicate. Review every thumbs-down and sample thumbs-up. Classify confirmed failures, write a test with expected evidence, change one thing at a time, tune on development and check on fresh questions. Pseudonymise comments, limit retention, and do not treat votes as ground truth ([audit design](audit-and-logging.md)).

## Security, privacy and third-party risk

Tools are typed, read-only and bounded. Retrieved passages are untrusted data; MCP replies are validated. In a synthetic attack comparison repeated three times, the guarded setup passed 50 of 54 attacks versus 42 for the naive setup. The answer prompt and guards changed together, so the comparison cannot identify which defence helped. Both setups failed three of eight harmless look-alikes. This does not establish safety against adaptive attacks or an individual layer's effect ([threat results](experiments/threat-v2-results.md)).

**Proposal:** replace shared demo codes with government identity and source roles. Apply permissions before retrieval. Approve model endpoints, residency, retention, audit access and publisher terms before using restricted data. Test each security layer against independent paraphrases, hostile passages, unsafe tool requests and harmless look-alikes.

## Latency and cost

The live agent sends statistical lookup through MCP. Direct and MCP routes query the same local observations. Moving report search and calculation into MCP was slower and showed no answer-quality gain in a one-run, 65-question sample, so it was not adopted ([comparison](experiments/served-chain-mcp-all.md)). Removing statistics access also removes the calculator's input ([ablation](experiments/served-chain-no-stats.md)).

The live site runs on one DigitalOcean Droplet behind Caddy, using Docker Compose and GitHub Actions. The app has one worker; budget and audit state are local files, and request limits are in memory. Provider-side spend limits, rollback and load behaviour are unverified ([deployment runbook](deploy.md)).

**Proposal:** keep this deployment until load tests show a bottleneck. Separate ingestion and index builds from question serving. Publish versioned data and indexes atomically, with rollback. Before adding app replicas, move budget, rate-limit and audit state to shared services and give query workers read-only corpus access. Measure latency, failures and cost before testing caches or smaller models.

## Priorities and measurement

1. **Report-table arithmetic.** Pre-register one extraction change, test known cases, then confirm on new blind questions. Proposed threshold: 0.50 accuracy on predefined numerical cases, with no rise in false answers or weaker definition and citation checks.
2. **Independent review.** Have three analysts label a stratified blind set before AI suggestions. Proposed targets: agreement of at least 0.70 and an accuracy interval no wider than 0.10. Do not tune on this set.

## Limitations and threats to validity

Development questions shaped the design. The original test shares evidence with development; fresh questions have since been reused. Neither test demonstrated an answer-quality gain. Questions and labels were AI-drafted and signed off by one human reviewer. The primary judge is from the generator's provider family. A small number of runs does not establish stability. Citation checks are mechanical; arithmetic can use wrong inputs. Synthetic attacks do not establish general security. The expanded corpus, newer planner, monitoring, rollback, government identity and production scale remain untested.

## Mocked or unverified components and their production replacements

No live capability is mocked; hostile-server cases are synthetic tests. Government use still requires approved identity, source permissions, model processing and data rights. Automated refresh is not implemented. Do not scale beyond one worker until budget, audit and rate-limit state have a reliable shared home.
