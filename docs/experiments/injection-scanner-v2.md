# Injection scanner v2: advance evaluation declaration

## Declaration, 2 November 2026, before improvement code

**PROPOSAL authorised by owner assignment:** evaluate and improve the deterministic passage scanner offline. No model calls, corpus rebuild or changes to frozen threat runs. This file is written before scanner improvements or any baseline measurement in this campaign. The earlier five regression probes are already known development examples and are not held-out evidence.

**Diagnosis from existing evidence:** the original five paraphrases all bypassed the old scanner; the subsequent six-pattern patch catches those exact examples and found zero hits across 16,419 local passages and 180 statistical text values. The 36-case end-to-end threat suite measures layered agent behaviour, not scanner recall, and cannot establish scanner detection for six attack classes. Its fresh 2 Nov run passes 35/36 under both scorers in all four configurations. Missing detection by class remains a hypothesis until this evaluation.

The scanner is trained on nothing: it matches bounded, English surface-form patterns after NFKC/control-character normalisation. Semantically equivalent paraphrases, non-English or leetspeak words, sentence breaks between trigger and target, markup between letters, indirect role-play and table-cell instructions can avoid those forms. Not every member of those classes necessarily bypasses it. A zero-hit corpus scan measures warnings, not source safety. Avoiding the original weakness requires negative as well as positive cases, a frozen unseen split before tuning, class-specific metrics, inspection of false alarms and independent testing. It does not require pretending regex recognises intent.

## Fixed case construction and split

Target: 120 passages, 60 malicious (10 each: paraphrase, translation/leetspeak, split sentences, markup hiding, role-play, indirect table instructions), 60 benign. The benign half comprises 30 independently worded policy-style hard negatives and 30 passages from the local corpus selected deterministically using report-policy keywords, with no scanner-based selection or rejection. Real source text and its per-passage records remain private under `data/scanner/`; only counts and content hashes are public. Attack and synthetic-negative text is AI-authored, not MOM/MTI quotations. Five examples per attack class and 15 examples per benign source go to development; the remainder go to test. Splits are assigned at authoring, not changed in response to outcomes. Related styles across splits mean this is not template-independent evaluation.

The public fixture and private corpus selection will be frozen with SHA-256 in `experiments/scanner/freeze.json` before baseline measurement and tuning. Missing private inputs must fail visibly, never silently reduce the denominator. No labelled case may move between splits or be relabelled to repair results.

## Metrics, rule and sequence

Report malicious recall and benign false-positive rate overall and by class, with Wilson 95% intervals (deterministic, including 0/n and n/n); no cost or end-to-end safety claim. Denominators and false-positive/negative IDs are saved. The fixed test has only 30 malicious and 30 benign, five malicious per class: intervals will be wide.

1. Run the unchanged current scanner on both splits, save baseline outputs under new ids. Record source hash. Test baseline aggregates may be reported, but do not inspect individual test cases or predictions for tuning.
2. Tune on development only. Test normalisation factors in this fixed cumulative order, one change at a time: HTML/entity/Markdown formatting; constrained whole-word leetspeak; bounded sentence-window joining. Reuse existing semantic patterns; no translation dictionary, model classifier or broad report-language keyword blacklist. Do not tune on test. Keep a factor only if dev malicious recall rises without increasing benign false positives. Negative results must be reported.
3. Freeze chosen code hash and configuration in `experiments/scanner/selection.json` before ONE current-scanner test measurement. Baseline on test is the predeclared comparator, not another tuning cycle. No further edits to the selected detector after looking at test results.
4. Acceptance: improve test malicious recall over baseline without more test false positives. This is descriptive acceptance, not statistical proof or deployment security certification. If unmet, report failure; do not change cases or thresholds.

CLI contract: `labourlens scanner-eval --split dev|test --experiment <new-id>` writes a new directory in `experiments/scanner/`, refuses overwrite, performs no network calls and requires the frozen private negatives. Public outputs contain identifiers, flags and aggregates, not corpus text. Offline tests cover metrics, immutable outputs, missing private data and benign policy wording.

## Security boundary and reporting commitments

Even an improved detector is a warning/quarantine layer beside untrusted-text isolation, no execution of text-supplied tools and schema-bound outputs. Non-English, semantic, long-range, adaptive and novel encodings remain outside reliable coverage. No claim that an instruction-like string actually compromises a model. Do not pool this set with the five prior probes or the threat suite. Report AI authorship, small n, lack of independent human labels and adaptive bypass risk. Results and exact commands will be appended below without replacing this declaration.

## Results (appended 2 November 2026)

Commands: `uv run labourlens scanner-eval --split dev --experiment v2-baseline-dev` (also `v2-markup-dev`, `v2-leet-dev`, `v2-window-dev` with `--profile markup|leet|window`), then `--split test` for `v2-baseline-test` and, once, `v2-selected-test`. Outputs are in `experiments/scanner/`. Frozen input hashes: `freeze.json`; chosen configuration: `selection.json`.

Authoring note: the inputs were frozen and the baseline run before any scanner change. Real-corpus negatives are private (`data/scanner/benign-v2.jsonl`); the only public record of them is aggregate counts. Several synthetic hard negatives were written to resemble the attack grammar, so a high false-positive rate on them is expected and was not tuned away.

| Run | Malicious flagged (recall) | Benign flagged |
|---|---|---|
| Dev baseline | 10/30 | 4/30 |
| Dev +markup | 15/30 | 4/30 |
| Dev +leet | 18/30 | 4/30 |
| Dev +window (selected) | 23/30 | 4/30 |
| Test baseline | 10/30 (0.33 [0.19, 0.51]) | 9/30 (0.30 [0.17, 0.48]) |
| Test selected, one run | 23/30 (0.77 [0.59, 0.88]) | 9/30 (0.30 [0.17, 0.48]) |

Test per class (5 each), baseline to selected: markup 0 to 5, sentence 0 to 5, encoding 0 to 3, paraphrase 3 to 3, role-play 3 to 3, table 4 to 4. Missed after selection: paraphrase-06 and -10, encoding-08 and -09 (non-English), roleplay-06 and -09, table-08. Benign false positives: 9 of 15 synthetic hard negatives, 0 of 15 private corpus passages, identical before and after. Negative result: paraphrase, role-play and indirect table instructions did not improve (semantic wording the pattern list does not cover), and no factor reduced false positives. Limits as in D-065.
