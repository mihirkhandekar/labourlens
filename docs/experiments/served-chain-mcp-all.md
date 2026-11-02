# Served chain with all three agent tools over MCP: pre-declaration

**PROPOSAL / analysis rules, 2 November 2026.** Written after the offline implementation and offline tests, before any paid run of this arm. D-016 applies: new ids only, no overwrite, frozen results untouched. This file reports no result of the new arm. The decision it tests is [D-066](../decisions.md); the harness it extends is described in the [served-chain pre-declaration](served-chain-eval.md).

## Question

Does sending all three agent tools over MCP instead of only `get_series` change accuracy, latency, cost or the number of tool errors on the same 65 cases, for both models, in one run each?

The only intended difference between the arms is **tool transport**:

| Arm | `search_reports` | `get_series` | `calculate_change` | Existing result? |
|---|---|---|---|---|
| `served-dev-S65-direct-on` | in process | in process | in process | yes |
| `served-dev-S65-mcp-on` | in process | MCP | in process | yes |
| `served-dev-S65-mcpall` (new) | MCP | MCP | MCP | not run |

The new id holds one file set per model (`gpt-6-luna`, `gpt-5.6-luna`), as the existing arms do. Same 65 cases (51 stratified development gold cases plus 14 hand-written probes, `experiments/served/mixed-sample.jsonl`), same prompts, same web steps (small-talk, contextualise, triage, agent), retrieval `r3`, base tool set, planner and answer models, 80 second run deadline. The harness refuses to run on a Singapore date other than 2 November 2026 because the probes are anchored to it; a different day needs a new registered fixture, not a quiet change here.

## What is routed, and what is not

- `search_reports`: the app embeds the query itself (it holds the API key; the server never does) and sends the vector, the original question and the retrieval mode. The server filters by period and release, fuses BM25 and dense rankings and returns the 30-chunk rerank pool with its passages. **Reranking stays in the app** because it calls a model. Everything after the rerank is the same code as before.
- `calculate_change` (and `calculate_from_text_values`, which the base tool set does not offer): the app sends observation ids or passage ids, never numbers; the server recomputes from its own table or passage text and returns the result. The checks and arithmetic are one shared function used by both routes.
- Failures are typed and never fall back to the in-process tools: a timeout or error from the server is an operational failure in the trace, not missing evidence.

## Known differences besides transport (declared before the run)

1. **Text normalisation in the rerank prompt.** The MCP client sanitises every string it receives (Unicode NFKC). The in-process route passes raw chunk text to the reranker. Measured offline on the current corpus: **57 of 1,847 chunks (3.1%)** and 313 of 16,419 passages change under that normalisation. Evidence text shown to the answer step is sanitised on both routes, so only the rerank prompt differs.
2. **Quarantine of instruction-like passages.** The client withholds a passage or chunk the scanner flags; the in-process route keeps it, flagged. Measured offline: **0 of 1,847 chunks and 0 of 16,419 passages** are flagged by the current scanner, so no difference is expected on this corpus.
3. **Model non-determinism.** Provider-default sampling means a repeat of the same arm can differ. The two existing arms show it: on `gpt-5.6-luna` behaviour accuracy was 0.908 (`mcp-on`) and 0.877 (`direct-on`); on `gpt-6-luna` both were 0.908 with one case better and one worse. One run cannot separate transport from this noise.

## Metrics

Unchanged from the [served-chain pre-declaration](served-chain-eval.md): behaviour accuracy (all, gold, probes), false-answer rate, over-abstention, calculation correctness, operational failures, tool-error rate, false diversions, probe failures, per-step latency, total latency p50 and p95 (nearest rank, excluding one-off start-up), cost per case from saved provider usage and `specs/prices.yaml`. Added for this arm:

- MCP attempts and errors by tool, from the raw rows' `served.tool_calls` (search and calculation calls) and `statistics_calls`, with the error kind of each failed attempt.
- Per-call time of `search_reports` from the trace (`execute_tool` events, `seconds`), compared across the three arms. Descriptive; not a pass criterion.
- Start-up time, reported separately (`shared_startup_seconds` in provenance): the server now loads the report corpus.
- Evidence overlap: per case, the share of evidence ids shared with the `mcp-on` arm. Descriptive only. Parity of the tools themselves is established offline by `tests/mcp/test_agent_tools.py`, not by this run.

## Paired comparisons

Both comparisons use the existing `labourlens paired` tooling on the 65 mixed cases, both models, candidate `served-dev-S65-mcpall`: against `served-dev-S65-mcp-on` (the isolated change: two more tools over MCP) and against `served-dev-S65-direct-on` (the whole MCP route). Read the paired difference, the case and component bootstrap intervals (two-sided 90%, seed and resamples as in `paired.py`), the better/worse counts and the exact McNemar p. The rule that decides whether *retrieval* gain is demonstrated does not apply to this question; its verdict field is ignored. Intervals are descriptive.

## What would count as a problem

Fixed now, per model, against `served-dev-S65-mcp-on`:

| Check | Problem if |
|---|---|
| Accuracy | behaviour accuracy is lower by 3 or more cases (0.046 or more; below 0.862) |
| False answers | false-answer count is higher by 2 or more cases |
| Operational failures | any (the `mcp-on` arm had 0 for both models) |
| Tool errors | `mcp_error_count` is higher by more than 3, or any attempt of `search_reports`, `calculate_change` or `get_statistic` fails with a transport kind (`timeout`, `unavailable`, `malformed`, `oversized`, `quarantined`) |
| Latency | total p95 is more than 25% above the `mcp-on` value: above **43.3 s** for `gpt-6-luna` (34.67 s) and above **40.1 s** for `gpt-5.6-luna` (32.04 s) |
| Statistics parity | `compare_statistics` against `mcp-on` returns `fail` (matched `get_statistic` calls with different rows) |
| Diversions | any false diversion of an answerable gold case |

A drop of one or two cases is inside the spread already seen between the existing arms; it is reported and not called a problem. Any problem is reported with its case ids. There is no clean-pass wording if a check could not be evaluated.

## Limits

One run per model and arm; development evidence reused; 14 hand-written probes; generator, triage and judge are the same provider family (the judge is `gpt-6.1-terra`, distinct from the generators); the judge is an AI. This is not independent evaluation, not human review, not a statistical non-inferiority demonstration and not a production reliability or capacity claim. It does not evaluate the browser layer, admission control or budget. The offline memory and latency figures in D-066 were measured on one macOS machine, not in the deployment container.

## Offline checks that exist before the run

`tests/mcp/test_agent_tools.py` compares each tool field by field between the in-process route and the MCP route (offline fixture corpus, committed observations table, fake chat client), including every refusal path, a stdio run of a real server process, a trace test that all three tools carry `transport: mcp`, timeout, crash and error tests, and two `corpus`-marked tests on the real index. `tests/evaluation/test_served_mcp_all.py` covers the dry run and provenance. These test equivalence of the tools, not the accuracy of the chain.

## Cost estimate

From `specs/prices.yaml` (retrieved 2026-10-30) and the measured cost per case of the `mcp-on` arm (`gpt-6-luna` $0.00268, `gpt-5.6-luna` $0.00385): generation about **$0.42** for 65 cases and both models (`served-exp --dry-run` prints the same figure). Scoring the new arm with `eval` (judge `gpt-6.1-terra`) cost $0.118 for the `mcp-on` arm, so about **$0.12** more. Query embeddings are cached for repeated queries and cost a fraction of a cent otherwise. Expect roughly **$0.55** in total; provider usage, not this estimate, is the record.

## Parent execution commands

These spend money when provider keys are present. Commit first so the recorded git head names the implementation. Do not reuse the tag if an attempt has reserved it.

```sh
uv run labourlens served-exp --split dev --gold experiments/served/mixed-sample.jsonl --pairs gpt-6-luna gpt-5.6-luna --tag S65-mcpall --retrieval r3 --route mcp-all --web-steps on --dry-run
uv run labourlens served-exp --split dev --gold experiments/served/mixed-sample.jsonl --pairs gpt-6-luna gpt-5.6-luna --tag S65-mcpall --retrieval r3 --route mcp-all --web-steps on
uv run labourlens eval --exp served-dev-S65-mcpall --split dev --gold experiments/served/mixed-sample.jsonl --labels gpt-6-luna gpt-5.6-luna
uv run labourlens paired --gold experiments/served/mixed-sample.jsonl --candidate served-dev-S65-mcpall --baseline served-dev-S65-mcp-on --models gpt-6-luna gpt-5.6-luna --out experiments/served/paired-S65-mcpall-vs-mcp-on.json
uv run labourlens paired --gold experiments/served/mixed-sample.jsonl --candidate served-dev-S65-mcpall --baseline served-dev-S65-direct-on --models gpt-6-luna gpt-5.6-luna --out experiments/served/paired-S65-mcpall-vs-direct-on.json
uv run python -c 'import json; from pathlib import Path; from labourlens.evaluation.served_exp import compare_statistics; print(json.dumps({m: compare_statistics(Path(f"data/runs/served-dev-S65-mcpall/{m}.jsonl"), Path(f"data/runs/served-dev-S65-mcp-on/{m}.jsonl")) for m in ("gpt-6-luna", "gpt-5.6-luna")}, indent=2))'
```

The first command is free: it validates the fixture and the id, prints the plan and the estimate, and creates nothing. The run needs the local corpus and the cached vectors (the server fails to start rather than embedding chunks) and an `OPENAI_API_KEY` in the parent environment only; the key is never passed to the server process.

## Results

None yet.

## Deviations and result (recorded 2 November 2026, after the run)

The pre-declaration above is unchanged. This section records what happened.

**Deviation: one model only.** The arm was run for `gpt-6-luna` on all 65 cases. The run for `gpt-5.6-luna` was stopped at 17 of 65 cases at the owner's request and was not rerun, so there is no result for the second model on this arm and the pre-declared two-model comparison was not completed.

**Result (`gpt-6-luna`, 65 served questions, one run).** Sources: `experiments/runs/served-dev-S65-mcpall/gpt-6-luna.metrics.json` (generation metrics in [runs](../../experiments/runs/)); `experiments/served/paired-S65-mcpall-vs-mcp-on.json` (paired against statistics-only MCP) and `experiments/served/paired-S65-mcpall-vs-direct-on.json` (paired against direct), in the [served-chain evidence directory](../../experiments/served/).

| Measure | All three tools over MCP | Statistics lookup only over MCP | Direct (in process) |
|---|---|---|---|
| Behaviour accuracy | 0.877 (57/65) | 0.908 (59/65) | 0.908 (59/65) |
| Paired difference of the all-three route | | -0.031; 1 case better, 3 worse, p = 0.63 | -0.031; 0 better, 2 worse, p = 0.50 |
| False answers | 3 | 3 | 3 |
| Operational failures | 0 | | |
| Median latency | 14.3 s | 12.4 s | 10.8 s |
| 95th percentile latency | 51.4 s | 34.7 s | 32.8 s |
| Cost per question | about $0.0026 | | |

The 95th percentile is above the limit set in advance (43.3 s). The accuracy difference is not demonstrated: the all-three route has two fewer correct cases out of 65 than either comparator in one run, with exact p values of 0.50 and 0.63. The route is slower, with no accuracy gain.

**Decision.** The all-three route is kept as a built and measured option (`LABOURLENS_TOOL_TRANSPORT=mcp_all`) but is not the live default. The live app sends only the statistics lookup over MCP (`mcp_stats`), as before. See the note under the all-tools-over-MCP entry in the [decision log](../decisions.md).
