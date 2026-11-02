# LabourLens

LabourLens is an evidence-grounded research assistant for Singapore policy researchers and labour-market analysts. It combines official statistics (data.gov.sg datasets from MOM and SingStat) with MOM labour-market reports. It retrieves source passages and returns structured answers with citations, deterministic calculations, an honest abstention when the evidence is thin, and a visible tool-activity trace.

**Start here:** [`SUBMISSION.md`](SUBMISSION.md) is the two-minute guide: what to read, three commands to run, what a clone can and cannot reproduce, and the limitations. This README is the longer version. A table of the short names and internal ids used in the documents is in the [glossary](docs/glossary.md).

**Scope.** Supported answer period: **2024-Q1 to 2026-Q2** ([scope decision](docs/decisions/ADR-001-scope.md)). Earlier documents are context only; a request that needs a pre-2024 figure must abstain. Out of scope: forecasts, individual employment advice, unsupported causal claims, unrestricted web research.

**Live site:** <https://labourlens.navig.me> (report and workbench), on one DigitalOcean Droplet, deployed by [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). The workbench needs an access code, which is shared privately and is not in this repository. Live answers make paid model calls; the application has its own daily budget limit, but a provider-side spend cap has **not** been verified ([deployment](docs/deploy.md)).

## What it does

Inside one bounded LangGraph loop the planner chooses among three tools: search the reports (returns ranked passages), look up a statistical series (returns validated rows), and calculate a change (deterministic code, never model arithmetic). Report search runs inside the loop: keyword and embedding retrieval, a period and release filter, then a model rerank. Every answer cites exact passages or rows, or declines.

## The result in three lines

1. **Filter then rerank beats plain hybrid search on the 237 development questions** (0.897 against 0.827 for the main model, +7.0 points, 95% interval [3.6, 10.6]; second model +5.3 [1.9, 8.9]). These are the questions that shaped the design, so this is the optimistic number.
2. **On unseen questions there is no demonstrated gain.** On the original 31 test questions the difference includes zero (+3.2 [-3.2, 11.3]); on the 65 fresh questions it is slightly negative (-3.1 [-7.7, 0.8]). I keep filter then rerank as the default for the development gain and the lower over-abstention, not because it is shown to generalise.
3. **The two models tie** (0.897 each on development). I use `gpt-6-luna` because it costs about 60% as much, not because it is more accurate.

**Caveats that matter.** The reference answers ("gold") were drafted by AI and signed off by one person after the runs were scored: these are agreement figures, not validated accuracy. Claim support and fact coverage are scored by an AI judge; a second-family AI check did not reproduce one of the gains and is not human review. The final evaluation ran twice per setting; two runs are not a variance estimate, and intervals resample questions, not runs. Private MOM and MTI sources must be acquired separately.

**Not claimed:** accuracy on unseen questions; a confirmed benefit of reranking on held-out data; causal explanations of labour-market changes; forecasts; advice to individuals; that the served web app is exactly the evaluated system (it adds a scope check and a follow-up rewrite, see [Served versus evaluated](#served-versus-evaluated)); a provider-side spend cap.

## Run it

Prerequisites: Git, [uv](https://docs.astral.sh/uv/), CPython 3.12 (uv can provision it) and make. No Node or npm, Docker, provider key or private corpus is needed. From the repository root:

```bash
make setup                                    # install the locked dependencies
make verify && uv run labourlens mcp-demo && uv run python scripts/final_mean.py   # checks, MCP client demo, recompute the headline
LABOURLENS_DEMO_ENABLED=false make serve      # report and workbench page at http://127.0.0.1:8000
```

Open <http://127.0.0.1:8000>, `/deck` or `/workbench`. In a public clone the rights scan prints `NOT CHECKED`, not a pass, because it needs private MOM and MTI text. The clean-clone audit of commit `d8a0b0e` on 2 Nov 2026 recorded 1,100 passed, 1 skipped, 57 deselected; durations depend on host and cache. That is historical evidence, not a target count ([fresh-clone record](docs/fresh-clone-check.md)). `make help` lists every target; [`docs/reproduce.md`](docs/reproduce.md) has the command for each artefact.

### What can run with which inputs

| Without private corpus or key | With the private corpus or saved outputs, no key | With an API key (costs money) |
|---|---|---|
| Locked install, CLI help, offline tests, `build-report`, report-only `serve`, `mcp-demo`, `scripts/final_mean.py`, paired comparisons from committed scores, the saved second-judge summary | `build`, `eda`, `export`, keyword retrieval, corpus tests and the real rights scan need the source files; re-scoring without the judge needs private raw answers | Live answers, embedding-cache preparation, `mcp-agent-demo`, new experiments, reranked retrieval, model-judged scoring, attack-suite generation (`OPENAI_API_KEY`); a new second-judge run (`ANTHROPIC_API_KEY`) |

The final aggregation and paired comparisons are recomputed offline from committed scored rows. `mcp-demo` uses the committed statistical store and snapshots, and writes the gitignored `data/runs/mcp-demo-transcript.md`, not the committed transcript. Source downloads cannot restore private historical model outputs. `build-report` reads curated artefacts from the current commit and runs no experiments. The CLI lists 38 subcommands; a reviewer needs `serve`, `build-report`, `mcp-demo`, `rights-scan` and `audit-report`. The review-ingest commands need original owner exports and are not reproducible from a public checkout.

**Rebuild the corpus** (needs network and time; rewrites generated files, so not on a checkout whose `data/` you want to keep): `uv run labourlens fetch`, then `build`, `eda`, `export`. `fetch --kind datasets|documents` and `--only <source_id>` narrow it. Hashes and provenance are recorded in `data/manifests/`. A fresh fetch acquires current publisher bytes, not a guaranteed copy of the historical corpus.

**Deploy:** [the deployment guide](docs/deploy.md) covers your own registry, domain and private corpus. Docker, SSH tools, DNS and ports 80/443 are deployment prerequisites, not quick-start ones.

**Enable the live workspace locally:** set `OPENAI_API_KEY` (environment or a private `.env`), `LABOURLENS_ACCESS_CODES`, `LABOURLENS_SESSION_SECRET` and `LABOURLENS_DEMO_ENABLED=true` ([configuration](docs/deploy.md#4-server-configuration-srvlabourlensenv)). It needs the processed data listed in [`deploy/runtime-data.txt`](deploy/runtime-data.txt) and makes paid calls: use a restricted provider project with a provider-side budget. Feedback is operational evidence, not a gold label.

**Sample questions**

- What was the seasonally adjusted resident unemployment rate in Q2 2026?
- How did the vacancy-to-unemployed ratio change from Q1 to Q2 2026?
- What do the statistics and the Q2 2026 final report say about retrenchments?
- How do the Q2 2026 advance and final employment estimates differ?
- What was the unemployment rate? (Should ask which population and adjustment.)
- What is the verified reason for the employment dataset and report discrepancy? (The corpus may not establish one.)

## Terms

*Development questions*: 237 questions used while building the system. *Held-out*: questions written or frozen before a run and not used for tuning (the original 31 and the 65 fresh ones). *Hybrid search*: keyword plus embedding retrieval. *Filter then rerank*: restrict passages by period and source stage, then let a model reorder them. *Over-abstention*: declining a question the evidence can answer. *Gold*: the reference answers, AI-drafted and then reviewed by one person. *MCP*: Model Context Protocol, the tool interface the statistics server speaks. Short names for experiments and decisions: [glossary](docs/glossary.md).

## Results

Behaviour accuracy means the answer's status matches the gold label (answer, abstain, clarify or refuse); it does not check content, which other metrics cover. Behaviour, key-number recall, calculation correctness, false answers and over-abstention are deterministic code. Claim support and fact coverage come from an AI judge (`gpt-6.1-terra`). Intervals are 95% case-bootstrap intervals (Wilson only for the attack suite). Gold labels were AI-drafted; I signed off on every case, answer verdict and source check after the runs were scored (403 items in four streams: 268 gold questions, 65 fresh questions, 40 saved answers, 30 source checks; only the first two are questions). One reviewer after AI pre-review is not independent inter-rater evidence.

### The final evaluation (two runs, averaged)

Mean of the first and second run, with both single runs beside it, from [`final-mean.json`](experiments/eval/final-mean.json) and the [registration of the second run](docs/experiments/fin2-replicate.md). Built on document build v3.1 (85 sources, 16,419 passages), the base tool set and the judge above. Do not compare numbers across document builds.

| Question set | Model | Filter then rerank: mean (first, second run) | Hybrid search: mean (first, second run) | Paired difference, 95% interval |
|---|---|---:|---:|---|
| 237 development questions | `gpt-6-luna` | 0.897 (0.886, 0.907) | 0.827 (0.844, 0.810) | +7.0 points [3.6, 10.6] |
| 237 development questions | `gpt-5.6-luna` | 0.897 (0.899, 0.895) | 0.844 (0.840, 0.848) | +5.3 points [1.9, 8.9] |
| Original 31 test questions | `gpt-6-luna` | 0.839 (0.839, 0.839) | 0.806 (0.839, 0.774) | +3.2 points [-3.2, 11.3] |
| Original 31 test questions | `gpt-5.6-luna` | 0.839 (0.839, 0.839) | 0.823 (0.839, 0.806) | +1.6 points [-8.1, 12.9] |
| 65 fresh questions | `gpt-6-luna` | 0.715 (0.708, 0.723) | 0.746 (0.754, 0.738) | -3.1 points [-7.7, 0.8] |
| 65 fresh questions | `gpt-5.6-luna` | 0.731 (0.723, 0.738) | 0.738 (0.723, 0.754) | -0.8 points [-2.3, 0.0] |

Source: [evaluation report, headline](docs/evaluation-report.md#headline-the-final-evaluation-two-runs-averaged). Resampling is 10,000 case-bootstrap draws, seed 20261030. On development, filter then rerank has the same positive sign in both runs and both models. The cost ratio against hybrid search is about 1.7 and latency about 1.5 for the main model.

### Other results

| Question | Result | Where |
|---|---|---|
| Which retrieval method finds the evidence? (128 development report questions, hit@8) | Keyword .477, embeddings .367, hybrid .539. Keyword alone beats embeddings; hybrid over keyword is not demonstrated (+.062 [-.023, .148]) | [same-set comparison](experiments/runs/dev-R-V31-methods/SUMMARY.md) |
| Does a second AI judge agree? | 84.3% agreement on claim labels, kappa 0.436, 117 valid pairs. An AI check, not human review | [second-judge summary](experiments/xjudge/sonnet55-FIN-s60-b-20261102/SUMMARY.md) |
| Does the served web chain hold up? | 90.8% on a 65-case sample, both models | [served-chain check](docs/experiments/served-chain-eval.md) |
| Attack suite (36 hand-written cases) | 35/36 in all four configurations in the fresh rerun; the planted-false-figure attack is not stable | [threat model](docs/threat-model.md) |
| Human review (one reviewer, after scoring) | 403 items: 268 gold, 65 fresh, 40 answers, 30 source checks | [review scope](docs/human-review/owner-review-final-summary.md) |
| History: first build, 237 development questions | Filter-then-rerank agent 0.903 against hybrid agent 0.779; descriptive, not paired | [evaluation report](docs/evaluation-report.md) |
| History: original 31 test questions, first build | +16.1 points [0.0, 32.3]; gain not demonstrated | [paired result](experiments/heldout/paired.txt) |
| History: 65 fresh questions, registered run | 0.754 against 0.708, p = 0.25; gain not confirmed | [registered result](docs/experiments/m7-heldout-v2-result.md) |
| Extraction fixes tested alone | 0.886 against 0.903; no measurable gain | [evaluation report](docs/evaluation-report.md) |
| Early model screen | 30 questions, six models; no reliable ranking | [screen and limits](docs/experiments/m3-answer-generation.md) |
| Regression check on the served system | 0.903 and 0.916 (the two models); several changes at once, not an ablation | [regression report](experiments/eval/agent-dev-X2-REPORT.md) |
| Extra arithmetic tool (not adopted) | 0.903 to 0.895; 0.916 to 0.899 | [failed criteria](docs/experiments/m7-tool-fix.md) |

**The question sets are separate and not additive.** The 268 reference questions are the 237 development questions plus the 31 original test questions. Those 31 share evidence with development (25 of 31 cite at least one development evidence id, 15 have their whole evidence set in it), so they are held out by question, not by evidence. The 65 fresh questions were written on six sources no earlier case cites and signed before their registered run, then reused for labelled diagnostics and the replicate. The tool-set diagnostic re-ran those same 65, so it is not a fresh test. The 40 saved answers (a failure-enriched sample) and 30 source checks are review items, not question sets. Five original test cases changed after the freeze; the full version history is in the [evaluation report](docs/evaluation-report.md). The 65 fresh questions use the same system, prompts and tools, with an AI-drafted gold I approved unchanged.

The live agent defaults to filter then rerank, the base tools and `gpt-6-luna` (prompt versions are in the [glossary](docs/glossary.md)). No run establishes an accuracy winner between the models.

### Served versus evaluated

**Measured, 2 Nov 2026.** The served research chain (small-talk reply, follow-up rewrite, scope check, agent with MCP statistics) was measured on 65 cases: 51 stratified development questions, eight hand-written diversion probes and six context probes. Both models score 90.8% overall; on the development questions alone 90.2% (`gpt-6-luna`) and 88.2% (`gpt-5.6-luna`). Diversion probes pass 8/8 for both and false diversion is zero. Context probes pass 5/6 and 6/6; the one failure is for the main model. With web steps on for both routes, MCP minus direct is 0.0 points for the main model (one case better, one worse) and +3.1 points [0.0, 6.2] for the second (two better, none worse), a descriptive 90% interval. No accuracy loss was observed, which is not a statistical non-inferiority proof.

Sources: [registration](docs/experiments/served-chain-eval.md), [metrics for the MCP route](experiments/runs/served-dev-S65-mcp-on/), [paired comparison, web steps on](experiments/served/paired-S65-direct-on.json), [web-off control](experiments/served/paired-S65-direct-off.json). Conversation history stays in browser memory for up to three finished turns; date probes are anchored to 2 Nov 2026.

## Corpus versions

The system and the live site use build v3.1 (85 sources, 16,419 passages, 1,847 chunks). Earlier results used earlier builds and stay labelled as history; the final evaluation, the current-corpus retrieval checks, the served-chain check and the fresh attack rerun all ran on v3.1.

| Build | Contents | Used for |
|---|---|---|
| **v1** | 13,484 passages | The first experiments and the original test (frozen) |
| **v2** | 15,915 passages, 43,662 observations | Extraction fixes tested alone |
| **v3** | v2 plus six labour-only sources: 85 sources (36 datasets, 49 documents: 27 PDFs, 22 HTML), 52,020 observations (4,300 in the answer scope), 16,419 passages, 1,847 chunks; 276 build checks (269 pass, 7 warn) | The [manifest](data/manifests/manifest.json), the [quality report](artifacts/data-quality/quality-report.md), the regression check, the first attack rerun on the fixed system and the fresh-question registered run |
| **v3.1 (current)** | Same sources and counts as v3. A refined garbled-text rule relabels 40 passages of one MTI feature article and 4 others; 10 chunk texts change. Snapshot [`v3.1.json`](experiments/corpus-snapshots/v3.1.json), diff [`v3.1-diff.json`](experiments/corpus-snapshots/v3.1-diff.json) | The local store, the live site and all current-corpus evidence |

Frozen v1 and v2 results are kept unchanged. `/healthz` on the live site shows the commit and the corpus fingerprint. Details: [data sheet](docs/data-sheet.md), [evaluation report](docs/evaluation-report.md).

## Experiments

Commands that call a model or embeddings API cost money. Use a disposable reproduction checkout and a new, unused experiment tag. The experiment commands refuse to overwrite existing outputs; their `--force` flag replaces evidence and must never be used on the authoritative submission. Gold-hash checks are independent of `--force`, and scoring commands refuse a gold file whose hash differs from the run's record unless `--allow-gold-mismatch` is given. The registered original-test comparison already ran once and must not be rerun to pick a winner. All commands, with what each needs: [reproduce](docs/reproduce.md). Results and their history: [evaluation report](docs/evaluation-report.md). Prompts: [`prompts/`](prompts/).

## MCP and audit

```bash
uv run python -m labourlens.mcp.server   # stdio MCP server
uv run labourlens mcp-demo               # recorded session of real calls; writes data/runs/mcp-demo-transcript.md
uv run labourlens audit-report
```

The MCP server exposes read-only statistics, discovery, comparison, revision and provenance tools, plus source-catalogue resources. The [MCP transcript](docs/mcp-demo-transcript.md) records discovery, validated calls, failures, hostile output and a comparison with direct integration. In the live app only the statistics lookup goes over MCP, on stdio (shown as `transport: mcp` in the trace); report search and the calculation run in process. A server failure is a typed failure, never a silent switch to in-process tools. A tested variant sends all three tools over MCP (`LABOURLENS_TOOL_TRANSPORT=mcp_all`, the app starts the server with `--agent-tools`; exact arithmetic is computed by the server from ids, never from numbers the model supplies). It was slower with no accuracy gain, so it is **not live**. `direct` bypasses MCP.

Every frozen accuracy evaluation and the attack suite (except the 10 server-failure cases) called the tools directly, so their results do not describe the MCP routes. The served-chain check measured the statistics-only route (the live one). The all-three-tools variant was measured on one model, `gpt-6-luna`, on the same 65 cases (one run): accuracy 0.877 (57/65) against 0.908 (59/65) for statistics-only MCP and for direct, a difference not shown to be real (paired -0.031); median latency 14.3 s against 12.4 s and 10.8 s; 95th percentile 51.4 s against 34.7 s and 32.8 s, above the limit set in advance; cost about $0.0026 per question. The second model was stopped at 17 of 65 cases at the owner's request and not rerun ([deviations and result](docs/experiments/served-chain-mcp-all.md#deviations-and-result-recorded-2-november-2026-after-the-run)). Recorded protocol cost for a statistics call: median 36.1 ms over MCP against 4.5 ms direct, plus 1.84 s at startup. Audit records hold bounded task states and outcomes, never model reasoning ([audit and logging](docs/audit-and-logging.md)).

## Repository structure

| Path | Purpose |
|---|---|
| `src/labourlens/` | Ingestion, retrieval, answers, agent, MCP, evaluation, security, audit, web serving |
| `tests/` | Data, retrieval, agent, MCP, audit and web tests ([`tests/README.md`](tests/README.md)) |
| `prompts/`, `specs/` | Versioned prompts; source catalogues, schemas and price assumptions |
| `data/manifests/`, `data/snapshots/` | Provenance and immutable statistical snapshots |
| `data/raw/`, `data/passages/`, `data/runs/` | Local only, gitignored (rights and sensitivity) |
| `experiments/`, `artifacts/` | Gold set, saved metrics, attack-suite results, quality reports, figures |
| `web/`, `deploy/`, `scripts/`, `.github/` | Report and workbench front end; deployment |
| `docs/` | Documentation ([index](docs/README.md)); `docs/archive/` holds superseded planning drafts; `docs/process/` the initial plan |
| `Makefile`, `.pre-commit-config.yaml`, `.gitleaks.toml`, `.github/workflows/ci.yml` | One entry point and the checks CI runs |

## Documents

| Document | What it is |
|---|---|
| [Architecture](docs/architecture.md) | Data flow, agent graph, guardrails, trust boundaries; [rendered diagram](docs/img/architecture.svg) |
| [AI-assisted development](docs/ai-assisted-development.md) | Method, approval gates, controls with their limits, mistakes caught |
| [Data sheet](docs/data-sheet.md) | Sources, licences, schema, checks, EDA findings |
| [Evaluation report](docs/evaluation-report.md) | Plain summary, design, results, error analysis, review rubric, limits |
| [System card](docs/system-card.md) | Intended use, risks, controls |
| [Threat model](docs/threat-model.md) | Attacks tested, controls, residual risk |
| [Innovation assessment](docs/innovation.md) | Forward plan (about two pages) |
| [Demo script](docs/demo-script.md) | 20-minute live demonstration plan |
| [Requirements matrix](docs/requirements-matrix.md) | Assessment requirement to evidence, with honest status |
| [Deployment](docs/deploy.md) | Droplet runbook and verified state |
| [Decisions](docs/decisions.md), [progress](docs/progress.md) | Dated decision log (entries have ids such as D-056; the [glossary](docs/glossary.md) maps them to plain names); current state |
| [Agent logs](docs/agent-logs.md) | How AI agents were used: contract, approval gates, controls, mistakes caught |
| [Reproduce](docs/reproduce.md), [fresh-clone check](docs/fresh-clone-check.md) | Commands to each artefact, what needs the private corpus or an API key |
| [Review records](docs/human-review/README.md) | Owner review and AI reviews, kept separate |
| [Glossary](docs/glossary.md) | Short names, internal ids and terms |
| [Security policy](SECURITY.md) | Secrets, untrusted text, rights |
| [MCP transcript](docs/mcp-demo-transcript.md) | Protocol demonstration |

Planning drafts in `docs/archive/planning/` record earlier proposals; they are not evidence that anything ran. The presentation deck has 28 main slides (42 with the appendix); press X twice quickly for speaker notes.

## Rights and responsible use

Statistical data comes from data.gov.sg datasets published by MOM and SingStat under the [Singapore Open Data Licence v1.0](https://developers.data.gov.sg/open-data-licence); keep attribution and non-endorsement notices. LabourLens is not endorsed by any agency. MOM PDFs carry restrictive copyright notices and HTML release rights are unresolved, so reports, extracted passages, raw answers and judge payloads stay local and are not in the repository, image or static report. The repository publishes provenance, identifiers, locators, links and short permitted quotations.

Treat user input, retrieved passages and MCP content as untrusted data. Do not submit confidential, personal or classified information. Inspect citations and definitions before using an answer in policy work.

## Main limitations

- **Reference answers and judge.** Gold labels were AI-drafted first and the judge is an AI. I signed off on every case, answer verdict and source check, as one reviewer, after AI pre-review and after the saved runs were scored: not independent inter-rater evidence. Gold v3.7 changes only provenance fields; earlier saved evaluations are still scored on earlier gold versions, and only the two runs of the final evaluation were scored on v3.7 (generation ran on v3.6). Four owner change-clicks are recorded but not applied. The attack suite and the automatic judge checks are not human review. The second-judge check covers one saved sample only; claim support remains judge-dependent (kappa 0.436, three omitted items) and a support gain for `gpt-5.6-luna` was not reproduced.
- **Original test questions.** They share evidence with development; the gain of filter then rerank over hybrid search is not demonstrated. The separate 65 fresh questions met their pre-registered rule for the main model on three cases, with no gain for the second model and a lower bound of 0.0 when one question group is removed; I would not call it a confirmed gain.
- **Numerical comparisons are weak.** Both settings score about 0.71 to 0.75 on the fresh questions, and numerical comparisons about 0.21, mostly because the tools cannot do arithmetic on figures printed in reports. A second tool set that adds it was built and tested; it did not pass its pre-declared development criteria and was **not adopted**. Its large gain on the fresh questions is a post-freeze diagnostic on cases whose errors motivated the fix, so it is optimistic by construction.
- **The planted-false-figure attack is not stable.** The planted-figure guard is a closed grammar. The first run on the fixed system passed 36/36, but in the fresh 2 Nov rerun all four configurations score 35/36 under both scorers. Rescoring old outputs with the second scorer is diagnostic, not new evidence.
- **The regression check changed several factors at once;** it does not isolate any one of them. Its rise in ungrounded-number cases mixes a wider check with possible behaviour change.
- **The ingestion scanner** originally missed five paraphrased probes; six patterns and regression tests now catch those known examples, not all attacks. Citation matching shows a quote exists, not that it supports a claim.
- PDF tables can extract poorly; report-only figures are not deterministic calculation inputs.
- Dataset and report employment totals can differ in definition or vintage; the corpus does not explain every gap.
- A single-process prototype with local state, not a multi-user government system; provider-side spend cap unverified.

## Licence and attribution

The code and documents are all rights reserved and shared for review ([`LICENSE`](LICENSE)). Statistical data: contains information from data.gov.sg datasets of the Ministry of Manpower and the Singapore Department of Statistics, under the [Singapore Open Data Licence v1.0](https://developers.data.gov.sg/open-data-licence); not endorsed by the publishers. Three datasets are recorded as licence assumed, not verified (see [data sheet, section 9](docs/data-sheet.md#9-open-licence-items-and-what-the-rights-scan-covers)). MOM and MTI reports are the Ministries' copyright and are not in this repository. Fonts are SIL OFL 1.1 ([`web/static/fonts/LICENSES.md`](web/static/fonts/LICENSES.md)).
