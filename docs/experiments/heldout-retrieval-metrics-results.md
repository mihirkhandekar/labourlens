# Retrieval on the original test and fresh questions: results

**MEASURED RESULT, 3 November 2026.** I ran the nine registered configurations on corpus v3.1, without changing gold or selecting a new configuration. [Registration](heldout-retrieval-metrics.md); [metrics and provenance](../../experiments/eval/heldout-retrieval-20261103-paid/metrics.json). Of 31 original test questions, 18 qualify as answerable text cases; of 65 fresh questions, 34 qualify. No eligible gold passage IDs are unresolved. Structured-only and non-answer cases are excluded by the registered eligibility rule.

## Every configuration

Strict hit@8 examines the first eight distinct context passages built from the first eight chunks, preserving context deduplication. Chunk hit@8 counts a gold passage anywhere in those eight chunks. MRR@10 uses the first relevant **chunk**, not passage rank.

| Configuration | Original strict hit@8 | Fresh strict hit@8 | Original chunk hit@8 | Fresh chunk hit@8 | Original MRR@10 | Fresh MRR@10 |
|---|---:|---:|---:|---:|---:|---:|
| BM25 | .167 | .500 | .389 | .912 | .231 | .545 |
| Dense | .111 | .500 | .278 | .824 | .150 | .497 |
| Hybrid | .167 | .500 | .444 | .882 | .266 | .618 |
| Hard period/release filter (R1a) | .167 | .500 | .778 | .912 | .342 | .624 |
| Soft bonus (R1b) | .167 | .500 | .667 | .912 | .327 | .625 |
| Soft bonus, half weight | .167 | .500 | .667 | .912 | .301 | .625 |
| Soft bonus, double weight | .167 | .500 | .722 | .912 | .343 | .625 |
| Rerank only (R2) | .556 | .941 | .722 | .971 | .657 | .887 |
| Filter then rerank (R3) | .778 | .941 | .889 | .971 | .778 | .887 |

| Paired R3 minus hybrid | Original, n=18 | Fresh, n=34 |
|---|---|---|
| Strict hit@8 | +.611 [.389, .833]; 11 better, 0 worse | +.441 [.294, .618]; 15 better, 0 worse |
| Chunk hit@8 | +.444 [.222, .667]; 8 better, 0 worse | +.088 [.000, .206]; 3 better, 0 worse |
| MRR@10 | +.512 [.326, .684]; 13 better, 0 worse | +.270 [.141, .408]; 15 better, 1 worse |

Intervals are 95% percentile case bootstraps, 2,000 resamples, seed 0. The JSON also records each arm's marginal intervals. There is no multiplicity-adjusted confirmatory significance claim. Rerank failures were zero in both sets for both reranked arms. New rerank usage cost was **$0.0784768**, about $0.078; this is recorded usage, not a provider invoice or the total project bill.

## Reading

The retrieval improvement from filter then rerank holds on both question sets under the strict passage metric. BM25 is strong on fresh questions: its chunk hit@8 of .912 exceeds hybrid's .882. Rerank-only and filter-then-rerank scores tie on fresh questions, so these results do not establish an added filter benefit there.

The existing two-run end-to-end comparison shows no demonstrated answer-status gain on either set. Taken together, retrieval was not the binding constraint for these questions on the measured metrics. This is an observation across the results; I did not investigate a cause per question. These literal-question retrieval diagnostics do not measure the model-rewritten queries used inside the agent.

## Limits

The original 31 overlap development evidence (25 of 31 in the published audit), making them optimistic. The fresh 65 are only partly independent: some sources and questions were new, but design, shared corpus and later diagnostic reuse limit independence. Gold evidence IDs were AI-drafted and signed off by one reviewer. The text subsets are small, and case-bootstrap intervals omit reranker sampling and gold uncertainty. Neither set is now a pristine confirmatory test. The run fills the retrieval-measurement gap; it does not establish an end-to-end answer gain, independent generalisation or full answer correctness. Frozen result files are unchanged.
