# M7 tool-coverage fix (tool set v2): design, pre-declared evaluation plan and commands

**Status (1 Nov 2026): IMPLEMENTED, RUN, NOT ADOPTED.** Sections 1 to 8 were written before any run and are unchanged (section 8 records the pre-run test results). Section 9 holds the measured results, the criteria verdict and the decision. Decision records: D-046 (design, pre-run) and D-048 (result) in `docs/decisions.md`.

This is a **new experiment outside the frozen held-out v2 protocol** (D-042, D-045). It changes no frozen file, gold label, scorer, existing prompt or earlier run record.

## 1. What and why

**Source of the problem.** `experiments/heldout-v2/error-analysis.json` (class names and ids only) attributes 11 of the 16 primary `r3` mismatches in held-out v2 to a tool coverage gap:

| Class (from the error analysis) | Cases | Capability gap in the code |
|---|---|---|
| `tool_gap_text_figure_arithmetic` | HO-V2-029 to 036 (8) | `Tools.calculate_change` takes only observation labels returned by `get_series`. A difference or percentage change between two figures printed in report text has no tool, and `answer_v3` says never to do arithmetic, so the agent abstains. |
| `tool_gap_dataset_dimension_label_and_round_budget` | HO-V2-025, 026, 027 (3) | `StatsData.query` needs an exact (case-insensitive) dimension label. A wrong first label costs a round, the corrected retry lands in round 2 of 2 (`MAX_ROUNDS`), and no round is left for the calculation. |

The design below uses only these class descriptions and the tool code. The v2 gold answers, raw runs and case texts were not read (D-016).

### 1.1 The new tool: `calculate_from_text_values`

Arguments (flat, so they fit the existing strict-schema call item): `passage_a, value_a, unit_a, basis_a, period_a, passage_b, value_b, unit_b, basis_b, period_b, kind`. `a` is the earlier or base figure, `b` the later one.

Deterministic checks, in `Tools.calculate_from_text_values` (`src/labourlens/agent/tools.py`); every failure returns a `ToolResult` with `invalid_arguments` and a corrective message, and no evidence is added:

1. `kind` is `difference` or `percent_change` (the existing `CHANGE_KINDS`).
2. `passage_x` must be a **P label that `search_reports` returned in this run** (an O or C label, or an invented label, is refused).
3. The passage must not carry injection flags (`ContextPassage.flags`): a flagged passage cannot be a source of figures, mirroring the rule that it cannot be cited.
4. `unit_x` is one of `percent, persons, dollars, ratio, vacancies`; `value_x` is one plain number (`2.9`, `-0.3`, `1,250`; no unit, no words); `basis_x` (1 to 120 characters) and `period_x` (1 to 40 characters) are short plain text from a restricted character set, so free text cannot carry markup into an evidence item.
5. **Number grounding:** after NFKC normalisation and removal of thousands separators, the value, as a `Decimal`, must equal a number printed in the cited passage text (so `2.90` matches `2.9`, `1,250` matches `1250`). A minus sign counts only when it directly precedes the digits and follows a space, a bracket or the start of the text, so a range such as 2024-2025 is not read as a negative number. A value that is not in the passage is refused with "copy the figure exactly as the passage prints it".
6. **Refuses mixed units and bases:** `unit_a` must equal `unit_b`, and `basis_a` must equal `basis_b` after case folding and punctuation normalisation (the planner is told to word them identically). Identical inputs (same passage, same value, same period) are refused.
7. Arithmetic is `compute_change`, the same function behind `calculate_change` and the MCP `compare_periods`: `Decimal`, half-up to 2 places, "percentage points" when the unit is percent, percent change from zero refused. The model never supplies a result.
8. The result is a `C` evidence item with id `calc:<12 hex>` (hash of the two passage ids, the two values and the kind), `stage="calculated"`, locator `P1,P2`, and text of the form:
   `Calculated difference of <basis> from report figures: <vb> - <va> = <result> <unit>. Inputs P1 (<va fmt>, <period_a>; <source_id>, <stage>) and P2 (...)`.

**Why the validator needed no change.** `validate.check` already accepts any label present in the context, requires a verbatim quote, and grounds claim numbers against the cited items and summary or caveat numbers against all context text. The new `C` item text carries both inputs and the result, so a claim that cites it and states the inputs or the result is grounded, and an invented number is still reported. `tests/retrieval/test_text_calc.py::test_validator_accepts_text_calculation_citation_and_grounds_its_numbers` demonstrates both the accepted case and an ungrounded `0.4`. The answer prompt `answer_v3` did not itself forbid the `C` label for report figures; it forbids hand arithmetic, which stays forbidden. `answer_v5` therefore only tells the model that a `C` item may rest on report figures and that those inputs may be stated when citing it.

**Planner visibility (necessary for the tool to be usable).** The planner never sees passage text (ADR-002 least exposure), so it could not choose figures. In tool set v2 the planner's evidence list adds, under each unflagged `P` passage, up to five `figure: "..."` lines: word windows of at most 12 words (7 before, 4 after) around a decimal, comma-grouped number, integer of 100 or more, or any number followed by `%`, passed through `sanitize_text`. Bare years are skipped. These snippets are untrusted text: flagged passages get none, the planner output is schema-constrained, and the tool re-checks every chosen value against the full passage, so a snippet is a convenience and never a trust boundary. This is part of the one factor, not a second factor: without it the tool cannot be called meaningfully.

**MCP.** Not changed. The MCP server exposes dataset capabilities only (`get_statistic`, `compare_periods` and so on) and has no access to report text, so there is nothing for it to mirror. The only MCP-visible interaction is the unknown-dimension error, which the agent enriches locally (below).

### 1.2 The dimension-label recovery

When `get_series` fails with the "dimension ... not found" error (either backend, detected by `tools.is_unknown_dimension`) and the tool set is v2:

* **Actionable error.** `Tools._dimension_help` replaces the message by one that lists the valid labels for that series (filtered by `source_id`, `indicator_id` and `adjustment` when given), with the closest matches first (`difflib`, cut-off 0.4), up to 80 labels, 1,800 characters. The labels come from the local read-only observations table, so the list is complete even though the MCP client truncates messages at 600 characters. A series without any dimension values says to leave `dimension` null. The earlier message was already a label list capped at 40 names, so the change is completeness, ranking and the explicit retry instruction.
* **Round budget.** The graph grants **one bonus evidence round per run** after such an error (`BONUS_ROUNDS = 1`, state field `bonus_rounds`, trace event `bonus_round_granted`), so the allowance is `MAX_ROUNDS + 1 = 3` for this error class only. Other errors do not extend it, a second unknown-dimension error does not extend it again, and `MAX_CALLS = 6` and `MAX_CALLS_PER_ROUND = 3` are unchanged. I chose the bonus round over making the retry free of the round count because the second option has no natural definition when the failed call shares a round with successful calls.

### 1.3 Configuration isolation

* `AgentConfig.tool_set` is `"base"` by default. `key()` is unchanged for `base`, and for `v2` appends `|tools=v2`, so a v2 run can never be mistaken for an earlier one.
* `tool_set="v2"` and the prompt pair `planner_v3` + `answer_v5` must be used together (`AgentConfig.__post_init__` raises otherwise), so a run cannot silently mix the new prompts with the old schema or the reverse.
* `plan_schema(shared)` and `plan_schema(shared, "base")` return exactly the earlier schema (three tools, 12 call properties, same `required` list); v2 appends the tool name and ten arguments and requires all of them (strict mode needs every property required). The `calculate_from_text_values` call is refused in a `base` run even if emitted.
* `Tools.tool_set` defaults to `"base"`; the dimension error and the snippets are gated on it, so earlier runs are byte-identical in behaviour. The web app and the threat suite use `AgentConfig()` and are unchanged.
* New CLI flag: `agent-exp --tool-set {base,v2}` (default `base`).
* Regression tests (all in `tests/retrieval/test_text_calc.py`): default and hybrid config keys unchanged; base schema equals the pinned structure and is not mutated by building the v2 schema; `ARGS` of the old tools unchanged; the SHA-256-based prompt hashes of `planner_v1` and `answer_v3` are pinned (`32c800c83425`, `9a9372faf52e`); the number of changed lines in the new prompts is pinned; the base config keeps two rounds on a script that gets three rounds in v2.

## 2. One-factor statement (D-016)

**Factor changed:** the tool set offered to the agent, as a bundle of three coupled parts: (a) arithmetic on report figures, with the planner snippets and prompt lines it needs; (b) actionable unknown-dimension error; (c) one bonus round after that error. Everything else is held fixed against X2: corpus v3, `r3` retrieval, rerank prompt `rerank_v1`, cross-check on, gold v3.6 and the dev split, the model pairs, judge `gpt-6.1-terra`, harness and scorer. The bundle is justified because both parts address one diagnosed capability gap (numerical comparisons that need a calculation the tool set cannot make) and because (b) and (c) are meaningless apart. If a regression appears, the three parts can be separated by unit-tested switches only with a further experiment; this run cannot attribute an effect to one part, and the report must say so.

**Tuning:** only on dev (D-016). No tuning has been done at all: the design came from the capability gap and synthetic unit tests. The planner snippet sizes (5 snippets, 7 words before, 4 after) were fixed by me before any run and are not tuned.

## 3. Exact prompt differences

New files, minimal diffs of the pinned originals, which are untouched. Output of `git diff --no-index -U0` (long lines are shown in full in the files):

`planner_v1.md` -> `planner_v3.md` (one line added, one line changed):

```
@@ -6,0 +7 @@ Tools (one list of calls per round; at most 3 calls per round)
+- calculate_from_text_values(passage_a, value_a, unit_a, basis_a, period_a, passage_b, value_b, unit_b, basis_b, period_b, kind): exact arithmetic on two figures printed in report passages (P1, P2, ...) that search_reports returned in an EARLIER round; the evidence list shows short `figure:` snippets under each passage. Use it when the question asks for a difference or percentage change of figures that appear in report text rather than in a dataset. a is the earlier or base figure, b the later. value is the plain number as printed (for example 2.9 or 1250); unit is one of percent, persons, dollars, ratio, vacancies; basis is a short description of what is measured, worded identically for a and b (measure, population, adjustment, scale); period says which period or release the figure is for. kind is difference or percent_change. The tool checks that each value occurs in its passage and refuses different units or bases. Never do arithmetic yourself.
@@ -9 +10 @@ Rules
-1. Round 1: gather evidence. Round 2 (only if needed): a calculation, or one more lookup after an error or a gap. Then finish. You have at most 2 rounds and 6 calls in total.
+1. Round 1: gather evidence. Round 2 (only if needed): a calculation, or one more lookup after an error or a gap. Then finish. You have at most 2 rounds and 6 calls in total. If get_series fails because a dimension label is unknown, the error lists the valid labels and you get one extra round for the corrected lookup, so then you have at most 3 rounds.
```

`planner_v1_user.md` -> `planner_v3_user.md` (one line):

```
@@ -3 +3 @@
-Round: {round} of 2. Calls used: {calls_used} of 6.
+Round: {round} (2 rounds, or 3 after an unknown dimension error). Calls used: {calls_used} of 6.
```

`answer_v3.md` -> `answer_v5.md` (two lines changed):

```
@@ -1 +1 @@
-... exact calculations done by a tool (C1, C2, ...). The supported period is 1Q 2024 to 2Q 2026.
+... exact calculations done by a tool (C1, C2, ...), either on published statistics or on figures printed in report passages. The supported period is 1Q 2024 to 2Q 2026.
@@ -4 +4 @@ Rules
-1. ... Do not do arithmetic yourself: use a C item for any difference or percentage change.
+1. ... Do not do arithmetic yourself: use a C item for any difference or percentage change. A C item may name report passages as its inputs; the figures it was calculated from are part of the C item and you may state them as inputs of that calculation, citing the C item.
```

(`...` marks the unchanged text of the line; the files hold the full lines.) `answer_v3_user.md` and `answer_v5_user.md` are byte-identical. The prompt SHA-256 prefixes (first 12 hex of system + user, as `load_prompt` computes) are `planner_v3` 9574fc7121ca and `answer_v5` b674cd1e3707, against `planner_v1` 32c800c83425 and `answer_v3` 9a9372faf52e.

## 4. Pre-declared evaluation plan (decided before any run)

Fixed before running: the success criteria below, the commands, and the rule that no case, label, scorer or prompt is changed after seeing output. Any deviation needs a dated amendment here before the run.

### 4.1 Experiment X3 (development regression check against X2)

* **System:** `planner_v3`, `answer_v5`, `--tool-set v2`, `--retrieval r3`, cross-check on (default), corpus v3, gold v3.6, dev split n=237, both models (`gpt-6-luna`, `gpt-5.6-luna`), judge `gpt-6.1-terra`, one run per model.
* **Baseline:** X2 (`experiments/eval/agent-dev-X2/`), same corpus, retrieval, cross-check and gold. X2 point values and counts (from its files): behaviour correct 214/237 (0.903, interval [0.865, 0.941]) for `gpt-6-luna` and 217/237 (0.916, [0.878, 0.949]) for `gpt-5.6-luna`; 6 false-answer cases each; cases with an ungrounded number 25 (0.105, [0.068, 0.143]) and 39 (0.165, [0.118, 0.215]).
* **X3 passes only if, for each of the two models (no pooling, no disjunction):**
  1. **Behaviour accuracy does not drop beyond the X2 interval:** X3 point estimate at or above the X2 lower bound, i.e. at least 205/237 correct (0.865) for `gpt-6-luna` and at least 209/237 (0.878) for `gpt-5.6-luna`.
  2. **False-answer rate does not rise:** the number of non-answer cases that X3 answered is at most 6 for each model (the X2 count).
  3. **No new ungrounded numbers:** (a) zero cases that used `calculate_from_text_values` end with an ungrounded number; and (b) cases with an ungrounded number at most the X2 upper bound: 34 of 237 (0.143) for `gpt-6-luna` and 51 of 237 (0.215) for `gpt-5.6-luna`.
  4. **No operational regression:** operational failures at most the X2 count for each model (read from `metrics.json`).
* Reported descriptively, not gating: calc-correct rate (n=24 in X2), numerical-comparison family accuracy, key-number recall, claim support, tool-error rate, use and refusal counts of `calculate_from_text_values`, how often `bonus_round_granted` fired, rounds and tool calls per case, latency and cost per case, and the cases whose behaviour result changed against X2 (a descriptive list; with n=237 differences under about 10 points are noise, per the X2 report).
* **A failed criterion is reported as a failure and the tool set is not adopted as the served default;** no cherry-picking of models.

### 4.2 Post-freeze diagnostic on the v2 gold (`V2post`)

* **Label: post-freeze diagnostic.** The v2 cases are now known, and this fix was motivated by their error analysis, so this is not held-out evidence and not a confirmatory test (D-045 already requires a fresh set and a fresh pre-registration for any held-out claim about a fixed system). It checks only whether the diagnosed gap closes.
* **Run:** the same two arms as the frozen v2 protocol, `r3` and `hybrid`, with `planner_v3`, `answer_v5`, `--tool-set v2`, both models, gold `experiments/gold/heldout_v2_v1.jsonl` (SHA-256 `e3d16597d542d33d106b4e9291aa3b92ca5fcdf19aa4d3c2b3319c0543efa542`), cross-check on, tags `V2post-r3` and `V2post-hybrid`. The frozen `agent-heldout-V2-*` records are not touched (`agent-exp` refuses to reuse an id).
* **Reported descriptively (no gating, no verdict string quoted as confirmation):** behaviour accuracy per arm and model against the frozen v2 results; `numerical_comparison` (14 cases; 3 correct in every frozen arm); the 11 targeted cases (HO-V2-025 to 027 and 029 to 036) separately from the other 54, which act as a regression check; false answers (the frozen r3 arm had 0; any false answer is flagged); ungrounded numbers; tool refusals. `paired` prints a `decision` string that applies the D-042 rule to retrieval; for these runs it must not be quoted as a verdict.
* The improvement on `numerical_comparison` is expected by design for the 11 targeted cases and is **not** evidence of general capability. Gains confined to the 11 targeted cases and a flat remainder is the expected pattern; a change in the other 54 cases in either direction is what the diagnostic should be watched for.
* The remaining five frozen mismatches (HO-V2-011, 022, 050, 051, 063) are outside this fix and are not expected to change; any change is reported but not attributed.

### 4.3 Threats to validity (stated in advance)

* Bundled factor (section 2): no attribution to the three parts.
* One run per model and arm; sampling noise from model sampling alone is not separated from the tool-set effect (no repeated runs).
* The AI judge and AI-drafted gold; the v2 gold was approved by the owner without independent re-review. Updated 1 Nov 2026: the owner has since recorded a decision on every gold case in the review interface (gold v3.7). The labels are AI-drafted, signed off by the owner; one reviewer, after AI pre-review, not independent inter-rater evidence. The saved runs were scored on v3.6 and were not rescored on v3.7.
* Planner visibility of figure snippets widens the planner's exposure to untrusted text by at most 5 short windows per unflagged passage. The existing threat suite (`labourlens threat-test`) has not been run with tool set v2; the planner snippet path is covered only by unit tests (flagged passages get none; chosen values are re-verified). A threat run under a new experiment id is a recommended step before any adoption, not a part of the pass criteria above.
* `_calc_correct` in `agent/experiments.py` scores only observation-based calculation gold (two observation ids with periods). A text-figure calculation is not scored by it and no existing gold case has text-figure calculation inputs (checked by structure, not by reading case texts). Scoring of the targeted cases therefore rests on behaviour, key-number recall and the judged coverage measures, as in the frozen runs.

## 5. Commands for the parent (all call paid APIs except the last two; need `OPENAI_API_KEY`)

Record `git rev-parse HEAD` first and commit this change before any run, so the provenance in the raw records points at a clean tree. Check first with no API use:

```
uv run pytest -q -m 'not corpus'
uv run pytest -q -m corpus -k agent
```

X3 (dev; the same shape as the X2 run, plus the three v2 options):

```
uv run labourlens agent-exp --split dev --pairs gpt-6-luna gpt-5.6-luna --planner-prompt planner_v3 --answer-prompt answer_v5 --tool-set v2 --retrieval r3 --tag X3
uv run labourlens eval --exp agent-dev-X3 --split dev --labels gpt-6-luna gpt-5.6-luna
```

V2post (post-freeze diagnostic, held-out v2 gold under new tags):

```
uv run labourlens agent-exp --split heldout --gold experiments/gold/heldout_v2_v1.jsonl --planner-prompt planner_v3 --answer-prompt answer_v5 --tool-set v2 --retrieval r3 --tag V2post-r3 --pairs gpt-6-luna gpt-5.6-luna
uv run labourlens agent-exp --split heldout --gold experiments/gold/heldout_v2_v1.jsonl --planner-prompt planner_v3 --answer-prompt answer_v5 --tool-set v2 --retrieval hybrid --tag V2post-hybrid --pairs gpt-6-luna gpt-5.6-luna
uv run labourlens eval --exp agent-heldout-V2post-r3 --split heldout --gold experiments/gold/heldout_v2_v1.jsonl
uv run labourlens eval --exp agent-heldout-V2post-hybrid --split heldout --gold experiments/gold/heldout_v2_v1.jsonl
```

Paired comparisons (no model calls; new output files, `experiments/heldout-v2/paired.json` is not overwritten). The first isolates the tool-set change at fixed `r3`; the second repeats the registered retrieval comparison on the post-fix system:

```
uv run labourlens paired --gold experiments/gold/heldout_v2_v1.jsonl --candidate agent-heldout-V2post-r3 --baseline agent-heldout-V2-r3 --models gpt-6-luna gpt-5.6-luna --out experiments/heldout-v2/paired-postfix-toolset.json
uv run labourlens paired --gold experiments/gold/heldout_v2_v1.jsonl --candidate agent-heldout-V2post-r3 --baseline agent-heldout-V2post-hybrid --models gpt-6-luna gpt-5.6-luna --out experiments/heldout-v2/paired-postfix-r3-vs-hybrid.json
```

Dev X3 against X2 per case (`paired` cannot be used for dev: it demands every case of the gold file, which also holds the held-out split). Read-only, from the saved score files:

```
python3 - <<'E'
import json
for m in ("gpt-6-luna", "gpt-5.6-luna"):
    load = lambda e: {r["case_id"]: r for r in map(json.loads, open(f"experiments/runs/{e}/{m}.scores.jsonl"))}
    a, b = load("agent-dev-X2"), load("agent-dev-X3")
    print(m, "behaviour ok X2/X3:", sum(r["behavior_ok"] for r in a.values()), sum(r["behavior_ok"] for r in b.values()),
          "| false answers:", *[sum(r["expected"] != "answered" and r["status"] == "answered" for r in x.values()) for x in (a, b)],
          "| ungrounded cases:", *[sum(r["n_ungrounded_numbers"] > 0 for r in x.values()) for x in (a, b)],
          "| new-tool cases with ungrounded numbers:", sum("calculate_from_text_values" in r["tools_used"] and r["n_ungrounded_numbers"] > 0 for r in b.values()),
          "| changed:", sorted(c for c in a if a[c]["behavior_ok"] != b[c]["behavior_ok"]))
E
```

## 6. Cost estimate (from saved usage; not a measurement of the new runs)

Basis: per-case cost and judge totals in the saved metrics files (`cost_per_case_usd`, `judge_cost_total_usd`), prices as recorded by the harness.

| Run | Saved basis | Estimate (USD) |
|---|---|---|
| X3 generation | X2: 237 x 0.00285 = 0.68 (`gpt-6-luna`), 237 x 0.00463 = 1.10 (`gpt-5.6-luna`) | 1.77 unchanged, up to 2.04 if prompt growth is +15% |
| X3 judging | X2: 0.243 + 0.269 | about 0.51 |
| V2post generation | frozen v2: r3 65 x (0.00334 + 0.00485) = 0.53; hybrid 65 x (0.00159 + 0.0036) = 0.34 | 0.87, up to 1.00 at +15% |
| V2post judging | frozen v2: 4 x about 0.043 | about 0.17 |
| **Total** | | **about 3.3 to 3.7** |

Assumption behind the "+15%" upper figure: the longer planner prompt (about 250 tokens, twice per run at most) and, in round 2, up to five short snippets per passage (a few thousand tokens at most; X2 used on average about 22,000 prompt tokens per case, mostly in the answer step). A third round, when granted, adds one planner call. This growth is an assumption, not measured. Owner-reported spend has run above file-derived sums before (D-044: about $3 reported against about $2.5 derived), so budget for roughly 20% more.  The cap on calls (6) is unchanged, so cost is bounded per case.

## 7. Files changed

* `src/labourlens/agent/tools.py`: `calculate_from_text_values`, `figure_snippets`, `is_unknown_dimension`, `Tools._dimension_help`, `Tools.tool_set`, constants.
* `src/labourlens/agent/graph.py`: `AgentConfig.tool_set` and coupling check, `plan_schema(shared, tool_set)`, `ARGS`/`REQUIRED`, bonus round, planner snippets, base-config refusal of the new tool.
* `src/labourlens/agent/experiments.py`, `src/labourlens/cli.py`: `--tool-set` plumbing.
* `src/labourlens/report/build.py`: the public trace whitelist knows the new tool name.
* `prompts/planner_v3.md`, `planner_v3_user.md`, `answer_v5.md`, `answer_v5_user.md` (new); existing prompts untouched.
* `tests/retrieval/test_text_calc.py` (new, 35 tests).
* `docs/experiments/m7-tool-fix.md` (this file), `docs/decisions.md` (D-046).

## 8. Verification actually run

* `uv run pytest -q -m 'not corpus'`: **726 passed, 56 deselected** (65.5 s), including the 35 new tests.
* `uv run pytest -q -m corpus -k agent`: **3 passed, 779 deselected** (`data/` is present).
* No model, paid, build, fetch or index command was run. Behavioural claims about the agent with real models are untested until X3 and V2post are run.

## 9. Results (1 Nov 2026) and decision

**MEASURED RESULT, with the limits stated in section 4.3.** Sources: `experiments/eval/agent-dev-X3/`, `experiments/eval/agent-heldout-V2post-{r3,hybrid}/`, `experiments/heldout-v2/paired-postfix-toolset.json`, `experiments/heldout-v2/paired-postfix-r3-vs-hybrid.json`, and the criteria evaluation `experiments/tool-fix/criteria.py` -> `experiments/tool-fix/criteria.json` (counts and case ids from the saved score files; thresholds are the constants declared in section 4.1, not recomputed). One run per model and arm. The dev gold hash is identical for X2 and X3 (`6169a9deca78`, gold v3.6); the v2 gold hash is `e3d16597d542` for the frozen and post-fix runs.

**Run history (cost note).** The first X3 attempt crashed in `score_run` on the new `bonus_round_granted` trace event, which has no `tool` field. The scoring bug was fixed and the experiment re-run with `--force`. The discarded generation cost about 1.5 USD (owner-reported; not file-verifiable). The results below are from the re-run only. The scoring fix does not touch generation: the agent-relevant code between the X2 and X3 recorded heads differs only by the tool-set files, prompts and CLI plumbing.

### 9.1 Dev X3 against the pre-declared criteria (section 4.1): FAIL for both models

Counts are integers from the saved score files. Thresholds were fixed before the run.

| # | Criterion | `gpt-6-luna` | PASS/FAIL | `gpt-5.6-luna` | PASS/FAIL |
|---|---|---|---|---|---|
| 1 | Behaviour correct at least 205 / 209 of 237 (X2 lower bound) | 212 (X2: 214) | **PASS** | 213 (X2: 217) | **PASS** |
| 2 | False-answer cases at most 6 | 7 (X2: 6) | **FAIL** | 7 (X2: 6) | **FAIL** |
| 3a | No ungrounded number in a case that used `calculate_from_text_values` | 1 of 10 such cases (DEV-331) | **FAIL** | 3 of 18 such cases (DEV-025, 226, 326) | **FAIL** |
| 3b | Cases with an ungrounded number at most 34 / 51 | 27 (X2: 25) | **PASS** | 30 (X2: 39) | **PASS** |
| 4 | Operational failures at most the X2 count (0) | 0 | **PASS** | 1 (X2: 0) | **FAIL** |
| | **All criteria** | | **FAIL** | | **FAIL** |

Notes on the failures, stated without softening the rule:
* **Criterion 2** is one case over the limit for each model. The extra answered non-answer case is DEV-627 in both models (a numerical-comparison case that X2 got right). For `gpt-6-luna` the other six recur from X2. For `gpt-5.6-luna` five recur, DEV-404 dropped out and DEV-604 was added. One case is within sampling noise, but the criterion was declared with no tolerance.
* **Criterion 3a** is a zero-tolerance rule on a small number of cases. Whether the ungrounded numbers are the new tool's fault was not investigated per case (that would need reading model outputs; the case list is in `criteria.json`).
* **Criterion 4** for `gpt-5.6-luna` is a single provider-side HTTP 520 error page in the answer step of DEV-026, not a tool fault, but the pre-declared rule has no exception for the cause, so it is a FAIL.
* Criteria 1 and 3b pass for both models. The X2 intervals are wide (n=237): differences below about 10 points are noise.

### 9.2 Dev X3 against X2, descriptive (not gating)

| Measure | `gpt-6-luna` X2 | X3 | `gpt-5.6-luna` X2 | X3 |
|---|---|---|---|---|
| Behaviour accuracy | .903 [.865, .941] | .895 [.852, .932] | .916 [.878, .949] | .899 [.857, .937] |
| Behaviour correct (of 237) | 214 | 212 | 217 | 213 |
| False-answer cases | 6 | 7 | 6 | 7 |
| Over-abstentions | 6 | 8 | 5 | 8 |
| Cases with an ungrounded number | 25 (.105) | 27 (.114 [.076, .156]) | 39 (.165) | 30 (.127 [.084, .173]) |
| Calc correct (n=24) | .750 (18) | .792 (19) | .750 (18) | .792 (19) |
| Key-number recall | .836 | .829 | .845 | .874 |
| Claim support | .860 | .887 | .794 | .834 |
| Fact coverage | .719 | .734 | .745 | .802 |
| Answers contradicting a reference fact | .023 | .023 | .017 | .011 |
| `numerical_comparison` correct (of 34) | 30 | 30 | 30 | 28 |
| Cases that used `calculate_from_text_values` | 0 | 10 | 0 | 18 |
| Cases that reached a third round | 0 | 3 | 0 | 6 |
| Median / p95 latency (s) | 14.0 / 40.9 | 13.9 / 40.8 | 13.9 / 33.8 | 13.6 / 40.2 |
| Cost per case (USD) | .00285 | .00298 | .00463 | .00484 |

The dev set shows **no behaviour gain**: both X3 point estimates are slightly below X2 and well inside X2's interval, and `numerical_comparison` is flat (`gpt-6-luna`) or two cases lower (`gpt-5.6-luna`). Per-case churn is symmetric: 4 cases gained and 6 lost for `gpt-6-luna`, 5 gained and 9 lost for `gpt-5.6-luna` (listed in `criteria.json` under `changed_cases`; most changed cases are outside `numerical_comparison`). With one run per model, sampling noise alone can produce this churn, so the churn is not attributed to the tool set. The development set contains few numerical comparisons that need arithmetic on report text (24 calculation cases, all observation-based gold), so a null result on dev does not contradict the diagnosed gap; it also means dev cannot show the benefit. Cost per case rose 5% for both models.

**Tool behaviour, read from the private raw run records (not committed).** `gpt-6-luna` made 9 successful and 2 refused calls of the new tool on dev; `gpt-5.6-luna` made 8 successful and 12 refused. The refusals of `gpt-5.6-luna` are almost all the same mistake: it put the text of a `figure:` snippet into `passage_a` instead of the passage label (P1, P2, ...). That is a usability weakness of the planner snippet format as designed (not a validation failure: the tool correctly refused). It was not tuned, because tuning on this evidence would break the one-factor rule; a change of the snippet format would be a new experiment. `bonus_round_granted` events: 8 (`gpt-6-luna`) and 10 (`gpt-5.6-luna`) on dev (an event is logged per unknown-dimension error, and one run can log several in one round).

### 9.3 V2post: post-freeze diagnostic on the held-out v2 gold (65 cases)

**Labels, read first.** This is a **post-freeze diagnostic, NOT held-out evidence, and NOT a replacement of the frozen D-045 result**, which stands unchanged. The tool set was **designed after the errors of exactly these 65 cases were analysed** (11 of 16 mismatches were assigned to the gap it addresses), so any gain here is **optimistic by construction**. The dev X3 result in 9.1 and 9.2 is the cleaner check, and it shows no gain. The `decision` string inside the two paired JSON files applies the D-042 retrieval rule and is not a verdict on the tool set; it is not quoted here.

Behaviour correct (of 65), frozen run (89c51d7, `planner_v1`, `answer_v3`) against post-fix run (`planner_v3`, `answer_v5`, tool set v2):

| Arm and model | Frozen | Post-fix | Over-abstentions | False answers | Cases with ungrounded number | `numerical_comparison` (of 14) | Cases using the new tool (post) |
|---|---|---|---|---|---|---|---|
| r3, `gpt-6-luna` | 49 (.754) | 59 (.908) | 13 to 3 | 0 to 0 | 2 to 1 | 3 to 12 | 7 |
| r3, `gpt-5.6-luna` | 47 (.723) | 55 (.846) | 14 to 7 | 0 to 0 | 5 to 3 | 3 to 10 | 8 |
| hybrid, `gpt-6-luna` | 46 (.708) | 57 (.877) | 14 to 4 | 1 to 1 | 2 to 3 | 3 to 12 | 7 |
| hybrid, `gpt-5.6-luna` | 47 (.723) | 53 (.815) | 14 to 7 | 1 to 2 | 4 to 6 | 3 to 9 | 6 |

Paired, post-fix r3 against frozen r3 (`paired-postfix-toolset.json`; the two runs differ by the tool set, the two prompts and the code between the recorded heads, with the same gold):

| Model | Paired difference | Better / worse | McNemar exact p | Case interval | Component interval |
|---|---|---|---|---|---|
| `gpt-6-luna` | +0.154 | 10 / 0 | 0.002 | [0.077, 0.231] | [0.071, 0.222] |
| `gpt-5.6-luna` | +0.123 | 9 / 1 | 0.0215 | [0.046, 0.200] | [0.058, 0.194] |

Of the 11 targeted cases (HO-V2-025 to 027, 029 to 036), the post-fix r3 arm got 9 right for `gpt-6-luna` (frozen: 0; HO-V2-027 and 029 still abstain) and 7 for `gpt-5.6-luna` (frozen: 0). On the other 54 cases `gpt-6-luna` r3 moved from 49 to 50 and `gpt-5.6-luna` r3 from 47 to 48 (2 better, 1 worse), which is the regression check on non-targeted cases. Within the targeted gain, `numerical_comparison` rises from 3 of 14 in all four frozen arms to 12, 10, 12 and 9 of 14 post-fix.

Paired, post-fix r3 against post-fix hybrid (`paired-postfix-r3-vs-hybrid.json`), descriptive only:

| Model | r3 | hybrid | Paired difference | Better / worse | McNemar exact p | Case interval |
|---|---|---|---|---|---|---|
| `gpt-6-luna` | .908 | .877 | +0.031 | 3 / 1 | 0.625 | [-0.015, 0.077] |
| `gpt-5.6-luna` | .846 | .815 | +0.031 | 4 / 2 | 0.6875 | [-0.031, 0.092] |

On the post-fix system the retrieval difference is two to three cases, and the intervals include zero for both models. This is the same direction as D-045 (r3 slightly ahead) but the registered D-042 conditions are not met here, and it is not a retest of the registered comparison.

**What 9.3 shows and does not show.** It shows that the diagnosed capability gap closes for most targeted cases when the tool is available and that the non-targeted cases did not visibly regress in this one run. It does not show a general gain, a gain on unseen questions, or that each of the three bundled parts contributes. It cannot support a held-out claim: the questions and failure classes were known. Two targeted cases still abstain for `gpt-6-luna` and four for `gpt-5.6-luna`, and the `gpt-5.6-luna` refusals above are one visible cause (inferred from the refusal messages, not shown by a controlled test).

### 9.4 Verdict and decision

* **Pre-declared X3 criteria: FAIL for both models** (criteria 2 and 3a for both, criterion 4 additionally for `gpt-5.6-luna`). Under the rule written in section 4.1 the tool set is **not adopted** as the served default.
* **The default `AgentConfig.tool_set` stays `"base"`.** Nothing in the web app, the threat suite or the evaluation defaults changed.
* **Recommendation for any future adoption, not a decision to adopt:** all dev criteria must pass in a fresh run AND the threat suite (`labourlens threat-test`, new experiment id) must pass under tool set v2. The threat suite has **not** been run under v2, so planner exposure to figure snippets is untested beyond unit tests.
* **What would be a sound next step (a new experiment, not done):** fix the snippet format so the planner cannot mistake snippet text for a passage label (for example label every snippet with its P label), keep everything else fixed, and judge it on dev against X2 with criteria declared beforehand; then a fresh evidence-disjoint held-out set, because the v2 set is spent for this purpose (D-045).
* The frozen D-045 result, `experiments/heldout-v2/paired.json`, all earlier prompts and run records are unchanged.

### 9.5 Cost of the experiment (from saved metrics; the crash figure is owner-reported)

| Item | USD |
|---|---|
| X3 generation (237 cases): `gpt-6-luna` 0.706, `gpt-5.6-luna` 1.146 | 1.85 |
| X3 judging: 0.237 + 0.256 | 0.49 |
| V2post generation (4 arms of 65 cases): r3 0.208 + 0.319, hybrid 0.118 + 0.255 | 0.90 |
| V2post judging: 0.055 + 0.048 + 0.054 + 0.053 | 0.21 |
| **Retained runs, file-derived** | **3.45** |
| Discarded first X3 attempt (scoring crash; owner-reported, not file-verifiable) | about 1.5 |
| **Total including the crash** | **about 4.95** |

The pre-run estimate in section 6 was 3.3 to 3.7 USD for the retained runs; the file-derived 3.45 falls inside it. The crash was not in the estimate.
