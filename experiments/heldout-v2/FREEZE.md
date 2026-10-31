# Held-out v2 preregistration and run gate (design A, corpus v3)

**Status: PRE-RUN DRAFT, written 31 Oct 2026 before any generation, retrieval, scoring or output inspection for these cases. Acceptance rule revised the same day (revision 2) before any run.** It becomes a freeze only when the owner signs off the preconditions below and the final hashes are re-verified. Supersedes the earlier structured-only draft of this file. Design, leakage argument and limits: `docs/experiments/m7-heldout-v2-design.md`.

## What is being frozen
- **Gold:** `experiments/gold/heldout_v2_draft.jsonl`, 65 cases, SHA-256
  `698940357c090c4beed4ba6532f66967dc7175297a3d1ffcd5fd6325e128fb70`.
  Every case is `draft`, `reviewed_by=null`, authored blind to all system output, and cites **only** corpus-v3 sources that no existing gold case, saved dev run or tuning step has touched: `mom-wage-practices2025`, `mom-nwc-lower-wage2025`, `mti-2026-q2-feature-ai-employment`, `unit_labour_cost_index_quarterly`, `value_added_per_worker_quarterly`, `avg_weekly_paid_hours_quarterly`. Any edit changes the hash; replace this section, never reuse an old hash.
- **Schema:** `experiments/gold/heldout_v2.schema.json` (all 65 cases validate; `labourlens.retrieval.gold.validate` returns no errors).
- **Corpus v3:** snapshot `experiments/corpus-snapshots/v3.json` SHA-256 `6caba3d61a3addbef4b182ec3455e99fa8e509ff056e5ecdf82fe4da33377bc6` (49 documents, 16,419 passages, 1,847 `merge200` chunks, chunk fingerprint `d684aa76e93a8c4a3821bc39891d8c5bd21a36f871819e24e9b95d6d752c305e`, manifest SHA-256 `5bb67d4e36572d1573eb3cc6834d449fc44e053215f98e4a4895b17607e1449b`).
  - `data/processed/observations.parquet` SHA-256 `bb5d14d8df1c5eaaa8e18a8979dab4b6eb40eaf4059002f4884b04975165b7d3`.
  - Passage fingerprint (SHA-256 of sorted `passage_id:text_sha256` lines, 16,419 passages): `c7ec1f684e7edfe34e36e21865e88b6b88e42bea674b4a6c3e4a243fa11e99f4`.
- **Prompts (unchanged from the registered original held-out):** `planner_v1` `df68ef8e5e287d1a0b1f71d938e85ec25b4f03eeec501bc439a3a77aec2482dc`; `planner_v1_user` `e59f408b00f5a99e0fb867c635a84d2d77947171620ab035f6067a3cdfb8136f`; `answer_v3` `e854b64c72116c4c175082e70f39c312ed94b1f37778e7daf3f9a51de1bac350`; `answer_v3_user` `c4f4ef05d7d1b87fca94bee65cbf2a38999c181dc2e92bced9cdf8ef92b006e7`; `rerank_v1` `e45ed816ccefd679d046cf9bcbd4dad92ba27b20cfc5f45b900063b84784793a`; `judge_v1` `85f3529fca32faec681b3d4b1e6899b8620c383ed2aa54bc423241e2b7f4a10f`.
- **Prices:** `specs/prices.yaml` SHA-256 `634b32441c3495b4c3ec13efa3af1e9cc99e5c7523eac3a15a5c238c3acaeb5c`.
- **Code:** record `git rev-parse HEAD` immediately before running. Authoring-time HEAD was `0e5bd3b341e2b5ec6694329d3b04116d38732bc9` plus uncommitted work (paired module, `--gold`, scorer unit widening, review-pack tab). The parent must commit that state first. Both arms must run on identical code, including the T-I06 cross-check decision (D-038) and the extraction fixes.
- **Supporting records:** `experiments/heldout-v2/evidence-audit-v3.json` (independence audit, per-case ids), `authoring-checks.json`, `components.json` (39 evidence components, 22 carry evidence ids, published before any run). The older `evidence-audit.json` documents the overlap of the original held-out set and the earlier structured-only inventory; `experiments/gold/heldout_v2_structured_draft.jsonl` keeps those 60 structured-only cases as an unregistered secondary diagnostic (`HO-V2S-*`), not part of this freeze.

## Composition (decided before any run)
| Family | n | Notes |
|---|---:|---|
| factual_lookup | 22 | 6 dataset, 16 report text |
| numerical_comparison | 14 | 6 dataset (4 with a gold calculation), 8 arithmetic on report text |
| cross_source_synthesis | 8 | report pairs and report-plus-dataset pairs |
| revision_conflict | 3 | **thin**: no labour-only revision pair exists in the new sources; only original-vintage-unavailable abstentions |
| ambiguity_insufficient_causal | 10 | 4 clarify, 5 abstain, 1 refuse |
| adversarial | 8 | 4 direct injection plus answerable question, 4 refuse |

Behaviours: 44 answer, 4 ignore-injection-and-answer, 8 abstain, 4 clarify, 5 refuse (21 non-answer or injection cases). Answerable cases with report text evidence: 34 of 48; the other 14 rest on dataset tools used identically by both arms and are expected to dilute any retrieval effect.

## Preconditions before any model call
1. **Owner review of the 65 cases** in the review pack tab "Held-out v2" (not yet built into the real pack), or an explicit owner decision to run unreviewed. AI authoring and AI checks are not human review. If the owner changes any label, re-hash and amend this file before running.
2. **Owner acceptance of the scope-sensitive cases:** five `mti_ai_feature` cases rest on a study of firm AI use through 2024, published in Q2 2026. If the owner rules that earlier-period analyses must abstain (D-031), relabel them before freezing; do not relabel after a run.
3. Re-verify every fingerprint above. Any change to corpus, prompts, prices or code needs a dated amendment first.
   Also fix and record the environment for **both** arms: the T-I06 source-conflict guard is on unless `LABOURLENS_CROSSCHECK=off` (or `LABOURLENS_GUARDS=off`) is set. Run both arms with the same setting, decide it before running, and write the choice into this file. `OPENAI_API_KEY` is required; no key is stored in the repo.
4. Validate: `uv run python -c "from labourlens.retrieval import gold; from pathlib import Path; e=gold.validate(Path('experiments/gold/heldout_v2_draft.jsonl')); print(e); raise SystemExit(bool(e))"`
5. Run the non-corpus tests once (`uv run pytest -q -m 'not corpus'`).
6. Never relabel from system output; never drop or rerun cases selectively.

## Registered comparison
Single factor: retrieval `r3` versus `hybrid`. Fixed: `planner_v1`, `answer_v3`, rerank prompt `rerank_v1` (fixed model `gpt-6-luna`), judge `gpt-6.1-terra`, same harness and tools; planner and answer use the same model, `gpt-6-luna` or `gpt-5.6-luna`. One run per arm. Operational failures stay in the denominator.

Exact commands, in order (they call paid APIs; run only after the preconditions):
```
uv run labourlens agent-exp --split heldout --gold experiments/gold/heldout_v2_draft.jsonl --tag V2-r3 --retrieval r3 --pairs gpt-6-luna gpt-5.6-luna
uv run labourlens agent-exp --split heldout --gold experiments/gold/heldout_v2_draft.jsonl --tag V2-hybrid --retrieval hybrid --pairs gpt-6-luna gpt-5.6-luna
uv run labourlens eval --exp agent-heldout-V2-r3 --split heldout --gold experiments/gold/heldout_v2_draft.jsonl
uv run labourlens eval --exp agent-heldout-V2-hybrid --split heldout --gold experiments/gold/heldout_v2_draft.jsonl
uv run labourlens paired --gold experiments/gold/heldout_v2_draft.jsonl --candidate agent-heldout-V2-r3 --baseline agent-heldout-V2-hybrid --models gpt-6-luna gpt-5.6-luna --out experiments/heldout-v2/paired.json
```
Raw runs go to gitignored `data/runs/agent-heldout-V2-*`. Scores and `paired.json` are committed; they never overwrite `experiments/heldout/*` or any registered run. `labourlens paired` makes no model calls and implements the rule below in `src/labourlens/evaluation/paired.py` (seed 20261031, 20,000 resamples). It refuses to run unless every scored arm's `metrics.json` records this gold file's SHA-256 (`labourlens eval --gold` writes it); `labourlens agent-exp` refuses to overwrite an existing experiment id without `--force`.

## Acceptance rule decided in advance (revision 2, 31 Oct 2026, still before any generation, scoring or output inspection)
Revision 1 (both models, 97.5% two-sided intervals, plus a veto on added false or contradicted answers) is **withdrawn**. The simulation below shows it would almost never pass at the effect sizes already seen. Decision record: D-042.

**R3 gain demonstrated** only if, for the **primary model `gpt-6-luna`** (the model the system ships), all hold:
1. Both arms scored exactly the same 65 cases (no missing or extra case).
2. Paired behaviour-accuracy difference (R3 minus hybrid) has a **one-sided 95% lower bound above zero** under the case bootstrap (implemented as the lower end of the two-sided 90% percentile interval, 20,000 resamples, seed 20261031).
3. The same lower bound is above zero when resampling **evidence components** (cases sharing any acceptable passage or observation id move together).
4. At least **20 evidence-carrying components** (the draft has 22).
5. R3 adds no false-answer case relative to hybrid (a veto for the primary model).
6. The owner-review and reservation preconditions were met without a protocol deviation affecting only one arm.

`gpt-5.6-luna` is a **pre-specified replication**: its result is reported in full with the same conditions, never gates the verdict, and is not combined with the primary into a conjunction or a disjunction. Answers contradicting a reference fact are **reported, not a veto** (an AI judge decides them and the simulation did not price a veto on them). Otherwise the statement is: **gain not demonstrated**, reported descriptively. Also reported, not gating (`sensitivity_descriptive` in `paired.json`): exact McNemar p-value on discordant pairs, per-family counts, a conservative source-group cluster interval (10 groups), the result without the five `mti_ai_feature` cases, and the result restricted to the cases that have report-text gold evidence. A pass supports "R3 improved behaviour on these new sources under this system"; it does not establish unseen-domain generalisation.

## Power and false-positive rate (MEASURED RESULT of a simulation, no model output used)
`experiments/heldout-v2/power.py` (seed 20261101, 2,000 simulations per cell, 1,000 bootstrap resamples; output `power.txt`) simulates paired per-case outcomes on the real structure: 65 cases, 39 components (22 carry evidence), 34 report-text answerable cases, 17 non-answer cases. Assumptions are listed in the script header: R3 worse on 4% of cases, better on (effect + 4)%; either all cases can move or only the 34 report-text cases can; components optionally move together (clustering 0 or 0.5); the two models are independent replicates (real ones are correlated). Monte Carlo error is about 1 point.

Probability that the rule passes, by true paired effect (ranges are over the four assumption sets):

| rule | effect 0 (false-positive rate) | +5 | +10 | +16 |
|---|---:|---:|---:|---:|
| Revision 1: both models, 97.5% two-sided, guard veto | 0.0-0.1% | 1.5-2.6% | 11-19% | 31-53% |
| Both models, 95% one-sided, guard veto | 0.1-0.4% | 4-6% | 19-30% | 46-67% |
| **Revision 2 (adopted): primary model only, 95% one-sided, case and component, guard veto** | **3.0-5.2%** | **21-24%** | **45-54%** | **68-84%** |
| Either model passes (rejected) | 6.3-10.2% | 38-43% | 67-82% | 89-98% |

Trade-off, stated plainly: revision 2 is a weaker rule. At zero true effect it passes about 3 to 5 times in 100 (the intended 5% one-sided level), where revision 1 passed about never; that is the price of power. At +10 points, the size of the original held-out gain, power rises from roughly 11-19% to 45-54%, and at +16 from 31-53% to 68-84%. It remains underpowered at +5. "Either model passes" was rejected because it nearly doubles the false-positive rate. A conjunction over both models was rejected because it loses most of the power, and its extra stringency is not needed when one model is primary. The false-answer veto costs about one point of power in the simulation, so it is kept. A failed rule is still not evidence of no gain, and a pass is a one-sided 5%-level result from one run, not proof.

## Conditional cost estimate (inference, not a cap)
Saved original-held-out mean generation cost per case (USD): r3 0.00193 and 0.00343, hybrid 0.00124 and 0.00271 for `gpt-6-luna` and `gpt-5.6-luna`. At 65 cases that is about $0.61 for generation, plus about $0.22 for judging scaled from the saved judge totals (0.1045 USD over 31 cases per four arms): about **$0.82** in total. The larger corpus and new document lengths can change token use; reranking cost per query is unchanged by corpus size only if the candidate pool size is unchanged. Prices from `specs/prices.yaml` were read on 2026-10-30 and are not re-verified here.

## Known leakage that remains
Same system prompts, tools, reranker model and prompt, embedding model, planner and agent code as dev; same publishers and series families; the wage-practices 2025 report is the sibling edition of a 2024 report used in dev (only 2025 figures are asked); the MTI feature article studies firm AI use in a window ending 2024; question styles resemble dev. These cases test fresh evidence, not a fresh system.
