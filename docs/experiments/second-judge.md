# Second-family judge check — advance declaration (2 Nov 2026)

**DECISION / owner-requested implementation, D-062.** Written before xjudge code or paid calls. Purpose: does another model family agree with `gpt-6.1-terra` on claim support, reference-fact coverage and contradiction? This does not change generation, retrieval, gold or frozen evaluations.

## Controlled comparison

Use Anthropic Messages API model `claude-sonnet-5-5` (constant in code; override `LABOURLENS_XJUDGE_MODEL`, recorded in outputs). Availability is not yet probed. Reuse `prompts/judge_v1.md`, `harness.judge_input` and `harness.JUDGE_SCHEMA` verbatim. Anthropic forced `judgement` tool use transports this identical JSON schema; no tool is executed. This provider-specific structured-output mechanism is a residual difference, not a different rubric. Validate exact claim/fact indices and allowed labels locally; reject truncated or malformed output. No repair prompt or changed rubric.

**Pre-paid adapter amendment (2 Nov):** after the free dry-run, official [model IDs](https://platform.claude.com/docs/en/models/overview) confirmed `claude-sonnet-5-5`; official [structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) lists support for native `output_config.format` JSON schema. Use that native constrained-output transport instead of the initially proposed forced tool, preserving the identical schema/prompt and avoiding thinking/tool-choice incompatibilities. No prefill, tool or rubric change is needed; no paid result was read before this amendment.

## Sample fixed before results

Run 1 only: development `agent-dev-FIN-{r3,hybrid}`, original test `agent-heldout-FIN-{r3,hybrid}`, fresh `agent-heldout-FINV2-{r3,hybrid}`. Exclude FIN2. Four arms: two generators (`gpt-6-luna`, `gpt-5.6-luna`) times two retrievals. For each generator, pool the three sets and restrict to cases answered with claims in **both** retrieval arms. Select 60 case IDs without replacement, seed **20261102**, proportional largest-remainder allocation by `(question set, family)`, deterministic sorted strata and IDs. Use the exact same IDs in r3 and hybrid (120 calls per generator, 240 total before identical-payload cache reuse). Separate generators may have different eligible populations. Refuse a short population rather than silently lower n. This conditional sample excludes asymmetric answering and does not estimate behaviour accuracy. Record populations, allocations, IDs, input hashes and gold hashes; no resampling after seeing verdicts. Existing first-judge caches must match their input fingerprint; never call OpenAI or silently substitute missing judgments.

## Analysis and problem flags

Report pooled per-claim raw agreement and Cohen kappa on supported/partial/unsupported (align by index); per-answer raw agreement and kappa on any unsupported claim and any contradicted reference fact (contradiction denominator: answers with facts). Give disagreement IDs/label pairs grouped by family, not source quotations or judge notes. Report each arm's pooled supported/all-claims and covered/all-facts ratios under both judges. On paired IDs report r3-minus-hybrid pooled rate differences and mean per-answer paired differences under both judges, overall and by question set. A kappa below **0.4**, or a strictly positive/negative paired difference changing sign between judges, is a problem requiring explicit discussion, not a reason to select a preferred judge. Zero versus nonzero is reported separately, not called a sign flip. Undefined kappa (constant labels) is labelled undefined. No significance or equivalence claim.

## Cost, rights and operational boundaries

**VERIFIED FACT:** official [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing) fetched 2 Nov 2026 lists Sonnet 5.5 standard input $2 and output $10 per million tokens. Store in `specs/prices.yaml`; no discount assumed. Token usage times list prices is an estimate, not an invoice. Unpriced model overrides report tokens only on dry-run and refuse paid execution because a dollar cap cannot be enforced without verified prices.

Dry-run makes no API calls and prints token estimates (UTF-8 bytes/3 plus schema/tool allowance, estimated output 1,000 tokens/call; not a tokenizer or price guarantee). Paid execution reserves a conservative per-attempt bound using input bytes plus 4,096 overhead tokens and max output 6,000 before every attempt, including retries. Abort before a request if reservation would exceed `--max-usd`; successful usage replaces its reservation with measured token cost. Uncertain failed attempts retain their full reservation. This is an application-side list-price cap, not a provider billing limit. Three attempts maximum, 180-second timeout each, exponential backoff for transport/429/5xx only. No unbounded repair. Abort on unexpected usage above reservation.

Key is read only from `ANTHROPIC_API_KEY`; no .env reading, key printing or response-body error logs. Raw outputs/cache stay under gitignored `data/runs/xjudge/`. Public `experiments/xjudge/<id>/` contains only IDs, hashes, labels, counts, rates and summaries. Never overwrite an experiment ID, including an aborted run. New ID may reuse content-addressed successful calls. Cache costs are distinguished from new spend.

**Not claimed:** human review, independent ground truth, a second generation run, full-population coverage, unseen generalisation, repeated-run variance, or exact invoice cost. Same AI-drafted gold and selected answered cases remain limitations. No paid result exists at declaration time.

## Parent commands (key already exported privately)

```bash
uv run labourlens judge-xfamily --experiment sonnet55-FIN-s60-20261102 --dry-run
uv run labourlens judge-xfamily --experiment sonnet55-FIN-s60-20261102 --max-usd 5
uv run labourlens judge-xfamily --experiment sonnet55-FIN-s60-20261102 --summary
```

The third command reads the saved paired/agreement summary only; no model calls or rewrites. If capped or failed, inspect status; use a new experiment ID to continue with cached calls, never overwrite an existing ID.

## Pre-paid continuation amendment — 2 Nov 2026

Written after inspecting the aborted first attempt and **before continuation code or any further paid calls**. This is a post-observation operational amendment, not the original protocol. The immutable first ID completed 53/240 items. Its next cached response, `DEV-316`, primary generator, hybrid, returned **four claim labels for three claims**, indices `[0,1,2,2]`; both labels for index 2 were `partial`. It returned both required fact labels `[0,1]`. No label was actually omitted: the validator's generic message also covered overproduction. Output usage was **211 tokens**, far below 6,000; the adapter had accepted only a normal `end_turn`. There is no observed output truncation, so **retain max output 6,000** and do not deduplicate or impute labels.

For incomplete, duplicate, extra or otherwise invalid claim/fact indices, permit **one fresh semantic retry with exactly the same system prompt, user payload, JSON schema and token limit**, no corrective instruction. Transport retries retain their existing independent bound and cap accounting. Preserve the initial cache file unchanged; put the retry in a separate content-addressed `.retry1.json` file. Successful original caches remain reusable under the new experiment ID. Record attempt token/cost usage and the semantic retry count separately from item counts.

If the retry still fails complete-index validation, record the item as **`judge_omitted`** (the umbrella category includes omitted, duplicated and extra indices), with expected/returned counts, indices and a reason code only. Never manufacture verdicts, deduplicate them or silently drop the item. Publish these items as a separate disagreement type by arm and family. **Any `judge_omitted` item is a protocol problem**, alongside kappa below .4 or a nonzero sign flip.

Claim/answer label agreement and paired arm rates use only case IDs with valid judgments in **both** arms; explicitly report sampled, valid, omitted, excluded-pair and analysed-pair counts by generator and question set. This preserves the same paired population for both judges instead of comparing different denominators. Omission counts remain on all 240 sampled items; every excluded partner is identified and not counted as an omission itself. Results are conditional on valid pairs and carry an explicit incompleteness warning when omissions exist. An operational HTTP/budget failure still aborts the run, not an omission label.

Continuation commands (new immutable ID; existing successful call caches reused):

```bash
uv run labourlens judge-xfamily --experiment sonnet55-FIN-s60-b-20261102 --dry-run
uv run labourlens judge-xfamily --experiment sonnet55-FIN-s60-b-20261102 --max-usd 5
uv run labourlens judge-xfamily --experiment sonnet55-FIN-s60-b-20261102 --summary
```

The original $3.318388 dry-run is a deliberately coarse token heuristic, not observed spending. Parent reported about $0.20 at the first abort; do not project an invoice from that partial sample.
