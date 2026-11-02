# Innovation assessment

**What this covers.** A forward plan for turning LabourLens into a secure government research capability, written by the author with AI assistance. Results are marked **MEASURED**; everything else is a **PROPOSAL** and not built. Methods, intervals and caveats are in the [evaluation report](evaluation-report.md); corpus builds are explained in the [README](../README.md#corpus-versions). Gold labels were drafted by AI and the judge is an AI. The owner went through the labels in the review interface and signed off on every case, answer verdict and source check (four separate streams, 403 items). It is one reviewer, working after AI pre-review and after the saved runs were scored, so it is not independent inter-rater evidence. Every accuracy figure is an agreement figure, not validated accuracy.

## 1. Improve retrieval and answer quality

**Current headline (MEASURED, D-061).** The mean of FIN and FIN2 on corpus v3.1 gives filter-then-rerank behaviour accuracy 0.897 versus hybrid 0.827 on 237 development questions for `gpt-6-luna` (+7.0 points, 95% case-bootstrap interval [3.6, 10.6]); the second model's gain is +5.3 [1.9, 8.9]. Primary over-abstention is 3.2% versus 10.1%. Neither test set demonstrates a gain: primary original-test means 0.839/0.806 (31 cases), fresh 0.715/0.746 (65). Both singles remain in the evaluation report; FIN alone is history, not the headline. Development shaped the design; two runs do not estimate variance.

**History (earlier build, corpus v1).** Period and release filtering plus an LLM rerank (A3) lifted `gpt-6-luna` behaviour accuracy from 0.779 [0.728, 0.830] (A1, hybrid) to 0.903 [0.865, 0.937] on development cases and cut over-abstention from 0.157 to 0.030. Populations differ (235 versus 237 cases), so this is descriptive, not a paired test. On the 31 original held-out cases the paired gain, 0.161 [0.000, 0.323], is **not demonstrated**; those cases share evidence with development.

**History (original run on corpus v3).** On 65 held-out v2 cases, written on sources no earlier case cites and run once, the pre-registered rule is met for the primary model, but the effect is three cases and the second model shows none; I would not call it a confirmed gain ([result](experiments/m7-heldout-v2-result.md)). Both arms score about 0.71 to 0.75, held back by arithmetic over report figures (0.214). A tool set built to close that gap failed its pre-declared dev criteria and was not adopted (D-048). **PROPOSAL:** a second attempt with a safer snippet format, a threat run under it, and a fresh held-out set, since the v2 questions are now known.

## 2. Detect changing data, models and user needs

Immutable snapshots, source contracts and revision comparison exist. **PROPOSAL:** before serving a refresh, check schema changes, missing periods and revisions; run a fixed canary set daily and before any model, prompt or index change, recording hashes, expected evidence, status, latency and cost; hold the release on an unexplained regression and keep the previous configuration. Pin model identifiers, track deprecations, and review question families, clarification rates and feedback weekly. None of this runs as a service today.

## 3. Confidence, explanation and human oversight

Passage locators, observation lineage, claim citations and a task timeline support inspection. Confidence should show evidence coverage and review status, not a model's self-rating dressed as a probability.

**PROPOSAL:** stratified human review, especially of abstentions and answers that look right, from a smaller sample that reviewers judge before seeing the AI suggestion, ideally by more than one person. Feedback already joins to runs; a supervised loop would classify a failure, draft a regression case, get it reviewed, change one factor and rerun. This is not reinforcement learning.

## 4. Privacy, governance and third-party risk

Tools are read-only and bounded, MCP results are screened, and hostile-server fixtures exist. **MEASURED:** fresh 2 Nov threats give 35/36 in all four configurations under both scorers. The 31 Oct run is history: defended primary 36/36, second model 35/36, naive 35/36. The suite shows no general safety or causal defence effect. T-I06 plants a false figure in a passage; its deterministic dataset cross-check (D-038) is closed-grammar and **not shown stable across runs**. See the [threat model](threat-model.md).

**PROPOSAL** for sensitive use: government identity, source-level permissions, approved retention, restricted audit access and an approved processing agreement. Redaction does not anonymise questions, and shared access codes do not identify researchers. Provider data-use terms for the passages are unverified (D-022). Restricted source text stays out of public packages.

## 5. Latency and cost

The current primary development means cost about $0.002845 per case for r3 versus $0.001695 for hybrid; the mean of run medians is 14.35 s versus 10.05 s (about 1.4 times latency). FIN alone's 15.1/9.9 s is history. Costs are saved-usage list-price estimates, not bills. **PROPOSAL:** retain embedding caches and bounded tools, test filter-only routing separately, and watch supported-answer coverage, p95 latency and failures. Application reservations are not provider spending caps.

## 6. First two priorities and acceptance targets

**First: harden the filter-plus-rerank default.** On human-reviewed cases, measure passage coverage, behaviour accuracy, over-abstention, latency and cost. A further change needs a paired gain of at least 5 points with a 95% interval above zero, no rise in over-abstention, p95 under 40 s and mean cost under $0.005 per case.

**Second: independent review and daily canaries.** Targets: human and AI agreement of at least 0.80, reviewed regression tests within two working days, and a seeded regression detected within one daily cycle. These are targets, not results. Held-out outcomes already seen are never tuned on.
