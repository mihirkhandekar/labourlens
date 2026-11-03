"""Served annual answers must paraphrase report passages: a copied run of 7+ words is a validation error that triggers the one bounded
repair, listing only the copied run. Deterministic fakes: no key, network or corpus."""
import json

import pandas as pd

from labourlens.agent import graph as g
from labourlens.agent import tools as tl
from labourlens.answer import llm, validate
from labourlens.answer.context import ContextPassage
from labourlens.answer.schema import Answer

SOURCE = "restructuring in outward facing sectors drove most of the rise in layoffs during the quarter"
RUN = "restructuring in outward facing sectors drove most of the rise in layoffs"


def _answer(summary, claim="Retrenchments rose.", **kw):
    return dict(status="answered", summary=summary, claims=[dict(text=claim, citations=[dict(label="P1", quote="outward facing sectors")])],
                caveats=[], clarification_question="", reason="", **kw)


def _ctx():
    return [ContextPassage("P1", "p1", "fixture", "Fixture", None, "final", "p.1", SOURCE, ()),
            ContextPassage("O1", "o1", "fixture", "Fixture", None, "dataset_snapshot", "row", "restructuring in outward facing sectors drove most", ())]


def test_validator_lists_only_the_copied_runs_in_every_free_text_field():
    answer = Answer.model_validate(dict(
        status="answered", summary=f"MOM attributed the rise to {RUN}.", reason="", clarification_question="",
        caveats=["Independent wording only.", f"Also: {RUN}"],
        claims=[dict(text=f"{RUN} again", citations=[dict(label="P1", quote="outward facing sectors")])]))
    errors = validate.report_copy_errors(answer, _ctx())
    assert len(errors) == 3
    assert errors[0].startswith("summary copies") and f'"{RUN}"' in errors[0] and "MOM attributed" not in errors[0] and "during the quarter" not in errors[0]
    assert errors[1].startswith("caveats[1]") and errors[2].startswith("claims[0].text")


def test_validator_accepts_a_paraphrase_a_six_word_overlap_and_open_data_overlap():
    six = "restructuring in outward facing sectors drove"
    answer = Answer.model_validate(_answer(f"Layoffs rose as firms reorganised outward oriented operations; {six} was the phrase."))
    assert validate.report_copy_errors(answer, _ctx()) == []
    open_data = [ContextPassage("O1", "o1", "fixture", "Fixture", None, "dataset_snapshot", "row", SOURCE, ())]
    assert validate.report_copy_errors(Answer.model_validate(_answer(SOURCE)), open_data) == []


def _obs():
    cols = dict(source_id="retrenched_employees", indicator_id="retrenched_employees", unit="persons", population="establishments",
                adjustment="not_applicable", dimension="", release_stage="dataset_snapshot", in_answer_scope=True, missing_reason="",
                observation_id="obs0", source_locator="row0", period="2026-Q1", value=3830.0)
    return pd.DataFrame([cols])


class _NoSearch:
    def search(self, q, k):
        return []


def _run(monkeypatch, drafts):
    seen = []

    def search_reports(self, query, k=8):
        item = self._add("P", "passage-1", "mom-2026-q2-final", "Report", None, "final", "p1", SOURCE)
        return tl.ToolResult(True, [item], "1 new passages: P1")

    monkeypatch.setattr(tl.Tools, "search_reports", search_reports)
    plan = [[{"id": "s", "name": "search_reports", "arguments": json.dumps({"query": "retrenchment reasons", "k": 4})}], []]
    answers = list(drafts)

    def chat(model, messages, max_completion_tokens=6000, extra=None, schema=None, schema_name="answer", **kw):
        if "tools" in kw:
            return llm.LLMResult("", 10, 5, 0, 0.01, tool_calls=plan.pop(0))
        seen.append(messages)
        return llm.LLMResult(json.dumps(answers.pop(0)), 10, 5, 0, 0.01)

    monkeypatch.setattr(llm, "chat", chat)
    cfg = g.AgentConfig(planner_mode="tools", planner_prompt="planner_v7", answer_prompt="answer_v9", tool_set="annual")
    shared = tl.Shared(world=(_NoSearch(), {}, {}), observations=_obs())
    tools = tl.Tools(shared, cfg.retrieval, "q", cfg.tool_timeout_s)
    final = g.build_graph(shared, tools, cfg).invoke({"question": "Why did retrenchments rise?", "round": 0, "calls_used": 0, "attempts": 0, "trace": []},
                                                     {"recursion_limit": 40})
    return final, seen


def test_a_copied_run_triggers_one_repair_that_lists_only_the_run(monkeypatch):
    final, seen = _run(monkeypatch, [_answer(f"MOM attributed the rise to {RUN}."), _answer("MOM pointed to restructuring in export-facing firms.")])
    assert final["outcome"] == "answered" and final["attempts"] == 2
    repair = seen[1][-1]["content"]
    assert repair.startswith("Your previous answer failed") and f'"{RUN}"' in repair and "paraphrase" in repair
    assert "MOM attributed" not in repair and "during the quarter" not in repair
    assert [e["event"] for e in final["trace"] if e["node"] == "validate_answer"] == ["invalid", "valid"]


def test_a_still_copied_repair_is_not_a_failure_and_is_left_to_the_projection(monkeypatch):
    copied = _answer(f"MOM attributed the rise to {RUN}.")
    final, seen = _run(monkeypatch, [copied, copied])
    assert final["outcome"] == "answered" and len(seen) == 2
