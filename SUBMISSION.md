# LabourLens: where to start

An evidence-grounded research assistant for Singapore labour-market questions: official statistics (data.gov.sg) plus MOM reports, passage-level citations, deterministic arithmetic, abstention, one bounded LangGraph agent, a read-only MCP statistics server and an evaluation harness. Inside the loop the planner chooses among three tools: report search returns ranked chunks, series lookup returns structured observations, and calculation uses deterministic code. In the live app only the statistics lookup goes through MCP.
The deck has 28 main slides, 42 total including the appendix index and references A to M. Limitations and next steps remain in Summary and the evaluation/attack material; current-build facts are on slide 11. Press X twice quickly for speaker notes; no notes button is shown.

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

1. Gold labels were drafted by AI. One person reviewed them after the saved runs were scored: not independent, not blind to model output. Gold v3.7 changes no label. The earlier saved evaluations were not rescored on it; only the final FIN/FIN2 evaluations (D-056, D-061) were scored on v3.7 for the development and registered held-out sets, with `--allow-gold-mismatch` because generation ran on v3.6.
2. The AI judge is an AI; the threat suite and automatic checks are not human review. A second-family check on one saved FIN sample (D-062: 117 valid pairs, three omitted items, claim-label kappa 0.436) partly addresses same-provider judging, but claim support remains judge-dependent and the `gpt-5.6-luna` support gain was not reproduced.
3. The original held-out set shares evidence with development; its gain over hybrid retrieval is not demonstrated. Gold labels for five of its cases changed after the freeze; all versions are kept.
4. Final-system headline (D-061, corpus v3.1) is the mean of two runs per arm: development r3/hybrid 0.897/0.827 and 0.897/0.844, +7.0 [3.6, 10.6] / +5.3 [1.9, 8.9] points (95% case intervals). No gain is demonstrated on original test 31 (0.839/0.806 and 0.839/0.823) or fresh 65 (0.715/0.746 and 0.731/0.738). The earlier rule met on three cases remains labelled history, not confirmation. Both single runs remain visible in the README.
5. Numerical comparisons score low (0.214 on held-out v2) because tools cannot do arithmetic on figures printed in reports; the fix was tested and not adopted.
6. Final arms ran twice (FIN and FIN2); two runs are not a variance estimate. Other experiments ran once per configuration unless labelled. Intervals resample cases, not runs.
7. T-I06 is not shown stable: 31 Oct primary defended 36/36, fresh 2 Nov all four configurations 35/36 under both scorers. Old-output v2 rescoring is post-hoc only. The scanner formerly missed five paraphrase probes; six patterns and regression coverage now address those known probes, not all attacks.
8. Three datasets are under an assumed, unverified licence; 23 documents have unresolved rights; MOM and MTI text is local-only.
9. Table extraction from PDFs is unreliable; numbers come from the datasets, text supplies explanation.
10. The served chain is now measured on a 65-case sample (51 reused dev gold plus 14 hand-written probes): 90.8% both models, no observed MCP/direct accuracy loss with web steps on. It is one run, not independent or a non-inferiority proof; one primary context probe failed. Full-set final evaluation still omits web steps and MCP. Open items in [`docs/progress.md`](docs/progress.md) and [`docs/data-sheet.md`](docs/data-sheet.md) section 9 include the unverified provider spend cap and deferred review findings.
11. Same-set retrieval check (D-063, corpus v3.1, 128 development report questions): hit@8 BM25 .477 [.391, .562], dense .367 [.289, .453], hybrid .539 [.453, .625]. BM25 alone beats dense. Hybrid over BM25 is not demonstrated (+.062 [-.023, .148]); hybrid over dense is +.172 [.102, .242]. The early 24-question, hit@10 result remains labelled history. Retrieval is the agent's `search_reports` tool inside its loop, not a pre-agent input; only the live `get_series` statistics tool uses MCP.
