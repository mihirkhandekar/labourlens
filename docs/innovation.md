# Innovation assessment

AI-authored assessment, refreshed 31 October 2026. This note distinguishes implemented controls from proposals for government policy research. Results use gold v3.2: 268 draft cases (237 development, 31 held-out). No human review is completed; the owner-authorised held-out execution used unreviewed AI gold and remains provisional.

## 1. Improve retrieval and answer quality

**MEASURED RESULT:** on 128 answerable development text cases, hybrid hit@8 was 0.570 [95% CI 0.492–0.656]; period/release filtering reached 0.844 [0.781–0.906], reranking 0.789 [0.726–0.859], and their combination 0.969 [0.938–0.992]. Gold and reranker are model-made, so shared bias remains possible. Sources: D-029 and `docs/experiments/m6-retrieval-improvements.md`.

End-to-end gpt-6-luna comparisons:

| Run | Cases | Behaviour accuracy [95% CI] | Median / p95 seconds | Estimated USD/case |
|---|---|---|---|---|
| A1 | 235 | 0.779 [0.728–0.830] | 10.7 / 22.8 | 0.00137 |
| A2 | 235 | 0.762 [0.706–0.813] | 12.7 / 24.7 | 0.00142 |
| A3 | 237 | 0.903 [0.865–0.937] | 15.4 / 35.6 | 0.00212 |
| A4 | 237 | 0.899 [0.861–0.937] | 14.8 / 35.6 | 0.00215 |
| A5 | 237 | 0.907 [0.869–0.941] | 16.4 / 37.5 | 0.00217 |

Sources: `experiments/eval/agent-dev-A{1..5}/gpt-6-luna.metrics.json`. A1–A3 gains are descriptive, not paired significance across unequal populations. Over-abstention fell from 0.157 to 0.030; false-answer rate moved from 0.025 to 0.030. A2 changes the answer prompt, A4 tests widening, and A5 changes the planner; none establishes measurable benefit. D-030/D-032 retain `gpt-6-luna`, `planner_v1`, `answer_v3`, `r3`. D-031 requires abstention for pre-2024 subject-period requests, even with available historical evidence. Filtering still needs hardening against later restatements; quotation containment does not establish claim support.

**Scoring correction:** A1–A5 were re-judged after stale AI judgments survived the gold v3.2 change. The judge cache now fingerprints its inputs; the behaviour table above is unchanged, but previous support/coverage figures are superseded. A3's current `gpt-6-luna` claim support is 0.887 (309 claims), reference-fact coverage 0.728 (309 facts), and direction-aware deterministic calculation correctness 0.750 (24 cases). An initial strict scorer incorrectly rejected valid wording/units and misread “not relative percent change”; that scorer defect was fixed, and development/held-out calculation scores were recomputed without new generation. This post-run scoring-code change is a deviation, not a capability regression. Source: `experiments/eval/agent-dev-A3/gpt-6-luna.metrics.json`.

**Registered held-out result:** with `planner_v1`/`answer_v3`, R3 versus hybrid behaviour accuracy is 0.839 versus 0.677 for `gpt-6-luna`, and 0.871 versus 0.742 for `gpt-5.6-luna` (31 cases each). Paired gains are 0.161 [95% CI 0.000–0.323] and 0.129 [0.000–0.290]. Both are **inconclusive** under the registered rule requiring an interval strictly above zero; retain R3 provisionally, not as a confirmed win. Sources: `experiments/eval/agent-heldout-H-{r3,hybrid}/*.metrics.json`, `experiments/heldout/paired.txt`.

**Executed deviations:** `experiments/heldout/FREEZE.md` records owner authority and hashes, but human-review-before-freeze was not satisfied. An extra `gpt-4.1-mini` run was unregistered and is excluded from conclusions. An initial evaluation invocation selected the wrong split and was rerun with `--split heldout`; no configuration or label was changed after seeing results. The held-out set is now exposed, not an untouched tuning resource.

## 2. Detect changing data, models and user needs

Immutable snapshots, contracts and revision comparisons exist. **PROPOSAL:** inspect refreshes for schema changes, missing periods and revisions before serving a new index. Run fixed canaries daily and before model, prompt or index changes, recording hashes, expected evidence, statuses, support, latency and cost. Hold releases on unexplained regressions and retain the previous configuration.

Pin versioned model IDs where available, track deprecations, and review question families, clarification rates and feedback weekly. Hosted behavior can drift despite unchanged requests. These review schedules and alerts are not deployed services.

## 3. Confidence, explanation and human oversight

Passage locators, observation lineage, claim citations and task timelines support inspection. Confidence should communicate evidence coverage and review status, not a model self-rating presented as probability.

**PROPOSAL:** have humans review a stratified sample including abstentions and apparently successful answers; check definitions, sufficiency and support. Publish human/AI-judge disagreement alongside uncertainty intervals. Feedback already joins to run IDs; the supervised loop should classify failures, draft a regression case, obtain review, change one factor and rerun. This is not reinforcement learning. Human evaluation remains incomplete.

## 4. Privacy, governance and third-party risk

Read-only tools, bounded execution, screened MCP results and hostile-server fixtures exist. Corrected defended runs passed 35/36 for each luna model [Wilson 95% CI 0.858–0.995] and 34/36 for mini [0.819–0.985]. Both luna models repeated a planted figure; mini also failed a status criterion and followed a subtle instruction. The earlier defended 36/36 claim was invalid: six indirect fixtures failed before reaching the model. Corrected fixtures exercise all six; historical naive hybrid runs are not a paired R3 ablation. Source: `experiments/threats/SUMMARY.md`.

**PROPOSAL:** cross-check passage numbers against compatible validated observations, matching population, adjustment, units and release vintage. Measure planted-figure rejection and false alarms on genuine revisions separately; never silently overwrite a conflict. A5 is a completed, inconclusive planner experiment, not this cross-check.

Before sensitive use, require government identity, source-level permissions, approved retention, restricted audit access and an approved processing agreement. Redaction and pseudonyms do not anonymise questions; shared codes do not identify researchers. OpenAI data-use terms remain unverified (D-022). Keep restricted source text out of public packages and minimise external content. See `docs/security-review-web.md` and `docs/audit-and-logging.md` for implemented controls and remaining risks.

## 5. Latency and cost

A3 trades higher latency and cost for better observed development accuracy. Filtering needs no additional model call; combined retrieval adds roughly 3.2 seconds and $0.00075 per retrieval query in the saved retrieval study.

**PROPOSAL:** preserve embedding caches and fixed tool budgets; evaluate filter-only routing for simple lookups as a separate factor. Monitor supported-answer coverage with p95 latency, failures and charges. Timeout billing is unknown without usage; application reservations are not provider spending caps.

## 6. First two priorities and acceptance targets

**First: harden the existing filter-plus-rerank default.** On human-reviewed development cases, measure passage coverage, behavior accuracy, over-abstention, latency and cost. Proposed thresholds for another change: paired accuracy gain ≥5 percentage points with its 95% interval above zero, no increased over-abstention, p95 <40 seconds and mean cost <$0.005/case.

**Second: human-reviewed evaluation and daily canaries.** Proposed targets: human/AI agreement ≥0.80, reviewed regression tests within two working days, and detection of deliberately seeded regressions within one daily cycle. These are targets, not results. Do not tune against held-out outcomes. A4 and A5 are completed development experiments without measurable benefit, not pending improvements.
