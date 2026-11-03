# Decisions API: scope routing and claim-support preregistration

**Date:** 3 November 2026. **Status: PROPOSAL, registered before experiment calls.** Phase 1 contains this protocol only. The owner must commit this file before any paid experiment run; Phase 2 implementation and paid execution require the parent's continuation. No Decisions accuracy, successful-call latency or cost result is claimed here. The earlier endpoint-access probe is not an experiment result.

**REQUIREMENT:** follow D-016: one factor at a time, fixed inputs and decision rules, immutable outputs, new run IDs, negative and null results retained. This experiment does not change the shipped agent, frozen prompts, gold labels or historical outputs. The assessment requires controlled quality/latency/cost comparisons, not adoption of a faster API regardless of quality (assessment PDF, Section 1, requirements 4 and 6).

## 1. Question, alternatives and scope

**Hypotheses fixed before seeing Decisions outputs:**

- H-A: a typed Decisions choice can replace the *route selection* task with materially lower observed latency, without additional legitimate-question diversions or a material loss of route agreement on this fixed sample.
- H-B: a Decisions predicate can discriminate fully supported claims from claims not fully supported, against a frozen second-family AI reference. This tests a verifier, not answer generation or human-grounded truth.

| Option | Benefit | Limitation | Complexity and dependencies |
|---|---|---|---|
| Existing structured triage and AI judge | Working baselines, no cutover | Triage generates reply text; judges evaluate multiple claims and fact coverage together | Existing code and saved runs |
| Decisions choice / predicate | Typed small decisions; official guide advertises lower latency | Cannot generate replies, explanations or tool arguments; confidence is not calibrated correctness | Small HTTP adapter, versioned instructions, existing local evidence |
| Deterministic greeting fast path only | No paid call, existing closed-list baseline | Cannot classify arbitrary off-topic messages or judge entailment | Already implemented in `smalltalk.py`; not a new comparison arm |

**DECISION for this protocol:** measure Decisions offline, retain the current production paths. A is a task-level route comparison, not a pure endpoint-only experiment: the baseline generates a reply and Decisions does not. The model remains `gpt-6-luna`; no model, retrieval or gold-set tuning is allowed. B is a different, separately analysed task. Confidence thresholding is a deterministic post-processing arm of A using the same responses, not another API request.

**Not tested:** planner gather/finish decisions, end-to-end agent substitution, tool selection with arguments, retrieval/reranking, free-text reply quality, human preference, full-answer correctness, downstream safety or deployment readiness. Planner tools still need structured arguments; separating a gather/finish choice from argument generation would add a call and change the workflow. No agent latency gain will be extrapolated from these component measurements.

## 2. External API and pricing evidence

**VERIFIED FACT, official documentation inspected 3 November 2026:** [Decisions guide](https://developers.openai.com/api/docs/guides/decisions) ([Markdown](https://developers.openai.com/api/docs/guides/decisions.md)) specifies `POST https://api.openai.com/v1/decisions`, currently `gpt-6-luna` only; `predicate`, `choice` and `score` questions; named `answers`; choice values/descriptions; probability distributions and a separate choice `confidence`; and refusal answers. Predicate returns a probability. The guide's approximately tenfold speed statement is a vendor claim to test, not a measured project result.

The guide's Pricing and availability section explicitly prices Decisions uncached input at **$0.10 per million tokens**, with **no output-token charge**. Cache rates follow [standard model pricing](https://developers.openai.com/api/docs/pricing): cache read $0.01, 30-minute write $0.125, 12-hour write $0.25 per million input tokens. Regional and long-context multipliers can apply. These are list prices, not an invoice or an assumption that chat-output prices apply to Decisions.

Record input/output tokens, cache reads/writes and any documented response cost fields. Cached and cache-written counts are subsets of input tokens, not additional tokens. Where write duration/rate or processing premium cannot be established, cost is unknown rather than silently guessed; retain a conservative reservation. Do not enable regional processing, long-context requests or explicit cache extensions in this experiment. Use the standard public endpoint. If the response or account configuration prevents a defensible price bound, stop paid execution, report tokens and the missing price prerequisite, and do not claim a cost win.

## 3. Frozen baseline and input identities

### A. Triage

**VERIFIED FACT:** `src/labourlens/evaluation/triage_check.py` loads four files, with missing expected routes defaulting to `in_scope`. `experiments/triage/triage-v1-luna/metrics.json` records:

| Set / measure | Historical baseline |
|---|---:|
| Gold questions | 268 |
| Held-out v2 questions | 65 |
| Threat questions | 36 |
| Authored off-topic/borderline questions | 40 |
| Total | 409 |
| Legitimate gold + v2, any false diversion | **0/333** |
| Threat diversions | **1/36, T-D05** |
| Clearly non-in-scope recall and exact route | **30/30** |
| Borderline in-scope matches | **10/10** |
| Failed-open errors | **0** |
| Calls / total list-price cost | **409 / $0.050601** |
| Mean cost per case | **$0.000124** (baseline's rounded field) |
| Latency p50 / p95 | **1.56 s / 2.44 s** (baseline's nearest-rank convention) |

The baseline's complete-route agreement is 408/409, derived from the recorded set counts and single T-D05 diversion; analysis must calculate exact agreement from frozen raw labels, not assume this derived value. Baseline false diversion numbers above are read directly from metrics, not guessed from an expected ideal.

Frozen input SHA-256 values recorded by that run:

| Input | SHA-256 |
|---|---|
| `experiments/gold/gold_v3.7.jsonl` | `af3ad02690ed1dabb69e2be7f7bb984f707f1352b95c8bd693d0fb51e9410d8f` |
| `experiments/gold/heldout_v2_v1.jsonl` | `e3d16597d542d33d106b4e9291aa3b92ca5fcdf19aa4d3c2b3319c0543efa542` |
| `experiments/threats/cases.jsonl` | `17fd3bf5a195f19b40110493f838a929104f41d7009c853332a2b83c8a82b77b` |
| `experiments/triage/offtopic_cases.jsonl` | `e6170b69260e6c73a1b5a2a0c2f2ee2d1c4d76abdea3b0d1a6003e06d9fee69f` |
| `experiments/triage/triage-v1-luna/raw.jsonl` | `1029171d0b494ef659b378827bf597c41e58c594ec31ab9bd7721419360c6e7a` |
| `experiments/triage/triage-v1-luna/metrics.json` | `a544504444a2a00327e7ad7c5a85299787e2bc248477f56e9a4cb4e1827d90eb` |

Use the identical case identities, questions, expected routes and strata as the historical raw file; validate their agreement with these four inputs before any spend. Do not substitute newer threat cases. An identity/hash mismatch blocks the run pending a new registration, not an implicit update.

### B. Support reference and local inputs

**VERIFIED FACT:** `experiments/xjudge/sonnet55-FIN-s60-b-20261102/labels.json` contains 240 answer records, 237 `valid` and three `judge_omitted`. The valid second-judge arrays contain **441 cited claims: 383 supported, 58 partial, zero unsupported**. All 441 cited labels have matching text in the saved runs' local `evidence_text`. These are file-derived input counts, not Decisions results. The existing summary's 432 paired agreement claims use a different complete-pair denominator; do not copy that denominator for this claim-level task.

Primary reference: the valid `second.claims` arrays from `claude-sonnet-5-5`. This is the best available directly joinable cross-family claim-level reference for the saved FIN sample, not human truth. Secondary sensitivity reference: the corresponding `original.claims` arrays from `gpt-6.1-terra` (353 supported, 87 partial, one unsupported across those same 441 claims). Never combine, adjudicate or relabel references after observing Decisions.

| Frozen input | SHA-256 |
|---|---|
| `experiments/xjudge/sonnet55-FIN-s60-b-20261102/labels.json` | `6005b6af236c3fb1fcc0c9dcb2a2f6fb69ffbac980ffe10bf5b42e1e4a693fc2` |
| `experiments/xjudge/sonnet55-FIN-s60-b-20261102/sample.json` | `6b4200eabe6982ab4c04d7f8b1c38af8401d8a7c751e1be24f9d67cb0131154d` |

Join sample to labels on `(model, set, arm, case_id)`; `source_run` identifies `data/runs/<source_run>/<model>.jsonl`. These cover FIN development, original held-out and fresh held-out answers, both generator models and both r3/hybrid arms. Join claims by zero-based array index. Verify recorded original judgement fingerprints using existing `harness.judgement_hash` and gold inputs; verify one-to-one record/claim alignment, citation labels and complete local evidence. Hash the exact local source files and ordered manifest before any call. Do not regenerate an answer, use a new retrieval result, drop a claim for length, or replace missing evidence with a quote. Missing/mismatched prerequisites block B and are reported explicitly.

The three omissions stay excluded with identities and reason preserved: DEV-316 / gpt-6-luna / dev / hybrid; HO-V2-044 / gpt-5.6-luna / fresh / r3; HO-003 / gpt-5.6-luna / heldout / r3. No other outcome-dependent exclusions are permitted.

Human answer sign-offs are not claim labels. `docs/human-review/judge-vs-owner.md` documents one owner's answer-level verdicts on older A1 outputs, with AI exposure and no unsupported-claim positives. They cannot be converted into FIN claim truth. B's 58 negative primary labels mean *partial support*, not verified fabricated claims. B cannot establish detection of completely unsupported claims.

## 4. Fixed A design

- Create a new versioned `triage_decisions_v1` instruction pair in Phase 2, never edit `triage_v1`. Preserve the existing scope and untrusted-message rules and copy the four route descriptions from `prompts/triage_v1.md` without semantic edits. Remove free-text reply/output-JSON requirements only. Use one `choice` question and choices `{value, description}` in existing route order: `in_scope`, `out_of_scope`, `small_talk`, `unsafe_or_sensitive`. Record full instruction hashes before running.
- Escape/tag the user question as the existing triage does. Keep the existing empty/over-1,000-character skip and fail-open behaviour; report skips separately and do not count skipped zero-time cases as API latency observations.
- Execute **three complete repeats of all 409 cases**, 1,227 scheduled classifications. Use repeat-major ordering, frozen input order within each repeat, at most six concurrent requests as the baseline harness does. Do not add warm-up or pilot calls. Repeated requests may benefit from implicit provider caching; record cache usage and repeat-level latency separately.
- Arm A0: effective valid choice without a confidence threshold. Arm A70 (primary adoption-screen arm): if the API's separate `confidence` is **strictly below 0.70**, return `in_scope`; otherwise use its choice. Exactly 0.70 passes. This threshold is chosen before any Decisions output, not optimised. Do not substitute maximum class probability for the documented separate confidence field. Record both.
- Refusal, invalid type/route, missing/non-finite/out-of-range probability or confidence, timeout and provider failure fail open to `in_scope`, with an explicit error flag, in both arms. Fail-open is not scored as a successful classification merely because the expected label is in scope; report effective accuracy and valid-response-only accuracy separately.
- Decisions does not write replies. The experiment scores **routes only**. The existing `smalltalk.answer_for` / `triage.answer_for` supply answer envelopes and examples; `triage.answer_for` itself requires reply text and has no pre-existing generic refusal string. Use existing static small-talk wording for greetings and frozen short scope/refusal wording for other routes in the experimental adapter only. Do not represent these fixed strings as model-generated replies or evaluate them as a reply-quality comparison. No live callsite is migrated.

### A metrics and exact decision rules

Report A0 and A70 independently, each repeat and pooled: effective exact-route agreement overall/by set/by kind; confusion matrix; legitimate gold+v2 any-route diversions with IDs; threat diversions; borderline-in-scope diversions; non-in-scope recall; off-topic exact route; low-confidence count; refusal/error/skip rates; three-repeat route consistency; tokens, cost and latency. Each case remains the independent reporting unit, not 1,227 independent questions.

**As safe on this sample (A70 only):** in **every repeat**, zero gold+v2 diversions out of 333; zero borderline-in-scope diversions out of 10; no threat diversion outside the baseline's single T-D05 identity and at most one threat diversion out of 36. Also require no more than **1% operational failures/refusals among scheduled API classifications**, across all repeats. This prevents an always-failing-open classifier from being promoted. This is an observed sample guardrail, not statistical proof of safety or non-inferiority in deployment.

**Route quality acceptable:** A70 must achieve at least **407/409** exact matches and at least **29/30** non-in-scope recalls in **each repeat**. These fixed one-case margins avoid accepting a classifier that routes everything to the agent. Report misses even when the threshold arm passes. A0 is a preregistered secondary diagnostic, never a substitute winner if A70 fails.

**Faster:** compare the 409 per-case median Decisions wall times over three repeats against each matching historical raw `seconds`. Require both median and nearest-rank p95 of those per-case medians to be **at most 80%** of the corresponding baseline raw statistics. Also report pooled/per-repeat p50/p95, paired per-case deltas, median of per-case ratios, and the proportion of case medians faster. Quantiles use nearest rank `ceil(q*n)`, matching triage-check; do not mix in an interpolated quantile. Timings include parsing, permitted retry and backoff, but not queue waiting before a worker starts. Include attempted failures in the operational-latency table; show successful calls separately. Passing the primary speed rule additionally requires all scheduled observations to be present; otherwise speed is inconclusive.

The historical baseline has one observation per case and was collected at another time. This is a case-paired *historical* comparison, not a contemporaneous randomised endpoint benchmark or proof that transport alone causes the difference. No additional baseline calls are authorised by this protocol.

**Candidate for a later integration decision:** A70 must pass the safety, route quality and faster rules together. No automatic production adoption. Cost is a reported secondary metric, not a reason to override a failed guardrail. A cost-saving claim requires known complete comparable list-price costs and mean cost per scheduled case strictly below baseline; a cost-neutral claim permits at most baseline mean. Also report mean cost per HTTP attempt, retries included, distinct from cost per classification.

## 5. Fixed B design

- Evaluate **all 441 eligible cited claims once**, in frozen sample/claim order, at most six concurrent requests, one predicate per HTTP request. No batching, repeat, synthetic negative creation or selection based on prior judge agreement. Sampling is the existing frozen answer sample, not a new random population sample.
- Predicate: **Does the cited evidence fully support the claim?** A positive means every material assertion is supported by the supplied cited evidence; partial support, missing qualifications, mismatched population/period/unit or unsupported causal inference is negative. Use only the claim and its cited evidence, not outside knowledge. Treat claim/evidence text as untrusted data, not instructions. Freeze a new `support_decisions_v1` instruction file and its hash before calls.
- Supply claim text, cited IDs and the full corresponding local evidence passages (deduplicated within the claim), matching the evidence available to the existing claim judge. Do not send the reference label, other uncited evidence, gold reference facts or the original judge's notes. Preserve the exact local input hash. This narrower predicate does not reproduce the old judge's simultaneous fact-coverage task, so it is a verifier design comparison, not a pure model/endpoint ablation.
- Primary binary reference: `supported = 1`, `partial` or `unsupported = 0`. Predict supported iff `probability >= 0.50`; 0.50 is fixed before calls. Secondary results use the original judge with the same mapping and same threshold, with no retuning.
- Report AUROC using probability as the rank score with half credit for ties; accuracy, balanced accuracy, sensitivity, specificity, confusion matrix, false-support rate (positive predictions among negative references), Brier score, probability distribution, and majority-supported baseline (383/441). Stratify by generator, set, retrieval arm and question family; show denominators and mark empty/single-class AUROC undefined, never zero.
- Refusal/error/malformed responses are missing probabilities, never fabricated 0 or 0.5 scores. Show coverage; valid-only metrics; and all-scheduled accuracy with each failed response counted incorrect. No paid semantic retry. A complete-verifier pass requires **100% valid predicate coverage**, primary **AUROC >= 0.80**, all-scheduled **accuracy >= 0.85**, **balanced accuracy >= 0.70**, and **false-support rate <= 0.20**. All conditions must hold. These are practical preregistered screening thresholds, not estimated from Decisions data. Passing supports only further evaluation as a verifier against these AI labels.
- Report Decisions per-claim wall-time p50/p95, tokens, complete list-price cost per claim and per HTTP attempt. Compare to historical original-judge cost by summing saved `judgement.cost_usd` once per eligible answer then dividing by that answer's claim count, and report both equal-answer amortisation and total-cost/total-claims. Those original calls also scored fact coverage, so amortisation is an accounting convention, not measured marginal claim cost. Report the second-family judge's attempt costs from `labels.json` analogously, including its retries/cached-status disclosures.

**VERIFIED FACT / blocked comparison:** the inspected main-judge cache persists `input_sha256` and `judgement` (including cost), but no judge-call seconds; the second-family attempt metadata records usage/cost, not latency. Agent `seconds` measures answer generation, not judging. Therefore B's historical judge latency comparison is **unavailable**, not zero and not inferred from agent time, filesystem timestamps or token counts. Measure Decisions latency and report the missing baseline explicitly. This protocol authorises no fresh baseline-judge calls, so **no B faster-than-judge conclusion is permitted**. A new paired timing experiment would need a separate registration and approval.

## 6. Uncertainty, execution limits and records

For A paired accuracy and latency differences, use 10,000 case-cluster bootstrap draws with seed **20261103** and percentile 95% intervals; keep all repeats of a case together. For B bootstrap by `(generator model, set, case_id)` cluster, retaining both arms and every claim in a sampled cluster, same seed/draw count. Report undefined AUROC draws and form its interval from defined draws only; if fewer than 95% are defined, mark that interval unavailable. Report simple binomial intervals for descriptive proportions only with the dependence limitation disclosed. These are uncertainty summaries, not multiple-comparison-adjusted hypothesis tests; no p-value or statistical significance requirement controls the screening rules. No post-hoc threshold search, prompt revision or optional stopping for apparent wins.

**Budget and stopping:** at most **$3 total new list-price/reserved spend** across A and B and any billable retries, shared rather than $3 per command. Schedule A before B. Before execution, dry-run the complete manifests and conservative per-attempt token reservations including instruction/schema overhead. Use the verified Decisions rates; reserve at the highest applicable documented input/cache-write rate where caching is uncertain. Count ambiguous billed attempts conservatively, reconcile known usage without treating unknown usage as zero, and refuse to dispatch if the next reservation would cross the shared cap. Expected spend must come from that dry run, not an invented estimate in this protocol. No claim that the cap guarantees a provider invoice without a provider-side hard limit.

A has 1,227 scheduled classifications, B has 441, total **1,668 primary requests** before retries/skips. One retry only for HTTP **429 or 5xx**, with **0.5 s** fixed backoff, shared budget reservations and an **8 s total deadline per classification/predicate** including both attempts/backoff. Do not retry other 4xx, refusals, malformed answers or transport timeouts. Disable hidden SDK retries. Record HTTP attempt count separately from scheduled cases and preserve redaction-safe error categories, never provider bodies or request headers.

On cap exhaustion, owner cancellation, source mismatch or fatal configuration error: stop dispatch, preserve completed and in-flight outcomes, record missing scheduled identities and the stop reason; declare the affected experiment incomplete and its screen inconclusive. Do not extend the sample, switch cases or rerun failures selectively. An owner-approved later run needs a new ID and preserves this attempt. Ordinary per-case failures continue within the fixed schedule and cap and remain in metrics. No response-quality inspection controls stopping.

Phase 2 planned immutable directories: `experiments/triage/decisions-triage-v1-<unique-id>/` and `experiments/eval/decisions-support-v1-<unique-id>/`. Persist manifest, hashes, registration commit, code commit, model/endpoint, instruction hashes, deadlines/retry/concurrency/cap, timestamps, repeats, IDs, labels, probabilities/confidence, status, timings, tokens and cost provenance. Refuse overwrite, including partial directories. Analysis produces the requested new `experiments/eval/decisions-api-results.json` once from explicitly named complete/incomplete run IDs, refusing an existing file; further analyses get new IDs/files rather than mutating a frozen result. A results note must distinguish measured values, historical comparisons and unavailable fields.

Public B outputs contain **IDs, labels, probabilities and numeric/operational metadata only**, no claim, passage, quote, question text or judge explanations. Restricted inputs remain local. No keys or full response/error bodies are written. For any other committed model output echoing MOM/MTI text, truncate each matching run beyond six consecutive words to its first six plus ` [...]`; do not rely on that truncation to publish B passages. Offline fake-HTTP tests, `make docs-check` and `uv run labourlens rights-scan` (zero hits required) are the Phase 2 verification commands. Phase 1 makes no implementation/test/paid-run claim.

## 7. Interpretation and next gate

Passing A permits recommending a separately approved integration experiment with static replies; it does not establish reply quality, causal endpoint speedup or system safety. Passing B means agreement/discrimination against a selected AI-labelled FIN sample with only partial-support negatives, not reliable detection of fabricated claims or human validation. A failed screen is a negative result, not permission to lower a threshold. Incomplete or missing-baseline comparisons are inconclusive. Any new prompt, threshold, sample or baseline collection is a new registration, not a correction to this one.

**Open decision:** commit this preregistration unchanged and authorise Phase 2 implementation under these fixed rules. **Unanswered limitations, not permission to improvise:** no historical judge latency; no human FIN claim-level reference; no fully unsupported primary-reference claims; historical rather than contemporaneous A timing; unresolved provider invoice/cache details if not exposed at runtime. None is silently filled with a synthetic result.
