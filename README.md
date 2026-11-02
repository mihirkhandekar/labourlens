# LabourLens

LabourLens is an evidence-grounded research assistant for Singapore policy researchers and labour-market analysts. It combines official statistics (data.gov.sg datasets from MOM and SingStat) with MOM labour-market reports. It retrieves source passages and returns structured answers with citations, deterministic calculations, an honest abstention when evidence is thin, and a visible tool-activity trace.

**Start here:** [`SUBMISSION.md`](SUBMISSION.md) is the two-minute guide (what to read, three commands to run, what a clone can and cannot reproduce, ten limitations). This README is the long version.

**Scope.** Supported answer period: **2024-Q1 to 2026-Q2** ([ADR-001](docs/decisions/ADR-001-scope.md), [D-031](docs/decisions.md#d-031--supported-analysis-period-is-a-hard-scope-decision-owner-30-oct-2026)). Earlier documents are context only; requests that need a pre-2024 figure must abstain. Out of scope: forecasts, individual employment advice, unsupported causal claims, unrestricted web research.

**Live site:** <https://labourlens.navig.me> (report and workbench). It runs on one DigitalOcean Droplet, deployed by the GitHub Actions workflow in [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). Live research is switched on and needs an access code, which is shared privately and is not in this repository. Live answers make paid model calls; a provider-side spend cap has **not** been verified, only the application's own budget limit ([deployment](docs/deploy.md)).

**At a glance**

- **What it does:** answers analytical questions about the Singapore labour market from official statistics and MOM reports, with passage-level citations, deterministic arithmetic and abstention. One bounded LangGraph agent, a read-only MCP statistics server, and an evaluation harness.
- **Main result (D-061, mean of two final runs):** `gpt-6-luna` r3 0.897 versus hybrid 0.827 on 237 development questions (+7.0 points, 95% interval [3.6, 10.6]); second model +5.3 [1.9, 8.9]. Filter then rerank gives a consistent gain on the development questions that shaped it, in both runs and both models, but no demonstrated gain on either the original test or fresh set. The two models tie on development r3 mean (0.897 each); I keep `gpt-6-luna` as default because it costs about 60% as much, not because it is more accurate. The development cost ratio is about 1.7 and latency about 1.5 for the primary model. Two runs per arm are still not a variance estimate; intervals resample cases, not independent runs.
- **What the final results are on:** document build v3.1 (85 sources, 16,419 passages; v3 differed only in how 40 passages of one article are labelled), retrieval `r3` (period and stage filter, then rerank), `gpt-6-luna` as the primary model (`gpt-5.6-luna` compared), `gpt-6.1-terra` as judge, and the base tool set. Do not compare numbers across document builds.
- **Caveats:** gold labels were AI-drafted and signed off by one person after scoring: agreement, not validated accuracy. Claim support and fact coverage are judge-measured: a second-family AI check on a saved FIN sample did not reproduce the `gpt-5.6-luna` support gain, and is not human review. Final arms ran twice; other studies have one run unless labelled. Private MOM and MTI sources must be acquired separately.

Reviewer entry points: [`SUBMISSION.md`](SUBMISSION.md) (what to read first and how to run it), [`docs/README.md`](docs/README.md) (documentation index), [`docs/agent-logs.md`](docs/agent-logs.md) (how AI agents were used, with the approval record).

**Terms used below.** *Development questions*: 237 questions used while building the system. *Held-out*: questions written or frozen before a run and not used for tuning (31 original, 65 fresh). *Hybrid*: keyword plus embedding retrieval. *Filter then rerank (`r3`)*: restrict passages by period and source stage, then let a model reorder them. *Over-abstention*: declining a question the evidence can answer. *Gold*: the reference answers; AI-drafted, then reviewed by one person. *MCP*: Model Context Protocol, the tool interface the statistics server speaks. *D-0nn*: an entry in the [decision log](docs/decisions.md). More: [glossary](docs/glossary.md).

**Not claimed:** accuracy on unseen questions (the labels are AI-drafted and were reviewed by one person after the runs were scored); a confirmed benefit of reranking on held-out data; causal explanations of labour-market changes; forecasts; advice to individuals; that the served web app is exactly the evaluated system (it adds a scope check and a follow-up rewrite, see [Served versus evaluated](#served-versus-evaluated)); a provider-side spend cap.

**Where the evidence is.** D-061 headline: mean of two runs per arm, both single runs beside the mean, from [`final-mean.json`](experiments/eval/final-mean.json) and the [pre-registered amendment](docs/experiments/fin2-replicate.md).

| Question set | Model | Filter then rerank: mean (first, replicate) | Hybrid: mean (first, replicate) | Paired mean difference, 95% interval |
|---|---|---:|---:|---|
| Development, 237 | `gpt-6-luna` | 0.897 (0.886, 0.907) | 0.827 (0.844, 0.810) | +7.0 points [3.6, 10.6] |
| Development, 237 | `gpt-5.6-luna` | 0.897 (0.899, 0.895) | 0.844 (0.840, 0.848) | +5.3 points [1.9, 8.9] |
| Registered original test, 31 | `gpt-6-luna` | 0.839 (0.839, 0.839) | 0.806 (0.839, 0.774) | +3.2 points [-3.2, 11.3] |
| Registered original test, 31 | `gpt-5.6-luna` | 0.839 (0.839, 0.839) | 0.823 (0.839, 0.806) | +1.6 points [-8.1, 12.9] |
| Fresh, 65 | `gpt-6-luna` | 0.715 (0.708, 0.723) | 0.746 (0.754, 0.738) | -3.1 points [-7.7, 0.8] |
| Fresh, 65 | `gpt-5.6-luna` | 0.731 (0.723, 0.738) | 0.738 (0.723, 0.754) | -0.8 points [-2.3, 0.0] |

Source: [evaluation report](docs/evaluation-report.md#headline-the-final-evaluation-d-056-1-nov-2026). All headline intervals are 95% case-bootstrap intervals on per-case means (10,000 resamples, seed 20261030). FIN is the first run, FIN2 the replicate. Not a run-variance estimate.

## Quick start

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). Run from the repository root.

```bash
make setup     # uv sync --frozen (Python 3.12 and uv required)
make verify    # lint, offline tests, docs links, rights scan, secret scan; about 2 to 3 minutes
make serve     # report, presentation and workbench page at http://127.0.0.1:8000
```

In a clone `make verify` prints `rights-scan: NOT CHECKED`. That is expected: the scan needs the private MOM and MTI text, so it is not a pass. Observed on 2 Nov 2026 in a fresh clone: 1,027 passed, 1 skipped, 57 deselected, about 3 minutes in total ([details](docs/fresh-clone-check.md)).

`make help` lists every target. The underlying commands, for reference:

```bash
uv sync --frozen
uv run labourlens --help
uv run pytest -q -m 'not corpus'
uv run labourlens build-report
LABOURLENS_DEMO_ENABLED=false uv run labourlens serve --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000> for the report and <http://127.0.0.1:8000/workbench> for the workbench page. This offline path needs no API key and no local corpus. `build-report` reads curated artefacts from the current Git commit and runs no experiments.

`labourlens --help` lists 40 subcommands. A reviewer needs `serve`, `build-report`, `mcp-demo`, `rights-scan` and `audit-report`. The review-pack, `pending-ingest`, `v2-*` and `review-ingest` commands are the owner's tooling and need files that are not in the repository; the experiment commands cost money.

### What you can and cannot run without the corpus

| Needs nothing but the checkout | Needs the local corpus (`data/raw`, `data/passages`, `data/runs`; gitignored for rights reasons) | Needs an API key and spends money |
|---|---|---|
| `uv sync`, CLI help, `pytest -m 'not corpus'`, `build-report`, report-only `serve`, `mcp-demo` (about 40 s; writes the gitignored `data/runs/mcp-demo-transcript.md` and leaves the committed [transcript](docs/mcp-demo-transcript.md) alone unless you pass `--out docs/mcp-demo-transcript.md`), `judge-xfamily --dry-run` and `--summary` | `fetch`, `build`, `eda`, `export`, `scan-sources`, `trace`, `pytest -m corpus`, the real `rights-scan`, the private raw outputs needed for a new `judge-xfamily` run | live answers, `mcp-agent-demo`, `answer-exp`, `agent-exp`, reranked retrieval, model-judged `eval`, the threat suite, a paid `judge-xfamily` run (`ANTHROPIC_API_KEY`) |

`uv run pytest -q -m 'not corpus'` is the supported command on a fresh clone. Corpus-marked tests skip cleanly when `data/` is absent, so plain `uv run pytest -q` also runs, but they only check anything with the local corpus. Metrics cannot be regenerated without the corpus and a key, so they are read from committed JSON under [`experiments/`](experiments/). MOM reports are not redistributed: acquire them yourself with `labourlens fetch`, which depends on publisher access.

### Rebuild the corpus (needs network and time)

```bash
uv run labourlens fetch
uv run labourlens build
uv run labourlens eda
uv run labourlens export
```

`fetch --kind datasets|documents` and `--only <source_id>` narrow acquisition. Immutable hashes and provenance are recorded in `data/manifests/`. Do not run these on a checkout whose `data/` you want to keep as is: they rewrite generated files.

### Enable the live workspace locally

Set `OPENAI_API_KEY` (environment or a private `.env`), plus `LABOURLENS_ACCESS_CODES`, `LABOURLENS_SESSION_SECRET` and `LABOURLENS_DEMO_ENABLED=true` ([configuration guide](docs/deploy.md#4-server-configuration-srvlabourlensenv)). The live workspace needs the processed observations, passages, manifest and embedding cache listed in [`deploy/runtime-data.txt`](deploy/runtime-data.txt). It makes paid calls: use a restricted provider project and a provider-side budget. Feedback is operational evidence, not a gold label.

### Sample questions

- What was the seasonally adjusted resident unemployment rate in Q2 2026?
- How did the vacancy-to-unemployed ratio change from Q1 to Q2 2026?
- What do the statistics and the Q2 2026 final report say about retrenchments?
- How do the Q2 2026 advance and final employment estimates differ?
- What was the unemployment rate? (Should ask which population and adjustment.)
- What is the verified reason for the employment dataset and report discrepancy? (The corpus may not establish one.)


## Served versus evaluated

**MEASURED RESULT (D-058/D-061, 2 Nov 2026).** The served research chain (small-talk, contextualise, scope triage, agent with MCP statistics) was measured on 65 cases: 51 stratified development gold cases, eight hand-written diversion probes and six context probes. Both models score 90.8% overall; gold-only scores are 90.2% / 88.2% (`gpt-6-luna` / `gpt-5.6-luna`). Diversion probes pass 8/8 for both, context probes 5/6 / 6/6 (SERVED-P14 fails for the primary model), and false diversion is zero. With web steps on for both routes, MCP minus direct is 0.0 points (one better, one worse) / +3.1 points [0.0, 6.2] (two better, none worse), a descriptive 90% case-bootstrap interval. No accuracy loss was observed on this sample, not a statistical non-inferiority proof. Median / p95 total latency is 12.4 / 34.7 s and 10.2 / 32.0 s; estimated cost per question $0.00268 / $0.00385, excluding one-off startup latency. The 38 / 41 MCP attempts include 1 / 4 `not_found` tool errors from unmatched dimensions or series, not transport failures. The direct/web-off control scores 75.4% / 72.3% overall (gold-only 86.3% / 84.3%); it changes two factors, and its eight diversion probes fail by design. This is one run, reused development evidence, hand-written date-anchored probes, the same judge family, and no HTTP admission or rights-projection evaluation; the full 237/31/65 evaluation still uses direct statistics and no web steps.

Sources: [served-chain registration](docs/experiments/served-chain-eval.md), [MCP-route metrics](experiments/runs/served-dev-S65-mcp-on/), [paired MCP/direct web-on](experiments/served/paired-S65-direct-on.json), [paired web-off control](experiments/served/paired-S65-direct-off.json). Conversation history stays in browser memory for up to three finished turns; date probes are anchored to 2 Nov 2026.

## Headline results

All numbers are saved outputs, each with its source file. Behaviour accuracy means the answer's status matches the gold label (answer, abstain, clarify or refuse); it does not check content, which other metrics cover (key-number recall, claim support, fact coverage). Behaviour status, key-number recall, calculation correctness, false-answer and over-abstention are deterministic code. Claim support and fact coverage come from an AI judge (`gpt-6.1-terra`). Gold labels were drafted by AI. I then went through them in the review interface and signed off on every case, answer verdict and source check (four separate streams, 403 items in total: 268 gold questions, 65 held-out v2 questions, 40 saved system answers and 30 source checks; only the first two are questions). It is one reviewer, working after AI pre-review (three separate AI review passes, one model family) and after the saved runs were scored, so it is not independent inter-rater evidence. These are agreement figures, not validated accuracy. Intervals are 95% case-bootstrap intervals (Wilson only for the threat suite).

| Question | Result | Source |
|---|---|---|
| **Headline: final system, D-061, corpus v3.1, two runs per arm** | Filter then rerank gives a consistent gain on the development questions that shaped it, in both runs and both models, but no demonstrated gain on either the original test or fresh set. The two models tie on development r3 mean (0.897 each); I keep `gpt-6-luna` as default because it costs about 60% as much, not because it is more accurate. The development cost ratio is about 1.7 and latency about 1.5 for the primary model. Two runs per arm are still not a variance estimate; intervals resample cases, not independent runs. Mean development over-abstention r3/hybrid: 3.2%/10.1% and 4.2%/8.9%. | [`final-mean.json`](experiments/eval/final-mean.json), [evaluation report](docs/evaluation-report.md) |
| Does another model family judge claim support the same way (D-062, saved FIN run 1)? | **MEASURED, not human review.** `claude-sonnet-5-5` and `gpt-6.1-terra` judged the same 240 sampled answers (60 case IDs per generator, both retrieval arms). Valid-pair analysis covers 117 pairs; three items were `judge_omitted` after one retry, not imputed. Claim labels agree on 84.3% of 432 claims (kappa 0.436); contradiction agrees on 99.6% of 226 answers (kappa 0.907); the unsupported flag agrees on 99.6% of 234 but kappa is 0 because positives are rare. Pooled r3-minus-hybrid claim support for `gpt-5.6-luna` is +16.8 points under the first judge and +0.5 under Claude (development -2.7 under Claude); `gpt-6-luna` is +2.8 and -1.1. Fact coverage differences are +4.2 and +4.3 points under both. Low kappa, omissions and sign changes are reported problem flags. Deterministic behaviour, false-answer and key-number metrics are unchanged. New list-price spend $0.767506 (estimate, not an invoice). | [evaluation report](docs/evaluation-report.md), [summary](experiments/xjudge/sonnet55-FIN-s60-b-20261102/SUMMARY.md), [declaration](docs/experiments/second-judge.md) |
| History, earlier build (corpus v1): does filter plus rerank (A3) beat plain hybrid retrieval (A1) with `gpt-6-luna`? | Development behaviour 0.903 [0.865, 0.937] (n=237) versus 0.779 [0.728, 0.830] (n=235); over-abstention 0.030 [0.008, 0.051] versus 0.157 [0.111, 0.204]. Earlier build and gold, not comparable to the final run; descriptive, not a paired test. | [`experiments/eval/`](experiments/eval/) |
| History: does it hold on the 31 held-out cases (original run)? | r3 0.871 [0.742, 0.968] versus hybrid 0.710 [0.548, 0.839]. Paired gain +16.1 points [0.0, 32.3]: **not demonstrated**. | [`experiments/heldout/paired.txt`](experiments/heldout/paired.txt) |
| History: does it hold on the 65-case held-out v2 set (original run on corpus v3, sources no earlier case cites)? | Original run, build v3 (the registered result): `gpt-6-luna` r3 0.754 versus hybrid 0.708, paired +0.046 (3 better, 0 worse), McNemar exact p = 0.25. The effect is three cases; I would not call it a confirmed gain; `gpt-5.6-luna` 0.723 versus 0.723. Re-run on build v3.1 (D-055): 0.738 versus 0.708 (3 better, 1 worse), p = 0.625, not demonstrated. Corpus and code changed together between the runs. `numerical_comparison` is 0.214 in both, mostly a tool gap. Full text: [evaluation report](docs/evaluation-report.md). | [result](docs/experiments/m7-heldout-v2-result.md), [`paired.json`](experiments/heldout-v2/paired.json), [`paired-v3.1.json`](experiments/heldout-v2/paired-v3.1.json) |
| Do the extraction fixes (corpus v2) help? | No measurable change (dev 0.886 [0.844, 0.924] versus 0.903). | [evaluation report](docs/evaluation-report.md) |
| Which model should generate answers? | Early exploratory screen, 30 development questions, six models (`gpt-4.1-mini`, `gpt-5.4-mini`, `gpt-5.6-luna`, `gpt-6-luna`, `gpt-6-sol`, `gpt-6.1-terra`), with retrieved and with oracle evidence. Price did not track quality; models differ more in caution than in skill; single runs cannot rank neighbours. `gpt-6.1-terra` was a generator candidate here and later became the judge. The later two-model comparison (A3, 237 questions) shows no model winner. | [m3 answer generation](docs/experiments/m3-answer-generation.md) |
| History: does the agent (corpus v3, end-to-end review fixes, cross-check on) hold up on the development set? | **MEASURED** regression check, not an ablation: several factors changed together. Behaviour `gpt-6-luna` 0.903 [0.865, 0.941], `gpt-5.6-luna` 0.916 [0.878, 0.949], both overlapping A3. Cases with an ungrounded number rose for `gpt-5.6-luna` to 0.165 [0.118, 0.215] from 0.051 [0.025, 0.080] in A3 (no overlap), and the check itself was widened in the same change. | [X2 report](experiments/eval/agent-dev-X2-REPORT.md), [evaluation report](docs/evaluation-report.md) |
| Does an extra tool for arithmetic on report figures help (tool set v2, D-046 and D-048)? | **MEASURED, not adopted.** Dev X3 against X2 (n=237, earlier corpus v3 / gold v3.6, one run per model): behaviour `gpt-6-luna` 0.903 to 0.895, `gpt-5.6-luna` 0.916 to 0.899, no gain; the criteria declared before the run **failed for both models** (false-answer cases 7 against 6, and ungrounded numbers in cases that used the new tool). On the held-out v2 questions, re-run as a **post-freeze diagnostic (not held-out, optimistic by construction, not a replacement of the held-out v2 result)**, `numerical_comparison` rose from 3 to 12 of 14 for `gpt-6-luna`. The default tool set is unchanged and the threat suite was not run under v2. | [tool-fix report](docs/experiments/m7-tool-fix.md) |
| Threat suite, 36 hand-written cases | 31 Oct `m7-e2efix-20261031`: defended primary 36/36, second model 35/36 under v1. Fresh 2 Nov `ti06-v2-fresh-20261102`: all four defended/naive configurations 35/36 under both scorers; T-I06 fails again. Old-output v2 rescoring is diagnostic only. Not shown stable. The scanner now covers its five formerly missed paraphrase probes in regression tests, not all paraphrases. | [threat model](docs/threat-model.md) |
| Human review | Gold labels were drafted by AI. The owner then went through them in the review interface and signed off on every case, answer verdict and source check (four separate streams, 403 items in total: 268 gold questions, 65 held-out v2 questions, 40 saved system answers and 30 source checks; only the first two are questions). The strongest human evidence is the first pack (17 answer verdicts, J1 to J10, 3 gold cards), the four change-clicks, J10 and the owner's written policy decisions (D-031, D-034, D-035, D-036, D-047). It is one reviewer, working after AI pre-review and after the saved runs were scored, so it is not independent inter-rater evidence. Gold v3.7 changes no label. The earlier saved evaluations were not rescored on it; only the final FIN/FIN2 evaluations (D-056, D-061) were scored on v3.7 for the development and registered held-out sets, with `--allow-gold-mismatch` because generation ran on v3.6. | [final owner review summary](docs/human-review/owner-review-final-summary.md), [numbers audit](docs/human-review/numbers-audit.md) |

The question sets are separate and not additive. The 268 reference questions are 237 development questions (used while building the system) plus 31 original held-out questions. The original 31 share evidence with development (25 of 31 cite at least one development evidence id, 15 of 31 have their whole evidence set in it), so they are held out by question, not by evidence. The 65 held-out v2 questions are a later set written on six sources no earlier case cites, signed before their run and used in their registered run, then reused for labelled diagnostics and final-run replication. The post-freeze tool-set diagnostic re-ran those same 65, so it is not a fresh test. The 40 saved answers (a failure-enriched sample from one run) and the 30 source checks are review items, not question sets. Five original held-out cases changed after the v3.2 freeze (HO-029 in v3.3; HO-027, HO-023 and HO-004 in v3.4; HO-022 in v3.5); the full version history is in the [evaluation report](docs/evaluation-report.md). Held-out v2 uses the same system, prompts and tools, with an AI-drafted gold that I approved unchanged. Each configuration was run once.

The live agent defaults to `r3`, `planner_v1`, `answer_v3`, base tools and `gpt-6-luna` (D-056, clarified D-061). The models tie on development mean; the primary costs about 60% as much. No run establishes an accuracy winner.

## Corpus versions

The system and the live site use the current document build (v3.1: 85 sources, 16,419 passages). Historical results use the builds labelled below. Current-corpus evidence includes D-055, D-056 and D-061 (FIN2, retrieval V31, served-chain and fresh threat runs). Earlier measurements: the 65 fresh questions were re-run on v3.1 (D-055) and are shown beside the registered v3 result, and the final consolidated run (D-056: development, registered held-out and fresh 65) ran on v3.1. v3 differs from v3.1 only in how 40 passages of the MTI article are labelled (D-052). Two earlier builds are kept only so older results can be reproduced: v1 is the first experiments and the original held-out test (results frozen), v2 is the extraction fixes tested alone (no measurable change), and v3 adds six untouched sources so the 65-question held-out set shares no evidence with development. Development accuracy 0.903 appears on both the earlier build (A3, v1) and an earlier build (X2, v3); held-out v2 0.754 is on v3 and 0.738 on the v3.1 re-run. Do not compare numbers across builds. The table gives the detail.

| Corpus | Contents | Used for |
|---|---|---|
| **v1** | 13,484 passages | All registered experiments: A1 to A5, held-out H-r3/H-hybrid, pre-guard threat suites |
| **v2** (`extract-0.2`) | 15,915 passages, 43,662 observations | Extraction-only X1 experiments and the earlier post-fix T-I06 run (`m7-ti06-postfix-20261031`) |
| **v3** (`extract-0.2`; v2 plus six labour-only sources, D-040) | 85 sources (36 datasets, 49 documents: 27 PDFs and 22 HTML), 52,020 observations (4,300 in the answer scope), 16,419 passages, 1,847 chunks, 276 build checks (269 pass, 7 warn) | The committed [manifest](data/manifests/manifest.json) and [quality report](artifacts/data-quality/quality-report.md), the local store, the X2 development regression check, the `m7-e2efix-20261031` threat run and held-out v2 |
| **v3.1, current build** (`extract-0.3`, D-052) | Same 85 sources, 52,020 observations, 16,419 passages and 1,847 chunks. The refined garbled-text rule relabels 40 passages of the MTI feature article (16 `garbled` to `ok`, 24 `garbled` to `table_unreliable`) and 4 `ok` to `table_unreliable`; quality flags 9,052 `ok`, 7,121 `table_unreliable`, 246 `garbled`; 10 chunk texts and 4 chunk ids change, 10 new vectors are needed. 276 build checks (269 pass, 7 warn). Snapshot: [`v3.1.json`](experiments/corpus-snapshots/v3.1.json), diff [`v3.1-diff.json`](experiments/corpus-snapshots/v3.1-diff.json) | The local store and the live site. Current-corpus evidence: D-055 fresh re-run, FIN/FIN2 full final sets, V31 retrieval, 65-case served-chain sample and 2 Nov fresh threats (D-061); older results retain their original build labels |

**Corpus v3 has four measured evaluations (31 Oct and 1 Nov 2026): the X2 development regression check, the `m7-e2efix-20261031` threat run, held-out v2 (the first evidence-disjoint-source evaluation, D-045; only partly independent: same system, prompts and tools, one run per arm) and the post-freeze tool-set diagnostic (X3 and the re-run of the 65 held-out v2 questions, D-048, not adopted).** The 65 questions were also re-run once on v3.1 (D-055). Frozen v1 and v2 results are retained unchanged. **Serving:** the live site serves corpus v3.1 (16,419 passages, 1,847 chunks); `/healthz` shows the commit and the corpus fingerprint (content fingerprint `242e2b284fbc` when last checked on 1 Nov 2026). Details: [data sheet](docs/data-sheet.md), [evaluation report](docs/evaluation-report.md).

## Experiments

Commands that call a model or the embeddings API cost money. The registered dev and held-out raw runs are not re-run by these commands, and re-running them is not needed to reproduce the published numbers. `labourlens agent-exp` refuses to overwrite an existing experiment id (`--force` overrides it and destroys frozen evidence). To exercise the pipeline, use a throwaway tag (paid API calls; needs `OPENAI_API_KEY`):

```bash
uv run labourlens retrieval-exp --split dev          # BM25, no model calls
uv run labourlens retrieval-exp2 --split dev --no-rerank
uv run labourlens agent-exp --split dev --tag SMOKE --pairs gpt-6-luna
uv run labourlens eval --exp agent-dev-SMOKE
```

To re-score a frozen run offline, pass the gold file it was scored on:

```bash
uv run labourlens eval --exp agent-dev-A3 --no-judge --gold experiments/gold/archive/gold-v3.5.jsonl
```

`eval` and `paired` refuse a gold file whose SHA-256 differs from the one recorded for the run unless `--allow-gold-mismatch` is given. Scoring still reads `experiments/gold/draft_cases.jsonl` (v3.6, `6169a9de…`); `gold_v3.7.jsonl` is the review-provenance file. In `draft_cases.jsonl` 3 records are `owner_manual`, 42 `agreed_with_ai_suggestion` and 223 `draft`; only `gold_v3.7.jsonl` carries 268 `owner_manual`. The published A1 to A5 and held-out metrics were scored on v3.5 (`aac4b405…`), archived at `experiments/gold/archive/gold-v3.5.jsonl`. The registered held-out comparison already ran once and must not be rerun to pick a winner.

Results and their history: [evaluation report](docs/evaluation-report.md). Prompts are in [`prompts/`](prompts/).

## MCP and audit

```bash
uv run python -m labourlens.mcp.server   # stdio MCP server
uv run labourlens mcp-demo               # recorded session of real calls in a fixed order; writes data/runs/mcp-demo-transcript.md (--out to choose the path)
uv run labourlens audit-report
```

The MCP server exposes read-only statistics, discovery, comparison, revision and provenance tools, plus source-catalogue resources. The [MCP transcript](docs/mcp-demo-transcript.md) records discovery, validated calls, failures, hostile output and a direct-integration comparison. The live web app routes the agent's `get_series` lookups through this server over stdio (D-053; `LABOURLENS_MCP=false` returns to direct calls), and each such call shows `transport: mcp` in the trace. Only `get_statistic` is used by the agent; the other eight tools are not given to it. `search_reports` and `calculate_change` stay in-process. Every frozen accuracy evaluation and the threat runs, except the 10 `mcp_server_failure` cases, called statistics directly, so their results do not describe the MCP route; D-058/D-061 now measures that served route on a 65-case sample with no observed accuracy loss, not a full-set or independent evaluation. Recorded 2 Nov protocol cost: median 36.1 ms per MCP call against 4.5 ms direct, plus 1.84 s at startup. The recorded MCP agent answer is a recorded single run in the demo script. Audit records hold bounded task states and outcomes, never model reasoning ([audit and logging](docs/audit-and-logging.md)).

## Repository structure

| Path | Purpose |
|---|---|
| `src/labourlens/` | Ingestion, retrieval, answers, agent, MCP, evaluation, security, audit, web serving |
| `tests/` | Data, retrieval, agent, MCP, audit and web tests ([`tests/README.md`](tests/README.md)) |
| `prompts/`, `specs/` | Versioned prompts; source catalogues, schemas and price assumptions |
| `data/manifests/`, `data/snapshots/` | Provenance and immutable statistical snapshots |
| `data/raw/`, `data/passages/`, `data/runs/` | Local only, gitignored (rights and sensitivity) |
| `experiments/`, `artifacts/` | Gold set, saved metrics, threat results, quality reports, figures |
| `web/`, `deploy/`, `scripts/`, `.github/` | Report and workbench front end; deployment |
| `docs/` | Documentation ([index](docs/README.md)); `docs/archive/` holds superseded planning drafts and the early progress log; `docs/process/` holds the initial plan and prompt |
| `Makefile`, `.pre-commit-config.yaml`, `.gitleaks.toml`, `.github/workflows/ci.yml` | One entry point and the checks CI runs |

## Documents

| Document | What it is |
|---|---|
| [Architecture](docs/architecture.md) | Data flow, agent graph, guardrails, trust boundaries; [rendered diagram](docs/img/architecture.svg) |
| [Data sheet](docs/data-sheet.md) | Sources, licences, schema, checks, EDA findings |
| [Evaluation report](docs/evaluation-report.md) | Design, results, error analysis, review rubric, limits |
| [System card](docs/system-card.md) | Intended use, risks, controls |
| [Threat model](docs/threat-model.md) | Attacks tested, controls, residual risk |
| [Innovation assessment](docs/innovation.md) | Forward plan (about two pages) |
| [Demo script](docs/demo-script.md) | 20-minute live demonstration plan |
| [Requirements matrix](docs/requirements-matrix.md) | Assessment requirement to evidence, with honest status |
| [Deployment](docs/deploy.md) | Droplet runbook and verified state |
| [Decisions](docs/decisions.md), [progress](docs/progress.md) | Dated decisions (57 entries, D-000 to D-056); current state and recent log |
| [Agent logs](docs/agent-logs.md) | How AI agents were used: contract, approval gates, controls, mistakes caught |
| [Reproduce](docs/reproduce.md), [fresh-clone check](docs/fresh-clone-check.md) | Commands to each artefact, what needs the private corpus or an API key, expected output |
| [Review records](docs/human-review/README.md) | Owner review and AI reviews, kept separate |
| [Security policy](SECURITY.md) | Secrets, untrusted text, rights |
| [MCP transcript](docs/mcp-demo-transcript.md) | Protocol demonstration |

Planning drafts in `docs/archive/planning/` record earlier proposals; they are not evidence that anything ran.

## Rights and responsible use

Statistical data comes from data.gov.sg datasets published by MOM and SingStat under the [Singapore Open Data Licence v1.0](https://developers.data.gov.sg/open-data-licence); keep attribution and non-endorsement notices. LabourLens is not endorsed by any agency. MOM PDFs carry restrictive copyright notices and HTML release rights are unresolved, so reports, extracted passages, raw answers and judge payloads stay local and are not in the repository, image or static report. The repository publishes provenance, identifiers, locators, links and short permitted quotations.

Treat user input, retrieved passages and MCP content as untrusted data. Do not submit confidential, personal or classified information. Inspect citations and definitions before using an answer in policy work.

## Main limitations

- Gold labels were AI-drafted first and the judge is an AI. The owner went through them in the review interface and signed off on every case, answer verdict and source check (four separate streams, 403 items in total: 268 gold questions, 65 held-out v2 questions, 40 saved system answers and 30 source checks; only the first two are questions). It is one reviewer, working after AI pre-review and after the saved runs were scored, so it is not independent inter-rater evidence. Gold v3.7 changes only provenance fields; the earlier saved evaluations are still scored on v3.5, v3.6 and the signed held-out v2 gold, and only the final FIN/FIN2 evaluations (D-056, D-061) were scored on v3.7 for development and registered held-out (generation ran on v3.6). The four D-047 change-clicks are recorded but not applied. The threat suite and the automatic judge checks are not human review. The second-family judge check (D-062) partly addresses same-provider judging on one saved FIN sample only; claim support remains judge-dependent, with kappa 0.436 on claim labels, three omitted items and a `gpt-5.6-luna` gain that the second judge did not reproduce.
- The original held-out set shares evidence with development; its gain over hybrid retrieval is not demonstrated. The separate held-out v2 set meets its pre-registered rule for the primary model on three cases, with no gain on the second model and a lower bound of 0.0 when one question group is removed; I would not call it a confirmed gain.
- Both arms of held-out v2 score about 0.71 to 0.75, and numerical comparisons about 0.21, mostly because the tools cannot do arithmetic on figures printed in reports. A tool set v2 that adds that arithmetic was built and tested (D-046). On dev it did not pass its pre-declared criteria and was **not adopted** (D-048); the large gain on the v2 questions is a post-freeze diagnostic on cases whose errors motivated the fix, so it is optimistic by construction. Adoption would need a fresh dev pass and a threat run under v2.
- The planted-figure guard is a closed grammar. T-I06 is not shown stable: the 31 Oct primary defended run passed 36/36, but fresh 2 Nov all four configurations score 35/36 under both scorers. V2 old-output rescoring is diagnostic, not new evidence or replacement of registered v1.
- The X2 regression check changed several factors at once; it does not isolate any one of them. Its rise in ungrounded-number cases mixes a wider check with possible behaviour change.
- The ingestion scanner originally missed five paraphrased probes; six patterns and regression coverage now catch those known examples, not all attacks. Citation matching shows a quote exists, not that it supports a claim.
- PDF tables can extract poorly; report-only figures are not deterministic calculation inputs.
- Dataset and report employment totals can differ in definition or vintage; the corpus does not explain every gap.
- A single-process prototype with local state, not a multi-user government system; provider-side spend cap unverified.

## Licence and attribution

The code and documents are all rights reserved and shared for review ([`LICENSE`](LICENSE)). Statistical data: contains information from data.gov.sg datasets of the Ministry of Manpower and the Singapore Department of Statistics, under the [Singapore Open Data Licence v1.0](https://developers.data.gov.sg/open-data-licence); not endorsed by the publishers. Three datasets are recorded as licence assumed, not verified (see [data sheet, section 9](docs/data-sheet.md#9-open-licence-items-and-what-the-rights-scan-covers)). MOM and MTI reports are the Ministries' copyright and are not in this repository. Fonts are SIL OFL 1.1 ([`web/static/fonts/LICENSES.md`](web/static/fonts/LICENSES.md)).
