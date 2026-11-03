# Served chain without statistics lookup — PRE-REGISTRATION

**Registered:** 2 November 2026, before any run of this arm (but see the ordering disclosure in the Result section: the commit came later). **Status:** pre-registration only; no results recorded. Owner approved a one-factor ablation under D-016. This is an experiment-only route, not a live-app setting.

## Question and hypothesis

How much does the structured statistics store add beyond report text? **HYPOTHESIS:** removing statistics lookup lowers accuracy on factual-lookup and numerical-comparison questions. Abstentions may rise because the report evidence does not establish the requested figures; false answers may also rise if the model substitutes inadequate report text. These are predictions, not measured results.

## Arms and fixed settings

| Arm | Statistics lookup | Reports and calculation | Role |
|---|---|---|---|
| `served-dev-S65-direct-on` | direct `get_series` | direct | existing primary baseline |
| `served-dev-S65-mcp-on` | MCP `get_statistic` via `get_series` | direct | existing secondary baseline |
| `served-dev-S65-nostats` | disabled, not offered | direct | new candidate |

**DECISION:** single model `gpt-6-luna` for both planner and answer; exactly one run on the same 65 cases in `experiments/served/mixed-sample.jsonl` (51 development gold cases and 14 probes), tag `S65-nostats`, route `no-stats`, web steps on, retrieval `r3`, base tool set. No additional model arm. The fixture is anchored to Singapore date 2 November 2026; the harness rejects a later date. Do not change the fixture to work around that restriction.

The isolated change relative to direct-on is removal of `get_series`: the offered tools are exactly `search_reports` and `calculate_change`, both in process. The MCP-on comparison is secondary because its statistics lookup also used a different transport. Frozen prompt files are not edited: the runtime planner tool-catalogue bullet for `get_series` and its structured-output tool enum are filtered. Other prompt instructions, including the calculation tool's reference to earlier observation labels, remain byte-for-byte unchanged. The dataset metadata catalogue is retained; it contains definitions, not lookup results. A forced `get_series` call produces a traced `disabled_tool` error without invoking either statistics backend or crashing.

All limits and validators stay unchanged: six calls, two evidence rounds, ten seconds per call, 80-second run deadline, the same contextualise/triage/answer prompts and output checks. `calculate_change` still requires observation labels returned earlier in the run; without statistics lookup it cannot acquire those labels. No report-figure arithmetic tool is added as a workaround. The live `LABOURLENS_TOOL_TRANSPORT` choices and default are unchanged. Run provenance records `route: no-stats`, `tool_transport: direct`, `tool_list_filtered: true`, and the offered tool list.

## Metrics and interpretation

Report these for the candidate and both existing baselines, restricting comparisons to `gpt-6-luna`:

- Behaviour accuracy with two-sided 90% interval, all 65 cases; also separate gold and probes. Accuracy here means matching the expected answer status, not a claim that every answer is factually correct. Report content-quality evaluation separately.
- Paired accuracy differences versus direct-on and versus mcp-on using `labourlens paired`: case and component bootstrap 90% intervals, better/worse counts and exact McNemar p, with existing seeds/resample settings. The retrieval-gain decision field is not an acceptance rule for this ablation.
- Accuracy by question family, explicitly including factual lookup and numerical comparison; show denominators and keep small-family findings descriptive.
- False answers, abstentions (including over-abstention on answerable cases), tool-error counts/rates and disabled-tool errors, operational failures and false diversions.
- End-to-end latency median and p95, per-step latency, and startup separately; token-derived cost per question and total, using committed `specs/prices.yaml`.

**Stopping/reporting rule:** report whatever happens, including negative, null, failed or incomplete outcomes. No reruns, arm replacement, case removal, threshold tuning or post-result gold edits. Preserve partial raw outputs if interrupted and label them incomplete. One stochastic run on an already-used development sample cannot establish generalisation or eliminate model sampling noise. Neither a drop nor a null difference proves the statistics store is universally necessary or unnecessary.

## Commands

The dry run makes no paid calls and prints the plan without creating experiment outputs. The second command is the **only paid generation run** and is for the owner to execute with the existing local corpus and credentials; never print credentials.

```sh
uv run labourlens served-exp --split dev --gold experiments/served/mixed-sample.jsonl --pairs gpt-6-luna --tag S65-nostats --retrieval r3 --route no-stats --web-steps on --dry-run
uv run labourlens served-exp --split dev --gold experiments/served/mixed-sample.jsonl --pairs gpt-6-luna --tag S65-nostats --retrieval r3 --route no-stats --web-steps on
uv run labourlens eval --exp served-dev-S65-nostats --split dev --gold experiments/served/mixed-sample.jsonl --labels gpt-6-luna
uv run labourlens paired --gold experiments/served/mixed-sample.jsonl --candidate served-dev-S65-nostats --baseline served-dev-S65-direct-on --models gpt-6-luna --out experiments/served/paired-S65-nostats-vs-direct-on.json
uv run labourlens paired --gold experiments/served/mixed-sample.jsonl --candidate served-dev-S65-nostats --baseline served-dev-S65-mcp-on --models gpt-6-luna --out experiments/served/paired-S65-nostats-vs-mcp-on.json
```

**Cost forecast, not a result:** about $0.0026 per question, or $0.17 for 65 generation questions, anchored to the existing primary-model served arm and the committed token prices (gpt-6-luna input $0.10/output $0.50 per million tokens). The dry-run estimate uses the saved mcp-on cost per case. The actual candidate may use a different number of report searches, tokens and answer repairs. This is not a spending cap or invoice; the subsequent `eval` command can incur separate judge calls. The paired commands are offline. No candidate results are filled in this pre-registration.


## Result (recorded 2 November 2026, after the run)

The pre-registration above is unchanged. This section records what happened. Sources: `experiments/runs/served-dev-S65-nostats-b/gpt-6-luna.metrics.json` and `.scores.jsonl`; `experiments/eval/served-dev-S65-nostats-b-REPORT.md` (judge `gpt-6.1-terra`); `experiments/served/paired-S65-nostats-vs-direct-on.json` and `experiments/served/paired-S65-nostats-vs-mcp-on.json`. `gpt-6-luna` only, 65 served questions, one run per arm, retrieval `r3`, web steps on.

### Deviation: the tag changed from `S65-nostats` to `S65-nostats-b`

The first attempt, tag `S65-nostats`, was stopped by a 25-minute command timeout set by the person running it, after 44 of 65 cases. The harness cannot resume a run, so one complete run was made under the new tag `S65-nostats-b` with identical settings (same model, route, retrieval, web steps, fixture and prompts). This is an operational rerun of an incomplete run, not a rerun to change a result. The 44 interrupted rows were not scored, not paired and not used anywhere; they remain only as an unscored raw file in the local ignored `data/runs/served-dev-S65-nostats/`, and no `experiments/` directory exists for them. The pre-registered commands and tag in this file still show `S65-nostats`; the evidence uses `-b`.

### Ordering and provenance disclosure

- **The pre-registration commit came after the first attempt started.** The registration and the `no-stats` route code were committed together in `f11afd2` at 22:47:20 on 2 November 2026. The first attempt (`S65-nostats`) began at 22:11 and the complete run (`S65-nostats-b`) at 22:36, so the commit was made after the first, interrupted attempt started and while the second was running. Git therefore does not show that the registration came first. The only evidence of order is local file times: this file was created at 22:09:57, before the first attempt's output folder (22:11:19). File times are local and editable, so treat that as weak evidence.
- **The recorded `git_head` predates the route code.** The run provenance records `1b549cd` (21:59:21), which does not contain the `no-stats` route; `f11afd2` does. The run used code that was not yet committed, and the provenance has no dirty-tree flag.
- **Other pre-registrations.** For the FIN2 replicate (`7e44dc2`) and scanner v2 (`8edb968`), the registration text and the results were also committed together, so git timestamps do not prove that the text came first there either. For FIN2 the local registration file was created at 09:48:05 and the first FIN2 run folder at 10:08:53; the amendment to a mean-of-two headline was last written at 10:18:03, after generation had started, as the amendment says. For scanner v2 the file times in this checkout were all rewritten (16:25:04), so no file time shows the order; it rests on the declaration's own wording and on the input hashes recorded in `experiments/scanner/freeze.json`.

### Headline

| Measure | Statistics tool removed (`nostats-b`) | Direct `get_series` (`direct-on`) | `get_series` over MCP (`mcp-on`) |
|---|---|---|---|
| Behaviour accuracy, all 65 | 0.692 [0.585, 0.800] (45/65) | 0.908 (59/65) | 0.908 (59/65) |
| Gold only (51) / probes (14) | 0.608 / 1.000 | 0.882 / 1.000 | 0.902 / 0.929 |
| Paired difference of removal | | -21.5 points; 90% case-bootstrap interval [-30.8, -13.8]; 0 better, 14 worse; exact McNemar p = 0.0001 | -21.5 points; [-30.8, -12.3]; 1 better, 15 worse; p = 0.0005 |
| False answers (count) | 3 (rate 0.06 of 50) | 3 | 3 |
| Answers contradicting a reference fact | 4 | 1 | 1 |
| Over-abstentions on answerable cases | 15 of 65 (0.231) | 1 (0.015) | 0 |
| `calculate_change` correct | 0 of 6 | 5 of 6 (0.833) | 5 of 6 (0.833) |
| Key-number recall | 0.404 | 0.836 | 0.870 |
| Gold passage cited (any), answerable cases | 0.310 | 0.738 | 0.738 |
| Operational failures / false diversions | 0 / 0 | 0 / 0 | 0 / 0 |
| Latency, median / 95th percentile | 34.6 s / 54.4 s | 10.8 s / 32.8 s | 12.4 s / 34.7 s |
| Mean prompt tokens per question | 27,966 | 19,998 | 20,722 |
| Cost per question | about $0.0035 | about $0.00257 | about $0.00268 |

The false-answer rate and the over-abstention rate use the denominators printed in each arm's evaluation report, which differ slightly between arms, so the table compares counts for false answers. The 90% intervals are two-sided case bootstraps from `labourlens paired`; the component bootstrap intervals are [-29.7, -13.3] (direct-on) and [-30.4, -12.3] (mcp-on). The behaviour-accuracy interval of the removal arm in the first row is the 95% interval printed in its evaluation report. Judge cost for scoring this arm was $0.0431.

### By question family (behaviour accuracy)

| Family | n | Statistics tool removed | Direct | MCP | Over-abstentions, removed arm |
|---|---|---|---|---|---|
| Factual lookup | 15 | 0.867 | 1.000 | 1.000 | 2 |
| Numerical comparison | 7 | 0.143 | 0.857 | 1.000 | 6 |
| Revision conflict | 4 | 0.250 | 1.000 | 1.000 | 3 |
| Cross-source synthesis | 8 | 0.750 | 1.000 | 1.000 | 2 |
| Adversarial | 8 | 0.500 | 0.750 | 0.750 | 2 |
| Ambiguity, insufficient evidence, causal | 9 | 0.667 | 0.667 | 0.667 | 0 |
| Served context probes | 6 | 1.000 | 1.000 | 0.833 | 0 |
| Served diversion probes | 8 | 1.000 | 1.000 | 1.000 | 0 |

Cases that got worse than direct-on, by family (descriptive, from the paired file): numerical comparison 5, revision conflict 3, factual lookup 2, cross-source synthesis 2, adversarial 2; ambiguity and both probe families 0. Against mcp-on, six numerical cases got worse. Denominators are small: the numerical family has 7 cases and the revision family 4.

### What the traces show

- **No forced calls.** The saved traces contain zero `disabled_tool` errors and no attempt to call `get_series`: with the tool removed from the catalogue and the structured-output enum, the planner never asked for it. The offered tools were `search_reports` and `calculate_change`, as registered.
- **More searching.** The removal arm made 103 report searches over the 65 questions (102 ok, 1 error) against 61 for direct-on and 62 for mcp-on. Planner rounds: 42 questions used two rounds, against 34 in both other arms. `calculate_change` was never called (8 calls in direct-on, 6 in mcp-on), because it needs observation labels that only the removed tool returns.
- **Slower and larger.** Median time inside the agent step was 34.3 s against 14.1 s (direct-on) and 12.6 s (mcp-on); median time of one report search was 5.3 s against 4.0 s and 4.5 s; mean prompt tokens rose by about 40% and cost per question by about a third. These are the arm's own measurements. The three arms ran at different times, so some of the gap could come from provider load; I did not test that, and the searches and longer prompts are the only differences visible in the traces. Latency is therefore not a clean comparison with the other arms.
- **Tool errors.** One tool error in each arm (a `search_reports` error here, a `get_series` error in the others), rate 0.015.
- **Evidence in context.** The gold evidence was in the retrieved context for 0.643 of answerable cases against 0.976 in both other arms.

### Interpretation

**Capability, not transport.** Both baseline arms retain the `get_series` statistics tool. Direct calls `StatsData.query` in process, without a network or protocol; MCP calls server tool `get_statistic` in a separate process, running the same query over the same local `observations.parquet`. Both share the observation-label path (`O1`, `O2`, etc.), and `calculate_change` accepts only returned labels. MCP adds no data or second knowledge source. The live default is `mcp_stats`; the local default is direct and needs no MCP server. Comparing those baselines tests transport with information held fixed, so a tie is expected but does not establish equivalence. This ablation instead removes statistics access and its calculation inputs from both possible routes. This explanation does not amend the frozen pre-registration above.

On this 65-question sample, taking the statistics tool away lowers behaviour accuracy from 90.8% to 69.2%: about 21 points, with a paired interval that excludes zero against both arms. Read it with three limits. Removal also removes the only source of the observation labels that `calculate_change` needs, so "0 of 6 correct" and most of the numerical-family drop follow almost by construction; the arm tests "no structured lookup and no calculation input", not "report text in place of the data". It is one run, on 51 reused development cases and 14 of my own probes. And MCP against direct is a tie here (both 0.908; one case better and one worse in the earlier comparison), which is not evidence that the transport has no effect: one run each cannot show equivalence. Within those limits, the structured store carries the numerical and revision questions in this sample: the retrieved report text did not give the model what it needed, and the model mostly abstained (15 over-abstentions, 6 of them in the 7 numerical cases) rather than guess.

Not every loss is an abstention. Answers contradicting a reference fact rose from 1 to 4, so removal also produced some wrong content, not only refusals. False answers, as counted by the evaluation report, stayed at 3 in every arm.

### What this does not show

- **One run, 65 cases.** The sample is 51 reused development cases and 14 hand-written probes. Model sampling noise is unmeasured; the two baselines differ by one case in the earlier comparison. The numerical family has 7 cases and the revision family 4, so family figures are descriptive.
- **A missing calculation input, not a calculation failure.** `calculate_change` needs observation labels from `get_series`. Removing the lookup removes that input, so "0 of 6 correct" reflects the missing observations, not a defect in the arithmetic tool. Report text was not given a substitute arithmetic path, by design.
- **Not a statement about all use.** It does not show the store is necessary for questions outside this sample, or that report text could never be enough with a different tool design.
- **Gold and judge.** The gold labels were drafted with AI help and reviewed by the owner (not independent inter-rater evidence). The judge `gpt-6.1-terra` is an AI from the same provider family as the generator.
- **Latency.** Not a clean comparison, as noted above.
- **Transport.** Direct and MCP use the same lookup and were each run once; a null difference between them is not a proof of equivalence.

### Verdict against the pre-registered hypothesis

The pre-registration set no numeric pass mark; it asked for whatever happened to be reported. The hypothesis was that removing the lookup lowers accuracy on factual-lookup and numerical-comparison questions and may raise abstentions and false answers. Result: **supported for accuracy and abstentions, not for false answers.** Numerical comparison fell from 0.857 (direct) and 1.000 (MCP) to 0.143; factual lookup from 1.000 to 0.867 (2 cases, small); over-abstentions rose from 1 and 0 to 15; false answers did not rise (3 against 3). Drops in revision conflict, cross-source synthesis and adversarial questions were not named in the hypothesis and are reported as observed. The paired intervals against both baselines exclude zero.
