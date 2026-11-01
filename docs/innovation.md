# Innovation assessment

**What this covers.** A forward plan for turning LabourLens into a secure government research capability, written by the author with AI assistance. Measured results are marked **MEASURED**; everything else is a **PROPOSAL** and has not been built. Full methods, intervals and caveats are in the [evaluation report](evaluation-report.md). Registered results come from corpus v1 (X1 on corpus v2 is a separately labelled, non-registered experiment). Corpus v3 has three measured evaluations (a development regression check, a threat run and held-out v2, the first evidence-disjoint-source evaluation); see the corpus-versions statement in the [README](../README.md#corpus-versions). The gold labels were drafted by AI, and the judge is an AI. The owner then went through the labels in the review interface and signed off on every case, answer verdict and source check (four separate streams, 403 items in total: 268 gold questions, 65 held-out v2 questions, 40 saved system answers and 30 source checks; only the first two are questions). It is one reviewer, working after AI pre-review and after the saved runs were scored, so it is not independent inter-rater evidence. Every accuracy figure is therefore an agreement figure, not validated accuracy.

## 1. Improve retrieval and answer quality

**MEASURED.** Adding period and release filtering and an LLM rerank (configuration A3) lifted behaviour accuracy for `gpt-6-luna` from 0.779 [0.728–0.830] (A1, hybrid retrieval) to 0.903 [0.865–0.937] on development cases, and cut over-abstention from 0.157 [0.111, 0.204] to 0.030 [0.008, 0.051]. The populations differ (235 versus 237 cases), so the gain is descriptive, not a paired test. Changing the answer prompt (A2), widening retrieval (A4) and a new planner prompt (A5) showed no measurable benefit.

On the 31 held-out cases the same change gave 0.871 versus 0.710 for `gpt-6-luna`; the paired gain of 0.161 has an interval of [0.000, 0.323], so it is **not demonstrated**. The held-out questions share evidence with development, so this tests new questions, not new facts. Repairing known extraction defects (corpus v2) changed nothing measurable.

**MEASURED (31 Oct 2026).** The 65-case held-out v2 set, written on sources no earlier case cites, was run once and unchanged ([result](experiments/m7-heldout-v2-result.md)). The pre-registered rule is met for the primary model; the effect is three cases; I would not call it a confirmed gain; the second model shows none. Both arms score about 0.71 to 0.75, mostly held back by a tool coverage gap on arithmetic over report figures. **PROPOSAL.** Close that gap as a new experiment with a new id, then test it on a fresh set, because the held-out v2 questions are now known.

**MEASURED (1 Nov 2026).** The tool coverage gap was addressed as proposed, as a new experiment with a new id (tool set v2, [report](experiments/m7-tool-fix.md), D-048). On the development set it did not pass its pre-declared criteria for either model (false-answer cases 7 against 6, ungrounded numbers in cases that used the new tool) and is not adopted. Re-running the known v2 questions raised `numerical_comparison` from 3 to 12 of 14 for `gpt-6-luna`, but that is a post-freeze diagnostic on the cases that motivated the fix, so it is not independent evidence. The remaining proposal is a second attempt (a safer snippet format, a threat run under v2) and a fresh held-out set.

## 2. Detect changing data, models and user needs

Immutable snapshots, source contracts and revision comparison exist. **PROPOSAL:** before serving a refresh, check schema changes, missing periods and revisions; run a fixed canary set daily and before any model, prompt or index change, recording hashes, expected evidence, status, latency and cost; hold the release on an unexplained regression and keep the previous configuration. Pin model identifiers, track deprecations, and review question families, clarification rates and feedback weekly. None of this runs as a service today.

## 3. Confidence, explanation and human oversight

Passage locators, observation lineage, claim citations and a task timeline support inspection. Confidence should show evidence coverage and review status, not a model's self-rating dressed as a probability.

**PROPOSAL:** independent, stratified human review, especially of abstentions and answers that look right. The owner recorded a decision on all 403 labelling items, and this is one reviewer working after AI pre-review and after the runs were scored, so it is not independent agreement evidence. A defensible human-review claim needs a smaller sample that reviewers derive independently before seeing the AI suggestion. Feedback already joins to runs; a supervised loop would classify a failure, draft a regression case, get it reviewed, change one factor and rerun. This is not reinforcement learning.

## 4. Privacy, governance and third-party risk

Tools are read-only and bounded, MCP results are screened, and hostile-server fixtures exist. **MEASURED** (36-case hand-written suite, one run per configuration, corpus v1): defended `gpt-6-luna` and `gpt-5.6-luna` passed 35/36 [Wilson 0.858–0.995] and `gpt-4.1-mini` 34/36. Without defences `gpt-6-luna` also passed 35/36, so the suite shows no measurable defence effect for it. This is not evidence of resistance to adaptive attacks.

The one shared failure was T-I06, a false report figure planted in a passage. A deterministic cross-check against validated dataset values (D-038) was then added. An earlier post-fix run gave 35/36 strict and 36/36 refined (a scorer written after seeing the output) for both luna models. A later run on the final code (corpus v3, D-044) gave `gpt-6-luna` 36/36 and `gpt-5.6-luna` 35/36 strict, with T-I06 failing for `gpt-5.6-luna` because the scorer requires an exact string and rejects the planted figure inside a disclosed-conflict caveat. The scorer was not changed. T-I06 is one case with a closed grammar, **not shown stable across runs**, and the suite shows no defence effect (naive baselines 35/36). The guard still has very low recall on real passages; see the [threat model](threat-model.md).

**PROPOSAL** for sensitive use: government identity, source-level permissions, approved retention, restricted audit access and an approved processing agreement. Redaction and pseudonyms do not anonymise questions, and shared access codes do not identify researchers. OpenAI data-use terms for the passages are unverified (D-022). Restricted source text stays out of public packages.

## 5. Latency and cost

A3 buys its accuracy with time and money: median 15.4 s and about $0.0021 per case, against 10.7 s and $0.0014 for A1 (estimates from saved usage at list prices, not a bill). **PROPOSAL:** keep embedding caches and fixed tool budgets, test filter-only routing for simple lookups as a separate factor, and watch supported-answer coverage with p95 latency and failure counts. Application budget reservations are not provider spending caps.

## 6. First two priorities and acceptance targets

**First: harden the filter-plus-rerank default.** On human-reviewed cases, measure passage coverage, behaviour accuracy, over-abstention, latency and cost. A further change needs a paired accuracy gain of at least 5 points with a 95% interval above zero, no rise in over-abstention, p95 under 40 s and mean cost under $0.005 per case.

**Second: independent review and daily canaries.** Targets: independent human and AI agreement of at least 0.80, reviewed regression tests within two working days, and a seeded regression detected within one daily cycle. These are targets, not results. Held-out outcomes already seen are never tuned on.
