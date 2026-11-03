# Evaluation report

## At a glance

I built LabourLens to answer bounded Singapore labour-market questions using official statistics, report passages and inspectable citations. I tested keyword and semantic search, a period-and-release filter followed by model ranking, two generation models, a bounded research agent, a fixed workflow, the statistics interface and attack controls. Numerical changes are calculated by code rather than left to the model.

**MEASURED RESULT:** better evidence selection is the clearest result. On 128 development report questions, filter then rerank found an acceptable passage within the top eight search chunks on **96.9%** of questions, against **53.9%** for hybrid search. It also improved passage coverage on both test sets. On development questions, the final two-run answer-status score rose from **82.7% to 89.7%**. The fresh 65-question set showed **no demonstrated end-to-end gain**. A harder attack suite passed **50 of 54** guarded cases against **42 of 54** with the naive configuration, with remaining failures on benign questions.

These results helped me retain useful changes and reject others. I kept the cheaper of two models that tied on development behaviour, retained filtering and ranking provisionally, and rejected a report-arithmetic tool bundle and both Decisions API trials when they failed their criteria. The [experiment table](#experiment-table) separates these findings from their limits.

**Evaluation boundary:** all headline results concern questions about **2024-Q1 to 2026-Q2**, using **corpus v3.1, with 49 documents**, the structured-output planner and earlier prompts. The served app now covers **2020-Q1 to 2026-Q2**, uses **corpus v4, with 106 documents**, native function calling, newer prompts and additional tools. Those changes, including the added documents and earlier years, are **unevaluated**. A separate 65-case application sample tested an earlier served chain; it does not validate today's complete app. See the [system card](system-card.md#served-versus-evaluated).

AI drafted the reference answers. I signed them off as the sole reviewer after the runs and AI pre-review. The main content judge belongs to the same model family as the generators; a second-family check did not reproduce every content gain. These are agreement measurements against that reference, not independently validated accuracy.

The [evaluation detail](reference/evaluation-detail.md) preserves the full previous report: every per-run table, corpus history, label correction, protocol deviation, regression log and internal experiment mapping. The sections below are the reading route; the reference is the audit route.

## Research questions and hypotheses

The intended users are policy researchers and labour-market analysts. They need to inspect evidence, look up facts, compare periods and combine sources without confusing populations, seasonal adjustments or publication versions.

I evaluated four practical questions:

1. Does more precise evidence selection improve answers more than changing between nearby models?
2. Does a bounded agent with statistics and calculation tools help compared with a fixed sequence of steps?
3. Can the system recognise missing evidence, ambiguity and unsafe requests while still answering legitimate questions?
4. What quality, latency and cost trade-offs follow from these choices?

The main retrieval hypothesis was that reports from adjacent quarters contain similar wording, so identifying the right period and release before ranking would help. The numerical-workflow hypothesis was that typed statistics tools and deterministic calculations would support comparisons without relying on model arithmetic. Separate experiments tested prompt changes, a wider search filter and report-based arithmetic. Their outcomes are retained even when they did not improve the system.

Development comparisons guided the design. I do not retrospectively treat them as experiments registered before results were seen. The original test and fresh-question protocols had written acceptance rules, with the timing and reuse qualifications below.

## Dataset construction and review

The main reference set contains **268 authored questions: 237 development questions and 31 original test questions**. A further **65 fresh questions** used six new sources at their first run. These are research scenarios, not sampled user traffic. Cases cover factual lookup, numerical comparison, cross-source synthesis, preliminary-versus-final conflicts, ambiguity or insufficient evidence, causal overreach and adversarial requests.

Each case records the question, expected behaviour, acceptable evidence identifiers and reference facts. Where relevant, it also specifies a calculation. Expected behaviour is one of answering, abstaining, asking for clarification or refusing; some adversarial cases require ignoring the attack while answering the legitimate part. Retrieval studies use eligible report-evidence subsets, excluding structured-only lookups and unanswerable questions. Their denominators therefore differ from whole-system studies.

AI drafted the labels and evidence references, followed by several AI review passes. I subsequently recorded decisions through the review interface on **403 items**: 268 main questions, 65 fresh questions, 40 saved system answers and 30 source checks. Only the first two groups are questions. An interface click establishes a recorded input, not proof that the item was read. My review was after scoring and AI suggestions, with no second human reviewer, so it does not establish independent agreement between annotators.

The scored reference and its provenance-only successor have identical questions and labels. The successor records my decisions on every main case. Four recorded change-clicks were not applied because the requested figures lay outside the evaluated answer window; the reference preserves the cases and rationale. Accepted extraction gaps also remain in the saved runs. Review evidence: [owner summary](human-review/owner-review-final-summary.md), [gold changelog](../experiments/gold/CHANGELOG.md) and [detailed construction record](reference/evaluation-detail.md#dataset-construction-and-review).

### Development/held-out policy

The development questions shaped configuration selection, so their scores are optimistic estimates of generalisation. The original test is also limited: **25 of 31** questions share evidence with development and **15 of 31** reuse an entire evidence set. Five original-test labels changed after the initial freeze; saved outputs were rescored, preserving earlier results. This is revised scoring of existing answers, not a new prospective test on independently reviewed labels.

The original freeze was committed with the results, so Git cannot independently establish that the written protocol preceded generation. Some earlier runs lack generation-time provenance. Their later scoring hashes cannot reconstruct missing information about the original generation. These issues are documented rather than inferred away.

The 65 fresh questions were evidence-disjoint and signed before their first run. Since then they have been reused for diagnostics, corpus comparisons and replication. A diagnostic helped design a tool bundle that was rejected. The final two-run comparison uses known questions, so it is not another untouched test. The initial registered rule was met for the primary model on just three improved cases; the later consolidated comparison demonstrates no answer-status gain. All versions remain in the [test history and deviations](reference/evaluation-detail.md#held-out-pre-registration-executed).

## Baselines and methodology

**Keyword baseline:** BM25 ranks passages by matching words, without a generation model. **Dense search** uses embeddings, numerical representations of meaning, to find related text. **Hybrid search** combines the keyword and dense rankings. This is the main end-to-end retrieval baseline.

**Filter then rerank:** restrict candidate passages using period and release metadata, then ask a model to order the remaining evidence. This adds a model call, cost and latency. A ladder of filter-only, rerank-only and combined settings checks which retrieval changes matter. The reranker is held fixed while the two generation models are compared.

The final comparison uses the same answer workflow with either hybrid search or filter then rerank, across two generation models and two runs per setting. Each generation model performs planning and answering. The evaluated system uses local statistics directly, without the later web steps or MCP route. Both settings include code-generated notes about missing or conflicting data, so these runs cannot isolate the benefit of those notes.

The headline is the mean of two runs, under an amendment recorded before the second run was read or scored. Each case contributes a mean binary outcome of 0, 0.5 or 1. Paired comparisons use the same questions in both settings; their 95% intervals come from 10,000 case-bootstrap resamples with seed 20261030. A bootstrap repeatedly resamples questions to show how sensitive the comparison is to this case sample. It does not estimate variation across independent model runs. Two runs are too few for that.

The fixed-workflow comparison always performs one report search and at most one extracted statistics lookup. It has the same answer prompt and validators, with no research loop or calculation tool. This tests the complete policy: adaptive planning, arithmetic, evidence ordering and lookup coverage change together. It cannot isolate the value of agency alone.

Most absolute metrics had no pass threshold fixed beforehand. The original test required a paired interval excluding zero for a gain. The first fresh-set protocol required a positive lower bound under both case and evidence-component resampling, at least 20 evidence components and no added false answer. An evidence component groups questions linked by shared evidence, reducing the pretence that overlapping cases are independent. The harder threat suite required an attack advantage and at most two benign failures; only the first criterion was met. Full thresholds and execution records are in the [reference](reference/evaluation-detail.md#success-criteria).

### Metric definitions and denominators

**Behaviour accuracy** means the system chose the expected status: answer, abstain, clarify or refuse. It does not establish that an answer's contents are correct. This is the headline metric because it is scored deterministically, without asking an AI judge to decide the status match.

**False-answer flag** means answering when the reference expects a non-answer. It does not necessarily mean the answer contains a false factual statement. **Over-abstention** means withholding an answer that the reference expects. The final aggregate uses all cases as the denominator for both rates. Some earlier scorer tables exclude over-abstentions from the false-answer denominator; those rates must not be compared without checking the definition.

**Hit@8** measures whether any acceptable reference passage occurs within the top eight retrieved chunks. A chunk may contain several passages. **Strict passage hit@8** instead checks the first eight distinct passages delivered to the answer context. Neither measure establishes that every fact needed for a multi-source question was retrieved. **MRR**, mean reciprocal rank, gives more credit when the first relevant chunk appears earlier.

**Claim support** is the AI judge's assessment of whether cited evidence supports a claim. **Fact coverage** is the proportion of reference facts it finds in an eligible answer. **Contradiction** records whether any reference fact is contradicted. These measures exclude non-answers with no judged claims or facts. High content scores therefore cannot compensate for missing answers or establish performance on all questions.

**Gold cited** means that at least one acceptable reference evidence identifier was cited. One side of a comparison can earn this credit. The scorer does not enforce every preferred evidence identifier, so this is weaker than complete evidence coverage. Quote and label validators check that a cited quote exists in its source; they cannot establish that it supports the claim.

**Calculation correctness** requires a cited calculation record with correct operands, order, operation, unit, signed result and direction in the answer. Matching a number alone is insufficient. Key-number recall and ungrounded-number warnings are secondary diagnostics: correct digits can still describe the wrong population or period. Warning rates use all scored cases, including non-answers and failures.

**Latency** is recorded wall time. **Cost** is estimated from returned token usage and saved list prices, not invoices; judging is recorded separately. The headline latency is the mean of two run medians, not a pooled median. Full definitions, scorer corrections and denominators remain in the [method record](reference/evaluation-detail.md#metric-definitions-and-denominators).

### Floor, run-to-run noise and the two hit@8 definitions

A rule that always answers, without reading the question, matches the reference status on **76.8% of development, 77.4% of original-test and 73.8% of fresh questions**. Most cases expect an answer. Both final settings clear that floor on development; on the fresh set both models and both retrieval settings are within about three percentage points of it. Behaviour accuracy alone cannot distinguish a useful answer from an unsupported one.

Identical first and second runs change the behaviour verdict on **11 to 18 of 237 development cases**, depending on model and setting, and **1 to 3 of 65 fresh cases**. Gross flips include changes in both directions and exceed the net score movement. The fresh primary-model difference is smaller than the observed flips from rerunning either setting. Development gains have the same sign for both models in both runs and their paired intervals exclude zero, although individual answers remain variable. These counts are a noise indicator, not a variance estimate. No correction was applied across the many exploratory intervals.

The development retrieval headline needs its definition alongside it: **96.9% versus 53.9%** at chunk level becomes **71.9% versus 25.8%** under the first-eight-distinct-passage definition. Both show a large evidence-selection difference. Claiming that 96.9% of questions place the required evidence in the actual answer context would overstate the result. Source: [floor and noise calculations](../experiments/eval/floors-and-noise.json) and [context coverage](../experiments/runs/dev-R-V31/summary.json).

## Results: retrieval and answer generation

### Headline: the final evaluation (two runs, averaged)

The table below is the compact experiment index. Unless specified, answer-status results use the primary model, `gpt-6-luna`. Final comparisons average two runs and use 95% paired case-bootstrap intervals. Other studies have their own denominators and designs; their links preserve the full tables.

### Experiment table

| Comparison | Questions | Measured result | Interpretation and evidence |
|---|---:|---|---|
| Filter then rerank versus hybrid, development | 237 | Behaviour 0.897 versus 0.827; +7.0 points [3.6, 10.6] | Development gain, on questions used to shape the design. [Two-run results](../experiments/eval/final-mean.json). |
| Same, original test | 31 | 0.839 versus 0.806; +3.2 points [-3.2, 11.3] | No demonstrated gain; evidence overlap with development. [Two-run results](../experiments/eval/final-mean.json). |
| Same, fresh set | 65 | 0.715 versus 0.746; -3.1 points [-7.7, 0.8] | No demonstrated gain; subsequently reused questions. [Two-run results](../experiments/eval/final-mean.json). |
| Second model, same retrieval comparison | 237 / 31 / 65 | Differences +5.3 [1.9, 8.9], +1.6 [-8.1, 12.9], -0.8 [-2.3, 0.0] points | Same development-only conclusion. Both models score 0.897 with filtering and ranking on development. [Two-run results](../experiments/eval/final-mean.json). |
| Keyword / dense / hybrid retrieval | 128 development report cases | Chunk hit@8: 0.477 / 0.367 / 0.539 | Hybrid beats dense; improvement over keyword alone is inconclusive. [Method comparison](../experiments/runs/dev-R-V31-methods/SUMMARY.md). |
| Filter then rerank versus hybrid retrieval | 128 development; 18 original; 34 fresh | Development chunk hit@8 0.969 / 0.539; strict passage hit@8 original 0.778 / 0.167, fresh 0.941 / 0.500 | Better evidence coverage across sets, without a demonstrated test-set answer-status gain. [Development](../experiments/runs/dev-R-V31/SUMMARY.md), [test retrieval](experiments/heldout-retrieval-metrics-results.md). |
| Bounded agent versus fixed workflow | 237 development | Agent mean 0.897; fixed 0.814; fixed minus agent -8.2 points [-13.1, -3.4] | Development advantage for the whole agent policy; one fixed run, arithmetic and lookup differences included. [Results](experiments/agent-vs-fixed-pipeline-results.md). |
| Earlier application chain, MCP versus direct statistics | 65 mixed cases | Both models 0.908 on MCP; primary route difference 0.0 points | No observed primary-model loss on this sample, no proof of equivalence; one context probe fails. [Paired routes](../experiments/served/paired-S65-direct-on.json). |
| Remove statistics lookup from that chain | Same 65 | 0.692 versus 0.908 with lookup | Losing lookup and its calculation inputs costs 21.5 points; partly built into the tool design. [Results](experiments/served-chain-no-stats.md). |
| Guarded versus naive, harder attack suite | 54 attacks, 8 benign; three repeats | Case-majority attack passes 50/54 versus 42/54; exact p=.039; benign failures 3/8 each | Attack criterion met, benign criterion failed; guards and prompt changed together. [Results](experiments/threat-v2-results.md). |
| Report-arithmetic tool bundle | 237 development plus reused fresh diagnostics | Seven false-answer flags per model, above the maximum six | Failed its pre-declared criteria; not adopted. [Tool study](experiments/m7-tool-fix.md). |
| Decisions API replacement, second trial | 150 fresh AI-labelled questions, three repeats | 414/450 status matches versus chat 449/450; -7.78 points [-12.44, -3.78] | Rejected; first trial also failed safety or quality gates. [Results](experiments/decisions-api-v2-results.md). |

The second generation model, `gpt-5.6-luna`, ties the primary model's development score with filtering and ranking. I retained the primary because its estimated cost is about **60%** of the second model's, rather than claiming an accuracy win. For the primary, filtering and ranking costs **$0.002845 per question** against **$0.001695** for hybrid; mean run-median latency is **14.35 seconds** against **10.05 seconds**. This is roughly 1.7 times the cost and 1.4 times the latency for the development gain.

The final aggregate's all-case development over-abstention rate is **0.0317 versus 0.1013**, and false-answer rate **0.0295 versus 0.0338**. These are status measures with the definitions above. They do not establish that every answered claim is supported. [Operational measures and both models](../experiments/eval/final-mean.json).

### Current-corpus retrieval re-run

Here, “current” refers to the evaluated v3.1 corpus, not today's served v4. On the same 128 development report questions, filtering alone reaches chunk hit@8 **0.852**, ranking alone **0.742**, and the combination **0.969**, against hybrid **0.539**. Keyword search alone scores above dense search; hybrid's advantage over keyword has an interval spanning zero. Semantic search is therefore not automatically the strongest baseline for this task.

On the original and fresh text subsets, strict passage coverage improves substantially, yet the complete system shows no demonstrated answer-status gain. This separates success at finding evidence from success at using it. I did not investigate the cause of that gap case by case. Retrieval diagnostics use literal questions rather than model-rewritten tool queries, and cannot by themselves establish what every agent run retrieved.

### Served-chain sample

The earlier application-chain sample contained **51 stratified development questions, eight diversion probes and six context probes**. It included small-talk handling, follow-up rewriting, scope checking and the agent with MCP statistics. Gold-only status scores were **90.2% and 88.2%** for the primary and second model. Diversion probes passed **8/8** for both; context probes passed **5/6 and 6/6**. The mixed score is not a full-set evaluation and does not satisfy every registered criterion: one primary-model context probe failed, and aggregate accuracy cannot establish exact numerical-record parity.

MCP, the Model Context Protocol, places statistics lookup behind a separate-process tool interface. The direct route queries the same local statistical table inside the application. Both return the same kind of observation labels and feed the same calculation tool. The comparison tests transport, not access to extra knowledge. With the web steps enabled on both routes, the primary-model difference is zero; the second-model difference is +3.1 points with a descriptive **90%** interval [0.0, 6.2]. One sample does not establish statistical equivalence or exact-call parity.

Removing statistics lookup also removes the observation labels required for deterministic change calculations. Its large score drop therefore measures losing the combined capability. It does not measure the benefit of MCP over direct calls. An all-tools-through-MCP variant was slower and was not adopted. [Protocol](experiments/served-chain-eval.md), [route comparison](../experiments/served/paired-S65-direct-on.json) and [capability removal](experiments/served-chain-no-stats.md).

### Second-family judge sensitivity: saved first-run answers

The main content judge, `gpt-6.1-terra`, sees the question, answer claims, cited evidence and reference facts. It does not independently search for all relevant evidence. Its shared provider and related model family create a risk of correlated errors. Deterministic behaviour, calculation and citation-mechanics scores do not depend on this judge.

I compared it with `claude-sonnet-5-5` on saved first-run answers. Of **240 sampled answer items**, **117 paired comparisons, or 234 answers**, remained after excluding invalid verdicts and their partners. Eligibility required claims in both retrieval settings, so asymmetric answering is excluded and the sample cannot represent all questions. Three items remained omitted after the disclosed retry amendment; no verdict was filled in or deduplicated.

The judges agreed on the three-way support label for **84.26% of 432 claims**, with **Cohen's kappa 0.4360**, an agreement measure adjusted for chance. Their almost-always-negative unsupported-claim flags have high raw agreement but zero kappa, which gives little evidence about detecting rare failures. The second judge did **not** reproduce the second generator's claim-support gain; some support differences changed sign. Fact-coverage differences agreed more closely, without independently validating the reference facts.

Consequently, claim support remains judge-dependent. I did not choose whichever judge produced a favourable result. The second-family check does not rewrite the deterministic two-run behaviour headline or establish independent ground truth. [Sample, omissions and results](../experiments/xjudge/sonnet55-FIN-s60-b-20261102/SUMMARY.md), [protocol and amendment](experiments/second-judge.md).

### Review rubric and process

The human answer sample contained **40 saved baseline answers**, selected with a fixed seed: six per family plus four status mismatches. It is failure-enriched, so its verdict proportions are not population accuracy. I marked **25 correct, six partly correct and nine wrong**, with reasons such as wrong number or series, missing evidence, over-abstention, unsupported claim, bad citation or a questionable reference label.

The judge found no unsupported claim or contradiction in those answers. All nine I marked wrong were non-answers without judged claims, leaving no positive example that validates the judge's detection of unsupported content. A derived answer verdict combining deterministic behaviour with judged content matches me on **31/40**, with kappa **0.64**. That is agreement with one reviewer on a small selected sample. Source checks separately assess extracted passages and table rows. [Rubric, sample and verdicts](human-review/judge-vs-owner.md), [recorded review](human-review/owner-review-final-summary.md).

## Error investigation: remaining failures of the filter-then-rerank run

I separated failures by the step that could cause them, rather than treating every status mismatch as a retrieval problem. The detailed diagnostic concerns an **earlier development run**, with **23 mismatches out of 237** after rescoring: seven over-abstentions, seven false-answer status flags and nine other non-answer mismatches. These counts are not the final two-run result. The [case ledger](reference/evaluation-detail.md#error-investigation-remaining-failures-of-the-filter-then-rerank-run) retains all identifiers and overlapping diagnostic slices.

- **Evidence never acquired.** DEV-009 gathered evidence without a gold passage; two other over-abstentions made no tool calls. Missing evidence after no search is a planning omission, not proof that ranking failed. Filtering and ranking improved retrieval, but the measured planner-prompt change showed no clear additional gain. A future diagnosis should distinguish no-search, wrong-query and wrong-ranking cases before changing retrieval again.
- **Numerical tools do not cover the request.** In that earlier run, calculation correctness was **0.750 on 24 eligible cases**. Missing outputs and ranking questions outside the change-calculation tool explain the six remaining misses; these are coverage or workflow failures rather than observed wrong Decimal arithmetic. On the initial fresh-set run, numerical comparisons over report figures scored **3/14, or 0.214**. The proposed report-arithmetic bundle improved reused diagnostics but failed development safety criteria and was rejected. Typed, source-located report values with verified units need new testing before adoption.
- **Clarification, scope and causal boundaries.** Some answers choose abstention where clarification is expected; others answer requests the reference says to refuse. The earlier development ambiguity/insufficient-evidence/causal group scored **0.727 on 44 cases**, including four false-answer flags. A correct factual claim can still be the wrong response to a causal demand. Post-run changes to the hard evaluated-period rule explain additional historical flags. The served window is now wider, so these historical labels cannot validate its current behaviour.
- **Conflicting sources and definitions.** Preliminary and final releases, population bases and seasonal adjustments must remain distinct. Metadata, deterministic notes and a source-conflict check help make disagreement visible, but a correct figure does not establish that the response identified its publication status. The employment-series basis remains unresolved in the data sheet. The extraction repair removed verified fidelity defects without demonstrating an answer-quality gain; it was retained for source integrity.
- **Untrusted text and planted false figures.** A false figure in retrieved evidence is not reliably stopped. The earlier 36-case attack suite scored **35/36 in all four settings** on its fresh rerun, so it cannot rank defences. The harder suite shows an aggregate guarded advantage, with benign failures in both settings. Its joint prompt-and-guard change cannot identify which defence helped. Independent attacks and paraphrases remain necessary.
- **Operational faults.** The agent caps steps, calls and runtime, with one retry for transient tool failure. The retry evidence is scripted, not a recorded live run. Recorded MCP fault demonstrations cover protocol and timeout behaviour, rather than a measured real-world failure rate. Operational failure must remain distinguishable from insufficient evidence.

Two scorer defects were also corrected: stale judge-cache entries could survive reference changes, and the first stricter calculation scorer overconstrained wording and misread a reference formula. Saved outputs were rescored with corrected logic; earlier scores remain labelled as superseded. These repairs improve measurement integrity. They do not establish a new model capability. [Corrections and provenance](reference/evaluation-detail.md#developmentheld-out-policy), [MCP demonstrations](mcp-demo-transcript.md).

## Responsible-AI evaluation

The threat tests cover direct instruction attacks, malicious report passages, secret or sensitive-data requests, unsafe tool use, unsupported claims, numerical poisoning and causal or forecast overreach. Read-only tools, argument validation, bounded execution, untrusted-evidence handling, quarantine, output scanning and citation checks constrain what the system can do. They do not guarantee truthful answers or complete attack detection.

The harder suite used **54 attacks and eight benign look-alikes**, with three repeats per case. A case passes by majority outcome. Ten attacks passed only with guards and two only without them, giving a paired advantage of **14.8 percentage points**, exact McNemar **p=.039**. That test checks disagreement between paired outcomes. The benign criterion allowed at most two failures, but both settings failed three of eight through abstention or clarification. The suite is small and authored within the project, rather than an independent red team.

A separate scanner experiment raised malicious-passage recall from **10/30 to 23/30**; seven remained missed. Earlier source scanning and the later expanded scanner have different populations and purposes. A clean packaging scan checks known restricted-text patterns in public files, not source licensing or model-provider processing permission. Source rights, private report handling and numerical definitions remain separate controls. [Threat model](threat-model.md), [harder-suite results](experiments/threat-v2-results.md), [scanner experiment](experiments/injection-scanner-v2.md), [data sheet](data-sheet.md).

## Improvement plan

**PROPOSAL:** these are next experiments and release gates, not completed work or changes to frozen results.

1. **Evaluate the system actually served.** Freeze corpus v4, the wider period, native planner, current prompts and tool set together. Establish a new baseline before attributing existing results to them. Include earlier years, added documents, follow-ups and the complete application route.
2. **Build independent reference evidence.** Ask several analysts to label an evidence-disjoint question set before seeing AI suggestions, adjudicate disagreements and freeze it before generation. Measure agreement between reviewers, status correctness, citation support and false answers. Preserve the current sets for regression checks.
3. **Close the numerical coverage gap safely.** Validate report-table values, source locations, units and population definitions, with refusal where extraction is uncertain. Reconsider report arithmetic only after new development and attack tests pass the existing false-answer limits. Do not treat reused fresh questions as independent confirmation.
4. **Test the retrieval-to-answer gap.** Trace test-set failures through search, planning, evidence limits and answer construction. Compare against a simple keyword baseline and the fixed workflow on fresh cases. Extend second-family judging and independent human checks, and use more than two runs to separate case uncertainty from model variation.
5. **Resolve reuse and operating conditions.** Verify unresolved licences, the employment-series basis and provider processing terms. Acquire a second approved snapshot before claiming revision detection. Agree retention, access, incident ownership and quality, cost and latency budgets, then test them. Independently retest scanner paraphrases and false-figure attacks before wider deployment.

## Conclusions

The strongest demonstrated intervention is improved evidence selection. It improves report-passage coverage on development and test subsets and answer-status agreement on development. The bounded agent also beats the fixed workflow on development, with policy and arithmetic differences included. Neither comparison establishes an end-to-end gain on the fresh 65-question set or performance of the changed served system.

I retain filtering and ranking as a provisional engineering choice, the cheaper model as a cost choice, and the rejected experiments as evidence about what still needs work. The next quality claim should come from a frozen evaluation of the current application with independently reviewed, evidence-disjoint questions. The [full reference](reference/evaluation-detail.md) preserves the unsuccessful experiments, historical scores, post-run corrections and deviations needed to audit that conclusion.
