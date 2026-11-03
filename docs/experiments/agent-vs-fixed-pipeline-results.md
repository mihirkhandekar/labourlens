# Bounded agent versus fixed pipeline: results

**MEASURED RESULT, 3 November 2026.** I compared one fixed-pipeline run with two frozen agent runs on the same 237 development questions, using `gpt-6-luna`. [Registration](agent-vs-fixed-pipeline.md); [measured comparison](../../experiments/eval/agent-vs-fixed-pipeline.json). The saved decision is **agent development advantage** under the registered directional criteria. I did not run this comparison on the original test or fresh questions.

## Design and results

The fixed policy extracts at most one statistics request, always searches reports once with filter then rerank, and executes at most one lookup. It has no research loop or calculation tool. The answer prompt, evidence tools, validators and repair path are shared with the agent.

| Metric | Fixed, one run | Agent, first run | Agent, second run |
|---|---:|---:|---:|
| Behaviour accuracy | .8143 | .8861 | .9072 |
| False answers | 11 | 7 | 7 |
| Over-abstentions | 31 | 10 | 5 |
| Operational failures | 0 | 0 | 0 |
| Median latency, seconds | 15.27 | 15.06 | 13.64 |
| p95 latency, seconds | 28.33 | 35.43 | 34.11 |
| Recorded usage cost per question, USD | .002697 | .002841 | .002852 |
| Separate judge cost per question, USD | .000997 | .001039 | .001082 |

Behaviour accuracy measures expected answer status, rather than full answer correctness. The always-answer floor is .7679. Fixed minus agent is -7.17 points (case 95% interval [-12.24, -2.11], evidence-component interval [-12.44, -2.02], exact McNemar p=.0095) against the first run, and -9.28 points ([-14.36, -3.80], component [-14.47, -4.13], p=.0013) against the second. The agent's per-case two-run mean is .8966; fixed minus that mean is -8.23 points (case [-13.08, -3.38], component [-13.24, -3.35]). McNemar is undefined for the fractional mean. The agent adds no false-answer cases by count relative to fixed: 7 in either run versus 11.

## Content and arithmetic

The standard saved metrics retain the content scores, with different answered-case denominators where appropriate: [fixed](../../experiments/eval/agent-dev-FIXED1-r3/gpt-6-luna.metrics.json), [agent first](../../experiments/eval/agent-dev-FIN-r3/gpt-6-luna.metrics.json), [agent second](../../experiments/eval/agent-dev-FIN2-r3/gpt-6-luna.metrics.json).

| Metric | Fixed | Agent first | Agent second |
|---|---:|---:|---:|
| Calculation correctness, n=24 | .000 | .667 | .750 |
| Key-number recall, n=153 | .741 | .834 | .839 |
| Any gold evidence cited, n=189 | .725 | .820 | .841 |
| Judge-measured claim support | .795 (288 claims) | .833 (299) | .828 (326) |
| Judge-measured fact coverage | .731 (242 facts) | .752 (298) | .740 (312) |

Calculation correctness requires a deterministic calculation record, so fixed's zero follows mechanically from its tool policy. It does not measure the quality of its prose arithmetic independently. Claim and fact scores are same-provider AI judgments against AI-drafted references; differing denominators and selection of answered cases prevent a paired causal interpretation of these aggregate rates. Citation presence does not establish semantic support.

## Family slices

These are descriptive behaviour scores, with no family-level significance claim.

| Family | n | Fixed | Agent first | Agent second | Agent mean |
|---|---:|---:|---:|---:|---:|
| Factual lookup | 70 | .914 | .971 | .971 | .971 |
| Numerical comparison | 34 | .324 | .794 | .912 | .853 |
| Cross-source synthesis | 35 | .943 | .943 | .971 | .957 |
| Revision conflict | 19 | .895 | 1.000 | 1.000 | 1.000 |
| Ambiguity, insufficient evidence and causal overreach | 44 | .795 | .727 | .682 | .705 |
| Adversarial | 35 | .943 | .886 | .943 | .914 |

The fixed policy's weakest family is numerical comparison. Its absence of calculation records and repeated lookups is a design confound, declared in advance. The agent's weakest family is ambiguity, insufficient evidence and causal overreach; fixed scores higher there. I cannot attribute the overall gap to adaptive planning alone.

## Reading and limits

I retain the bounded agent on this development evidence: it scores higher in both paired comparisons and their mean, with fewer false answers and over-abstentions. The fixed arm is marginally cheaper per question and has a lower p95 latency, but its median is similar. The two agent runs flip 13 behaviour verdicts; a single fixed run gives no estimate of its own run-to-run variation.

This compares whole control policies, not LangGraph as a library or agents in general. The narrower extraction schema with an unchanged planner prompt can disadvantage fixed. Its mandatory search, fixed ordering, one-lookup limit, missing arithmetic and inability to recover through another research round travel together. Historical provider/runtime drift remains possible even with matching prompts, gold and corpus checks. Development-shaped questions, AI-drafted gold signed off by one reviewer, status-based scoring and the absence of original-test or fresh-question comparisons limit generalisation. Recorded usage estimates and judge costs are separate from a provider invoice. Existing frozen results remain unchanged.
