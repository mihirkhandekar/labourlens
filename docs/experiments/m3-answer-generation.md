# M3 experiment: structured, cited answer generation (dev split)

Status: dev only, nothing locked, held-out untouched. Gold labels are AI drafts, not reviewed by the owner. 30 in-scope dev cases: 24 expect an answer, 6 expect abstain, clarify or refuse. A single case moves a rate by 3 points (4 points on answer cases, 17 points on the six non-answer cases), so read differences under about 10 points as noise.

Code: `src/labourlens/answer/` (schema, context, validate, llm, pipeline, experiments); prompts in `prompts/` (`answer_v1*.md`, `repair_v1.md`); commands `uv run labourlens answer-exp --exp G1|G0|G3`. Tests: `tests/retrieval/test_answer_validate.py`. Decision: D-024 (claim-level citations with verbatim quotes). Raw model outputs contain MOM quotes and are kept local in `data/runs/`; committed: `experiments/runs/answer-dev-G*/` (metrics and per-case scores) and `*-SUMMARY.md`.

## What was built
Retrieve (hybrid RRF, merge200, text-embedding-3-large) -> label each source passage P1..Pn -> model returns a strict-schema JSON answer with claims, each citing a label and a verbatim quote -> deterministic checks (schema, label exists, quote is verbatim in the cited passage, status rules) -> at most one repair call -> otherwise marked invalid. Soft check: numbers in a claim not found in its cited text. Retrieved text is wrapped as untrusted data and the system prompt says not to follow instructions inside it.

## Metrics (all computed by code, none by a judge)
- `valid_rate`: passed all hard checks (after the repair, if used). `repair_rate`: needed a second call.
- `over_abstention_rate`: answer cases where the model did not answer. `false_answer_rate`: non-answer cases (abstain, clarify, refuse) where the model answered. These expose a trade-off that the plain behaviour accuracy hides.
- `numbers_complete_rate`: answered AND every key figure of the reference facts appears in the answer. A proxy for correctness, not a substitute for human review: it cannot tell a right figure for the wrong series.
- `gold_in_context_rate`: the gold passage was shown to the model (retrieval ceiling). `gold_cited_rate`: the answer cited a gold passage.

## G1: model comparison, retrieved evidence (k=5)
| model | valid | repair | behaviour | over-abstain | false-answer | numbers complete | gold in context | gold cited | p50 s | tokens (30 cases) |
|---|---|---|---|---|---|---|---|---|---|---|
| gpt-4.1-mini | 0.87 | 0.33 | 0.83 | 0.13 | 0.33 | 0.71 | 0.58 | 0.58 | 2.6 | 92,028 |
| gpt-5.4-mini | 0.97 | 0.33 | 0.70 | 0.25 | 0.17 | 0.63 | 0.58 | 0.50 | 2.7 | 91,101 |
| gpt-5.6-luna | 0.93 | 0.43 | 0.73 | 0.29 | 0.00 | 0.63 | 0.58 | 0.46 | 6.7 | 100,558 |
| gpt-6-luna | 0.93 | 0.30 | 0.60 | 0.42 | 0.00 | 0.50 | 0.58 | 0.38 | 5.6 | 96,349 |
| gpt-6-sol | 0.90 | 0.10 | 0.60 | 0.38 | 0.17 | 0.54 | 0.58 | 0.38 | 4.8 | 82,427 |
| gpt-6.1-terra | 1.00 | 0.10 | 0.57 | 0.42 | 0.00 | 0.42 | 0.58 | 0.42 | 6.3 | 79,550 |

## G0: same models with ORACLE evidence (gold passages put first, then the retrieved ones)
| model | valid | behaviour | over-abstain | false-answer | numbers complete | gold cited | p50 s |
|---|---|---|---|---|---|---|---|
| gpt-4.1-mini | 0.90 | 0.93 | 0.00 | 0.33 | 0.92 | 1.00 | 2.4 |
| gpt-5.6-luna | 0.90 | 0.87 | 0.08 | 0.17 | 0.88 | 0.88 | 6.1 |
| gpt-6-luna | 0.93 | 0.87 | 0.08 | 0.17 | 0.83 | 0.88 | 4.8 |
| gpt-6-sol | 0.97 | 0.83 | 0.13 | 0.17 | 0.83 | 0.83 | 5.3 |
| gpt-5.4-mini | 0.87 | 0.80 | 0.08 | 0.17 | 0.79 | 0.88 | 2.4 |
| gpt-6.1-terra | 1.00 | 0.73 | 0.21 | 0.17 | 0.71 | 0.79 | 6.5 |

## G3: how many chunks to show (k), two fast models
| config | valid | behaviour | over-abstain | false-answer | numbers complete | gold in context | tokens |
|---|---|---|---|---|---|---|---|
| gpt-4.1-mini k=3 | 0.83 | 0.77 | 0.21 | 0.33 | 0.50 | 0.50 | 74,539 |
| gpt-4.1-mini k=5 | 0.93 | 0.83 | 0.13 | 0.33 | 0.71 | 0.58 | 90,931 |
| gpt-4.1-mini k=8 | 0.90 | 0.90 | 0.04 | 0.33 | 0.75 | 0.69 | 143,018 |
| gpt-5.4-mini k=3 | 0.93 | 0.60 | 0.38 | 0.17 | 0.42 | 0.50 | 64,679 |
| gpt-5.4-mini k=5 | 0.90 | 0.73 | 0.17 | 0.00 | 0.58 | 0.58 | 86,984 |
| gpt-5.4-mini k=8 | 0.90 | 0.80 | 0.08 | 0.17 | 0.67 | 0.69 | 134,744 |

## What the data says (MEASURED, dev n=30)
1. **Retrieval is the main bottleneck, not the model.** With retrieved evidence the gold passage is shown in only 58% of cases and no model gets above 0.71 complete numbers. With gold evidence placed first (G0) every model rises sharply (0.71 to 0.92 for gpt-4.1-mini). Showing more chunks (k=8) lifts gold-in-context to 0.69 and every quality metric, at about 55% more tokens.
2. **Models differ in temperament more than in skill.** The gpt-6 family and gpt-5.6-luna abstain or ask for clarification often (over-abstention 0.29 to 0.42) and rarely answer a question they should not (false-answer 0.00 to 0.17). gpt-4.1-mini answers the most, scores highest on answer cases and false-answers on 2 of 6 non-answer cases (an ambiguous population question and one it should have abstained on). Neither is "better" without a policy choice about which error is worse for policy researchers; wrongly answering is the more dangerous one here.
3. **Run-to-run noise is real.** G1 was run twice with the same prompt; rates moved by up to 0.07 to 0.17 (for example gpt-6-sol false-answer 0.00 then 0.17), and the second G1 run also used a corrected context header, so it is not a pure repeat. Single runs on 30 cases cannot rank neighbouring models.
4. **Validation matters.** 10% to 43% of cases needed a repair call and 0 to 13% stayed invalid. Failures were mostly quotes not copied exactly or longer than 40 words (all models), and one missing reason. Without the verbatim check these answers would have carried invented quotes.
5. **Latency and size.** The mini models answer in about 2.5 s at p50; the gpt-6 and gpt-5.6 models take 4.8 to 6.7 s for similar token counts. Token totals per 30 cases are about 80,000 to 100,000 (about 3,000 per case) for k=5.

## Limits
- Six non-answer cases only; rates on that slice move in steps of 17 points.
- Draft labels, one model family (OpenAI), temperature and reasoning settings left at API defaults. Cost in currency is not reported: prices for these models were not given and are not known to me.
- `numbers_complete_rate` is a proxy; fact correctness, citation support and wording have not been judged (M6: LLM judge flagged as AI, plus the owner's human review).
- Numerical-comparison cases and prompt-injection fixtures are not covered yet (M4 and M5).
- Prompt wording was not varied. Tuning the prompt on six non-answer dev cases would overfit, so a prompt comparison should wait for more dev cases or be done on held-out-safe fresh cases.

## Candidate default (PROPOSAL, owner decision)
Retrieval: hybrid, k=8. Model: a mini model for latency (gpt-4.1-mini or gpt-5.4-mini) with the abstention policy decided by the owner; or gpt-5.6-luna if avoiding false answers matters more than latency. Not frozen.
