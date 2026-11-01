# Numbers audit: do the numbers a reader sees match the committed artifacts?

Read-only audit, 1 Nov 2026, repository HEAD `1f8226b` plus the uncommitted edits present at the time (`docs/evaluation-report.md`, `tests/web/test_deck.py`, `web/static/presentation/slides.js`). Nothing but this file was written. No model, judge, embedding or network call. Every figure below was recomputed from `experiments/eval/*/{metrics.json,cases.jsonl}`, `experiments/heldout-v2/*.json`, `experiments/runs/dev-R*`, `experiments/threats/**`, `experiments/tool-fix/criteria.json`, `data/export/*.json`, `data/manifests/manifest.json`, `data/processed/observations.parquet`, `data/passages/*.jsonl`, `experiments/corpus-snapshots/*.json`, `specs/prices.yaml`, the gold files, and the owner's raw review exports in `~/Downloads`. Line numbers are as read; the working tree was being edited concurrently, so re-grep before editing.

Scope read: `README.md`, `docs/evaluation-report.md`, `docs/system-card.md`, `docs/innovation.md`, `docs/demo-script.md`, `web/static/data/report.json`, `web/static/presentation/*.js` (30 main slides, 18 appendix slides).

## 0. Bottom line

* **Every performance number I could recompute matches its artifact.** I found no wrong behaviour rate, interval, cost, latency, count, price or threat result in the README, evaluation report, system card, innovation note, demo script or `report.json` evaluation rows (23 of 23 rows byte-equal to their `metrics.json`; 13 of 13 threat rows equal).
* **The numbers are right; the human-review wording is not supported by the evidence.** The final review rounds were recorded at a median of 0.4 to 0.8 seconds per card. See section 3. This affects "reviewed card by card" and "403 own clicks" everywhere it appears.
* **Real mismatches** are stale or contradictory statements, not wrong arithmetic: the deck still says corpus v3 has no held-out evaluation (it does), `report.json` still says "45 owner-reviewed gold cards, 223 drafts", the README calls bootstrap intervals "Wilson", and the README defines behaviour accuracy as status *and content*.

### Answers to the two questions

1. **Are gold labels and the judge manual or AI?**
   * **Gold labels: AI-drafted** (`drafted_by` = claude agents on all 268 dev/held-out records; `ai:claude` on the 65 held-out v2 records). A person's approvals are recorded on top of them. In `gold_v3.7.jsonl` all 268 records carry `owner_review.decision_source = owner_manual`; the default file `draft_cases.jsonl` (v3.6, still what `eval` and `retrieval-exp` read) shows 223 `review_status: draft`, 42 `agreed_with_ai_suggestion`, 3 `owner_manual`. No label changed in v3.7 (checked: v3.6 and v3.7 have identical question, expected_behavior, evidence, facts, calculation fields). Four owner change-clicks were recorded and not applied (D-047).
   * **Judge: AI** (`gpt-6.1-terra`, `prompts/judge_v1.md`; same provider as the generators). Key-number recall, behaviour status, calculation correctness, false-answer and over-abstention flags are deterministic code, not the judge. `docs/human-review/judge-vs-owner.md` (new, untracked) recomputes cleanly (I reproduced its 3-class table 17/8/0, 0/5/1, 0/0/9 and "judge flagged 0 of 40").
   * **Human evidence in the strict sense** is small: the first-pack own verdicts (17 answer verdicts at median 8 s, J1 to J10, 3 gold) plus whatever the final rounds are worth (section 3).
2. **Is the data correct?** Yes for every figure checked: corpus counts, evaluation tables, threat tables, retrieval ladder, held-out v2 and tool-set-v2 results, price table, cost and latency. The corrections needed are listed in section 4 (all in the "overclaim", "stale" and "internal contradiction" classes).

## 1. MATCH: recomputed and equal

### Corpus and data (README 33 to 41, eval report 5, system card 5, demo-script preflight, deck notes)

| Claim | Recomputed | Source | Result |
|---|---|---|---|
| 85 sources | 85 manifest entries | `data/manifests/manifest.json` | MATCH |
| 36 datasets / 49 documents (27 PDF, 22 HTML) | `dataset_csv` 36, `report_pdf` 27, `release_html` 22 | manifest `source_type`, `mime_type` | MATCH |
| 52,020 observations, 4,300 in answer scope | 52,020 rows; `in_answer_scope` sum 4,300 | `data/processed/observations.parquet` | MATCH |
| 16,419 passages | 16,419 lines in 49 files | `data/passages/*.jsonl`; `corpus-snapshots/v3.json` | MATCH |
| 1,847 chunks | 1,847 | `corpus-snapshots/v3.json` | MATCH |
| 276 checks (269 pass, 7 warn) | 269 + 7 | `data/export/quality.json` summary | MATCH |
| v1 13,484 passages; v2 15,915 passages, 43,662 observations | same | `corpus-snapshots/v1.json`, `v2.json`, `v2-observations.json` | MATCH |
| 33 of 85 records open licence (deck notes) | `verified_open_licence` 33 (plus 3 `assumed_open_unverified`, 26 all-rights-reserved, 23 unresolved) | manifest | MATCH |
| Demo figures 4,620 − 3,830 = 790; 3,030 (2024-Q1); advance 10,700 / final 11,400; dataset 14,700 | same | `data/export/series.json`, `reconciliation.json`; gold DEV-004, DEV-011, DEV-501 | MATCH |
| `report.json` KPI cards, 14 EDA rows (start, end, change, min, max, count), 85 source rows, quality 269/7 | equal to `data/export/*` (cards differ only in a shortened label) | `kpis.json`, `series.json`, `sources.json`, `quality.json` | MATCH |

### Retrieval ladder (eval report 90 to 102, 408 to 416; system card; deck dynamic from `report.json`)

R0 / R1a / R2 / R3 hit@8 with intervals and MRR@10, corpus v1 (0.570 [0.492, 0.656] / 0.844 [0.781, 0.906] / 0.789 [0.726, 0.859] / 0.969 [0.938, 0.992]; MRR 0.324, 0.542, 0.764, 0.912) and corpus v2 (0.539 [0.453, 0.625] / 0.867 [0.805, 0.930] / 0.742 [0.672, 0.812] / 0.953 [0.914, 0.984]; MRR 0.314, 0.496, 0.642, 0.784), n = 128: **MATCH** `experiments/runs/dev-R-SUMMARY.md` and `extraction-v2-X1/dev-R-SUMMARY.md`. Earlier 24-case figures (merge120 BM25 hit@10 0.58 / MRR 0.31; merge200 hybrid 0.79 / 0.46): **MATCH** `experiments/runs/dev-dense-E6/*`.

### End-to-end tables (eval report 105 to 120, 283 to 297, 408 to 470; README; system card; innovation; demo-script)

Compared every cell in these tables to `metrics.json`: **all MATCH** (behaviour with CI, over-abstention, false answer, claim support, unsupported, fact coverage, contradiction, gold cited, calculation correct, p50/p95, $/case, judge cost).
* A1 to A5, both luna models: e.g. A3 `gpt-6-luna` 0.903 [0.865, 0.937], n=237, over-abs 0.030, false 0.030, support 0.887, coverage 0.728, gold cited 0.836, calc 0.750 (n=24), 15.4 / 37.0 s, $0.00212, judge $0.2442. A1 0.779 [0.728, 0.830], n=235, 10.7 / 23.3 s, $0.00137.
* Stratified family tables (A1 vs A3, held-out r3 vs hybrid): MATCH `by_family`.
* A3 failure lists (23 mismatches; over-abstention 7, false-answer 7, other 9 with named IDs) and the registered held-out failure table (HO-IDs per arm): MATCH `cases.jsonl`.
* Registered held-out, four arms: r3 0.871 [0.742, 0.968] / 0.839; hybrid 0.710 [0.548, 0.839] / 0.742 [0.581, 0.903]; all cost/latency cells: MATCH. Calculation n=5, 0.800 [0.4, 1.0]: MATCH.
* Paired: luna6 +0.161 [0.000, 0.323], 6 better / 1 worse; luna5.6 +0.097 [-0.032, 0.226], 4 / 1; history v3.2 to v3.4 (+0.129 [0.0, 0.29] then +0.097): MATCH `experiments/heldout/paired*.txt`. Corpus-v2 diagnostic (+0.065 [-0.065, 0.194], 3/1; +0.097, 4/1): MATCH.
* X1 (dev 0.886 [0.844, 0.924] / 0.911; held-out X arms 0.839, 0.839, 0.774 [0.613, 0.903], 0.742 [0.581, 0.871]): MATCH.
* X2 (0.903 [0.865, 0.941] / 0.916 [0.878, 0.949]; ungrounded 0.076 to 0.080 to 0.105 and 0.051 [0.025, 0.080] to 0.101 to 0.165 [0.118, 0.215]; claim support 0.860 [0.817, 0.904], 0.794 [0.742, 0.846]; p95 40.9 / 33.8; $0.00285 / $0.00463): MATCH. The 5.6 ungrounded intervals do not overlap (0.080 < 0.118): MATCH as stated.
* Gold counts: 268 = 237 dev + 31 held-out; families 75/50/40/40/40/23: MATCH. Gold v3.7 SHA `af3ad026…`, v3.6 `6169a9de…`, v3.5 `aac4b405…`, v2 gold `e3d16597…` (equals `heldout_v2_draft.jsonl` plus `owner_review` only; checked field by field): MATCH.

### Held-out v2 (README 17; eval report 484 to 496; deck notes)

* Arms 0.754 [0.646, 0.846], 0.708 [0.600, 0.815], 0.723 [0.615, 0.815], 0.723 [0.615, 0.831]; over-abstention 0.200/0.215/0.215/0.215; false 0/0.020/0/0.020; cost $0.00334/$0.00159/$0.00485/$0.00360; p50/p95 18.7/37.7, 10.6/18.3, 16.5/31.4, 10.9/18.3: MATCH.
* Paired luna6 +0.0462, 3/0, McNemar exact p 0.25, case interval (90%) [0.0154, 0.0923], component interval [0.0114, 0.102], 39 components, 22 with evidence, 10 source groups; luna5.6 0.000, 2/2, [-0.0462, 0.0462]; without MTI group +0.0333 [0.0, 0.0667]; seed 20261031, 20,000 resamples: MATCH `paired.json`.
* `numerical_comparison` 3 of 14 in all four arms (0.214); 16 primary mismatches, 13 over-abstentions, 11 numerical, 8 + 3 tool-gap classes, gold passage in evidence 33/34 and 31/34: MATCH `error-analysis.json`.
* "About $1.04 together": $1.0434 from per-case cost plus judge: MATCH.
* Commit order: freeze signed export 13:19:56Z = 21:19:56 SGT, commit `89c51d7` 21:20, results `6f80ec9` 22:00: MATCH `git log`.

### Tool set v2, X3 and V2post (README 21; eval report 500 to 520; deck slide "Fixing the calculation gap", appendix L)

X3 behaviour .903 to .895 and .916 to .899 (212 and 213 of 237); false-answer cases 6 to 7 for both (limit 6); ungrounded-in-new-tool-cases 1 of 10 and 3 of 18; cases with ungrounded 27 and 30; operational failures 0 and 1 (HTTP 520); calc 18 to 19 of 24; numerical 30 to 30 and 30 to 28 of 34; cost +4.5%: MATCH `experiments/tool-fix/criteria.json` and X2/X3 metrics. V2post: correct of 65: r3 luna6 49 to 59 (+0.154, 10/0, p 0.002, [0.077, 0.231]); r3 5.6 47 to 55 (+0.123, 9/1, p 0.0215, [0.046, 0.200]); hybrid 46 to 57 and 47 to 53; `numerical_comparison` 3 to 12, 10 (r3), 12, 9 (hybrid); false answers r3 0 to 0, hybrid 5.6 1 to 2; 54 non-targeted cases 49 to 50 and 47 to 48; post-fix r3 vs hybrid +0.031 both (3/1, 4/2); over-abstentions 13 to 3 and 14 to 7: MATCH `paired-postfix-*.json` and `cases.jsonl`. Cost $3.45 retained (generation 2.76, judging 0.70): MATCH.

### Threat suite (README 18; eval report 245 to 275; system card; demo-script)

Pre-guard: luna6 defended 35/36, naive 35/36; luna5.6 35/36; mini 34/36 [0.819, 0.985] and naive 32/36 [0.747, 0.956]; Wilson [0.858, 0.995]; $0.0370, 8.0 s; category counts 6/5/5/4/6/10; T-D01/T-I02/T-I03/T-I06 failure lists; canary mentions 2/0. Post-fix (corpus v2): strict 35/36 both defended, refined 36/36, naive 35/36. Final `m7-e2efix-20261031`: luna6 36/36 [0.904, 1.000] $0.0450 7.1 s; luna5.6 35/36 $0.0939 6.6 s; naive 35/36 $0.0418 / $0.0790: **all MATCH** `SUMMARY.md` and `runs/*.metrics.json`. `report.json` security rows: MATCH.

### Review counts and prices

* **403 = 268 + 65 + 40 + 30; all `owner_manual` in the final state:** MATCH the raw exports. Gold v3.7 268/268; pending export (SHA `d2905bfd…`) 330 decisions (gold 265, sources 30, answers 23, v2 6, J10 6, all `owner_manual`); earlier export (SHA `60f2ec21…`) supplies the 3 manual gold plus 40 answers, 30 sources; v2 own clicks 59 (signing export) plus 6 (redo) = 65. "229 never decided + 101 redo = 330": MATCH. "0 agreed with AI in the final state": MATCH (but see section 3).
* 268 / 65 / 40 / 30 / 403, answer verdicts 25 correct / 6 partly / 9 incorrect (final, after redo; 0 of 23 changed): MATCH. First-pack provenance 30 own + 95 agreed (42 gold, 30 sources, 23 answers): MATCH. Four change-clicks DEV-034, DEV-202, DEV-626, DEV-627 not applied: MATCH `pending-review (1).json`.
* Prices `specs/prices.yaml` ($/1M tokens): luna 0.10 / 0.50, 5.6-luna 0.20 / 1.20, 4.1-mini 0.40 / 1.60, terra 1.00 / 5.00, embedding-3-large 0.13, astra 10 / 50: MATCH the system card table, deck cost slide notes, eval report.
* Deck: **30 main slides, 18 appendix slides** (index + A to L + 5 "M" slides): MATCH `slides.js` and the commit message; demo-script's "ten chapters plus Summary" MATCH `renderScope` through `renderWork`.
* Rubric weights 10/20/25/10/15/10/10 and ten scenarios, ten requirements (deck slide 2 notes): MATCH the assessment PDF.
* No test counts are quoted in any of the scoped files (README, eval report, system card, innovation, demo-script, deck, `report.json`). `docs/submission-audit.md` quotes 782 passed; not re-run here.

## 2. MISMATCH and overclaim findings

| ID | Statement | Evidence | Correct value / verdict |
|---|---|---|---|
| M1 | README 11: "Wilson 95% intervals in brackets" | Dev, held-out, X-series intervals are case-bootstrap (2,000 resamples, seed 7; `harness.py:114`). Wilson applies only to the threat suite. A3 214/237 gives Wilson [0.866, 0.942], reported [0.865, 0.937]. | MISMATCH (method label). Say "95% case-bootstrap intervals (Wilson for the threat suite)". |
| M2 | README 11: "Behaviour accuracy means the answer's status **and content** agree with a gold label" | `behavior_ok = a["status"] == expected` (`answer/experiments.py:44`; `evaluation/harness.py:90`). The eval report's own metric table says "Correct status does not establish correct content". | OVERCLAIM. Behaviour accuracy is status-only. |
| M3 | Deck: "Corpus v3 ... has two measured evaluations ... no held-out or evidence-disjoint evaluation" (`ch8-limits.js:41`, `ch-work.js:202`); "No held-out or evidence-disjoint evaluation exists on corpus v3" (`ch5-evaluation.js:271`); "no held-out or evidence-disjoint run on corpus v3" (`ch-work.js:48`); "...and no held-out or evidence-disjoint evaluation" (`slides.js:312`, appendix A) | README and eval report: corpus v3 has three measured evaluations (X2, e2efix threat, held-out v2 with 65 evidence-disjoint-source cases), plus X3 and V2post. The deck's own slides present held-out v2. `docs/submission-audit.md` B3 says the other three were fixed in `1f8226b`; they were not. | MISMATCH. Internal contradiction in the public deck. |
| M4 | `report.json` `work.milestones` lines 65963, 65988: "45 owner-reviewed gold cards, 223 drafts" / "45 reviewed/223 drafts"; line 66013 "documentation refresh in progress" | Gold v3.7: 268 of 268 owner-reviewed. | MISMATCH (stale). Also `work.decisions` ends at D-045 (line 65916); D-046, D-047, D-048 exist in `docs/decisions.md` and are cited on the deck. |
| M5 | Deck gold-edit counts: "four post-run label or evidence edits (HO-029, HO-027, HO-023, HO-004)" (`ch-work.js:129`; also "four gold edits" in `slides.js:262/507` notes); "three owner-approved post-run edits" (`ch5-evaluation.js:111`) | Held-out records that differ between gold v3.2 and v3.5: **HO-004, HO-022, HO-023, HO-027, HO-029 = five** (HO-022 in v3.5; DEV-018 is a dev change). Eval report is right (HO-029 v3.3; three in v3.4; HO-022 v3.5). | MISMATCH. Three, four and five all appear. Correct: five held-out cases. |
| M6 | Deck `ch-work.js:164 to 170`, "Recorded spend: about $…" | Ledger sums only `evaluation.rows` (A1 to A5, X1, X2, H, X-held-out), threats, answers, rerank. It omits the three result sets absent from that list: V2 ($1.04), V2post and X3 ($3.45). Recomputed ledger = $17.88; with those = about $22.38. The "owner reports about $3 for X2 and e2efix" is not reproducible from files (file-derived about $2.54). | MISMATCH (understates by about $4.50 or 20%). |
| M7 | Eval report 216, `pending.py:528`, `review-inventory.md` "How to finish": owner decided the pending pack "with 'Manual only' on" / "turn on 'Manual only'" | The pack HTML (`private/human-review/pending-review/index.html`) has no such control. Every click is stamped `owner_manual` unconditionally (`decide()`: `s.source = 'owner_manual'`; export: `decision_source: 'owner_manual'`). | MISMATCH. The flag cannot show a manual-only filter was used. |
| M8 | Review inventory table: gold "original held-out cases" 31 and "14 extra" decided, "`owner_review` on each record of `experiments/gold/draft_cases.jsonl`" | `draft_cases.jsonl` has 45 reviewed: 42 `agreed_with_ai_suggestion`, 3 `owner_manual`; 223 `review_status: draft`. Only `gold_v3.7.jsonl` carries 268 `owner_manual`. | MISMATCH for the file named; `eval` and `retrieval-exp` still read `draft_cases.jsonl` (`harness.py:220`, `gold.py:59`), as do the demo script and README. |
| M9 | README 103: "The current gold file is v3.6" | README 22 and everywhere else: gold v3.7 is the review-provenance gold. Both are true of different files. | Ambiguous. State that v3.6 is the scoring file and v3.7 the provenance file. |
| M10 | Eval report 200, 216 vs source cards: "30 source decisions (19 matches, 11 minor)" as the current count | Final own-click source decisions: **18 matches, 12 minor** (pending export). 19/11 is the first export, labelled so in `ch-work.js:159` but not in the eval report's current-state sentence. | One source card changed between rounds; report 18/12 as final and 19/11 as first export. |
| M11 | Deck `ch7-mcp.js:155`: "MCP matched direct output on 33 of 33 datasets" | `report.json`: 22 identical rows plus 11 matching refusals, 0 different. | Misleading. Say 22 identical, 11 same refusals. |
| M12 | Eval report 90: "MEASURED, gold v3.2 (current)" | Retrieval ladder ran on gold v3.2 (`647b26a2…`), now archived; current is v3.6/v3.7. | Label wrong. Replace "(current)" with "(archived v3.2, hash recorded)". |
| M13 | System card 54: "Answers with ungrounded-number flags 7.6%" | Metric is `cases_with_ungrounded_numbers`, denominator all 237 cases; the eval report warns the "answers" name is a legacy alias. | Rename the row. |
| M14 | Innovation 3: "Registered results come from corpus v1 and v2" | Registered results are corpus v1 only (README, eval report). X1 (v2) is a separately labelled non-registered experiment. | Correct to "v1". |
| M15 | Deck `slides.js:169`: source line "Independent review of 16 sampled passages" | The 16-passage audit is an AI pre-review (`docs/human-review/ai-pre-review-passage-spot-check.md`: "independent machine-assisted pre-review, not the owner's review"); 4 of the 16 are HTML, not PDF, though the slide says "against the original PDFs". | OVERCLAIM. Say "AI review of 16 sampled passages (12 PDF, 4 HTML)". |

### Effects stated without intervals, or stronger than the interval allows

* Deck caption "Retrieval was the only change that mattered" (`slides.js`, experiment-ladder slide): A1 to A3 is descriptive with unequal n (235 vs 237) and no paired test; the dev set guided choices. Soften to "the only change that moved accuracy beyond the intervals".
* "Claim support fell for both" (`ch5-evaluation.js:276`, `evaluation.js:174`, deck notes): X2 intervals overlap A3 for both models (e.g. 0.794 [0.742, 0.846] vs 0.874 [0.829, 0.916]). The eval report and system card word it correctly ("lower point estimate, not a demonstrated regression").
* README 17: held-out v2 headline carries a 90% interval and a McNemar p (good), but README 15 reports over-abstention 3.0% vs 15.7% without intervals (A3 [0.8%, 5.1%]); same in demo-script five numbers and innovation.
* `paired.json` and `report.json` `heldout_v2.decision` carry `demonstrated_gain: true` and the statement "R3 gain demonstrated for the primary model ... under the preregistered rule". Docs correctly hedge (three cases, p = 0.25, not replicated on luna5.6, lower bound 0.0 without one source group). The machine-readable string is stronger than the prose; a reader quoting it will overclaim.
* Directory and `split` names: `experiments/eval/agent-heldout-V2post-*` and `agent-heldout-X-*` (and `split: "heldout"` for X rows in `report.json`, which the deck ledger labels "Agent held-out runs") use "heldout" for post-freeze diagnostics. Prose labels them correctly; the identifiers do not.

## 3. Human-review evidence: what the timestamps show (priority)

The README, eval report (lines 3, 200, 204, 216, 280), system card line 3, innovation 3/23, demo-script 7/61/98, `report.json` line 57829, deck (`slides.js:202`, `ch8-limits.js:9,22,33,61`, `ch-work.js:154,208`) say all 403 items were "reviewed card by card ... by the owner's own click". The raw exports contain a timestamp per decision (`persist()` stamps `new Date()` at each decision). From the files in `~/Downloads`:

| Round | Decisions | Span | Median gap between consecutive decisions | Gaps ≤ 2 s | Min gap |
|---|---:|---|---:|---:|---:|
| Pending-review export (final; SHA `d2905bfd…`) | 330 | 02:59:00 to 03:05:15Z (**6.2 min**) | **0.39 s** | 306 of 329 | 0.23 s |
| of which gold | 265 | 3.4 min | about 0.8 s per card | | |
| of which sources / answers / v2 | 30 / 23 / 6 | 44 s / 20 s / 2.5 s | | | |
| Held-out v2 signing export (`heldout-v2-review (2).json`), owner_manual | 59 | 13:18:02 to 13:19:54Z (**1.9 min**) | **0.8 s** | 47 of 58 | |
| First pack (`review-results (8).json`), owner_manual answers | 17 | 17.9 min | 8.3 s | 0 | |
| First pack, agreed-with-AI (gold / answers / sources) | 42 / 23 / 30 | 22 / 7 / 23 min | 5.4 / 6.1 / 7.3 s | 0 | |

What this does and does not establish:
* A card shows the question, expected behaviour, evidence passages and AI comments. Reading one in under a second is not plausible, and 306 of 329 gaps are ≤ 2 s. The final-round timings are consistent with rapid keyboard confirmation of pre-selected suggestions, not with reading each card. I cannot tell from the file whether a held key or a script was involved; the page's key handler does call `decide()` on every `keydown` with no `e.repeat` guard, so a held key would produce decisions at the observed order of magnitude or faster.
* `decision_source: "owner_manual"` is a hard-coded constant in the page for any click or key (see M7). It records that the UI received an input, not that the owner read the card, and no "Manual only" mode exists in this pack.
* Agreement with the AI suggestion is 198/198 for gold in the final own-decision set, with only four change-clicks, none applied. That is what rapid confirmation would also produce.
* The held-out v2 pre-registration sign-off rests on 59 own decisions recorded in 1.9 minutes (6 more in 50 s earlier). The freeze, hashes and commit order are real; the "owner approved all 65 cases card by card" claim is the part the timestamps do not support.
* The strongest human evidence is therefore the first pack (17 answer verdicts, 10 J1 to J10 decisions, 3 gold, about 8 s per card for answers), the four change-clicks, J10 (6 items in 18 s), and the owner's written policy decisions (D-031, D-034, D-035, D-036, D-047).
* The 40 answer verdicts equal the independent AI review's counts exactly (25 / 6 / 9). That is possible but the redo changed 0 of 23, consistent with confirmation of existing suggestions.

Recommended wording until a real re-review is done: "The owner confirmed the AI-drafted labels through the review interface (403 recorded confirmations, 4 change-clicks not applied). In the final rounds decisions were recorded at about 0.4 to 0.8 s per card, so this is acknowledgement, not independent verification. Treat the gold as AI-drafted and AI-judged with owner sign-off." A defensible human-review claim needs a smaller sample with timing: for example re-do 40 answers and 30 gold cards with a minimum dwell time, then report agreement with the AI.

## 4. Prioritised fix list

**P0: honesty of the human-review claim (change wording, not numbers)**
1. Replace "reviewed card by card ... by the owner's own click" with the wording in section 3 at: `README.md:11,22,156`; `docs/evaluation-report.md:3,200,204,216,280` (also 25, 395, 482, 488, 531); `docs/system-card.md:3`; `docs/innovation.md:3,23`; `docs/demo-script.md:7,61,98`; `web/static/data/report.json:57829` and `evaluation.limitations[0..1]` (regenerate with `labourlens build-report` from `report/build.py` strings); `web/static/presentation/slides.js:202,203 (notes),312`; `ch8-limits.js:9,22,32,33,61`; `ch-work.js:154,208`; `ch5-evaluation.js` none. The same sentence is in `docs/human-review/owner-review-final-summary.md` ("Exact wording for the report") and `review-inventory.md`; add the timing table beside it.
2. Remove "'Manual only' on" at `docs/evaluation-report.md:216`; fix `src/labourlens/review/pending.py:528` and `review-inventory.md` "How to finish".
3. Add the timing finding to `docs/human-review/review-inventory.md` and `owner-review-final-summary.md` so the "own click" provenance is not read as attestation of reading.

**P1: factual mismatches in public pages**
4. `web/static/presentation/ch8-limits.js:41`, `ch-work.js:202`, `ch-work.js:48`, `ch5-evaluation.js:271`, `slides.js:312`: state that corpus v3 has three measured evaluations (X2, e2efix threat, held-out v2) plus the tool-set-v2 runs (X3, V2post, not adopted), and that held-out v2 is evidence-disjoint at source level only (partial independence).
5. `README.md:11`: "Wilson" to "case-bootstrap"; "status and content agree" to "status matches the gold label (answer, abstain, clarify, refuse)".
6. `web/static/data/report.json:65963,65988,66013` and `work.decisions` (add D-046 to D-048): rebuild after fixing the source strings in `docs/progress.md` and `docs/decisions.md` parse.
7. Deck gold-edit counts: `ch-work.js:129` and `ch5-evaluation.js:111` to "five held-out cases (HO-029, HO-027, HO-023, HO-004, HO-022)"; `slides.js:262,507` notes "four" to "five".
8. `ch-work.js:164 to 170` ledger: include V2, V2post, X3 (about $4.50 more) or relabel as "spend in the evaluation rows only"; `docs/evaluation-report.md` "owner reports about $3" vs file-derived $2.54.

**P2: stale or ambiguous labels**
9. `docs/human-review/review-inventory.md` gold rows: point to `gold_v3.7.jsonl` and say `draft_cases.jsonl` shows 42 agreed-with-AI, 3 manual, 223 draft. Add a one-line note in the README that scoring still reads `draft_cases.jsonl` (v3.6) and the provenance file is v3.7 (`README.md:103`).
10. `docs/evaluation-report.md:200,216`: give the final source decisions as 18 matches / 12 minor, first export 19 / 11.
11. `web/static/presentation/ch7-mcp.js:155`: "22 identical, 11 same refusals, 0 different".
12. `docs/evaluation-report.md:90` drop "(current)"; `docs/system-card.md:54` rename the ungrounded row; `docs/innovation.md:3` "corpus v1".
13. `web/static/presentation/slides.js:169` source line: "AI review of 16 sampled passages (12 PDF, 4 HTML)"; notes line says "original PDFs".

**P3: strength of effect statements**
14. Soften "Retrieval was the only change that mattered" (`slides.js` experiment-ladder caption); "claim support fell for both" (`ch5-evaluation.js:276`, `web/static/evaluation.js:174`); add intervals to the over-abstention 3.0% vs 15.7% statements (README 15, demo-script five numbers, innovation 1).
15. Add a note in `experiments/heldout-v2/paired*.json` consumers (or the report's `heldout_v2.decision`) that `demonstrated_gain: true` is the D-042 rule output and not a confirmed-gain statement; consider renaming `agent-heldout-V2post-*` / `agent-heldout-X-*` in prose as "post-freeze diagnostic".

## 5. UNVERIFIABLE (owner-supplied or needs a run)

* Droplet serves corpus v3, commit `c297146`, `/healthz` fingerprint `d402120f6f8f` (README, eval report 5, demo-script, deck). `c297146` exists in git (31 Oct 14:49); the live state is not file-verifiable. Already labelled "owner-supplied".
* "Owner reports about $3 for X2 and the threat rerun"; "about $1.5 for a first X3 attempt": owner-reported; file-derived X2 plus e2efix is $2.54.
* The 198/198, 61/64, 38/39, 29/30 agreement-with-AI figures: the AI suggestions are not stored in the exports (`ai_basis` is empty in the pending export) and the private AI files were not recomputed; plausible given 4 changes, not re-derived.
* Full test-suite counts (782 passed per `docs/submission-audit.md`): not re-run in this read-only audit.
* Licence verification claims for the 33 "verified open" datasets (the second blind review already reports it could not reproduce three); not re-checked online.
* The "first-pack priorities (13 rows an AI pre-review marked partly or incorrect)" statement in the eval report (216).
