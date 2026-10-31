# Held-out v2: owner review and approval (one page)

## What and why
`experiments/gold/heldout_v2_draft.jsonl` holds 65 AI-drafted test questions on six sources that no earlier experiment touched. After a run, they decide whether the retrieval change (`r3` versus `hybrid`) really helped. They only count if a human has checked them **before** any run. This page-and-command pair is that check. It is separate from the big review pack: one small file (about 3 MB), 65 cards.

## Three steps
1. **Build and open the page:** `uv run labourlens v2-review-pack`, then open `private/human-review/heldout-v2-review/index.html` in your browser (it is private: it contains MOM and MTI text, so never commit or share it).
2. **Read the 5 flagged AI-article cases first** (HO-V2-020, 021, 022, 052, 053; the page puts them first with a yellow note). Then go through the rest with the keyboard: `A` approve, `C` change the label (then `1` to `5` for the new behaviour and a one-line reason), `X` reject (one-line reason). Type your name, click **Download review file**.
3. **Preview and sign:** `uv run labourlens v2-approve --review-export <the downloaded file>` prints a plain summary and changes nothing. If it says nothing blocks signing, run the same command with `--write`.

Nothing is filled in for you: a card counts only after you press a button. About 65 cards, most take one look and one key. Your choices are saved in the browser as you go; download the file before closing.

## The independent AI review beside each card
Three separate AI reviewers (A, B, C, one model family, so their mistakes are correlated) checked all 65 cases before you. Each card shows their verdicts, confidence and reasons, plus the computed **AI consensus**: a verdict given by at least 2 of the 3 (with the same new behaviour when it is a change); otherwise “split”. The top of the page lists the 4 cases that need your judgement (HO-V2-043, 020, 021, 022) and the systematic issues they raised. **This is not human review.**

- **Agree with AI** (key `G`) exists only where there is a consensus and its agreeing reviewers are at least medium-confident, and it unlocks a few seconds after the card appears. It is recorded as `agreed_with_ai_suggestion`, never as an independent human judgement. `v2-approve` checks it against the hashes of the three AI files, reports your own clicks and your agreements separately, and writes both counts into the signed block with the words “owner decisions, per-card agreement with AI, not independent inter-rater evidence”.
- **Review the 61 unanimous approvals quickly** steps through only those cards, one key press each (`G` to agree, `A` to approve yourself, `C` or `X` to disagree). There is no select-all.
- HO-V2-043 is a 2-to-1 approve whose two approvals are low-confidence, so it gets no one-click button: choose Approve (keep with a caveat), Reject (drop) or Change label yourself.
- A summary you can commit (counts, who disagreed and why, agreement statistics) is in `docs/human-review/heldout-v2-ai-review-summary.md`; regenerate it with `uv run labourlens v2-ai-summary`. The raw reviewer files stay under `private/human-review/heldout-v2-ai/`.

## The five AI-article cases (D-031)
The MTI article was published in Q2 2026, but the study behind it uses firm data from 2018 to 2024, and the article itself says its analysis stops at 2024. D-031 and the guide say a question about a period before 1Q 2024 gets an abstention, whatever the publication date. The three cases that ask for the study's estimates (020, 021, 022) therefore need your ruling: keep as answerable, relabel to abstain, or drop. The recommendation (an AI's, not a ruling) is to **relabel to abstain**. It lowers the independent evidence groups from 22 to 20, exactly the minimum, so afterwards you cannot reject any other case that holds its own group; the page shows this count live. HO-V2-052 and 053 are abstentions whichever way you rule; the sixth AI-article case (043) follows your choice on 022.

## What happens after approval
`v2-approve --write` creates a **new** file, `experiments/gold/heldout_v2_v1.jsonl` (the draft is never edited), records your name, time and reason on every case, and appends a **signed block** to `experiments/heldout-v2/FREEZE.md`: the SHA-256 of the new gold file and of your export, git HEAD, corpus fingerprints, prompt and price hashes and the exact commands. It refuses if fewer than 60 cases, fewer than 8 non-answer cases or fewer than 20 independent evidence groups remain, or if the corpus content, prompts or prices differ from the recorded hashes. A change to the manifest alone is recorded as a note.

The run is separate and spends money (about a dollar at saved prices): `uv run labourlens v2-run --gold experiments/gold/heldout_v2_v1.jsonl` prints the five registered commands; add `--yes` to run them (needs `OPENAI_API_KEY`, and only works for the gold file signed in FREEZE.md).

## What you are NOT agreeing to
- Not agreeing that the system is good or that `r3` is better: approval only fixes the questions and expected answers.
- Not agreeing to any score: results are computed later by the preregistered rule (D-042), and may show no demonstrated gain.
- Not signing for the 2024 sibling-edition, wording-similarity or shared-system limits recorded in FREEZE.md; they remain.
- Not changing anything after the run: relabelling or dropping a case once results exist is not allowed.
- Not a legal or publication clearance: the page and export contain MOM and MTI text and stay private.
