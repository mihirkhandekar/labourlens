# Bounded agent versus a fixed pipeline

**PROPOSAL, pre-registered 3 Nov 2026 before any fixed-arm generation.** No result is claimed here. New id: `agent-dev-FIXED1-r3`. Frozen agent references: `agent-dev-FIN-r3` and `agent-dev-FIN2-r3`, primary model `gpt-6-luna` only. Never overwrite either reference or rerun to select a favourable result.

## Design

The existing answer-only pipeline uses a different evidence context and lacks the agent's cross-check path. Instead, reuse the existing graph's evidence execution, answer writer, schema, cross-check, validation, one repair, output guard and result format. Change only evidence control flow with `--control-flow fixed`:

1. The same `planner_v1` prompt and catalogue, model and 1,500-token limit are used once to extract at most one statistics lookup. Its schema allows only `get_series`, not general tool selection. The malformed-JSON retry remains identical to the agent. This is extraction, not an evidence-conditioned loop.
2. Always search the unchanged question once using R3, top eight chunks, then execute the extracted lookup if present. No query rewriting or second research round.
3. Assess evidence and write the answer with unchanged `answer_v3`, `gpt-6-luna`, 6,000-token answer limit and default generation settings. Keep the same validation repair, not an extra research step.

This is a non-adaptive LLM extraction pipeline, not a non-LLM baseline. A hand-written source/period parser would add many untested domain rules; the existing catalogue-constrained extraction is the smaller defensible baseline. The raw reference agent has no served-chain scope triage, conversation rewrite, web middleware or MCP transport; add none here. Statistics remain direct.

**Confounds and limits.** This compares whole evidence-control policies, not LangGraph as a library. Fixed evidence order, mandatory report search, maximum one lookup, inability to query again after errors and absence of deterministic calculation records are consequences of the fixed policy. The agent can choose arithmetic and multiple lookups; a calculation-correct penalty is expected mechanically and must be reported, not mistaken for better prose reasoning. The extraction schema is narrower but the prompt and its catalogue are unchanged; this prompt/schema mismatch may disadvantage the fixed arm and must be disclosed. Retrieval internals, evidence tools, answer prompt, model, validators and sampling remain the same. Historical code/time/provider variation remains a confound; frozen reference provenance is checked, not rewritten. A new result on development questions is exploratory evidence, not generalisation.

## Hypotheses and criteria

H0: neither control policy has a demonstrated behaviour advantage. H1: behaviour differs in either direction. No direction is assumed. Report the fixed-minus-agent paired difference against FIN and FIN2 separately, 95% case and evidence-component bootstrap intervals using existing paired code, exact two-sided McNemar p, and family tables. Primary descriptive comparison uses the agent's per-case two-run mean (0, 0.5, 1); bootstrap those paired differences, never coerce the mean to boolean. McNemar is meaningful only for each binary single-run comparison, not the mean.

Call a directional development advantage demonstrated only if both single-run comparisons and the mean have the same sign, both single-run case and component 95% intervals exclude zero in that direction, and neither single-run exact McNemar p exceeds .05. A proposed winner must add no false-answer cases relative to either reference. Otherwise say inconclusive, not equivalent. These criteria are stricter than the earlier retrieval rule. All family slices are descriptive. Report calculation correctness, key-number recall, citation and judged content metrics from the standard scorer; do not call status matching full answer correctness.

Report the always-answer floor from gold (answer and ignore-injection-and-answer labels), false answers, over-abstention, operational failures, per-family accuracy, median/p95 latency, recorded per-question token-cost estimate and judge cost separately. Fixed is one run: comparing it to both references and their mean does not estimate its own run-to-run variance. Earlier dev arms flip 11 to 18 of 237 cases between runs; report the actual primary R3 flips too. One new run cannot establish stability.

**Report as is:** preserve every case including failures, null scores and negative results; no favourable-run selection, no edits to gold, no tuning or second attempt based on the results. The 65 fresh questions are not run in this experiment: they are already reused and would add paid generation and judging without resolving single-run noise.

## Identity and reproducibility

Gold: `experiments/gold/gold_v3.7.jsonl`, development split, 237 case ids. Both frozen references record gold SHA256 `af3ad02690ed1dabb69e2be7f7bb984f707f1352b95c8bd693d0fb51e9410d8f`. Before comparison, require exact case-set equality, gold hash, agent config and prompt hashes, same `gpt-6.1-terra` judge and judge prompt, and corpus version. The offline comparison refuses mismatches. Scoring uses the current standard `eval` harness, not a new scorer. Record the current code provenance; historical source code cannot be assumed identical merely because prompts match.

**VERIFIED FACT, preparation only.** Frozen scoring commits are FIN `9f979a5d94af54e8a4b57707bac6e8b20b78fd1d` and FIN2 `41ec2da10433dfa633ac0c535e16d66560612fd8`. Source comparison found no scoring-function change: the harness difference adds sampling metadata; subsequent harness changes add overwrite protection. The answer scorer is unchanged. This verifies scorer source, not identical historical provider behaviour. FIN's generation gold hash differs from scoring gold because later review provenance was added; never claim generation and scoring gold bytes are identical. The preflight checks exact question text against both raw runs, current prompt hashes, scoring gold hash and report corpus identity before a paid call. The comparison repeats those checks after scoring.

**VERIFIED FACT, frozen inputs.** Offline inspection found 237 raw and 237 scored cases in each reference, with identical case ids and exact question text to the development split of gold v3.7. Both scoring gold hashes match; both raw runs have the cross-check enabled. The primary R3 references differ on 13 behaviour verdicts. This is input verification, not a fixed-pipeline result.

## Exact owner commands

No paid calls have been made by the preparation worker. The owner runs these once after reviewing this registration. Use the corpus v3.1 assets used by FIN; do not rebuild them on a different corpus.

```bash
LABOURLENS_GUARDS=on LABOURLENS_CROSSCHECK=on uv run labourlens agent-exp --split dev --gold experiments/gold/gold_v3.7.jsonl --pairs gpt-6-luna --retrieval r3 --planner-prompt planner_v1 --answer-prompt answer_v3 --tool-set base --control-flow fixed --tag FIXED1-r3
uv run labourlens eval --exp agent-dev-FIXED1-r3 --split dev --gold experiments/gold/gold_v3.7.jsonl --labels gpt-6-luna
uv run labourlens fixed-compare --gold experiments/gold/gold_v3.7.jsonl --candidate agent-dev-FIXED1-r3 --out experiments/eval/agent-vs-fixed-pipeline.json
```

The comparison writes only the new report; existing output is refused. No `--force`, gold-mismatch bypass or frozen-arm rescoring is allowed. The JSON includes both paired comparisons, mean comparison, family table, floor, cost and latency; standard eval produces the answer-content report. Copy results and limitations into the evaluation report only after they exist.

## Cost estimate, not a measured bill

At the supplied `gpt-6-luna` rates of $0.10 per million input tokens and $0.50 per million output tokens, assumed totals of 15,000 input and 3,000 output tokens per question (extraction, reranking, answer and occasional repair) give $0.003 per question, about $0.711 for 237. This is an illustrative estimate, not a cap or a measurement. Output limits and retries can raise it; embeddings and the separate `gpt-6.1-terra` semantic judge add costs. Report the saved usage-based generation cost and judge cost separately after the run; provider billing may include failed requests without recorded usage.

## Offline verification

```bash
uv run pytest tests/retrieval/test_agent.py tests/evaluation/test_fixed_comparison.py
uv run labourlens rights-scan
make docs-check
```
