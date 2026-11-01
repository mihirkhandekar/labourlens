# Held-out v2: result, interpretation and error analysis

**MEASURED RESULT (31 Oct 2026).** One run per arm on the signed held-out v2 set, corpus v3, code at `89c51d7`. Registered comparison: retrieval `r3` versus `hybrid`, `planner_v1`, `answer_v3`, cross-check on for both arms, planner and answer by the same model. Sources: `experiments/heldout-v2/paired.json`, `experiments/eval/agent-heldout-V2-{r3,hybrid}/` (metrics, cases, REPORT), signed block in `experiments/heldout-v2/FREEZE.md` (owner export `a428db90…`, gold `experiments/gold/heldout_v2_v1.jsonl`, SHA-256 `e3d16597d542d33d106b4e9291aa3b92ca5fcdf19aa4d3c2b3319c0543efa542`). Provenance: the signed freeze was committed first (`89c51d7`, 21:20 on 31 Oct 2026), the raw run records carry `generation_provenance` with that HEAD and the gold hash above, and the results were committed afterwards (`6f80ec9`, 22:00); both arms ran at the same HEAD. Raw runs are private (`data/runs/agent-heldout-V2-*`); this report reproduces ids, counts and paraphrased reasons only.

**Verdict.** The pre-registered rule is **met for the primary model**. The effect is **three cases**. I would not call it a confirmed gain. The second model shows none. Absolute accuracy is low in both arms, and most of the shortfall comes from a tool coverage gap that retrieval cannot fix.

## What the pre-registered rule says

D-042 (`docs/decisions.md`, `FREEZE.md`) decided in advance that the R3 gain is demonstrated only if, for the primary model `gpt-6-luna`, all of the following hold:

1. Both arms scored exactly the same 65 cases.
2. The paired behaviour-accuracy difference (R3 minus hybrid) has a one-sided 95% lower bound above zero under the case bootstrap (lower end of the two-sided 90% percentile interval, 20,000 resamples, seed 20261031).
3. The same lower bound is above zero when resampling evidence components (cases sharing any acceptable evidence id move together).
4. At least 20 evidence-carrying components exist (the set has 22).
5. R3 adds no false-answer case relative to hybrid.
6. Owner-review and reservation preconditions were met without a protocol deviation affecting one arm.

`gpt-5.6-luna` is a pre-specified replication that never gates the verdict. Answers contradicting a reference fact are reported, not a veto.

### Result for the primary model (`gpt-6-luna`)

| Rule condition | Observed (`paired.json`) | Met |
|---|---|---|
| Same 65 cases in both arms | complete, none missing or unexpected | yes |
| Case-bootstrap lower bound above 0 | difference **+0.0462**, 90% interval **[0.0154, 0.0923]** | yes |
| Component-bootstrap lower bound above 0 | interval **[0.0114, 0.1020]** over 39 components | yes |
| At least 20 evidence components | 22 | yes |
| No added false answers | R3 0, hybrid 1 | yes |
| No one-arm protocol deviation | none recorded; both arms ran the same code, corpus and settings | yes |

`paired.json` records `demonstrated_gain_primary: true` and the statement "R3 gain demonstrated for the primary model gpt-6-luna under the preregistered rule." That string is the D-042 rule output only, not a confirmed-gain statement (three cases, McNemar p 0.25, no replication on the second model). Behaviour accuracy is **0.754** (r3) against **0.708** (hybrid), 49 against 46 of 65 cases correct.

### Replication on `gpt-5.6-luna`

Accuracy **0.723** against **0.723**, difference **0.000**, 2 better and 2 worse, case interval **[-0.0462, 0.0462]**, component interval **[-0.0533, 0.0536]**, McNemar exact p = 1.0. The gain is **not replicated** on the second model.

## What the result does not show

- **Three discordant cases.** For `gpt-6-luna` r3 is better on 3 cases and worse on 0. McNemar exact p is **0.25**; a one-sided 95% bootstrap bound clears zero narrowly, but three cases is a very small effect.
- **Two of the three were decided before any retrieval, in the hybrid arm** (inference from the saved traces and the graph code). In HO-V2-021 and HO-V2-049 the hybrid arm's planner finished in its first step with zero tool calls. The first planner call sees only the question and "(none yet)" for evidence (`src/labourlens/agent/graph.py`, `plan_research`), so both arms receive the same input there. The two arms therefore differ at that step by sampling, not by retrieval. Only HO-V2-048 (hybrid answered with a figure; r3 asked which measure was meant) plausibly depends on retrieved evidence. On `gpt-5.6-luna` the same two cases go the other way: HO-V2-021 is wrong for r3 and right for hybrid, and HO-V2-049 is a zero-tool abstention for r3. That reversal supports the sampling reading. It is an inference, not a measured attribution.
- **No replication on a second model** (above).
- **Small n and structure.** 65 cases, 39 components of which 22 carry evidence ids, 10 source groups. The component and source-group intervals are narrower in effective sample size than the case count suggests.
- **Sensitivity without the MTI group.** The five `mti_ai_feature` cases were kept as `answer` against the AI reviewers' majority view. Without that group (n=60) the difference is **+0.0333** with interval **[0.0, 0.0667]**, 2 better and 0 worse: the lower bound is **no longer above zero**, so the rule's second condition would not be met. HO-V2-021 is an MTI case. On `gpt-5.6-luna` the same sensitivity gives +0.0167 [-0.0333, 0.0667].
- **Report-text cases only** (n=34): `gpt-6-luna` **+0.0294** [0.0, 0.0882], 1 better, 0 worse; `gpt-5.6-luna` **-0.0294** [-0.0882, 0.0], 0 better, 1 worse.
- **The two wins in the ambiguity family** (HO-V2-048 and -049) are clarification cases with no gold evidence. The retrieval filter and rerank are not designed to help there.
- **One run per arm**, so run-to-run variation is not measured. Planner and answer are sampled.
- **This set is only partly independent.** It uses fresh evidence but the same system, prompts, tools, reranker and question styles (`FREEZE.md`, "Known leakage that remains"). The gold was AI-drafted first and approved unchanged by the owner (at signing: 59 own decisions in the signing export; 6 by agreeing with an AI suggestion). Updated 1 Nov 2026: in the final review all 65 cards are recorded as the owner's own decision, with 61 of the 64 compared decisions matching the AI suggestion (agreement with a suggestion, not accuracy). The labels are AI-drafted, signed off by the owner; one reviewer, after AI pre-review, not independent inter-rater evidence. The result was not rescored.
- **Not combined with the earlier held-out.** The registered 31-case held-out remains inconclusive (`experiments/heldout/paired.txt`). The two sets are not pooled; a pooled claim would need its own pre-registration.

## Results by arm

| Arm | Model | n | Behaviour [95% CI] | Over-abstain | False answer | Claim support | Fact coverage | Key-number recall | Calculation correct | Gold cited | p50 / p95 s | $/case |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| r3 | gpt-6-luna | 65 | 0.754 [0.646, 0.846] | 0.200 | 0.000 | 0.935 | 0.780 | 0.707 | 0.500 (n=4) | 0.583 | 18.7 / 37.7 | 0.00334 |
| hybrid | gpt-6-luna | 65 | 0.708 [0.600, 0.815] | 0.215 | 0.020 | 0.898 | 0.755 | 0.696 | 0.500 (n=4) | 0.562 | 10.6 / 18.3 | 0.00159 |
| r3 | gpt-5.6-luna | 65 | 0.723 [0.615, 0.815] | 0.215 | 0.000 | 0.906 | 0.796 | 0.707 | 0.500 (n=4) | 0.583 | 16.5 / 31.4 | 0.00485 |
| hybrid | gpt-5.6-luna | 65 | 0.723 [0.615, 0.831] | 0.215 | 0.020 | 0.889 | 0.816 | 0.704 | 0.500 (n=4) | 0.542 | 10.9 / 18.3 | 0.00360 |

Cost and latency come from the metrics files. R3 adds a rerank call: `gpt-6-luna` median 18.7 s and p95 37.7 s against 10.6 s and 18.3 s for hybrid, and $0.00334 against $0.00159 per case. `gpt-5.6-luna`: 16.5 / 31.4 s and $0.00485 against 10.9 / 18.3 s and $0.00360. Generation for the four arms was about **$0.87** (per-case cost times 65 cases) and judging about **$0.17**, so roughly **$1.04** in total, against the $0.94 quoted in the signed block; per-case figures are means from the metrics files, and these totals are my sums, not recorded totals.

Both arms have `gold_cited_any` near 0.55 to 0.58 and zero unsupported claims; claim support is 0.935 (r3) and 0.898 (hybrid) for `gpt-6-luna`.

### Per-family tables

`gpt-6-luna` (primary):

| Family | n | r3 accuracy | hybrid accuracy | r3 over-abstain / false answers | hybrid over-abstain / false answers | r3 better / worse |
|---|---:|---:|---:|---|---|---|
| factual_lookup | 22 | 0.909 | 0.864 | 2 / 0 | 3 / 0 | 1 / 0 |
| numerical_comparison | 14 | 0.214 | 0.214 | 11 / 0 | 11 / 0 | 0 / 0 |
| cross_source_synthesis | 8 | 1.000 | 1.000 | 0 / 0 | 0 / 0 | 0 / 0 |
| revision_conflict | 3 | 1.000 | 1.000 | 0 / 0 | 0 / 0 | 0 / 0 |
| ambiguity_insufficient_causal | 10 | 0.800 | 0.600 | 0 / 0 | 0 / 1 | 2 / 0 |
| adversarial | 8 | 0.875 | 0.875 | 0 / 0 | 0 / 0 | 0 / 0 |

`gpt-5.6-luna` (replication):

| Family | n | r3 accuracy | hybrid accuracy | r3 over-abstain / false answers | hybrid over-abstain / false answers | r3 better / worse |
|---|---:|---:|---:|---|---|---|
| factual_lookup | 22 | 0.864 | 0.864 | 3 / 0 | 3 / 0 | 1 / 1 |
| numerical_comparison | 14 | 0.214 | 0.214 | 11 / 0 | 11 / 0 | 0 / 0 |
| cross_source_synthesis | 8 | 1.000 | 1.000 | 0 / 0 | 0 / 0 | 0 / 0 |
| revision_conflict | 3 | 1.000 | 1.000 | 0 / 0 | 0 / 0 | 0 / 0 |
| ambiguity_insufficient_causal | 10 | 0.700 | 0.700 | 0 / 0 | 0 / 1 | 1 / 1 |
| adversarial | 8 | 0.875 | 0.875 | 0 / 0 | 0 / 0 | 0 / 0 |

`numerical_comparison` is 0.214 in all four arms (3 of 14), and it carries 11 of the 13 over-abstentions of the primary r3 arm. Revision-conflict has 3 cases and is not interpretable. Adversarial cases are unchanged between arms.

## Error analysis

Method: for each of the 16 behaviour mismatches of the primary r3 arm I read the saved case record, the raw trace (tool names, arguments, errors, round counts), the model's status and short stated reason, and whether the gold passage or observation ids appear in the agent's evidence. The same check on the other three arms found no new failure type. No tool, prompt or label was changed, and nothing was rerun.

### Classification of the 16 primary r3 mismatches

| Class | Cases | Count |
|---|---|---:|
| **Tool coverage gap, text figures:** the question asks for a difference between two figures printed in a report. Both figures were retrieved (gold passages in evidence), but `calculate_change` accepts only observation labels from `get_series`, and `answer_v3` forbids arithmetic without a calculation item. The model abstains. | HO-V2-029, 030, 031, 032, 033, 034, 035, 036 | 8 |
| **Tool / round-budget gap, dataset dimension labels:** the planner passed a dimension label that did not match the dataset's exact label (for example "Manufacturing" against "Unit Labour Cost Of Manufacturing"), or omitted it and got a 130-row refusal. The error lists the valid labels, but the retry uses the second and last evidence round, so `calculate_change` is never called. | HO-V2-025, 026, 027 | 3 |
| **Retrieval miss (both arms):** gold passage absent from the 30 evidence items the agent gathered. | HO-V2-011 | 1 |
| **Model reasoning, false-premise question:** both gold passages retrieved; the model abstained ("evidence does not state the amount") where the gold expects the answer that no significant gain was found. | HO-V2-022 | 1 |
| **Answer-status choice on non-answer cases:** zero tool calls; the model abstained where the gold expects `clarify` (HO-V2-050, 051, missing year or series) or `refuse` (HO-V2-063, respondent names). Each response still declines, so this is a strict-status mismatch. | HO-V2-050, 051, 063 | 3 |
| **Scorer** penalising a correct answer | none among the 16 | 0 |
| **Gold label judged wrong** | none identified | 0 |

Totals: 11 numerical, 2 factual, 3 non-answer status. Thirteen are over-abstentions (`over_abstention_rate` 0.200); none is a false answer.

### Do the tools reach the three new datasets?

Yes. `get_series` returned rows for `unit_labour_cost_index`, `value_added_per_worker_chained` and the average-weekly-paid-hours series, and `calculate_change` worked on them in the cases where the dimension label was right: HO-V2-023 and HO-V2-024 (paid hours) were calculated and `calc_correct` is true for both. The failures are in how the series is addressed and in the two-round budget, not in dataset reach. The catalogue given to the planner reports only the number of dimension values, not their labels (`StatsData.catalogue_text`), and the query requires an exact case-insensitive label (`StatsData.query`).

### Does the scorer penalise correct answers?

Not for the primary metric. `calc_correct` has only four eligible cases and is 0.500 in all arms; the two false cases are abstentions (HO-V2-025 and 026), not wrong arithmetic. `key_number_recall` is 0.707 (r3, `gpt-6-luna`) and is lowered by correct answers that state a difference without repeating the two input levels (HO-V2-024 reports -0.1 hours without the inputs 43.1 and 43; HO-V2-028 reports a percentage while the gold lists levels). That affects a secondary metric only. I found no display-precision (four-decimal) or unit problem.

### Retrieval was not the main limit here

The gold passage was in the agent's evidence for **33 of 34** answerable text cases with r3 and **31 of 34** with hybrid. Thirteen of the 16 shared failures are therefore not retrieval failures, and all 16 mismatches of the r3 arm also occur in the hybrid arm. The hybrid arm adds only the three discordant cases. One reading, labelled as inference: the new sources are single editions with no near-duplicate quarters or releases, so the period and release filter that gave r3 its large advantage on the original development and held-out sets has little to fix.

## Top follow-up (not done here)

The primary limit on absolute accuracy is the tool coverage gap, which this experiment did not touch and which sits outside the frozen v2 protocol.

1. **Text-figure arithmetic.** `src/labourlens/agent/tools.py`, `Tools.calculate_change` (accepts only labels held in `Tools._obs`) and the rule in `prompts/answer_v3.md` ("use a C item for any difference or percentage change"). Options: a validated extraction of figures from cited passages into calculable items, or a reviewed answer rule that lets the model state a difference between two cited figures. Either needs its own design, tests and threat review, because it changes the trust boundary around arithmetic.
2. **Dimension discovery and the round budget.** `src/labourlens/agent/tools.py`, `StatsData.catalogue_text` (list or fuzzily match dimension labels) and `StatsData.query` (suffix or token matching of the label), and `src/labourlens/agent/graph.py` line 34 (`MAX_ROUNDS = 2`), for example one extra round only after a tool error.

**Fixing either and rerunning would be a new experiment with a new id, outside the frozen v2 protocol.** The held-out v2 result must not be re-scored or edited after such a fix. Because the v2 questions and the failure analysis are now known, a rerun on this set would also lose its held-out status; a fresh set is needed for any new held-out claim.

## Verdict sentence

The preregistered rule is met for the primary model; the effect is three cases, two of which were decided before any retrieval in the hybrid arm; I would not call it a confirmed gain; the second model shows none; and both arms are held back far more by a tool coverage gap (arithmetic on report figures and dataset labels) than by retrieval.
