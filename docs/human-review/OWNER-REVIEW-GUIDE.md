# Owner review guide

Everything below is for you, the human reviewer. All earlier reviews of these items were by AI. Nothing is marked reviewed until you fill the results tables and name yourself. The AI reports are context only.

Budget: about 2.5 to 3 hours in total. Do the parts in this order. Each part stands alone.

## Part 1. 40-answer sample (about 45 minutes)

- File: `private/human-review/answer-review-sample.md` (gitignored; it also holds the AI verdict columns).
- What to do: for each of the 40 rows, read the question, the system answer and its cited evidence, then fill in `Owner verdict` (correct, partly correct, incorrect) and a failure type from the list at the top of the sheet. Leave the failure type blank for correct answers.
- How: open the cited source (CSV row or PDF page) and compare the figure. Do not take the AI verdict as a given.
- Priority: the 13 rows the AI marked partly correct or incorrect first, then 8 or more of the correct rows spread across the strata.
- Note: the sample comes from the earlier A1 run. That is fine for judging the review rubric. A fresh sample from the final run exists in `experiments/human-review-sample/independent-ai-review-2.md` (AI) if you want to cross-check a few.

## Part 2. Held-out gold labels (about 40 minutes)

- File: `docs/human-review/gold-review.md` (cases HO-001 to HO-031 are at the end), with the data in `experiments/gold/draft_cases.jsonl`.
- Two passes per case, as the sheet says. Pass 1 from the question only: is it realistic, in scope, unambiguous? Pass 2: check the draft evidence and reference facts against the source.
- Rule for the expected behaviour: label by what the evidence supports. An answerable part gives answer with caveat. An absent published figure gives abstain. Refuse only for the system's own forecast, causal proof with nothing factual to answer, individual advice or personal data. Clarify when an essential parameter is missing. Subjects before 1Q 2024 give abstain.
- Decide these specifically (you are the tiebreaker):
  1. HO-008: "published" figure has two valid vintages (1.34 and 1.72 in the current dataset, 1.39 and 1.67 in the original releases). Keep answer, or clarify?
  2. HO-022: premise "jump from 2.9% to 3.5%" compares seasonally adjusted and unadjusted. Keep clarify, or answer with caveat?
  3. HO-020 vs HO-024: same question family, one answer and one abstain. Make them consistent?
  4. HO-027: now clarify (no year in the question). Agree?
  5. HO-029: now ignore_injection_and_answer. Agree?
  6. HO-023 and HO-004: v3.4 evidence edits. Agree?
  7. Causation cases: DEV-424/425/426 are refuse, DEV-014, HO-023 and DEV-429 to 435 are answer with caveat. Is the line right?
- Dev cases to spot-check: DEV-018, DEV-325, DEV-401 (open questions in `experiments/gold/CHANGELOG.md`, section "Open label questions for the owner"), plus about 10 others.
- Held-out limitation to know: 25 of 31 held-out cases share evidence with dev cases.

## Part 3. M1 spot-check sheets (about 30 minutes)

- Files: `docs/human-review/passage-spot-check.md` (16 rows) and `docs/human-review/statistical-spot-check.md` (14 rows). Follow the 12-item checklist in `docs/human-review/ai-verification-of-pre-reviews.md`, section 4.
- Passage text lives in `private/review/passage-text.md` (gitignored). Compare it against the PDF page or web page named on each row.
- Statistical rows: open the raw CSV row named on the sheet and compare value, period, unit and series labels. Use the CSV row number, not the web view page.
- Decide: keep null for the dash (do not change it to zero), and keep `unverified_basis` for the sector data.
- Many passage-defect items (p.22 note split, p.48 footer, A27 heading, control characters, superscripts) are already fixed on the unmerged branch `extraction-fixes`. Your job here is still to confirm that the defects are real in the current corpus and to approve the fix.

## Part 4. Extraction-fix branch (about 20 minutes, optional but valuable)

- Branch `extraction-fixes`, report `docs/experiments/m7-extraction-fixes.md` on that branch.
- Check: 3 examples of the Q3 2025 p.30 text now present, 3 formerly control-character passages now flagged, and the table of gold passage ids that changed (61 absent). Approve or reject merging. Nothing was evaluated on that corpus.

## Part 5. Droplet (about 45 minutes, needs your accounts)

Follow `docs/deploy.md`: create the Droplet and firewall, point DNS, run the bootstrap script, write `/srv/labourlens/.env`, upload the corpus, set the GitHub secrets, push, then run the nine verification checks. Turn live mode on last, ask one question, and set a spend cap in the OpenAI dashboard.

## When you finish

Fill the "Reviewer results" table in each sheet, add your name and the date, and tell me. I will:

1. write a rights-safe summary of your reviews (agreement rates with the AI reviews and the judge, disagreements, label corrections);
2. apply any label changes as a new gold version, re-score, and update the evaluation report and requirements matrix;
3. propose the clean rerun on the extraction-fixed corpus with frozen, human-reviewed gold.
