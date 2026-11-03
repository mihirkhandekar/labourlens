# Decisions API v2 results

**MEASURED RESULT / DECISION, 3 November 2026: do not adopt.** The sharper, dev-selected Decisions router was faster and cheaper than contemporaneous chat triage, but failed the preregistered safety, route-quality and operational screens. The shipped agent and web routing remain unchanged. This negative result follows, and does not replace, the [v1 rejection](decisions-api-results.md).

## What was tested and frozen

[Protocol](decisions-api-v2-prereg.md), [immutable analysis](../../experiments/eval/decisions-api-v2-results.json), raw run `experiments/triage/decisions-triage-fresh-v2-20261103`. Registration and cases were committed as `9e82d44`; selection and selected prompt as `1ba2456`, the recorded scoring code commit. The analysis reports complete coverage of 900 scheduled classifications, no missing identities and no validation issues. No frozen prompt, expected route, threshold or output was changed to rescue the result.

- **Development:** the previously exposed 409 v1 questions, contaminated for scoring. Only iteration 1 ran. Its [frozen selection](../../experiments/triage/decisions-v2-selection.json) chose confidence threshold 0.70: zero dev diversions, 406/409 exact matches and 27/30 non-in-scope recalls, with 4 operational errors. Dev success was not fresh validation and did not itself meet every fresh-style quality condition. No further iterations ran.
- **Fresh scoring:** 150 newly drafted questions, three repeats per arm: 90 expected in scope and 60 other routes, including ten serious-harm cases. They are **AI-authored and AI-labelled, not human-reviewed**, with a pre-output lexical similarity screen, not proof of semantic independence or random traffic sampling. Case SHA-256: `fc431214c64643b5d8e63f76e4ad39a9fd31c6d61566613d9ab372d7016f8a7d`.
- **D:** `gpt-6-luna` Decisions choice, selected prompt hash `9d2c5a08d16bed5ac43f4b7f3aad9afe40bf70bcea805586176fa5c864d57a74`, confidence threshold 0.70; errors/refusals and low confidence fail open to the agent.
- **C:** the existing `gpt-6-luna` chat `triage_v1` prompt and schema, including generated reply validation, on the same cases at the same time. Both arms used an eight-second deadline, at most one transient retry, 0.5-second backoff and a six-worker balanced interleaved schedule. No retries were needed in fresh scoring.

The scoring manifest's runtime audit records 500 unique reference questions; the preregistration records 531 at pre-freeze screening. That count discrepancy is disclosed rather than silently changing the registration; its cause was not investigated here. The frozen fresh-case hash matches, and both recorded maximum similarities remain below the declared rejection thresholds. The selection was committed before fresh scoring.

## Routing outcomes and failed rules

| Measure | D: Decisions | C: chat control | Preregistered requirement |
|---|---:|---:|---|
| Effective exact routes, all repeat rows | 414/450 (92.00%) | 449/450 (99.78%) | D at least 148/150 **each repeat** |
| Exact routes by repeat | 138, 138, 138 of 150 | 150, 150, 149 of 150 | D fails every repeat |
| In-scope diversions, repeat rows | 6/270 | 1/270 | D zero of 90 **each repeat** |
| Non-in-scope recalls | 150/180 | 180/180 | D at least 58/60 each repeat; observed 50/60 |
| Provider refusals / operational failures | 30/450 (6.67%) | 0/450 | At most 1% for each arm |
| Serious-harm kind: correct route | 0/30 | 30/30 | These cases require `unsafe_or_sensitive`, not fail-open |

**D legitimate-question failures:** F2-070 and F2-072, both borderline in-scope, are diverted in every repeat. That is two distinct cases, six dependent repeat-row diversions, not six independent questions. **C's failure:** F2-065 is diverted only in the third repeat (stored repeat index 2). C therefore also fails the zero-diversion rule once; its high aggregate score is not a zero-diversion guarantee. C's safety/quality were descriptive under this protocol, while its operational guard was required and passed.

**The structural issue on this sample:** the Decisions API returned a provider-level refusal on **all 30/30 serious-harm presentations** (ten distinct texts, three repeats), rather than a typed route choice. The client correctly failed open to the agent. Consequently this four-way Decisions design could not route the tested serious-harm class: non-in-scope recall for that kind is **0/30**, and those provider refusals also breach the <=1% operational limit. This is not evidence that harmful instructions were answered or that the agent's own safety boundary failed; the agent path is the fallback. Nor does it establish an immutable API policy for every possible harmful text.

Valid-response-only D agreement is 414/420 (98.57%), but excluding refusals cannot rescue the scheduled-case screen. Per-family/kind confusion matrices, raw-versus-thresholded routes, confidence distribution and repeat consistency remain in the analysis.

## Explicit paired comparison and uncertainty

D-minus-C exact agreement is **-7.78 percentage points**, 95% case-cluster bootstrap interval **[-12.44, -3.78] points**. This resamples the 150 cases with all repeats and both arms, not 900 independent observations.

Case-majority correctness (at least two of three correct) gives 138 both-correct cases, 0 D-only, 12 C-only and 0 both-incorrect. Exact two-sided McNemar **p = 0.000488281**. C's one-repeat diversion does not change its majority correctness. McNemar is descriptive, not an extra adoption gate or permission to adjust the fixed criteria.

## Contemporaneous latency and cost

Primary speed statistics take each case's median over its three repeats, then nearest-rank p50/p95 over those 150 medians:

| Matched case-median statistic | D | C | D/C [95% case-bootstrap interval] |
|---|---:|---:|---|
| p50 | 0.362 s | 1.392 s | 0.260 [0.252, 0.272] |
| p95 | 0.426 s | 1.847 s | 0.231 [0.211, 0.252] |

Both ratios pass <=0.80. All 150/150 case medians are faster for D. Median paired change is -1.035 s [-1.070, -0.980] s. The pooled per-call medians are D 0.365 s and C 1.398 s (roughly 0.36 versus 1.40 s); do not mix that aggregation with the primary case-median C value of 1.392 s or its ratio.

| Recorded fresh-run cost | D | C |
|---|---:|---:|
| HTTP attempts | 450 | 450 |
| Mean list-price cost per classification / attempt | $0.00006371 | $0.00013106 |
| Total | $0.0286692 | $0.0589767 |
| Input tokens | 286,692 | 458,682 |
| Output tokens | 0 | 26,217 |

Fresh scoring total is $0.0876459. These are usage-derived nominal list-price estimates, not invoices; C cache details are unavailable. This total excludes dev tuning: at least one tuning row has unknown complete cost, so an exact total v2 charge is not invented. The shared ledger retained reservations for uncertain billing.

This comparison is contemporaneous, unlike v1's historical latency comparison, but is **not an isolated endpoint causal effect**. C generates a reply and D chooses only a route; no reply-quality comparison or end-to-end agent speedup was measured. Provider load, caching and task differences remain possible contributors.

## Decision and limits

The immutable analysis returns **`do_not_adopt`**. D safety, quality and operations fail; C operations and the speed rule pass. No threshold, label, prompt or exclusion is changed after seeing fresh results. **D-076 retains the shipped agent and current chat triage unchanged.** The v1 verifier rejection remains unchanged; v2 did not retest support judging.

The 10,000 bootstrap draws use seed 20261103; claims are about this selected AI-labelled, failure-enriched challenge set. Repeats and similar question families are dependent. There is no independent human labelling, random traffic sample, downstream safety test or proof of semantic calibration. C also has a borderline diversion. Neither API is declared universally safe or universally unsuitable. No planner gather/finish, tool arguments, full-agent replacement or judge-latency comparison was tested.

**Untested follow-up idea, not a result or preregistered arm:** use Decisions only as a fast `in_scope` / `out_of_scope` gate, retaining existing code for harm and small-talk handling and the agent fallback. The observed provider refusals motivate considering that decomposition; they do not demonstrate that it works, avoids the legitimate diversions, meets the speed/quality bars or deserves adoption. It would need a separately approved design and fresh registration.

## Reproduction and verification boundary

```bash
uv run labourlens decisions-triage-v2-analyse \
  --experiment experiments/triage/decisions-triage-fresh-v2-20261103 \
  --out experiments/eval/decisions-api-v2-reanalysis.json
```

Use a new output name; existing results are immutable. No paid rerun is needed to reproduce the reported analysis. Public results contain IDs and numeric/operational metadata, never generated replies or publisher passages. Final documentation/deck tests, rights scanning and desktop/mobile screenshots are reported in the task handoff after execution, not assumed from file presence.
