# Innovation assessment

LabourLens helps Singapore labour-market analysts check public statistics against MOM reports and an MTI employment article. It covers Q1 2020 to Q2 2026, returns cited answers and calculates changes in code. It is a research prototype, not approved for government production.

## Current approach

Statistics retain measure, unit, period, population, release and source. Reports become searchable passages; uncertain tables are flagged. Keyword and meaning search are combined, filtered by period/release and reranked. One bounded agent retrieves evidence and calculates changes. Code checks structure, citation labels, quotations and numbers, not whether evidence supports a claim.

The four-tool served agent adds `annual_average`: a simple mean of four non-null quarterly rates from one series, never a partial average or official annual rate. Statistics lookup and averaging use two of the default MCP server's ten tools. Current prompts are `planner_v7`, `answer_v9`, `triage_v4` and `contextualise_v3`. Follow-ups carry bounded context as untrusted data. Why questions seek attributed MOM commentary, not inferred causation; abstention separates missing observations from missing method/commentary. These changes are unevaluated.

## How I would improve it

Every item is a proposal, not a demonstrated gain.

### Retrieval and answer quality

Filtering then reranking raised passage hit@8 from 54% to 97% on 128 development report questions. Full-system evaluation did not demonstrate an answer gain on either test set. Development shaped the design; the original test shares evidence with it, and fresh questions have since been reused. Report-table arithmetic failed its pre-set checks and was not adopted.

### Drift detection

Snapshots and provenance make rebuilds traceable. Acquisition still needs an operator; scheduled refresh, drift alerts and rollback are not implemented.

### Latency

Evaluated median answer time was about 14 seconds, with chained calls. A native-tool, reasoning-off smoke took 29.8/7.8/9.1 seconds versus structured planning's 53.1/8.6/12.8: three questions, accuracy unmeasured. Streaming shows progress; it does not shorten full-answer time. Moving all historical tools into MCP was slower without a quality gain.

**Change:** triage in parallel with first retrieval/planning; cache embeddings, repeated series lookups, prompts and permission-scoped responses; skip contextualisation without history; try smaller triage models and parallel read-only tools within three calls per round. Key caches by permissions, corpus, prompts and model. **Check:** paired full-answer p50/p95, accuracy, safety and cost on the same 237 development questions, then fresh blind cases.

### Third Decisions gate

Neither Decisions API trial was adopted. V1 matched 397/409 routes per repeat, recalled 19/30 non-in-scope cases and falsely supported 44/58 partially supported claims. V2 matched 414/450 repeat rows, diverted two distinct in-scope questions and refused all 30 serious-harm presentations. Case-median p50/p95 was 0.362/0.426 seconds versus chat's 1.392/1.847, yet safety, quality and operational gates failed.

The third preregistered attempt is untested, with no paid execution authorised: a two-way in-scope/out-of-scope gate after harm and small-talk handling, with agent fallback. Freeze prompts, model, confidence 0.70 and 150 fresh human-labelled cases (90 in-scope, 30 out-of-scope, 15 harm, 15 small-talk); three interleaved repeats; no tuning. Each repeat needs zero legitimate diversions, 148/150 correct routes, 29/30 out-of-scope recalls, failures at most 1% of 450 scheduled classifications per arm, p50/p95 within 80% of chat and no downstream safety regression. Owner approval comes first.

### Tools, review and coverage

- **annual_average:** evaluate completeness, nulls and citations end to end; add other typed tools only for demonstrated gaps.
- **Report tables:** verify cell, row/column, unit and population lineage; target 0.50 accuracy without more false answers, then confirm blind.
- **Blind re-review and ablations:** three analysts label a blind set before AI suggestions (kappa at least 0.70, interval no wider than 0.10); test each filter, reranker, guard and output check separately.
- **2020 to 2023 gold:** independently reviewed fresh cases with expected evidence and abstention; report by year.
- **Refresh and coverage:** immutable scheduled snapshots validated for schema, rights and revisions; new sources evaluated before serving.

## Production deployment and security

All of this is proposed. Built today: one DigitalOcean Droplet, Caddy, Docker Compose, GitHub Actions, an access-code gate, rights-scan checks, a synthetic threat suite and audit IDs. Budget and audit state are local; limits are in memory.

### Provenance, explainability and review

The workbench shows sources, passages, status and tool activity. Feedback stays with its run but does not change the system. **Proposal:** review every thumbs-down and sample thumbs-up, write expected-evidence tests, change one thing at a time, pseudonymise comments and never treat votes as ground truth.

### Security, privacy and third-party risk

Tools are typed, read-only and bounded; retrieved content is untrusted. Across three synthetic attack repeats, guarded passed 50/54 versus naive 42/54; both failed 3/8 harmless look-alikes. Prompt and guards changed together, so no individual defence effect is established, and adaptive attacks are untested.

**Production proposals:** edge/WAF and SSO, load balancer, stateless API replicas, bounded queue, research workers and SSE event store; separate ingestion, immutable object storage, read-only versioned search/DuckDB snapshots and isolated MCP; per-user RBAC with classifications enforced before retrieval and caching; secrets manager, WAF and shared rate limits; tamper-evident audit retention; injection and allow-listed egress controls; supply-chain review and penetration testing; legal and PDPA review of residency and provider data use; an approved LLM gateway for endpoints, spend and retention; observability, CI gates, rollback and encrypted backups; SLOs, on-call ownership, cost caps, restore and failover drills. Move from a public-data pilot to hardened beta only after these gates pass.

### Mocked or unverified components and their production replacements

No live capability is mocked; hostile-server cases are synthetic. Shared codes, one worker and local state are replaced by SSO and roles, queued workers with shared state, immutable versioned evidence with isolated MCP, a secrets manager with an approved gateway, and gated release with tested recovery.

## Making it ready for government use across departments

Proposed only; no compliance claim. Use the Singapore Model AI Governance Framework as a review reference: risk and impact assessment, accountable owners, human-in-the-loop review of consequential decisions, model and system cards, change control, CI evaluation gates and drift monitoring. For several departments, isolate tenants and corpora, share MCP only through authenticated read-only contracts, and keep ingestion specifications and a licence register. Roll out department by department after data-owner approval, isolation tests, training and support readiness, without time promises.

## Limitations and threats to validity

Labels were AI-drafted and signed off by one human; the primary judge shares the generator's provider family. Few runs do not establish stability. Expanded sources, served changes and production controls remain unevaluated. Faster classification is not an end-to-end speedup or evidence of safer answers.
