# LabourLens — decision log

Each entry: date, decision, alternatives, why, who approved, how reversible. Labels follow `CLAUDE.md`: **DECISION**, **PROPOSAL**, **VERIFIED FACT**, **ASSUMPTION**. ADRs in `docs/decisions/` hold the large architectural decisions; this log holds everything else.

## Settled

### D-000 — Domain, scope and LangGraph architecture
**DECISION** (owner, 30 Oct 2026). See `docs/decisions/ADR-001-scope.md` and `ADR-002-langgraph.md`. Not reopened without a real blocker.

### D-001 — Repository is private, shared with reviewers; designed as if it could become public
**DECISION** (owner, 30 Oct 2026). Alternatives: public GitHub; private repo; emailed zip.
**Why:** MOM's report PDFs are all-rights-reserved (**VERIFIED FACT**: notice text read in all four PDFs), so they stay out of Git under every option. A private repo lets reviewers run the project without publishing material we have no right to publish, and designing for public keeps the later option open at no cost.
**Reversible:** yes. Making the repo public later only requires the packaging test (`test_rights_packaging.py`) to pass.

### D-002 — Two kinds of documents: published and private
**DECISION** (owner, 30 Oct 2026). Published docs live in `docs/` and go to reviewers. Private notes live in `study/` and `private/` and are gitignored.
**Why:** the owner needs interview-prep and scratch research that reviewers should not see, and the assessment asks for specific public deliverables. A physical split with a gitignore rule is safer than relying on memory.
**Reversible:** yes.

## In discussion

### D-003 — Expand the structured data beyond the four approved datasets
**Owner request (30 Oct 2026):** add more structured data to make the project more impressive, including the good-to-haves, and implement them.
**Status: APPROVED by owner, 30 Oct 2026** ("Okay agreed, let's do this"): Tier 1 datasets plus the six analytics/engineering features, built with a spec-driven adapter. Tier 2 deferred. Formal record: `docs/decisions/ADR-003-structured-data-scope.md`. Per-dataset drop rule still applies (must reach 2026-Q2 and pass its contract in M1.1).

**VERIFIED FACT (listing probe, 30 Oct 2026):** data.gov.sg has ~190 MOM-managed datasets. The shortlist below came from that listing; IDs and last-updated dates were read from the API. Quarterly coverage through 2026-Q2 has **not** been checked per dataset; M1.1 must check it and drop any dataset that does not reach the scope window.

**Tier 1 — directly strengthens the research questions (quarterly, updated Sep–Oct 2026):**

| Candidate | Dataset ID | Why it earns its place |
|---|---|---|
| Overall Unemployment Rate, Quarterly | `d_ca32584c91ee07d091a4ce75fa868414` | Creates real resident vs overall ambiguity cases |
| Citizen Unemployment Rate, Quarterly | `d_1353f9be1a020ba1469852c49ee62db3` | Third population definition; strong disambiguation test |
| Job Vacancy Rate, Quarterly | `d_c57f5cd0558e429e2ac055d83030e75f` | Vacancy rate vs the approved vacancy ratio: tests "ratio is not a rate" |
| Number of Job Vacancy, Quarterly | `d_59a34aef12e0ecf666de5746e50586e8` | Counts beside rates |
| Number of Retrenched Employees by Industry, Quarterly | `d_61d92d31ca400be135190614277da825` | Retrenchment drill-down by sector; cross-checks the narrative in MOM reports |
| Retrenched Permanent / Term Contract, Quarterly | `d_493616c9e3c9bd5d1e273903aa693a16` / `d_7a7d656c3a358c429f2bd4c3e9a97809` | Splits the headline retrenchment count (hierarchy check: parts vs total) |
| Re-entry into Employment, 6 months / 12 months, Quarterly | `d_4d3ce3e889fdf1da6bd6e9d52667db91` / `d_614b0fa2aa808afced2982c37e846d13` | Outcome after retrenchment; last updated 6 Oct 2026, after the Q2 report, so it supports a freshness-and-revision case |
| Average Monthly Resignation Rate, Quarterly | `d_e58adb04ca812651cfecfa82acdf6c35` | Labour churn signal for synthesis questions |
| Average Monthly Recruitment Rate, Quarterly | `d_80247eca3da78635ed9e89aa5831e883` | Pairs with resignation |
| Number of Unemployed Residents / Overall Unemployed, Quarterly | `d_50f76f080c7e80c3b6acd4dfc9f29174` / `d_3fb7b082cd455ec9493ef5e994ef0db7` | Level counts that connect to the rates |

**Tier 2 — context, lower fit with the quarterly scope:**
Annual wages and income (`d_bd83b453...` Basic Wage Changes by Industry; `d_e5848828...` Total Wage Changes by Industry), annual retrenchment incidence, Short Work-Week/Temporary Layoff quarterly (`d_31d4c1a2...`, last updated 23 Mar 2026, so it may lack 2026-Q2).
**Excluded for now:** Foreign workforce datasets (last updated June 2024; stale and would not resolve the 14,700 vs 11,400 question for 2026). Holidays, leave, trade unions, arbitration: off topic.

**Analytics and engineering features that make the data layer more impressive (all deterministic, no LLM):**
1. **Cross-source reconciliation table:** advance vs final vs dataset for each headline figure (10,700 / 11,400 / 14,700), with release dates and definitions.
2. **Revision tracker:** every snapshot is stored with its hash, and a diff report lists any historical value that changed between snapshots. The SA series is revised yearly, so this is a real feature.
3. **Derived indicators with lineage:** retrenchment per 1,000 employees where a denominator is verified, SA minus NSA gap, vacancy-to-unemployed ratio recomputed from counts and compared with the published ratio (a built-in consistency check).
4. **Data-contract tests:** a declarative spec per dataset (columns, types, units, expected period range). A schema change fails loudly.
5. **Provenance explorer CLI:** `labourlens trace <observation_id>` prints observation → raw cell → snapshot → URL.
6. **EDA figures for the assessment:** at least two (for example, vacancy-ratio vs unemployment path 2024–26, retrenchments by industry), produced from the same validated store.

**Cost and risk:** the 4 approved datasets plus ~14 Tier-1 datasets is 18 adapters. This is manageable only if long-format datasets share one declarative adapter (a spec file, not code per dataset). The two special cases (unemployment `YYYY-MM`, sector wide table) keep custom code. Deadline is 4 Nov, so every added dataset trades against M2–M6 time, which carry 60% of the rubric.
**PROPOSAL (assistant):** include Tier 1 and the six features above, using a spec-driven adapter. Defer Tier 2. Hard rule: any dataset not reaching 2026-Q2 or failing its contract in M1.1 is dropped, not patched.
**Open:** owner confirms tiers. Then ADR-003.

## Awaiting

### D-004 — Commit raw dataset CSVs to the private repo
**PROPOSAL:** yes, with the Open Data Licence attribution notice. Only the Open-Licence datasets; never PDFs or MOM passage text.
**Why:** lets a reviewer reproduce results offline. **Not verified:** the licence page was read only via the planning docs; M1.1 must read it.

### D-005 — Approve "Implement Milestone 1"
**APPROVED by owner, 30 Oct 2026** ("I approve. Document everything properly."), for the full scope: 18-dataset spec-driven adapter (ADR-003), D-006 corpus, CSV snapshots committed to the private repo (D-004), local-only MOM files, six extra features. Milestone 1 stops at its gate; M2+ not approved. Failed datasets or documents are reported and dropped, not hidden.

### D-006 — Expand the unstructured corpus beyond the five approved MOM documents
**Owner question (30 Oct 2026):** are there more unstructured reports, since RAG needs enough text to be interesting, and the agent must be good.
**Status: APPROVED by owner, 30 Oct 2026** ("Yes I approve"): Labour Force in Singapore 2025 (findings, highlights, coverage/methodology PDFs) now; earlier advance and final releases once exact URLs are found from the MOM site in a browser session (never guessed). MTI and MAS sources excluded unless stable official links are verified. Rights stay `unresolved` per source until its own notice is read.
**VERIFIED FACT (probes, 30 Oct 2026):**
- `https://stats.mom.gov.sg/Pages/Labour-Force-In-Singapore-2025.aspx` returns 200 and lists 7 PDFs: survey findings, survey highlights, infographic, coverage and methodology, notations and abbreviations, preface, and a copyright notice. It is an annual MOM report, so it adds methodology and definitions, which are the passages that answer "what does this indicator mean" questions.
- `https://www.mti.gov.sg/Resources/Economic-Survey-of-Singapore` returns 200, but I found no PDF links in the page HTML. Link discovery for it is **unverified**.
- `https://www.mas.gov.sg/publications/macroeconomic-review` returned a "Maintenance" page. **Unverified**; skip.
- MOM press-release listing is rendered by script, so I could not enumerate earlier advance releases (3Q25, 4Q25, 1Q26) by URL. Exact URLs are **unverified**; guessing them returned 404.
**PROPOSAL:** add (a) Labour Force in Singapore 2025: survey findings, survey highlights, and coverage/methodology PDFs (3 documents), (b) the three earlier advance releases and the final press releases for Q3 2025 to Q1 2026, once their URLs are found from the MOM site (a browser session, not URL guessing), (c) MTI Economic Survey quarterly releases only if M1.1 finds stable official PDF links. Rights for each stay `unresolved` until its own notice is read. Methodology documents matter more than volume: they make definition questions answerable and give the agent real "which definition applies" work.
**Why more advance/final pairs:** the Q2 2026 pair is the only revision example. Q3 2025 to Q1 2026 pairs (if found) turn one anecdote into a measurable revision set.
**Cost:** each extra PDF adds extraction checks and manual passage review. Keep the manual-review quota proportional (10 passages minimum, spread across documents).

### D-007 — UI, deployment and authentication
**Owner request (30 Oct 2026):** think about deploying the UI, the interface, and authentication; use `kpi-dashboard-design` for dashboards; impress with data, design and visualisations.
**Status: PROPOSAL, for the M7 gate. No UI work in M1.**
**Owner question (30 Oct 2026):** personal DigitalOcean account; Spaces + backend + frontend on App Platform? Assistant guidance is in "D-007 deployment notes" below. Nothing is decided or created; no account actions are taken by the agent.
**Constraint found while thinking about this:** a hosted public UI would display extracted MOM report passages, and MOM reports are all-rights-reserved (D-001). So any hosted demo must show only short cited excerpts with links to the source, and must not be publicly reachable.
**Options:**
| Option | Benefit | Cost |
|---|---|---|
| A. Local only (`docker compose up` or two commands) | Zero rights risk, no hosting cost, works offline | Reviewers must run it |
| B. Private hosted demo behind an allow-list (reviewer emails only) | Easy for reviewers; shows deployment and authentication thinking | Needs a host, secrets handling, and a call on where passage text is stored |
| C. Public hosted demo | Easiest to share | Conflicts with the MOM copyright notice; rejected |
**PROPOSAL:** A as the guaranteed path, plus B if M1 to M6 finish on time. For authentication in B, put the app behind an identity-aware access layer with an email allow-list (one-time-code login), not hand-rolled passwords. Inside the app, keep roles minimal: `reviewer` (ask, inspect evidence) and `admin` (refresh data, see logs). This also gives the innovation write-up a real example of permission-aware retrieval.
**Design direction:** a research workbench, not a marketing page. Dashboards follow `kpi-dashboard-design`: 5 to 7 headline KPIs, context on every number (comparison, trend, period), consistent colour meaning, drill-down from summary to source, methodology visible on each card, no 3D charts. The `design-taste-frontend` skill is scoped to landing pages and says dashboards are out of its scope, so it applies only to a login or about page, if we build one.
**Chart ideas that earn their place:** headline strip (unemployment SA, vacancy ratio, retrenchments, employment change) with change vs prior quarter in the right units; vacancy ratio against unemployment over 2024-2026; retrenchments by industry (small multiples); the three Q2 employment numbers on one reconciliation chart with definitions; a provenance drawer that opens from any figure. Every chart is driven by validated observations, never by hand-typed values.
**Open:** stack choice, hosting choice and access layer are separate M7 decisions.

### D-008 — What "a good agent" means here
**PROPOSAL** (no code before M4): the agent is judged by the evaluation, not by features. Targets to measure, not claim: tool-selection accuracy, correct abstention on unanswerable or ambiguous questions, citation correctness, calculation exactness, and graceful tool-failure recovery, each stratified by case type. Design levers that matter more than extra tools: strict typed tool schemas, definition-aware refusal (resident vs overall, SA vs NSA), a "clarify before answering" path, and a deterministic reconciliation tool for advance vs final. These are already in ADR-002; M4 refines them.

### D-007 deployment notes (PROPOSAL, unverified platform details)
- **Keep M1 to M6 local.** Deployment adds no rubric credit before the core works. Decide at the M7 gate.
- **Where documents live in a hosted setup:** raw MOM PDFs should not be uploaded to any hosted bucket. Derived artifacts (Parquet observations, index files) go in a **private** object-storage bucket or are rebuilt at deploy time by the fetch script. App Platform disk is ephemeral, so the index must be rebuilt at start-up or loaded from private storage.
- **Access control on a personal account:** App Platform URLs are public by default. Put an allow-list in front (identity-aware proxy) or add app-level login. Which of these App Platform supports natively is **unverified**; check DigitalOcean docs at the M7 gate.
- **Secrets and spend:** LLM keys only as encrypted environment variables, with a provider-side spend cap and a teardown after the review.

### D-009 — How documents are stored for RAG in this project
**PROPOSAL** (decided at M2/M3 gates). Layers: raw files (local, gitignored), manifest (versioned JSON), passages (Parquet, one row per passage with locator and hash), keyword index (BM25), dense index (embeddings, store chosen at M3). No database server for a corpus of this size.

### D-010 — Presentation is an interactive report page
**DECISION** (owner, 30 Oct 2026). All docs, data and figures must be presentable. The presentation is an interactive, report-style web page reviewers can explore themselves, alongside the 20-minute live demo. Plan: `docs/presentation-plan.md`. M1 consequence: `labourlens export` writes presentation-ready JSON (`data/export/`, numbers and links only, no MOM text) and figures are slide-grade. Stack, hosting and PDF fallback are decided at the M7 gate. Reversible.

### D-011 — Human feedback loop in the interface (PROPOSAL)
Design in `docs/human-feedback-design.md`. Recommended: build a structured feedback loop (claim, citation, abstention, error-type labels, blind side-by-side preference), store it append-only, feed metrics, triage and gold-set growth, and export preference pairs as a data format only. Do not claim RLHF: no reward model or fine-tuning is performed. Alternative: add a lightweight reward-model or DPO experiment on open weights, which is out of scope for the time budget. Decided at M6/M7 gates.

### D-012 — Persist the BM25 index on disk (DECISION, owner, 30 Oct 2026)
The M2 keyword index is built once and persisted under `data/index/`, with a hash of the passage corpus and parser version in its name. On load, a mismatch between the index's corpus hash and the current passages fails loudly instead of serving stale text. Index files are derived from MOM text and stay out of git. Alternative rejected: rebuild in memory on every start (simpler, but hides staleness and slows each run). Reversible.

### D-013 — Managed PostgreSQL for the hosted demo (DECISION on direction, owner, 30 Oct 2026; provider and details open)
Owner preference: use a managed Postgres at the M7 hosted demo to show infrastructure skills. Scope: **M1 to M6 stay local and file-based (D-007, D-012).** At M7, Postgres stores run logs, tool traces and human feedback (D-011), and may later hold vectors via pgvector. For development parity, run the same Postgres version locally in Docker. Infrastructure should be defined as code (for example Terraform) and be explainable: network isolation (no public database endpoint), least-privilege roles, secrets outside the repo, backups and migrations (versioned SQL). **Constraint:** MOM text must not be stored in a cloud database unless the hosted copy is private and access-controlled (D-001, D-007); passages and indexes still rebuild at startup. Open: provider, region, pgvector use, cost. Honest trade-off: this adds hosting cost, setup time and a failure surface versus SQLite; it must not displace M2 to M6 work.

### D-014 — DigitalOcean as cloud provider (DECISION, owner, 30 Oct 2026)
The M7 hosted demo uses DigitalOcean Managed PostgreSQL (D-013). Provider-specific details are **unverified until M7** (current plans, pricing, regions, VPC and trusted-sources firewall behaviour, pgvector availability, Terraform provider capabilities): verify against DigitalOcean's official docs at that gate before building. No cloud resources are created before then, and nothing in M1 to M6 depends on this. Alternatives not chosen: other providers (no account preference stated).
