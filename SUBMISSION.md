# LabourLens: where to start

An evidence-grounded research assistant for Singapore labour-market questions: official statistics (data.gov.sg) plus MOM reports, passage-level citations, deterministic arithmetic, abstention, one bounded LangGraph agent, a read-only MCP statistics server and an evaluation harness. Inside the loop the planner chooses among three tools: report search returns ranked passages, series lookup returns structured observations, and calculation uses deterministic code. In the live app only the statistics lookup goes over MCP; a variant with all three tools over MCP was built and measured, was slower with no accuracy gain, and is not live.

The deck has 28 main slides (42 with the appendix). Press X twice quickly for speaker notes; no notes button is shown. Short names and internal ids used in the documents: [`docs/glossary.md`](docs/glossary.md).

## Read first

1. [`README.md`](README.md): results with caveats, how to run, repository map.
2. [`docs/architecture.md`](docs/architecture.md): components and trust boundaries ([diagram](docs/img/architecture.svg)).
3. [`docs/evaluation-report.md`](docs/evaluation-report.md): design, baselines, results, error analysis, limits.
4. [`docs/agent-logs.md`](docs/agent-logs.md): how AI agents were used, what stayed human, the approval record, the mistakes caught.
5. [`docs/requirements-matrix.md`](docs/requirements-matrix.md): each assessment requirement mapped to evidence, with honest status. Others: [system card](docs/system-card.md), [data sheet](docs/data-sheet.md), [innovation assessment](docs/innovation.md), [demo script](docs/demo-script.md), [index](docs/README.md).

## Run it

```bash
make setup
make verify && uv run labourlens mcp-demo && uv run python scripts/final_mean.py
LABOURLENS_DEMO_ENABLED=false make serve
```

Fresh-clone run, with the observed output: [`docs/fresh-clone-check.md`](docs/fresh-clone-check.md). Commands for every artefact: [`docs/reproduce.md`](docs/reproduce.md).

**Packaging:** hand over by GitHub URL, a fresh clone or `git archive HEAD`, never zip or copy the working folder. Ignored secrets, private corpus and assessment material are present alongside the tracked submission.

## What a clone can and cannot reproduce

- **Can (no key, no private data, no cost):** offline tests, lint, relative docs-link checks, history secret scanning if gitleaks is installed, static report/deck, report rebuilding, frozen hash checks, the real MCP client demo using the committed statistical store, final two-run aggregation and paired comparisons from committed scores.
- **Cannot:** anything that reads MOM or MTI text (retrieval indexes, live answers about report content, the quote scan against source text). Those documents are not redistributed; the rights scan prints `NOT CHECKED` in a clone. Raw model outputs are not in git; scores and metrics are.
- **Needs a key and spends money:** live answers, new experiments, the threat suite.

## Live demonstration

<https://labourlens.navig.me>: the report and deck are open. The research workbench needs an access code, which is sent separately and is not in this repository. Live answers make paid model calls; the application enforces a daily budget, but a provider-side spend cap has not been verified.

## Limitations

1. **Reference answers.** Gold labels were drafted by AI. One person (me) reviewed them after the saved runs were scored: not independent, not blind to model output. The latest gold version changes no label; only the two runs of the final evaluation were scored on it (with `--allow-gold-mismatch`, because generation ran on the previous version).
2. **The judge is an AI.** The attack suite and automatic checks are not human review. A second-family AI check on one saved sample (117 valid pairs, three omitted items, claim-label kappa 0.436) partly addresses same-provider judging, but claim support remains judge-dependent and the `gpt-5.6-luna` support gain was not reproduced.
3. **The original 31 test questions share evidence with development;** the gain of filter then rerank over hybrid search is not demonstrated there. Gold labels for five of its cases changed after the freeze; all versions are kept.
4. **Headline (final evaluation, two runs averaged, build v3.1).** On the 237 development questions filter then rerank scores 0.897 against 0.827 for hybrid search with the main model and 0.897 against 0.844 with the second (+7.0 [3.6, 10.6] and +5.3 [1.9, 8.9] points, 95% case intervals). No gain is demonstrated on the original 31 (0.839 against 0.806 and 0.823) or the 65 fresh questions (0.715 against 0.746 and 0.731 against 0.738). An earlier rule met on three cases stays labelled history, not confirmation. Both single runs are shown in the README.
5. **Numerical comparisons score low** (0.214 on the fresh questions) because the tools cannot do arithmetic on figures printed in reports; the fix was tested and not adopted.
6. **Two runs are not a variance estimate.** The final settings ran twice; other experiments ran once per configuration unless labelled. Intervals resample questions, not runs.
7. **The planted-false-figure attack is not shown stable:** 36/36 on the first run on the fixed system, 35/36 in all four configurations in the fresh 2 Nov rerun under both scorers. Rescoring old outputs is post-hoc only. The ingestion scanner missed five paraphrase probes; six patterns and regression tests now cover those known probes, not all attacks.
8. **Rights.** Three datasets are under an assumed, unverified licence; 23 documents have unresolved rights; MOM and MTI text is local-only.
9. **PDF table extraction is unreliable;** numbers come from the datasets, text supplies explanation.
10. **The served chain** is measured on a 65-case sample (51 reused development questions plus 14 hand-written probes): 90.8% for both models, no observed MCP-versus-direct accuracy loss with web steps on. It is one run, not independent and not a non-inferiority proof; one main-model context probe failed. The full final evaluation omits the web steps and MCP. Open items, including the unverified provider spend cap and deferred review findings, are in [`docs/progress.md`](docs/progress.md) and [`docs/data-sheet.md`](docs/data-sheet.md) section 9.
11. **Same-set retrieval check** (build v3.1, 128 development report questions, hit@8): keyword .477 [.391, .562], embeddings .367 [.289, .453], hybrid .539 [.453, .625]. Keyword alone beats embeddings; hybrid over keyword is not demonstrated (+.062 [-.023, .148]); hybrid over embeddings is +.172 [.102, .242]. The early 24-question hit@10 result stays labelled history. Retrieval is the agent's `search_reports` tool inside its loop, not an input before it.
