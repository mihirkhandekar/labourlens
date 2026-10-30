# Innovation assessment

Author: LabourLens project. Date: 30 October 2026. This note covers what is distinctive in the design, why it matters for policy research, what was tried and dropped, and what remains weak. It makes no claim about production impact. Evaluation results are not summarised here. See section 10 of the interactive page and `experiments/eval/`.

## What is distinctive

**1. Data-quality notes written by code, shown next to the evidence.** The tools in `src/labourlens/agent/tools.py` inspect the rows they return. They add a note when a period inside the requested range has no row, when the source marks a value as unavailable, when one result mixes indicators, populations or adjustments, and when the advance and final MOM releases of one quarter are both in the evidence. `src/labourlens/answer/context.py` places the notes in a separate block that cannot be cited. Rule 9 of `prompts/answer_v4.md` tells the model not to estimate a missing value and to report conflicting versions with their release stage.

*Why it matters.* A researcher needs to know that the figure is missing or revised before using it. A model left alone tends to smooth over such gaps. A note produced by code does not depend on the model noticing.

**2. Claim-level citation with verbatim-quote validation.** Each claim carries labelled citations and a short quote of at most 40 words. `src/labourlens/answer/validate.py` rejects the answer when a label was not in the context, a quote is not found in the cited item after whitespace and quote-mark normalisation, or a flagged item is cited. One repair attempt follows. Numbers in a claim that are absent from the cited text are listed separately (D-024).

*Why it matters.* A reviewer can check each claim against its quoted source in seconds. The check shows that the cited text contains the quote. It does not show that the text supports the claim. Support is scored separately in the evaluation.

**3. A bounded agent that fails closed on operational failures.** The graph in `src/labourlens/agent/graph.py` limits rounds, calls, time and retries. A tool outage, a timeout or a planner outage ends in `operational_failure`. The system never reports it as "no evidence". Tests for these paths are in `tests/retrieval/test_agent.py`. The threat model reports that for one model, 7 of 10 MCP fault cases ended in an operational failure and no answer (`docs/threat-model.md`).

*Why it matters.* In policy work, "the tool was down" and "the data does not exist" lead to different decisions. Keeping them apart protects the reader from a false absence.

**4. Hostile MCP server fixtures.** `src/labourlens/mcp/evil.py` is a test server with 14 modes, among them instructions inside result rows, an oversized reply, a schema change, a crash, a slow reply, an extra tool, a wrong version and a wrong name. The client in `src/labourlens/mcp/client.py` is tested against 13 of them (`tests/mcp/`, `src/labourlens/mcp/demo.py`, `experiments/threats/cases.jsonl`). The mode `poisoned_resource` is defined but no test or case refers to it. One mode carries an instruction that the heuristics do not catch. `docs/mcp-demo-transcript.md` records that it passes the client and that later layers handle it.

*Why it matters.* An MCP server is another party's code. Testing the client against hostile servers shows where the trust boundary holds and where it does not.

**5. A label-by-evidence rule for abstention.** Gold cases are labelled by what the evidence supports. If part of a question can be answered, the system answers that part and states caveats. If the question asks for a published figure that does not exist, the system abstains. It refuses only for its own forecast, a proof of causation with nothing factual to answer, individual advice and personal data. Clarification is for ambiguity that changes the answer. The rule and its effect on each case are in `experiments/gold/CHANGELOG.md`, section v3.

*Why it matters.* Without one rule, similar questions get different labels and the scores measure the labelling. With the rule, a causal question such as "did AI cause retrenchments" is scored on whether the system gives the published figures and a caveat.

**6. AI-reviewed gold set with a change log.** The gold set `experiments/gold/draft_cases.jsonl` has 268 cases (237 development, 31 held-out) according to the change log. Four AI reviews (`experiments/gold/ai-review/`) and two further AI reviews (`experiments/gold/ai-review-2/`) checked labels, evidence and numbers. Every change is listed with its reason, including changes not applied. All 268 cases have `review_status` set to `draft` and `reviewed_by` empty.

*Why it matters.* Reviewers can see how each label changed and why. The set has not had human review, and the evaluation reports say so.

## What was tried and rejected

- **Unconstrained planner schema.** One model looped on an invented indicator id. Enums built from the catalogue fixed this (`docs/experiments/m4-agent.md`, D-027).
- **Raw blocks as chunks, and fixed token windows.** Passages are too short, and windows ignore layout (D-015).
- **One generic MCP query tool with free-form filters.** It moves validation into the model and cannot be schema-constrained (D-028).
- **Serving MOM passages over MCP.** Rights (D-001, D-028).
- **Heuristics as the main injection defence.** They are bypassable by paraphrase. The prompt rules, the citation checks and the output guard carry the weight (`docs/threat-model.md`).

## Honest limits

- The evaluation uses AI-drafted gold labels and an AI judge. Human review has not happened yet, so results show agreement with draft labels, not accuracy against ground truth (`src/labourlens/evaluation/harness.py`).
- The default agent configuration in `src/labourlens/agent/graph.py` names `answer_v3`. Only `answer_v4` contains the rule on data-quality notes. The notes are built and passed to the model in either case. Until the default changes, the live page does not use the rule unless the configuration is set to `answer_v4`.
- The agent cannot compute a difference from figures that appear only in report text. `calculate_change` accepts observations from datasets only (`docs/experiments/m4-agent.md`).
- The threat suite is hand-written and not adaptive. It measures regressions more than worst cases. Only two hostile fixtures cover the added MCP tools (`docs/threat-model.md`).
- MCP has no OAuth, TLS or rate limiting. The HTTP transport accepts loopback only.
- The system sends MOM passages to a third-party API. The provider's data-use terms were not verified (D-022).

## Next steps

1. Human review of the gold set, the passage spot check and the statistical spot check (`docs/human-review/`).
2. Run the held-out split once after the gold set is frozen.
3. Set the default answer prompt to `answer_v4` if the evaluation supports it.
4. Add arithmetic over figures stated in report text.
5. Add a hostile fixture for each of the nine MCP tools.
6. Add adaptive attacks to the threat suite.
