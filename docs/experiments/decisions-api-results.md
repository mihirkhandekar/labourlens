# Decisions API results

**Status: results template, not an experiment result.** No paid execution, successful-call latency, measured quality, cost saving or screen outcome is claimed by this note. The immutable [preregistration](decisions-api-prereg.md) controls interpretation. Populate a dated results narrative only after the owner authorises execution and the parent-generated analysis exists. Do not insert illustrative numbers as measured values.

## Evidence and reproducibility

The parent analysis command consumes explicitly named triage and support run directories containing `manifest.json`, `raw.jsonl` and `status.json`. It writes `experiments/eval/decisions-api-results.json` by default, or a separately named output, using exclusive creation. An existing result is never overwritten. Further analyses require a new output file.

The generated JSON, not manually transcribed calculations, is the numerical source of truth. Its `inputs` records source directories, manifests, fingerprints and completion status. `triage.issues` and `support.issues` expose missing, duplicate, unexpected or mismatched identities. Incomplete runs remain recorded and their screens are inconclusive. A complete row count alone does not establish complete identities.

**MEASURED RESULT:** unavailable until an authorised run and its analysis are supplied. Record the actual output path, run IDs and approval/commit evidence in the eventual narrative. Offline synthetic test outcomes must not be represented as provider results.

## A: route selection

Read `triage.arms.A0` and `triage.arms.A70` for effective route agreement, valid-response-only agreement, confusion matrices, strata, per-repeat results, misses, diversion identities, non-in-scope recall and three-repeat consistency. A70 is the primary screen; A0 cannot replace it after a failed screen. The separate confidence threshold is fixed at 0.70, with equality passing. Invalid responses fail open but are not counted as valid successes.

Read `triage.operational` for scheduled classifications, HTTP attempts, failures/refusals, error categories, skipped inputs, low-confidence count, tokens, known/unknown costs and pooled/per-repeat wall times. Attempted failures belong in operational timings; skipped zero-time records do not. Successful timings are shown separately. Cache token fields are reported without adding cache subsets to total input tokens.

Read `triage.rules.each_repeat` for the legitimate-question, borderline, threat-identity and route-quality guardrails. Every repeat must satisfy them. The operational failure/refusal ceiling applies across scheduled classifications. `triage.rules` and `triage.decision` determine the screen, not an average that hides a failed repeat.

### Historical latency and cost comparison

`triage.latency` joins historical case identities to the median of each case's three Decisions times. It reports nearest-rank p50/p95, per-case deltas and ratios, the median ratio and proportion faster. The primary speed rule requires complete timing pairs and both p50 and p95 at most 80% of historical values. Missing observations make speed inconclusive.

`triage.paired_accuracy_case_cluster_bootstrap` and `triage.latency.case_cluster_bootstrap` report paired differences and percentile intervals. Cases, not repeated calls, are the independent resampling units. `triage.cost_comparison` permits a saving or neutral claim only with complete, known comparable costs; cost cannot override a failed safety or quality guardrail.

**Limitation:** historical baseline timings were collected at another time, once per case. This is not a contemporaneous randomised benchmark, a transport-only causal comparison, a reply-quality comparison or an end-to-end agent speedup. A passing screen only supports a separately approved integration decision.

## B: cited-claim support

Read `support.metrics.primary` for the frozen second-family AI reference and `support.metrics.original_judge_sensitivity` for the original judge sensitivity analysis. Each contains overall metrics, generator/set/arm/family strata and clustered uncertainty. Supported is positive; partial or unsupported is negative. The prediction threshold remains 0.50, with equality positive.

Report denominators, valid coverage, valid-only accuracy, all-scheduled accuracy counting failures incorrect, balanced accuracy, sensitivity, specificity, false-support rate, confusion matrix, Brier score, AUROC and the majority-supported baseline. `support.probability_distribution` exposes the valid probability distribution. Missing probabilities remain missing, not zero or 0.5. Empty and single-class AUROCs are unavailable, not zero. `support.rules` and `support.decision` apply all preregistered thresholds together.

`support.operational` reports Decisions wall times, token usage, attempts and list-price cost per scheduled claim and HTTP attempt. Unknown cost remains unavailable. `support.historical_original_judge_cost` and `support.historical_second_judge_cost` count each eligible answer cost once, then report equal-answer amortised cost per claim and total cost divided by total claims. Incomplete answer claims or unknown costs prevent a complete comparison. `support.second_judge_attempt_disclosure` records historical attempt, retry and cache-status counts.

**Historical judge timing: unavailable.** Neither saved original-judge metadata nor second-family attempt metadata contains judge-call seconds. Agent answer-generation time is not judge time. No B faster-than-judge conclusion is permitted, and no new baseline calls are authorised by this protocol.

**Limitation:** these are selected FIN AI claim labels, not human truth. Primary negative examples are partial-support claims, not verified fabrications. Judges also performed fact coverage, so amortisation is an accounting convention rather than measured marginal verification cost. A passing screen supports only further verifier evaluation.

## Uncertainty and interpretation

The analysis uses 10,000 bootstrap draws with seed 20261103 and percentile 95% intervals. A resamples complete case clusters with their repeats. B resamples `(generator model, set, case_id)` clusters, retaining both retrieval arms and all claims. Undefined AUROC draws are counted; an interval is unavailable when fewer than 95% of draws are defined. Intervals for incomplete inputs describe available observations and cannot establish a passing screen.

Wilson 95% binomial intervals are descriptive only: repeated questions, claims and retrieval arms are dependent. These are not multiple-comparison-adjusted hypothesis tests. No significance test, threshold search, selective rerun or post-hoc reference relabelling determines adoption. Retain failed and null outcomes as well as incomplete outputs.

## Verification and next gate

No verification outcome is asserted by this template. The parent records the exact offline test, documentation check and rights-scan commands and their observed results after implementation is complete. Public support outputs must contain identities, labels, probabilities and operational metadata only, never claim or evidence text. Any subsequent integration, new threshold, new prompt, new sample or baseline timing collection requires separate approval and, where applicable, a new registration.
