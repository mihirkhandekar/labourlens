# Served-chain evaluation pre-declaration

**PROPOSAL / analysis rules, 2 November 2026.** Written before the harness code and before any paid run. D-016 applies: new ids only, no overwrite, preserve frozen FIN results. No measurement is reported here.

## System and hypotheses

The actual web order is **small-talk fast path, contextualise, LLM scope triage, agent**. Small-talk stops immediately; otherwise contextualise uses no history for single-turn gold, but its relative-date and layoff rewrite gate remains active. Follow-up probes supply their explicit fixture history. This order intentionally mirrors the app, rather than changing it to contextualise first. Both entry points import the same runner and MCP shared-state factory. MCP uses the existing handshake, allow-list, timeout and bounded reconnect/retry policy. The base agent retains its 80 second deadline. Triage and rewrite use the served primary model even when the agent pair changes.

H1: on the identical selected gold cases, served behaviour accuracy differs from the saved agent-exp FIN r3 accuracy by no more than 0.03 in absolute proportion, separately for each model. Select FIN rows by the committed sample ids, not the full development denominator. FIN is not rerun or modified. Missing matching FIN rows make this hypothesis unevaluable.

H2: MCP and direct statistics routes return identical observation ids, periods, units and numerical values for identical get_series arguments. Compare tool-call argument signatures and the resulting observation evidence records. Only matched signatures are eligible. No shared calls means unevaluable, not a pass. Different LLM decisions are not transport parity failures. The requested direct/web-off run changes two factors: it is a descriptive baseline, not an isolated causal test of MCP. A strict parity conclusion requires replay of identical calls (the existing MCP parity tests or an additional matched-call audit), not equal aggregate accuracy.

## Sample, fixed before results

The mixed sample has **65 cases total: 51 existing development gold cases plus 14 new hand-written probes**. Select 51 from the 237 development cases, stratified proportionally by gold family using largest-remainder allocation, family-name ties, and Python Random seed 20261102. Within each family sort ids, then sample; sort the final ids. Require all families represented when their proportional allocation permits. Commit the resulting gold-only and mixed fixtures under experiments/served/. Gold labels remain unchanged. The gold-only fixture is used for FIN comparisons; probes are never described as gold or independent held-out evidence.

The fixed probes comprise 8 off-topic/small-talk messages and 6 follow-up/relative-date messages in experiments/served/probes.jsonl. Each carries provenance, expected behaviour and explicit context where needed. Relative dates use the actual Singapore date used by the web app, saved in run provenance. The fixture expectations are anchored to 2 November 2026; reject another date for this registered mixed sample instead of silently changing its meaning. Future runs need a new fixture/registration. Follow-up expectations test behaviour, not a new source-backed numerical gold answer. No case replacement after results.

## Metrics and pass/fail

Use agent-exp score_run and aggregate unchanged for behaviour accuracy, false-answer rate, over-abstention, calculation correctness, citation/number checks and operational failures. Report gold and probes separately, with the mixed total clearly labelled. False-diversion rate has answerable gold cases as denominator and counts a small-talk or triage stop before the agent; failed-open triage is not diversion. Require zero gold false diversions. Report rewrite/triage failures separately so an outage cannot masquerade as a successful gate.

Record per-case and mean per-step wall latency and estimated cost for small-talk, contextualise, triage and agent; total latency p50 (median) and p95 (nearest rank). Total includes all executed steps but excludes one-off shared-state/MCP startup, whose duration is reported separately. Record MCP attempt and error counts from the backend's bounded call log, including failed attempts before a successful retry. Cost uses saved provider usage and the existing price table, not a provider bill. Report missing usage as an explicit limitation of failed provider calls.

H1 passes only with absolute difference <= 0.03 for both models and zero false diversions. H2 passes only with at least one matched successful statistics call and exact equality on all matched numerical records; any mismatch fails. All 8 diversion probes must avoid the agent; all 6 context probes must reach the agent, with no rewrite/triage operational failure, and meet their fixture behaviour. Report each failing id. No clean pass if required data or calls are absent. Report failures, not just aggregate improvements.

## Limits and controls

One run per model/configuration, reused development evidence, hand-written probes, correlated model family for generation, triage and judging. Not independent evaluation, not human review, not a statistical non-inferiority demonstration, not a production reliability guarantee. Confidence intervals are descriptive case resampling only. Keep the route and enabled steps in provenance. Scoring with `eval` can add AI-judge measures but does not change those limitations. Paired mixed comparison describes the bundled served/direct difference; use the gold-only subset for H1 against FIN. No paid command has been executed by this implementation task.

## Parent execution commands

These commands spend money when provider keys are present. Commit the implementation and fixtures first so recorded git provenance names the implementation. Do not reuse these tags if an attempt has already reserved them.

```sh
uv run labourlens served-exp --split dev --gold experiments/served/mixed-sample.jsonl --pairs gpt-6-luna gpt-5.6-luna --tag S65-mcp-on --retrieval r3 --route mcp --web-steps on
uv run labourlens served-exp --split dev --gold experiments/served/mixed-sample.jsonl --pairs gpt-6-luna gpt-5.6-luna --tag S65-direct-off --retrieval r3 --route direct --web-steps off
uv run labourlens eval --exp served-dev-S65-mcp-on --split dev --gold experiments/served/mixed-sample.jsonl --labels gpt-6-luna gpt-5.6-luna
uv run labourlens eval --exp served-dev-S65-direct-off --split dev --gold experiments/served/mixed-sample.jsonl --labels gpt-6-luna gpt-5.6-luna
uv run labourlens paired --gold experiments/served/mixed-sample.jsonl --candidate served-dev-S65-mcp-on --baseline served-dev-S65-direct-off --models gpt-6-luna gpt-5.6-luna --out experiments/served/paired-S65.json
```

The paired rule in the existing command concerns demonstrated retrieval gain, not our H1 non-degradation rule. Treat its differences and intervals descriptively here, not its adoption verdict. Its mixed set includes new probes, and the two arms differ in both transport and front steps. The web-off control has no conversation rewrite and is expected to struggle with those probes. `--limit N` selects the first N ids in fixture order; `--case-ids ID ...` filters before that limit. Neither is a replacement for the registered 65-case sample.

The deterministic H1 comparison below reads the existing FIN case scores and selects exactly the 51 gold ids from the new run. It never rescales full-set FIN accuracy to the mixed denominator or rewrites FIN. The H2 comparison reads only statistics rows and matches by case plus exact arguments; different calls are reported unmatched, not assumed equal. Both commands are offline:

```sh
uv run python -c 'import json; from pathlib import Path; from labourlens.evaluation.served_exp import compare_fin; print(json.dumps({m: compare_fin(Path(f"experiments/runs/served-dev-S65-mcp-on/{m}.scores.jsonl"), Path(f"experiments/eval/agent-dev-FIN-r3/{m}.cases.jsonl")) for m in ("gpt-6-luna", "gpt-5.6-luna")}, indent=2))'
uv run python -c 'import json; from pathlib import Path; from labourlens.evaluation.served_exp import compare_statistics; print(json.dumps({m: compare_statistics(Path(f"data/runs/served-dev-S65-mcp-on/{m}.jsonl"), Path(f"data/runs/served-dev-S65-direct-off/{m}.jsonl")) for m in ("gpt-6-luna", "gpt-5.6-luna")}, indent=2))'
```

The committed gold allocation is factual lookup 15, numerical comparison 7, cross-source synthesis 8, revision conflict 4, ambiguity/insufficient/causal 9 and adversarial 8. Gold-only labels are duplicated without edits in `gold-sample.jsonl` to make the denominator inspectable. Both raw models include a fixed original `question` and arm `config` for compatibility with the existing scorer; `effective_question`, `executed_config`, `interpreted_as` and step metadata preserve what actually ran. No server budget/authentication or rights-projection HTTP layer is evaluated: this evaluates the served research chain, not the rendered browser response.
