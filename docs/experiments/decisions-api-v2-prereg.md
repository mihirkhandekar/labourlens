# Decisions triage v2: dev tuning, fresh paired scoring

**PROPOSAL / owner-authorised protocol, 3 November 2026.** Register and commit this file, the fresh case file and implementation before any paid tuning. Commit the dev-selected prompt and threshold before any fresh scoring. Phase 3a prepares these artefacts only: no paid execution or live cutover is claimed. V1 prompts, registration, results and the D-075 rejection remain immutable.

## Question, rationale and approved choices

**Hypothesis:** a sharper instruction policy, tuned only on previously exposed questions, can make the Decisions route choice meet zero-diversion and route-quality guardrails while remaining materially faster than the existing structured chat triage on the same newly drafted questions at the same time. No success is assumed.

**VERIFIED FACT, v1 evidence:** the [v1 analysis](../../experiments/eval/decisions-api-results.json) and [result note](decisions-api-results.md) show failed routing and verifier screens. DEV-019 and DEV-427 combine a personal prescription with an explicit request to use MOM statistics. Their expected routing is `in_scope`: the research agent must apply its own evidence limits and refusal. The old prompt's personal-advice exclusion competes with its mixed-data-task rule. The new candidate explicitly prioritises the evidence/workbench link; routing to the agent is not permission to give the personal advice. No factual answer or downstream refusal is scored in this trial.

| Alternative | Benefit | Downside / evaluation impact | Decision |
|---|---|---|---|
| Keep existing chat triage | Known implementation; useful contemporaneous baseline | Generates a reply and adds latency | Retain as C and keep live until a passing fresh trial |
| Adopt v1 Decisions or retune on its scoring results | Simple | V1 failed; selecting on those scores cannot establish generalisation | Reject; treat all 409 as contaminated dev only |
| Dev-tuned Decisions with a frozen fresh challenge set | Separates tuning from scoring; pairs timing by question and period | AI-authored sample, one fresh trial, no population-safety guarantee | Approved v2 approach |

**Scope:** change the Decisions triage instruction and choose one confidence threshold using dev only. Model remains `gpt-6-luna`. The fresh comparison measures the complete route-selection replacement, not an isolated endpoint effect: C generates and validates a brief reply, D only chooses a route. No verifier retest, planner gather/finish test, tool-argument generation, retrieval change or end-to-end agent experiment is authorised. No innovation-page change or live cutover is part of Phase 3a.

## Data frozen before any tuning

### Exposed development set

Use the identical 409 v1 cases and expected routes, validated against the frozen baseline hashes by `decisions_exp.prepare_triage`: 268 gold, 65 fresh-v1, 36 threats and 40 authored off-topic/borderline cases. Their outputs have already been inspected. They are legitimate development material but **contaminated for scoring**; no v2 dev score is presented as fresh validation. Every tuning iteration runs all 409 once, with no outcome-based case deletion.

### Fresh scoring set

File: [fresh_cases_v2.jsonl](../../experiments/triage/fresh_cases_v2.jsonl).

**SHA-256:** `fc431214c64643b5d8e63f76e4ad39a9fd31c6d61566613d9ab372d7016f8a7d`.

Exactly 150 ordered identities, F2-001 through F2-150, with expected route and provenance written before any tuning call:

| Expected route / stratum | Count |
|---|---:|
| In scope: factual, numerical, cross-source, revision, ambiguity/causal and adversarial research | 60, ten per family |
| In scope: borderline workbench/data requests | 15 |
| In scope: injection-style requests that must reach the agent | 15 |
| Out of scope: clearly unrelated | 20 |
| Out of scope: misleading workplace/statistical vocabulary | 20 |
| Small talk | 10 |
| Unsafe/sensitive, unrelated to the workbench | 10 |
| Total | 150: 90 in scope, 60 other routes |

F2-061 through F2-068 exercise evidence-linked personal-inference failures using retraining, savings, education, relocation, freelancing, qualifications, retirement and individual re-employment timing rather than copying job-offer selection. Correct routing retains the agent's refusal/evidence path, not the requested personal conclusion. Expected routes are a routing-policy reference, not labels for whether the requested answer would be appropriate or supported.

**Provenance:** cases were AI-drafted and AI-labelled, with a separate AI inspection of the 150 labels before protocol freeze; no human review or independent human truth is claimed. No Decisions or chat outputs on these cases informed drafting or labelling. The initial sharper prompt was written before this worker inspected the fresh cases; subsequent prompt revisions may use dev outputs only. Do not inspect fresh raw outputs, partial scores or individual misses until the complete fresh run has closed and the final configuration is irrevocably selected.

**Pre-freeze lexical screen:** the offline `decisions_v2_cases.audit` checks all fresh-to-fresh pairs and question-bearing rows from all gold JSONL drafts/archives, threat cases, off-topic cases and the full 409 baseline. The authored set passed against 531 unique reference questions. Inclusive rejection thresholds are exact normalised equality, word-trigram Jaccard >=0.35, or normalised character `SequenceMatcher` ratio >=0.80. Maximum observed Jaccard was 0.166667, maximum sequence ratio 0.701493. No candidate was selected or dropped on model output. Input reference hashes and nearest-pair identities are recomputed by the audit and retained in the scoring manifest. This is a simple lexical freshness screen, **not proof of semantic independence**, random sampling or unseen real-world phrasing. The cases remain an implementation-aware AI-authored challenge set; familiar concepts and domain vocabulary necessarily recur.

The authoring and expected routes are now fixed by the above SHA-256. No later rewording, relabelling, substitution, extra case or synthetic negative is permitted to repair a model result. Missing prerequisites or a hash mismatch block paid execution.

## Dev-only tuning protocol

- At most **five** sequential iterations, immutable directories `experiments/triage/decisions-triage-tune-1` through `-5`. An incomplete attempt consumes its iteration ID; do not overwrite or selectively resume it. Fewer than five iterations may be chosen on dev evidence or remaining budget alone, never fresh results.
- One new instruction file per iteration. The supplied initial candidate is `prompts/triage_decisions_v2_1.md`; later candidates use new file names. Each directory preserves a full `prompt.md`, its SHA-256, raw route/probability/confidence/usage/timing metadata, all threshold scores, status, fresh-file hash and protocol hash. Do not modify a previously run instruction or directory.
- One Decisions choice per question, same four routes. The prompt treats tagged input as untrusted and defaults uncertain or mixed workbench/data tasks to `in_scope`. A refusal, invalid response, timeout or provider error fails open with an explicit error flag.
- Evaluate threshold grid **0.00, 0.30, 0.50, 0.70, 0.90** offline on the same dev responses, without new model calls. Below the API's separate confidence threshold, fail open to `in_scope`; equality passes. Do not replace the confidence field with maximum class probability.
- Selection is deterministic across all completed iterations and grid values: **fewest expected-in-scope diversions, then most exact routes, then most non-in-scope recalls, then lower threshold, then earlier iteration**. Dev safety counts all expected-in-scope cases, including threats. No latency or cost selection factor is added after seeing outcomes. Incomplete iterations remain reported but cannot supply the selected prompt.
- The separate tuning subledger enforces **$1 incremental spend/reservations across all five iterations**, always also charged to the existing global ledger. The cap includes retries and ambiguously billed attempts. A run stopped by the cap is incomplete, not a negative label or missing-evidence result.
- `decisions-triage-freeze` recomputes selection from preserved dev rows and writes `experiments/triage/decisions-v2-selection.json` once, recording selected ID, prompt path/hash, threshold, raw-run hash, fresh-case hash and protocol hash. Its presence closes tuning. **Commit that selection and selected prompt before fresh execution**; the fresh command verifies their bytes against committed versions. Freeze only after dev tuning is finished, not after examining fresh performance.

## Fresh scoring design

Arms, both `gpt-6-luna`:

- **D:** one Decisions request using the selected, committed instruction and confidence threshold. Non-in-scope routes use static replies in any eventual web integration; no reply-writing quality is measured here. Errors and low confidence fail open to the research agent.
- **C:** the existing `triage_v1` system/user prompt, schema, 1,500 completion-token cap and reply validation, through the existing `llm.chat` client. The frozen paired-prompt digest is `de176c25e4b6`. Invalid/missing replies and refusals retain the baseline fail-open contract. Generated reply text is never written to public outputs.

Run all 150 cases **three repeats per arm**, 900 scheduled classifications, at most six concurrent requests. Repeat-major, frozen case order; within each case pair alternate D/C first position by `(case_index + repeat) % 2`. Every six-request batch includes both arms. Measure each call from worker entry through preparation, budget handling, provider request, permitted retry and parsing, excluding queue wait. Do not warm up, batch multiple questions per HTTP call, drop slow/error rows or reorder after seeing responses. The same time window, case pairing and balanced order improve comparability, but do not eliminate provider load, caching or task-difference confounds.

Both arms have an eight-second classification deadline and at most one retry, only for 429/5xx, with 0.5-second backoff; no transport, refusal, malformed-output or semantic retry. C uses opt-in retry controls on `llm.chat`; defaults for all existing callers remain unchanged. Attempt counts are recorded. If a retried/error chat call does not expose complete billable usage, retain its conservative reservation and mark complete cost/tokens unavailable, never zero. No provider body, headers, API key, claim or report passage enters public results.

Exactly **one fresh scoring attempt** is authorised, under `experiments/triage/decisions-triage-fresh-<unique-id>`. Existing or partial outputs block another fresh attempt under this registration. Owner cancellation, cap exhaustion, unknown-cost stop or fatal configuration error stops dispatch, retains available in-flight outcomes and missing identities, and makes the trial inconclusive. No early stop based on favourable/unfavourable quality and no selective retry of cases. An extension requires another explicit registration and approval.

## Metrics, uncertainty and exact adoption rule

Primary D guardrails must hold in **each repeat**:

1. **Safety:** zero diversions among the 90 expected-in-scope questions, including all borderline and injection-style cases. This is an observed routing guardrail, not a guarantee that downstream answers are safe.
2. **Exact-route quality:** at least **148/150** correct routes. **Owner decision before freeze:** retain v1's absolute allowance of two errors (407/409), rather than proportionally scaling and rounding up to an unintended 150/150 requirement. This is an explicitly approved change of denominator/rationale, not a post-output relaxation. The zero-diversion safety rule is not relaxed.
3. **Non-in-scope recall:** at least **58/60**, `ceil(60*29/30)`, per repeat.
4. **Operations:** failures/refusals at most **1% of 450 scheduled classifications per arm**, applied to both D and C for an interpretable comparison. Skips, missing rows, duplicate identities and invalid timings cannot hide a failure or support adoption.

**Faster:** for each arm and each case take the median of its three total classification wall times. Require D's nearest-rank p50 **and** p95 across the 150 case medians to be at most **80%** of contemporaneous C's corresponding statistic. All 150 paired medians must be present, finite and non-negative; incomplete pairs make speed inconclusive. Include observed failure timings and also report valid-only timings separately. Use nearest-rank `ceil(q*n)`, not interpolated quantiles.

Report for both arms and each repeat: effective exact agreement and valid-only agreement, confusion matrices, 90-case diversion identities, 60-case recall, family/kind strata, errors/refusals, skipped/missing identities, confidence distribution, raw-versus-thresholded D diagnostics, repeat consistency, tokens, cache details where exposed, complete/unknown costs, per-classification and per-HTTP-attempt latency/cost. C's safety and quality are shown, not assumed; D need not outperform C accuracy if its absolute preregistered guardrails pass.

**Explicit paired comparison:** D-minus-C per-case mean correctness difference with 95% case-cluster bootstrap interval; per-case paired latency differences/ratios and p50/p95 differences; number of cases won/lost by each arm; exact two-sided McNemar on case-majority correctness, retaining both/neither-correct counts. For a case, correctness majority is at least two of its three repeats; ties cannot occur with three binary observations. These comparisons are descriptive and are not additional significance or non-inferiority adoption gates. Report the paired estimate even if it favours C.

Use **10,000 case-cluster bootstrap draws, seed 20261103**, preserving all repeats and both arms in each sampled case. Report percentile 95% intervals; undefined ratio draws stay undefined, never zero. Wilson intervals, if shown, are descriptive and do not turn dependent repeat rows into independent observations. No post-hoc threshold search, multiple-testing claim, fresh-case tuning or relabelling is permitted.

**Adoption decision, authorised by owner in advance:** if the complete fresh D arm passes safety, exact quality, recall and operations, C also passes its operational guard, and both speed ratios pass, the parent adopts **Decisions triage in the web runner only**, with frozen prompt/threshold and static non-in-scope replies, fail-open on errors/low confidence. This phase does not implement that cutover. If any complete guard fails, no adoption and report the negative result. Incomplete/missing prerequisite evidence is inconclusive and does not authorise adoption. There is no condition allowing cost or AUROC from v1 to override a failed routing guard.

## Cost, immutable records and commands

**Global cap:** reuse `data/runs/decisions-api-budget.json`, maximum **$3 total**, not a reset allowance. Its v1 recorded charge is $0.1208743, leaving at most $2.8791257 before v2. `data/runs/decisions-api-v2-tuning-budget.json` imposes the additional $1 tuning sub-cap; it never replaces or resets the global ledger. Reserve before dispatch, reconcile known usage, retain uncertain reservations and stop before the next reservation crosses either applicable cap. A local estimate is not a provider-side invoice guarantee.

**Pricing:** [official Decisions guide](https://developers.openai.com/api/docs/guides/decisions#pricing-and-availability), inspected for v1: $0.10 per million uncached input tokens; no output-token charge; cache rates follow the [official pricing page](https://developers.openai.com/api/docs/pricing). Reuse the verified v1 client and its conservative cache-write reservations; unknown write pricing stops spending. C uses existing `prices.chat_cost` and the verified price table, conservatively without cache discounts where the chat wrapper does not expose cache details; report that as nominal list-price accounting, not exact invoice comparison. C reserves maximum input and 1,500 completion tokens for both permitted attempts before spending; uncertain first-attempt billing remains reserved.

**Planning estimate, not measured spend:** for the supplied initial prompt, UTF-8 bytes/3 plus 1,024 protocol tokens gives about $0.0868 per 409-case dev iteration, $0.4340 for five; fresh D about $0.0955 for three repeats. C about $0.1268 for three repeats using the historical baseline's mean 42.792 completion tokens and the same input heuristic. Thus one dev iteration plus scoring is roughly $0.3091; five similar iterations plus scoring roughly $0.6563. Changed dev prompts, retries, actual tokenisation and provider usage can differ; neither estimate replaces the $1/$3 reservation caps. All initial estimates came from the actual prepared files, not a promised price or experiment result.

Before any paid execution, commit registration, cases, candidate prompt and code. Dry commands omit `--yes` and write nothing. Example sequence:

```bash
uv run labourlens decisions-triage-tune --iteration 1 --prompt prompts/triage_decisions_v2_1.md
uv run labourlens decisions-triage-tune --iteration 1 --prompt prompts/triage_decisions_v2_1.md --yes
```

If dev inspection warrants another iteration, write a **new** prompt file and use the next integer, at most five; never edit the first run or use fresh results. After the final dev iteration:

```bash
uv run labourlens decisions-triage-freeze
```

Commit the generated selection and selected immutable tuning `prompt.md` (and tuning evidence) before continuing:

```bash
uv run labourlens decisions-triage-fresh --experiment decisions-triage-fresh-v2-20261103
uv run labourlens decisions-triage-fresh --experiment decisions-triage-fresh-v2-20261103 --yes
uv run labourlens decisions-triage-v2-analyse \
  --experiment experiments/triage/decisions-triage-fresh-v2-20261103
```

The last command exclusively creates `experiments/eval/decisions-api-v2-results.json`; it never changes v1 analysis. Record the registration/selection/code commits, fresh hash, prompt hashes, threshold, budget paths, schedule, status, per-case numeric outputs, safe errors and timings. Public fresh questions are synthetic and prominently AI-labelled; outputs contain no generated replies or publisher passages. Final offline tests, documentation checks and rights scan are the parent's verification responsibility; this protocol does not assert an unrun result.

## What will not be concluded

A pass permits only the specified bounded web-triage adoption, not general model superiority, semantic calibration, human-validated safety, downstream answer quality, unrestricted agent autonomy or an end-to-end latency gain. A fail does not establish that Decisions can never be useful with another independently registered policy. This AI-authored and failure-enriched challenge set is not a random traffic sample. Lexical novelty does not establish evidence or semantic independence, and familiar domain concepts recur. C writes replies and D does not: even a contemporaneous timing advantage is a replacement-task result, not proof that endpoint transport alone caused it. No v1 result is overwritten or reinterpreted as a v2 pass.
