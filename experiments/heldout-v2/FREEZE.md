# Held-out v2 preregistration and run gate

**Status: PRE-RUN DRAFT. Not an executed or approved confirmatory freeze.** Written 31 Oct 2026 before any generation, retrieval, scoring or output inspection for these cases. The draft is 60 structured-only dataset-period cases. It is not evidence-disjoint unseen-document validation. See `docs/experiments/m7-heldout-v2-design.md` for the blocker: no verified untouched substantive document exists.

## Fingerprints at authoring time
- Gold: `experiments/gold/heldout_v2_draft.jsonl`
  SHA-256 `7a8aee1f145f8c7490dccee2f0b75a8395cf373cbff7eaaa97aa94aede1cd427`
  Any edit before running changes this hash; replace this section, never use an older hash.
- Schema: `experiments/gold/heldout_v2.schema.json`.
- Observations: `data/processed/observations.parquet` SHA-256 `69ae768749cef6f2705dafbcf5ad9470b27e83eb7352a07a65afaed7d8c929dc`.
- Rebuilt passage fingerprint (SHA-256 over sorted passage_id:text_sha256 pairs): `d989838a5d0a17c7948619dcea5715045795e4bb4541c559a19cc0b6d71d3d29` (15,915 passages).
- Prices: `specs/prices.yaml` SHA-256 `634b32441c3495b4c3ec13efa3af1e9cc99e5c7523eac3a15a5c238c3acaeb5c`.
- Prompts: planner_v1 `df68ef8e5e287d1a0b1f71d938e85ec25b4f03eeec501bc439a3a77aec2482dc`; planner_v1_user `e59f408b00f5a99e0fb867c635a84d2d77947171620ab035f6067a3cdfb8136f`; answer_v3 `e854b64c72116c4c175082e70f39c312ed94b1f37778e7daf3f9a51de1bac350`; answer_v3_user `c4f4ef05d7d1b87fca94bee65cbf2a38999c181dc2e92bced9cdf8ef92b006e7`; rerank_v1 `e45ed816ccefd679d046cf9bcbd4dad92ba27b20cfc5f45b900063b84784793a`; judge_v1 `85f3529fca32faec681b3d4b1e6899b8620c383ed2aa54bc423241e2b7f4a10f`.
- Evidence reservation audit: `experiments/heldout-v2/evidence-audit.json`; source checks: `authoring-checks.json`; pre-run cluster membership: `components.json` (36 components).
- Code commit: record `git rev-parse HEAD` at run time. Parent must commit and record the final code state that includes the `--gold` support, the TI06 cross-check decision and any extraction merge before running. Do not mix an unpatched hybrid arm with a patched R3 arm.

## Authoring blindness
The cases were authored from current observations after ExtractionMerge confirmed the rebuild. No system answer, retrieval trace, score or judge output exists or was inspected for them. Observed old evidence was used only for exclusion. Unlogged candidate pools and human reading are unknown, so reserve exposure is not proven impossible.

Mechanical findings: 60 draft cases; all IDs exist; zero acceptable-evidence ID overlap with existing gold; zero overlap at dataset-period level with old gold or observed saved development evidence; all subject periods are 2024-Q1 through 2026-Q2. Counts: 20 factual lookup, 16 numerical comparison, 8 cross-source synthesis, 4 revision conflict, 6 ambiguity/insufficiency, 6 adversarial. Behaviours: 44 answer, 7 abstain, 3 clarify, 2 refuse, 4 ignore-injection-and-answer. That is 16 abstain/clarify/refuse/injection cases. Human review fields are null and no case is owner reviewed.

## Preconditions before any model call
1. Owner accepts the narrower claim, or approves additional untouched sources and a new confirmatory set. Without this the run is only a reserved-dataset diagnostic.
2. Owner has actually reviewed the 60 questions and labels, or the run is disclosed as unreviewed AI-drafted gold. Do not mark AI review as human review.
3. Code, corpus and prompt fingerprints above are re-verified. If any changes, write a dated amendment before running.
4. Validate:
   `uv run python -c "from labourlens.retrieval import gold; from pathlib import Path; e=gold.validate(Path('experiments/gold/heldout_v2_draft.jsonl')); print(e); raise SystemExit(bool(e))"`
5. Run the non-corpus test suite once. Never relabel from system outputs.

## Registered comparison
Single factor: retrieval `r3` versus `hybrid`. Fixed: `planner_v1`, `answer_v3`, rerank prompt `rerank_v1`, judge `gpt-6.1-terra`, same harness, models `gpt-6-luna` and `gpt-5.6-luna` for both planner and answer. Run once per arm. Include operational failures in the denominator. Do not run extra arms and then select among them.

Exact commands, one after another:
```
uv run labourlens agent-exp --split heldout --gold experiments/gold/heldout_v2_draft.jsonl --tag V2-r3 --retrieval r3 --pairs gpt-6-luna gpt-5.6-luna
uv run labourlens agent-exp --split heldout --gold experiments/gold/heldout_v2_draft.jsonl --tag V2-hybrid --retrieval hybrid --pairs gpt-6-luna gpt-5.6-luna
uv run labourlens eval --exp agent-heldout-V2-r3 --split heldout --gold experiments/gold/heldout_v2_draft.jsonl
uv run labourlens eval --exp agent-heldout-V2-hybrid --split heldout --gold experiments/gold/heldout_v2_draft.jsonl
```
The existing paired-bootstrap script is not in the repository; write the analysis from the rule below without changing it after seeing results.

## Acceptance rule decided in advance
A demonstrated R3 gain requires all of these:
- Complete paired data for the same 60 cases, both arms and both models.
- For each model, the 97.5% two-sided paired case-bootstrap interval for R3-minus-hybrid behaviour accuracy has a lower bound above zero (20,000 resamples, seed 20261031).
- Resampling whole evidence components from `components.json` also leaves each lower bound above zero.
- At least 10 independent components, review and reservation gates satisfied, no protocol deviation affecting only one arm.
- R3 has no more false-answer cases and no more reference-contradicting answers than hybrid for either model.

Otherwise report: gain not demonstrated. Report McNemar exact discordance as secondary, with family strata descriptive only. The current structured draft cannot satisfy the unseen-document claim; a pass is a reserved-dataset statistics-routing result only.

## Conditional cost estimate
[INFERENCE] Using saved original-held-out per-case costs (r3 .00193/.00343; hybrid .00124/.00271 USD for the two models) scaled to 60 cases: about $0.56 generation plus about $0.20 judging, about $0.76 in total. This is not a cap or a price check.
