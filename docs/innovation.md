# Innovation assessment

LabourLens helps Singapore labour-market analysts check public statistics against MOM reports and an MTI employment article. It covers Q1 2020 to Q2 2026, returns cited answers and calculates changes in code. It is a research prototype, not approved for government production.

## Current approach

Statistics retain measure, unit, period, population, release and source. Reports become searchable passages; uncertain tables are flagged. Keyword and meaning search are combined, filtered by period/release and reranked. One bounded agent retrieves evidence and calculates changes. Code checks structure, citation labels, quotations and numbers, not whether evidence supports a claim.

The four-tool served agent adds `annual_average`: a simple mean of four non-null quarterly rates from one series, never a partial average or official annual rate. Statistics lookup and averaging use two of the default MCP server's ten tools. Current prompts are `planner_v6`, `answer_v8`, `triage_v4` and `contextualise_v3`. Follow-ups carry bounded context as untrusted data. Why questions seek attributed MOM commentary, not inferred causation; abstention separates missing observations from missing method/commentary. These changes are unevaluated.

## Retrieval and answer quality

The retrieval experiment raised passage hit@8 from 54% to 97% on 128 development report questions. Full-system evaluation did not demonstrate an answer gain on either test set. Development shaped the design; the original test shares evidence with it, and fresh questions have since been reused. Report-table arithmetic failed its pre-set checks and was not adopted.

## Drift detection

Snapshots and provenance make rebuilds traceable. Acquisition still needs an operator; scheduled refresh, drift alerts and rollback are not implemented. **Proposal:** fetch immutable snapshots, validate schema, coverage, revisions and rights before promotion, record freshness and label stale data. Retain the previous approved version; test each update before serving it.

## Provenance, explainability and review

The workbench shows sources, passages, status and tool activity. Feedback stays with its run but does not change the system. **Proposal:** review every thumbs-down and sample thumbs-up; turn confirmed failures into expected-evidence tests, changing one thing at a time. Pseudonymise comments, limit retention and never treat votes as ground truth.

## Security, privacy and third-party risk

Tools are typed, read-only and bounded; retrieved content is untrusted. Across three synthetic attack repeats, guarded passed 50/54 versus naive 42/54; both failed 3/8 harmless look-alikes. Prompt and guards changed together, so no individual defence effect is established. These tests do not prove general security.

## How I would improve it

All changes below are proposals, not demonstrated gains.

- **Latency:** evaluated median answer time was about 14 seconds, with chained calls. A native-tool, reasoning-off smoke took 29.8/7.8/9.1 seconds versus structured planning's 53.1/8.6/12.8: three questions, accuracy unmeasured. Streaming shows progress; it does not shorten full-answer time. Parallel triage with first retrieval/planning; cache embeddings, repeated series lookups, prompts and permission-scoped responses; shorten contextualisation or skip without history; try smaller triage models and speculative read-only tools within three calls per round and the existing total budget. Bound waste, discard unused work and version caches by permissions, corpus, prompts and model. Before adoption compare full-answer p50/p95, accuracy, safety and cost on the same 237 development questions, then fresh blind cases.
- **Third Decisions gate:** neither Decisions API trial was adopted. V1 matched 397/409 routes per repeat, recalled 19/30 non-in-scope cases and falsely supported 44/58 partially supported claims. V2 matched 414/450 repeat rows, diverted two distinct in-scope questions and refused all 30 serious-harm presentations. Case-median p50/p95 was 0.362/0.426 seconds versus chat's 1.392/1.847; safety, quality and operational gates still failed. The third preregistered attempt is untested, with no paid execution authorised: two-way in-scope/out-of-scope only, retaining harm/small-talk handling and fallback. Freeze prompts, model, confidence 0.70 and 150 fresh human-labelled cases: 90 in-scope, 30 out-of-scope, 15 harm, 15 small-talk. Interleave three repeats; no tuning. Each repeat needs zero legitimate diversions, 148/150 correct routes and 29/30 out-of-scope recalls; failures at most 1% of 450 scheduled classifications per arm. Report bypasses separately. Require p50/p95 at most 80% of chat and no downstream safety regression. Report case-clustered intervals and cost; obtain approval before execution or adoption.
- **Tools:** evaluate annual_average completeness, nulls, definitions and citations end to end. Add other typed tools only for demonstrated gaps. Verify report-table cell, unit and row/column lineage before calculation; target 0.50 numerical accuracy without more false answers or weaker definition checks, then confirm blind.
- **Review and ablation:** three analysts independently re-review blind cases before AI suggestions; target kappa 0.70 and an accuracy interval no wider than 0.10. Test retrieval filters, reranking and each security layer separately, including harmless look-alikes, to identify contributions and false alarms.
- **Earlier-year gold:** independently review fresh 2020 to 2023 cases with expected evidence, definitions, revisions and abstention. Existing evaluation covers 2024 to 2026 only. Keep blind cases separate and report retrieval and answer quality by year and question family.

## Making it ready for government use across departments

All of this is proposed. Built today: one DigitalOcean Droplet, Caddy, access-code gating, Docker Compose, GitHub Actions, rights-scan checks, a synthetic threat suite and audit IDs. Budget/audit state is local; limits are in memory.

**Architecture:** edge/WAF and SSO, load balancer, stateless API replicas, bounded queue, research workers and SSE event store. Separate ingestion; immutable object storage and read-only versioned search/DuckDB snapshots; isolated MCP; shared budgets, rate limits and audit state; secrets manager; approved LLM gateway enforcing endpoints, spend and retention; observability, CI quality/security/rights gates, rollback, encrypted backups and restore drills.

**Access and assurance:** per-user RBAC, classifications and source permissions before retrieval and caching; approved residency and provider data use; authorised PDPA review; tamper-evident audit retention; injection controls and allow-listed egress; supply-chain review and penetration testing. Check denial, isolation and leakage across users, tools, caches and logs before restricted data.

**Governance:** use Singapore's Model AI Governance Framework as a review reference, not a compliance claim. Record risk/impact assessment, accountable owners and human-in-the-loop review for consequential decisions. Maintain model/system cards, change control, CI evaluation gates and drift monitoring; require authorised acceptance.

**Departments and operations:** isolate tenants and department corpora; share MCP only through authorised contracts. Define ingestion specifications and a licence register. Agree measured SLOs, on-call ownership, cost caps and disaster recovery; test backups, failover, timeout and rollback. Progress from public-data pilot to hardened beta to department rollout only after evidence-based gates, with no time promises.

## Limitations and threats to validity

Labels were AI-drafted and signed off by one human; the primary judge shares the generator's provider family. Few runs do not establish stability. Expanded sources, served changes and production controls remain unevaluated. Faster classification is not an end-to-end speedup or evidence of safer answers.

## Mocked or unverified components and their production replacements

No live capability is mocked; hostile-server tests are synthetic. The production proposals above replace shared codes, local state and unverified recovery. Departmental security, legal, data-owner and operational approval remain necessary; nothing here establishes compliance.
