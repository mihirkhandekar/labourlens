# Innovation assessment

**Scope and assumptions.** A plan for evolving LabourLens into a trusted research capability, not a claim of government readiness. I assume public or approved synthetic data, an analyst responsible for decisions and an approved government deployment. **MEASURED** means saved evidence; **PROPOSAL** means not built. Gold was AI-drafted, reviewed by one person after AI pre-review and scoring; the main judge is from the same model family. The three question sets are partially independent. Methods and intervals: [evaluation report](evaluation-report.md). The [site roadmap source](innovation-page.json) uses these same six headings.

## Improve retrieval and answer quality

**MEASURED:** current-corpus retrieval hit@8 is 0.969 versus hybrid 0.539 on 128 development text questions. Final primary-model development behaviour accuracy is 0.897 versus 0.827 on 237 questions, averaging two runs per arm. Neither final test set demonstrates a gain. Historical fresh-set numerical comparisons scored 0.214 (3/14), mostly because tools could not calculate over report figures; the attempted tool extension failed its criteria and was not adopted.

**PROPOSAL:** validate PDF table cells, units, populations and row/column lineage before deterministic calculation. Do not infer cells from `table_unreliable` passages. Test later reports restating earlier quarters, which hard period filters can miss. Expand quarters, MOM/MTI/SingStat series and languages only behind provenance and quality gates. Better extraction costs review effort; more retrieval or model complexity is not evidence of better answers.

## Detect and respond to change

**PROPOSAL:** extend existing corpus fingerprints, immutable snapshots and gold-hash checks into a release gate. Check schema, missing periods and revisions; rerun evaluation on every corpus, prompt or model change, retain the prior version and roll back unexplained regressions. Run daily canaries between releases.

Monitor retrieval hit rate on reviewed probes, abstention, citation validity, grounded-number rate, latency and cost per question. Use a fixed embedding probe set, pin model versions where available and alert on provider changes. Sample minimised, pseudonymised audit logs and feedback for changing question families, clarifications and unmet needs; have analysts review drift before changing coverage. This monitoring is not a service today; pseudonymisation does not eliminate privacy risk.

## Support confidence and human review

Passage citations, observation lineage, abstention reasons, conflict caveats, the evidence drawer, tool-call traces and feedback capture already support inspection. **PROPOSAL:** add table-row locators, side-by-side sources, evidence-coverage and review indicators, saved analyses, cited briefing exports and revision alerts. Confidence should describe evidence and disagreement, not a model self-rating presented as probability.

Route feedback into an analyst queue: classify the failure, draft a regression case, adjudicate, change one factor and rerun. Several reviewers should label before seeing AI suggestions, measure agreement and resolve differences. Extend the small second-family judge check to full scale and repeat runs to estimate variance. Review costs more, but today's single-reviewer and same-family-judge evidence cannot establish independent accuracy.

## Manage privacy and third-party risk

**PROPOSAL:** clear dataset licences, report rights and publisher agreements; replace shared demo codes with government SSO and role-based source permissions. Approve audit retention, restricted log access, minimisation and pseudonymisation. Data residency, private model endpoints and provider processing terms require approval; data-use terms remain unverified. Keep exportable evidence and a vendor exit plan, testing any alternative endpoint before switching. On failure, show unavailable or an approved cached analysis, not an unvalidated fallback.

Retain untrusted-text isolation, bounded read-only tools and MCP response validation; add independently tested injection classification, server allow-lists, incident owners and recurring red-team checks. **MEASURED:** scanner detection improved 10/30 to 23/30, with benign flags unchanged at 9/30. Fresh attacks scored 35/36 across configurations, not a general defence effect. The scanner is a warning layer. No live service on the innovation page is mocked: hostile-server fixtures are synthetic tests, not government infrastructure. Production replacements require approved SSO, private hosting and a reviewed model contract. No confidential data should go to external services.

## Control latency and cost

**MEASURED:** primary development filter-then-rerank mean cost is $0.002845 per question; the mean of run medians is 14.35 s, with p95 values 35.4 s and 34.1 s. Costs are saved-usage list-price estimates, not bills. All-three-tools MCP scored 0.877 versus 0.908 for the live statistics-only route; median 14.3 versus 12.4 s and p95 51.4 versus 34.7 s. It was slower with no demonstrated gain and is not live.

**PROPOSAL:** retain embedding caches; test version-keyed retrieval/answer caches, filter-only routing and smaller triage/rerank models against quality gates. Invalidate caches on revisions. Add token, call, latency and cost budgets, p95 alerts and provider limits. Target p95 below 40 s and mean cost below $0.005 on an approved mix, without quality regression. Cheaper routing trades quality risk for speed; application reservations are not provider spending caps.

## Prioritise two measurable improvements

**First, validated report-table arithmetic (PROPOSAL).** Pre-register one extraction/tool change. On the 14 known fresh-set numerical questions, now a regression set, target accuracy at least 0.50 versus historical 0.214, no rise in all-question false-answer rate on a fixed paired suite, and unchanged definition/citation checks. Confirm on newly written blind numerical questions; reject a failed safety or quality gate.

**Second, independent review and a blind set (PROPOSAL).** At least three analysts independently label a new stratified blind set before seeing AI outputs, then adjudicate. Target Fleiss' kappa at least 0.70 for behaviour labels and a 95% case-bootstrap headline accuracy interval no wider than 0.10; pre-register sampling and expand if needed. Report claim support, numerical correctness, disagreements and run variance separately. Never tune on that set. These thresholds are proposed acceptance criteria, not results; trustworthiness takes priority over fluent output.
