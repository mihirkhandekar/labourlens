# Served chain without statistics lookup — PRE-REGISTRATION

**Registered:** 2 November 2026, before any run of this arm. **Status:** pre-registration only; no results recorded. Owner approved a one-factor ablation under D-016. This is an experiment-only route, not a live-app setting.

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
