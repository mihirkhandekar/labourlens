# M7 evaluation fixes (31 Oct 2026)

Source: `docs/human-review/e2e-review-evaluation.md`. No model, network, fetch, build or index command was run. No raw run under `data/runs` and no frozen raw output was modified. Each change below was checked against the code or artifacts before it was made.

## Findings and what changed

| Finding | Verdict | Change |
|---|---|---|
| P1-1 `agent-exp` overwrites frozen runs | Confirmed (`agent/experiments.py` wrote raw runs, scores and SUMMARY unconditionally) | `agx.run` raises `FileExistsError` before any API call if the raw run, scores, metrics or SUMMARY for the experiment id already exist. `--force` overrides. Test: `tests/evaluation/test_guards.py`. |
| P1-2 `eval` rescores under a different gold | Confirmed | `eval` compares the gold file hash with the hash recorded for each run (its saved `metrics.json`, else the raw run's `generation_provenance`) and raises `GoldMismatch` before writing anything. `--allow-gold-mismatch` proceeds with a warning. Every `metrics.json` already carries `gold_sha256`; this is now enforced as a gate. Corpus identity is covered through the gold hash: v3.5 goes with corpus-v1 passage IDs, v3.6 with corpus-v3 IDs. |
| P1-7 `paired` ignores which gold was used | Confirmed | `paired.check_gold` requires every arm's `metrics.json` to record the given gold file's SHA-256; same `--allow-gold-mismatch` escape. The check that arms share an `agent_config` was not added (deferred). |
| gold v3.5 not in the tree | Confirmed | `experiments/gold/archive/gold-v3.5.jsonl` (SHA-256 `aac4b405b51c…`, commit `456ffa9`). Also v3.2 (`647b26a2…`, `b813274`), v3.3 (`96ec51ba…`, `cf6a4fe`) and v3.4 (`050bb40b…`, `43af8d5`); all four hashes are recorded in the changelog or saved metrics. Hash test in `tests/evaluation/test_guards.py`. Rescore frozen runs with `--gold experiments/gold/archive/gold-v3.5.jsonl`. |
| P2-2 `eval` with no raw runs writes a header-only report | Confirmed | `eval` raises `FileNotFoundError` when no raw run matches; nothing is written. |
| P2-1 p95 one rank low | Confirmed (see below) | Nearest rank `ceil(0.95 n)`; 22 committed metrics files and their REPORT.md lines patched from the committed `cases.jsonl` seconds. |
| P2-6 error panel pools stale score files | Confirmed in substance; the reviewer's 539 includes files the site never read (X runs); the site's 418 came from generation-time A1-A5 scores | Panel counts now come only from the rescored `experiments/eval/agent-dev-A[1-5]/*.cases.jsonl` records; rows with no current case record are dropped. Test added. |
| P1-6 v2 acceptance rule too strict | Confirmed by simulation | Rule revised before any run: see below. |
| P1-3 held-out freeze not independently timestamped; missing `generation_provenance` | Confirmed (text for DocsFix below) | Documentation only; nothing can be repaired retroactively. |

Not fixed (outside the assignment or needs a decision): P2-3 (`scripts/paired_v1.py`), P2-4 (shared-case paired A1 to A3 interval), P2-5 (calculation scorer leniency; changing it would change published calculation numbers), P2-8 (untracked snapshot directories belong to DataFix/parent), P2-9, P2-10, P1-4, P1-5, P2-7 (docs).

## p95 latency: before and after (seconds, from `experiments/eval/*/*.metrics.json`)

The reviewer's claim holds: the old code took rank `int(0.95 n) - 1` (0-based), one rank below the nearest-rank value. Held-out r3 `gpt-6-luna` was 26.6 and is 27.8; dev A3 `gpt-6-luna` was 35.6 and is 37.0. Every other metric is untouched; only `latency_p95_s` and the matching REPORT.md row changed.

| Run / model | n | before | after |
|---|---:|---:|---:|
| A1 gpt-4.1-mini | 235 | 10.7 | 10.8 |
| A1 gpt-6-luna | 235 | 22.8 | 23.3 |
| A2 gpt-5.6-luna | 235 | 20.6 | 21.2 |
| A2 gpt-6-luna | 235 | 24.7 | 25.9 |
| A3 gpt-5.6-luna | 237 | 34.4 | 34.7 |
| A3 gpt-6-luna | 237 | 35.6 | 37.0 |
| A4 gpt-5.6-luna | 237 | 34.7 | 36.1 |
| A4 gpt-6-luna | 237 | 35.6 | 35.9 |
| A5 gpt-5.6-luna | 237 | 34.0 | 34.5 |
| A5 gpt-6-luna | 237 | 37.5 | 37.6 |
| X1 gpt-5.6-luna | 237 | 34.0 | 34.2 |
| X1 gpt-6-luna | 237 | 33.5 | 35.4 |
| H-hybrid gpt-4.1-mini | 31 | 9.0 | 9.2 |
| H-hybrid gpt-5.6-luna | 31 | 19.7 | 20.0 |
| H-hybrid gpt-6-luna | 31 | 18.5 | 22.5 |
| H-r3 gpt-4.1-mini | 31 | 21.6 | 22.0 |
| H-r3 gpt-5.6-luna | 31 | 36.1 | 36.2 |
| H-r3 gpt-6-luna | 31 | 26.6 | 27.8 |
| X-hybrid gpt-5.6-luna | 31 | 17.4 | 18.7 |
| X-hybrid gpt-6-luna | 31 | 25.5 | 25.8 |
| X-r3 gpt-5.6-luna | 31 | 31.8 | 34.4 |
| X-r3 gpt-6-luna | 31 | 43.3 | 43.9 |

Prose and tables elsewhere that quote the old values need the same update (docs are not edited here): `docs/evaluation-report.md` (A3 and A4 rows, the held-out r3 row, the cost paragraph, the summary table), `docs/system-card.md` line 53, `docs/innovation.md` table, `docs/demo-script.md` line 53. The site reads the metrics files, so `report.json` follows once the committed files are rebuilt. `report.json` is built from the committed tree: re-run `uv run labourlens build-report` after these changes are committed.

## Site error panel: before and after

Pooled over A1-A5 (all models), counts of case records.

| | before (generation-time scores, 2,612 rows) | after (rescored cases, 2,597 rows) |
|---|---:|---:|
| behaviour mismatches | 418 | 393 |
| invalid output | 120 | 120 |
| tool errors | 191 | 191 |
| ungrounded-number warnings | 286 | 285 |
| operational failures | 0 | 0 |

The 15 dropped rows are cases removed from the gold or whose question text changed after the run, which the harness already excludes from the headline tables. `web/static/presentation/ch5-evaluation.js` names `experiments/runs/agent-dev-A1..A5/*.scores.jsonl` as the panel's source file list and should say `experiments/eval/agent-dev-A1..A5/*.cases.jsonl`.

## Held-out v2 acceptance rule: revision 2 (D-042)

Simulation: `experiments/heldout-v2/power.py`, output `experiments/heldout-v2/power.txt` (seed 20261101, 2,000 simulations per cell). Full table, assumptions and trade-off: `experiments/heldout-v2/FREEZE.md`. Summary of the probability that the rule passes (ranges over four assumption sets):

| rule | effect 0 | +5 | +10 | +16 |
|---|---:|---:|---:|---:|
| revision 1 (both models, 97.5% two-sided, two vetoes) | 0.0-0.1% | 1.5-2.6% | 11-19% | 31-53% |
| revision 2 (primary model `gpt-6-luna`, one-sided 95%, case and component bootstrap, false-answer veto; second model reported as replication) | 3.0-5.2% | 21-24% | 45-54% | 68-84% |

The reviewer was right that the Bonferroni allowance bought nothing under a conjunction. Revision 2 is weaker and passes by chance about 5 times in 100 at zero effect. The contradiction veto was moved to a reported guard because its cost was not simulated; the false-answer veto stays (cost about 1 point of power). `paired.py` implements it; `decide` now returns `demonstrated_gain_primary` and `replication_models`.

### Text for DocsFix: D-042 for `docs/decisions.md`

**D-042 (31 Oct 2026): held-out v2 acceptance rule revised before any run.** Context: the review of the first v2 rule (both models, 97.5% two-sided case and component bootstrap lower bounds above zero, no added false or contradicted answers) found the Bonferroni allowance redundant under a conjunction and the rule underpowered. A simulation on the real structure (65 cases, 39 components; `experiments/heldout-v2/power.py`) gives a pass probability of 11-19% at a true +10 points and 31-53% at +16. Options: keep (about 0% false positives, rarely passes); both models at one-sided 95% (19-30% and 46-67%); primary model only at one-sided 95% (45-54% and 68-84%, false-positive rate 3-5%); either model passes (67-82% and 89-98%, false-positive rate 6-10%). DECISION: primary model `gpt-6-luna` only, lower bound of the one-sided 95% bound above zero under both case and component bootstrap, at least 20 evidence components, no added false answers; `gpt-5.6-luna` reported as replication and never gating; contradicted answers reported, not a veto. Trade-off: the rule is weaker and is expected to pass by chance about 5% of the time at zero effect, and it remains underpowered at +5 points. Made before any generation, scoring or output inspection for these cases; implemented in `src/labourlens/evaluation/paired.py`. Reversible: any further change needs a new dated entry before the run. Approval: pending owner sign-off with the rest of the FREEZE preconditions.

### Text for DocsFix: README replacement for the A3 re-run commands (README lines 91-92)

Replace the instruction to run `labourlens agent-exp ... --tag A3` and `labourlens eval --exp agent-dev-A3` with:

> The registered dev and held-out raw runs are not re-run by these commands. `labourlens agent-exp` now refuses to overwrite an existing experiment id (it needs `--force`, which destroys frozen evidence). To exercise the pipeline, use a throwaway tag, for example `uv run labourlens agent-exp --split dev --tag SMOKE --pairs gpt-6-luna` (paid API calls; needs `OPENAI_API_KEY`), then `uv run labourlens eval --exp agent-dev-SMOKE`. To re-score a frozen run offline, pass the gold file it was scored on, for example `uv run labourlens eval --exp agent-dev-A3 --no-judge --gold experiments/gold/archive/gold-v3.5.jsonl`; `eval` and `paired` refuse a gold file whose SHA-256 differs from the one recorded for the run unless `--allow-gold-mismatch` is given. The HEAD gold file is v3.6 (`6169a9de…`); the published A1-A5 and H-* metrics were scored on v3.5 (`aac4b405…`), now archived at `experiments/gold/archive/gold-v3.5.jsonl`.

### Text for DocsFix: "Provenance limits" paragraph (for `docs/evaluation-report.md`)

**Provenance limits.** The original held-out freeze cannot be shown to precede its results. `experiments/heldout/FREEZE.md` has one commit, `d894dae`, which is also the commit that adds the held-out results, and that commit changes `agent/graph.py` and `agent/tools.py` after the freeze HEAD `617d168`. The held-out comparison was therefore pre-registered by a written record that git cannot time-stamp independently, and "same code for both arms and for dev" rests on the author's statement. Raw `H-hybrid` records carry `generation_provenance` (gold `647b26a2…`, HEAD `617d168`); raw `H-r3` records and all dev A1-A5 records have `generation_provenance: null`, so their generation-time gold, prompts and code cannot be read from the runs. What is recorded is a scoring-time fingerprint in each `metrics.json` (gold hash, prompt hashes, price table, HEAD at scoring), which is not proof of what generated the run. The raw runs themselves are local only (`data/runs`, gitignored). The held-out v2 set is designed to avoid this: its gold, corpus, prompt and price hashes are written before any run, `agent-exp` records generation provenance and refuses to overwrite a run, `eval` and `paired` refuse arms scored under a different gold, and the parent will commit `FREEZE.md` and the code before the run so that the commit order shows the freeze came first.

**Packaging note (2 Nov 2026).** The historical `docs/demo-script.md` named above is now kept locally as `study/demo-script.md`, not in the repository. The public demonstration deliverable is `docs/demo-plan.md`; historical line numbers above describe the original script.
