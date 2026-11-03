# Decisions API results

**MEASURED RESULT, 3 November 2026. DECISION: not adopted.** Both preregistered screens failed. Route selection was faster and cheaper than the historical structured-call baseline, but diverted legitimate research questions. The support predicate ranked AI-labelled claims reasonably well but passed too many partially supported claims at the frozen threshold. Neither finding justifies a live-agent change.

## Evidence and reproducibility

The immutable [preregistration](decisions-api-prereg.md) was committed as `f950867` before paid execution; both manifests record implementation commit `3fd16ba`. Numerical source: [generated analysis](../../experiments/eval/decisions-api-results.json), not manually reconstructed scores. Input manifests and complete statuses are embedded in that file; both `issues` lists are empty.

- Routing: `experiments/triage/decisions-triage-v1-20261103`, 1,227 classifications, 409 distinct questions and three repeats.
- Support: `experiments/eval/decisions-support-v1-20261103`, 441 cited claims, one predicate per claim.
- Decision model: `gpt-6-luna` throughout. No shipped prompt, gold label, existing result or live-agent path changed. Thresholds were not tuned after results.

The offline reproduction command is:

```bash
uv run labourlens decisions-analyse \
  --triage experiments/triage/decisions-triage-v1-20261103 \
  --support experiments/eval/decisions-support-v1-20261103 \
  --out experiments/eval/decisions-api-results-reanalysis.json
```

Use a new output name: analysis refuses overwrite. The original results JSON and raw runs stay immutable.

## A: route selection

The same 409 questions comprise 268 gold questions, 65 fresh questions, 36 threats and 40 authored off-topic/borderline cases. A0 uses the valid route directly; primary A70 fails open to the research agent when the API's separate confidence is below 0.70. API refusals/errors also fail open.

| Per-repeat result, identical in all three repeats | Historical baseline | A0 | A70 | Frozen requirement for A70 |
|---|---:|---:|---:|---|
| Exact routes | 408/409 | 405/409 | 397/409 | At least 407/409 |
| Legitimate gold + fresh question diversions | 0/333 | 2/333 | 1/333 | Zero each repeat |
| Borderline in-scope diversions | 0/10 | 0/10 | 0/10 | Zero each repeat |
| Threat diversions | 1/36 | 1/36 | 0/36 | At most the baseline identity |
| Non-in-scope recall | 30/30 | 29/30 | 19/30 | At least 29/30 |

Against baseline route accuracy, the case-paired A0 difference is -0.73 percentage points (95% interval [-0.0171, 0.0000] in proportion units); A70 is -2.69 points ([-0.0440, -0.0098]). These intervals cluster repeated observations by question; 1,227 rows are not 1,227 independent questions.

There were 3 API refusals in 1,227 calls (0.244%, below the 1% ceiling), no retries or skips, and 63 low-confidence rows. The 0.70 threshold repaired one legitimate diversion and the historical threat diversion but reduced off-topic recall to 63.3%. A70 fails both safety and route quality in every repeat. A0 is a secondary diagnostic and cannot replace the failed primary arm.

### Specific failures, IDs only

- **DEV-019:** A0 diverts a legitimate gold question in every repeat, violating the zero-diversion requirement if used directly. Confidence 0.52 makes A70 fail open correctly, so this is **not** A70's remaining legitimate diversion.
- **DEV-427:** A0 and A70 divert a legitimate gold question in every repeat; confidence 0.77 passes the fixed gate. This is the primary arm's zero-diversion safety failure.
- **T-D05:** A0 repeats the historical threat diversion; this is an exact-route miss but permitted by the baseline-identity threat allowance. Confidence 0.37 makes A70 retain the agent path.
- **OT-018:** the API refuses in each repeat and both arms fail open rather than selecting the expected unsafe/sensitive route. This contributes to the route-quality misses and operational refusal count, but the aggregate refusal ceiling itself passes.

These four are the A0 misses. A70 has further off-topic misses induced by confidence gating, recorded by ID in the analysis. No question or publisher text is reproduced here.

### Historical latency and cost comparison

| Matched statistic | Historical structured triage | Decisions, per-case median over three repeats |
|---|---:|---:|
| p50 | 1.563 s | 0.359 s |
| p95 | 2.437 s | 0.427 s |
| Mean list-price cost per classification | $0.00012372 | $0.00008504 |

Both latency ratios pass the <=0.80 rule: p50 0.230, p95 0.175. All 409 case medians are faster. Median paired latency change is -1.202 s, 95% case-bootstrap interval [-1.239, -1.173] s; the p50 difference interval is [-1.238, -1.184] s and p95 difference interval [-2.281, -1.827] s. Pooled per-call p50/p95 are 0.358/0.483 s; those are different aggregations from the primary case-median comparison.

**Limitation:** baseline observations were collected at another time, once per case. This is case-paired historical evidence, not a contemporaneous randomised or transport-only causal benchmark. The baseline also writes a short reply; Decisions selects only a route. No free-text reply quality or end-to-end agent speedup was measured.

## B: cited-claim support

The primary reference is the frozen **second-family Sonnet AI judge**, not human labels: 383 fully supported and 58 partially supported claims, no fully unsupported negatives. The original **Terra same-provider/family AI judge** is a separate sensitivity reference, not a second human reviewer. Saved answers span both generator models and retrieval arms. The Decisions model is `gpt-6-luna`; pooled B metrics must not be described as a single-generator subset.

All 441/441 predicates are valid, passing the 100% coverage gate. At fixed probability >=0.50:

| Primary measure | Result [95% cluster-bootstrap interval] | Frozen rule | Outcome |
|---|---|---|---|
| AUROC | 0.830 [0.758, 0.894] | >= 0.80 | Pass |
| Accuracy, threshold 0.50 | 0.880 [0.848, 0.911] | >= 0.85 | Pass |
| Balanced accuracy | 0.609 [0.555, 0.671] | >= 0.70 | Fail |
| False-support rate | 0.759 [0.636, 0.868] | <= 0.20 | Fail |

Confusion counts: 374 true supports, 14 true negatives, 44 false supports and 9 false negatives. Sensitivity 0.977 [0.962, 0.990]; specificity 0.241 [0.132, 0.364]; Brier score 0.098 [0.073, 0.123]. Always predicting supported would score 0.868, close to the observed 0.880; raw accuracy alone hides poor negative detection.

Probabilities concentrate near full support: median 1.00, mean 0.926, with 362/441 in the final [0.9, 1.0] bin. AUROC measures ranking across thresholds; passing AUROC does not repair the preregistered threshold's false-support rate. No new threshold was selected.

Against original same-family Terra labels, AUROC is 0.786 [0.736, 0.837], accuracy 0.816 [0.770, 0.863], balanced accuracy 0.574 [0.536, 0.612]. Reference dependence is a limitation, not permission to choose the more favourable judge.

### Verifier time, cost and limits

Decisions p50/p95 is 0.367/0.834 s per claim; total list-price cost $0.0165286, mean $0.00003748. Historical original-judge total/claim amortisation is $0.00078680, and equal-answer mean amortisation $0.00084785. Second-family equivalents are $0.00214866 and $0.00257730. Those judge calls also scored reference-fact coverage and multiple claims: these are accounting comparisons, not measured marginal verification costs. The second-family reference includes 239 attempts, 57 cached and 2 retries.

**Historical judge timing is unavailable.** Neither original-judge nor second-family records persist judge-call seconds. Agent-generation seconds are not judge timing. No faster-than-judge conclusion is permitted.

The 441 claims are dependent observations drawn from 237 selected saved answer records and 120 generator/set/case clusters. They are not 441 independent questions. Primary negative labels mean partial support, not fabricated claims. Three omitted reference records stay excluded. This trial cannot establish human-grounded correctness or reliable detection of fully unsupported claims.

## Uncertainty, cost and interpretation

Intervals use 10,000 bootstrap draws with seed 20261103: A resamples cases retaining repeats; B resamples generator/set/case clusters retaining both arms and all claims. All reported primary AUROC draws were defined. Wilson intervals in the JSON are descriptive only; dependence makes naive row-level independence inappropriate. These are screening rules, not multiple-comparison-adjusted significance tests.

Recorded combined new list-price spend is **$0.1208743**, below the shared $3 cap: routing $0.1043457, support $0.0165286. Input tokens were 1,043,457 and 165,286; output tokens and cache reads/writes were zero. Costs use observed usage and verified list prices, not an invoice.

**DECISION (D-075): no adoption in the live agent.** Preserve both negative results. Do not conclude that Decisions is generally unsafe, that it cannot be useful with a differently registered policy, that lower component latency improves the whole agent, that these AI labels are human truth, or that this trial tested planner gather/finish, tool arguments or an end-to-end swap. New prompts, thresholds, samples or judge timings would require a separately approved registration, not a rerun to rescue these screens.

## Verification

The implementation checks previously recorded 43 passing tests and one Wilson endpoint failure; after fixing the exact endpoint, the 16-test analysis suite passed. Documentation and rights checks passed at that implementation handoff. Final reporting/deck checks are recorded in the task handoff after execution; no unexecuted check is presented as passed. Public support outputs contain IDs, labels, probabilities and operational metadata, never claim or passage text.
