# Innovation assessment

**What this covers.** A forward plan for turning LabourLens into a secure government research capability, written by the author with AI assistance. Results are marked **MEASURED**; everything else is a **PROPOSAL** and not built. Methods, intervals and caveats are in the [evaluation report](evaluation-report.md); corpus builds are explained in the [README](../README.md#corpus-versions). Gold labels were drafted by AI and the judge is an AI. The owner went through the labels in the review interface and signed off on every case, answer verdict and source check (four separate streams, 403 items). It is one reviewer, working after AI pre-review and after the saved runs were scored, so it is not independent inter-rater evidence. Every accuracy figure is an agreement figure, not validated accuracy.

## 1. Improve retrieval and answer quality

**Final evaluation (MEASURED, D-056).** On the final system (corpus v3.1, one run per arm, `gpt-6-luna`), filter then rerank scores 0.886 against 0.844 for hybrid on the 237 development questions (+4.2 points, 95% interval [0.4, 8.4]; `gpt-5.6-luna` +5.9 points) and halves over-abstention (0.042 against 0.089). It shows **no gain on either held-out set**: 26 of 31 in both arms on the registered original test, and 0.708 against 0.754 on the 65 fresh questions (0 better, 3 worse, within noise). It costs about 1.7 times as much per question and about 1.5 times the latency. The development questions shaped the design, so the development gain is descriptive.

**History (earlier build, corpus v1).** Period and release filtering plus an LLM rerank (A3) lifted `gpt-6-luna` behaviour accuracy from 0.779 [0.728, 0.830] (A1, hybrid) to 0.903 [0.865, 0.937] on development cases and cut over-abstention from 0.157 to 0.030. Populations differ (235 versus 237 cases), so this is descriptive, not a paired test. On the 31 original held-out cases the paired gain, 0.161 [0.000, 0.323], is **not demonstrated**; those cases share evidence with development.

**History (original run on corpus v3).** On 65 held-out v2 cases, written on sources no earlier case cites and run once, the pre-registered rule is met for the primary model, but the effect is three cases and the second model shows none; I would not call it a confirmed gain ([result](experiments/m7-heldout-v2-result.md)). Both arms score about 0.71 to 0.75, held back by arithmetic over report figures (0.214). A tool set built to close that gap failed its pre-declared dev criteria and was not adopted (D-048). **PROPOSAL:** a second attempt with a safer snippet format, a threat run under it, and a fresh held-out set, since the v2 questions are now known.

## 2. Detect changing data, models and user needs

Immutable snapshots, source contracts and revision comparison exist. **PROPOSAL:** before serving a refresh, check schema changes, missing periods and revisions; run a fixed canary set daily and before any model, prompt or index change, recording hashes, expected evidence, status, latency and cost; hold the release on an unexplained regression and keep the previous configuration. Pin model identifiers, track deprecations, and review question families, clarification rates and feedback weekly. None of this runs as a service today.

## 3. Confidence, explanation and human oversight

Passage locators, observation lineage, claim citations and a task timeline support inspection. Confidence should show evidence coverage and review status, not a model's self-rating dressed as a probability.

**PROPOSAL:** stratified human review, especially of abstentions and answers that look right, from a smaller sample that reviewers judge before seeing the AI suggestion, ideally by more than one person. Feedback already joins to runs; a supervised loop would classify a failure, draft a regression case, get it reviewed, change one factor and rerun. This is not reinforcement learning.

## 4. Privacy, governance and third-party risk

Tools are read-only and bounded, MCP results are screened, and hostile-server fixtures exist. **MEASURED** (36 hand-written cases, one run per configuration): final-code defended `gpt-6-luna` passed 36/36 and `gpt-5.6-luna` 35/36; the naive baselines passed 35/36, so the suite shows no measurable defence effect and says nothing about adaptive attacks. The shared weak case is T-I06, a false figure planted in a passage. A deterministic cross-check against validated dataset values (D-038) addresses it, but T-I06 is one case with a closed grammar and is **not shown stable across runs**. See the [threat model](threat-model.md).

**PROPOSAL** for sensitive use: government identity, source-level permissions, approved retention, restricted audit access and an approved processing agreement. Redaction does not anonymise questions, and shared access codes do not identify researchers. Provider data-use terms for the passages are unverified (D-022). Restricted source text stays out of public packages.

## 5. Latency and cost

On the final system filter then rerank buys development accuracy with time and money: median 15.1 s and about $0.0028 per case against 9.9 s and $0.0017 for hybrid (the earlier A3 and A1 runs: median 15.4 s and about $0.0021 against 10.7 s and $0.0014; list-price estimates from saved usage, not a bill). **PROPOSAL:** keep embedding caches and fixed tool budgets, test filter-only routing for simple lookups as a separate factor, and watch supported-answer coverage with p95 latency and failure counts. Application budget reservations are not provider spending caps.

## 6. First two priorities and acceptance targets

**First: harden the filter-plus-rerank default.** On human-reviewed cases, measure passage coverage, behaviour accuracy, over-abstention, latency and cost. A further change needs a paired gain of at least 5 points with a 95% interval above zero, no rise in over-abstention, p95 under 40 s and mean cost under $0.005 per case.

**Second: independent review and daily canaries.** Targets: human and AI agreement of at least 0.80, reviewed regression tests within two working days, and a seeded regression detected within one daily cycle. These are targets, not results. Held-out outcomes already seen are never tuned on.
