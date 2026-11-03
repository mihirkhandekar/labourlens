import json

import pandas as pd
import pytest

from labourlens.agent import graph as g
from labourlens.agent import tools as tl
from labourlens.answer import llm


def _obs(rows):
    cols = dict(source_id="retrenched_employees", indicator_id="retrenched_employees", unit="persons", population="establishments",
                adjustment="not_applicable", dimension="", release_stage="dataset_snapshot", in_answer_scope=True, missing_reason="")
    return pd.DataFrame([{**cols, "observation_id": f"obs{i}", "source_locator": f"row{i}", **r} for i, r in enumerate(rows)])


class NoSearch:
    def search(self, q, k):
        return []


@pytest.fixture
def shared():
    df = _obs([{"period": "2026-Q1", "value": 3830.0}, {"period": "2026-Q2", "value": 4620.0},
               {"period": "2026-Q2", "value": 2.9, "indicator_id": "other", "unit": "percent"}])
    return tl.Shared(world=(NoSearch(), {}, {}), observations=df)


def test_difference_is_exact_and_uses_returned_labels(shared):
    t = tl.Tools(shared)
    assert t.get_series("retrenched_employees", "2026-Q1", "2026-Q2", indicator_id="retrenched_employees").ok
    r = t.calculate_change("O1", "O2")
    assert r.ok and "= 790 persons" in r.items[0].text


def test_calculate_change_rejects_labels_it_never_returned_and_mixed_series(shared):
    t = tl.Tools(shared)
    assert t.calculate_change("O1", "O2").error_kind == "invalid_arguments"  # nothing fetched yet
    t.get_series("retrenched_employees", "2026-Q1", "2026-Q2")
    assert t.calculate_change("O1", "O3").error_kind == "invalid_arguments"  # different indicator and unit
    assert t.calculate_change("O1", "O1").error_kind == "invalid_arguments"  # same period


def test_percentage_point_unit_for_rates_and_percent_change(shared):
    df = _obs([{"period": "2026-Q1", "value": 2.0, "unit": "percent"}, {"period": "2026-Q2", "value": 2.5, "unit": "percent"}])
    t = tl.Tools(tl.Shared(world=(NoSearch(), {}, {}), observations=df))
    t.get_series("retrenched_employees", "2026-Q1", "2026-Q2")
    assert "= 0.5 percentage points" in t.calculate_change("O1", "O2").items[0].text
    assert "= 25 percent" in t.calculate_change("O1", "O2", "percent_change").items[0].text


def test_get_series_enforces_scope_and_known_sources(shared):
    t = tl.Tools(shared)
    assert t.get_series("retrenched_employees", "2023-Q4", "2026-Q2").error_kind == "invalid_arguments"
    assert t.get_series("retrenched_employees", "2026-Q1", "2026-Q3").error_kind == "invalid_arguments"
    assert t.get_series("no_such_source", "2026-Q1", "2026-Q2").error_kind == "not_found"
    assert t.get_series("retrenched_employees", "Q1 2026", "2026-Q2").error_kind == "invalid_arguments"


def test_missing_value_is_never_shown_as_zero():
    df = _obs([{"period": "2026-Q1", "value": float("nan"), "missing_reason": "dash"}])
    t = tl.Tools(tl.Shared(world=(NoSearch(), {}, {}), observations=df))
    r = t.get_series("retrenched_employees", "2026-Q1", "2026-Q1")
    assert "no published number" in r.items[0].text and " 0" not in r.items[0].text


# ---- graph control flow with a scripted model --------------------------------------------------------------------

def _answer(status="answered", claims=None, reason="", clar=""):
    return json.dumps({"status": status, "summary": "s" if status == "answered" else "", "claims": claims or [], "caveats": [],
                       "clarification_question": clar, "reason": reason})


def _script(monkeypatch, planner, answers):
    plans, ans, calls = list(planner), list(answers), {"planner": 0, "answer": 0}

    def chat(model, messages, max_completion_tokens=6000, extra=None, schema=None, schema_name="answer"):
        key = "planner" if schema_name == "plan" else "answer"
        calls[key] += 1
        content = (plans if key == "planner" else ans).pop(0)
        return llm.LLMResult(content if isinstance(content, str) else json.dumps(content), 10, 5, 0, 0.01)

    monkeypatch.setattr(llm, "chat", chat)
    return calls


def _call(**k):
    base = dict(tool="get_series", query=None, k=None, source_id="retrenched_employees", period_from="2026-Q1", period_to="2026-Q2",
                dimension=None, adjustment=None, indicator_id="retrenched_employees", obs_a=None, obs_b=None, kind=None)
    return {**base, **k}


def _plan(decision="gather", calls=()):
    return {"decision": decision, "note": "n", "calls": list(calls)}


def test_planner_calls_are_capped_per_round_and_rounds_are_capped(shared, monkeypatch):
    five = [_call() for _ in range(5)]
    counts = _script(monkeypatch, [_plan(calls=five), _plan(calls=five), _plan(calls=five)], [_answer("abstained", reason="x")])
    r = g.run_agent("q", shared, save_trace=False)
    assert r["rounds"] == 2 and r["tool_calls"] == 6 and counts["planner"] == 2  # 3 + 3, then no third planner call
    assert [e["detail"]["dropped"] for e in r["trace"] if e["node"] == "plan_research"] == [2, 2]  # 5 asked, 3 allowed each round


def test_invalid_answer_gets_one_repair_then_is_marked_invalid(shared, monkeypatch):
    bad = _answer("answered", claims=[{"text": "x", "citations": [{"label": "P9", "quote": "q"}]}])
    counts = _script(monkeypatch, [_plan("finish")], [bad, bad, bad])
    r = g.run_agent("q", shared, save_trace=False)
    assert r["outcome"] == "invalid" and counts["answer"] == 2


def test_transient_tool_failure_is_retried_once(shared, monkeypatch):
    seen = {"n": 0}
    orig = tl.Tools.get_series

    def flaky(self, *a, **k):
        seen["n"] += 1
        if seen["n"] == 1:
            raise tl.TransientToolError()
        return orig(self, *a, **k)

    monkeypatch.setattr(tl.Tools, "get_series", flaky)
    _script(monkeypatch, [_plan(calls=[_call()]), _plan("finish")], [_answer("abstained", reason="x")])
    r = g.run_agent("q", shared, save_trace=False)
    assert seen["n"] == 2 and r["evidence"] and r["outcome"] == "abstained"


def test_tool_outage_is_operational_failure_not_missing_evidence(shared, monkeypatch):
    def boom(self, *a, **k):
        raise RuntimeError("down")

    monkeypatch.setattr(tl.Tools, "get_series", boom)
    counts = _script(monkeypatch, [_plan(calls=[_call()]), _plan(calls=[_call()])], [])
    r = g.run_agent("q", shared, save_trace=False)
    assert r["outcome"] == "operational_failure" and counts["answer"] == 0  # never reaches an "abstained" answer


def test_tool_timeout_is_operational_failure(shared, monkeypatch):
    import time

    monkeypatch.setattr(tl.Tools, "get_series", lambda self, *a, **k: time.sleep(0.5))
    _script(monkeypatch, [_plan(calls=[_call()]), _plan("finish")], [])
    r = g.run_agent("q", shared, g.AgentConfig(tool_timeout_s=0.05), save_trace=False)
    assert r["outcome"] == "operational_failure"


def test_late_tool_cannot_mutate_registry(shared, monkeypatch):
    import threading

    finish, completed = threading.Event(), threading.Event()
    original = tl.Tools.get_series
    registry = tl.Tools(shared)
    before = (list(registry.items), set(registry._ids), dict(registry._obs), dict(registry._n), list(registry.notes))
    calls = []

    def slow(self, **kwargs):
        calls.append(self)
        finish.wait(2)
        result = original(self, **kwargs)
        completed.set()
        return result

    monkeypatch.setattr(tl.Tools, "get_series", slow)
    _script(monkeypatch, [_plan(calls=[_call()]), _plan("finish")], [])
    graph = g.build_graph(shared, registry, g.AgentConfig(tool_timeout_s=0.02))
    try:
        result = graph.invoke({"question": "q", "trace": []})
        assert result["outcome"] == "operational_failure" and len(calls) == 1
    finally:
        finish.set()
    assert completed.wait(2)
    assert calls[0].items  # the worker really did finish and mutate its local registry
    assert (registry.items, registry._ids, registry._obs, registry._n, registry.notes) == before


@pytest.mark.parametrize("debug", [False, True])
def test_saved_trace_omits_evidence_unless_debug(shared, monkeypatch, tmp_path, debug):
    monkeypatch.setattr(g.paths, "DATA", tmp_path)
    monkeypatch.setenv("LABOURLENS_DEBUG_EVIDENCE", str(debug).lower())
    _script(monkeypatch, [_plan(calls=[_call()]), _plan("finish")], [_answer("abstained", reason="x")])
    result = g.run_agent("q", shared)
    saved = json.loads((tmp_path / "runs" / "agent" / f"{result['run_id']}.json").read_text())
    assert ("evidence_text" in saved) is debug
    assert all(len(item["sha256"]) == 64 for item in saved["evidence"])
    assert result["evidence_text"]  # private in-memory validation still has the evidence


def test_planner_outage_is_operational_failure(shared, monkeypatch):
    def chat(*a, **k):
        raise llm.LLMError("down")

    monkeypatch.setattr(llm, "chat", chat)
    assert g.run_agent("q", shared, save_trace=False)["outcome"] == "operational_failure"


def test_bad_tool_arguments_are_reported_to_planner_and_can_be_corrected(shared, monkeypatch):
    bad = _call(source_id="made_up")
    _script(monkeypatch, [_plan(calls=[bad]), _plan(calls=[_call()]), ], [_answer("abstained", reason="x")])
    r = g.run_agent("q", shared, save_trace=False)
    kinds = [e["detail"].get("error_kind") for e in r["trace"] if e["node"] == "execute_tool"]
    assert kinds == ["not_found", None] and r["evidence"]


def test_empty_or_oversized_question_is_rejected_without_model_calls(shared, monkeypatch):
    counts = _script(monkeypatch, [], [])
    assert g.run_agent("   ", shared, save_trace=False)["outcome"] == "rejected_input"
    assert g.run_agent("x" * 2000, shared, save_trace=False)["outcome"] == "rejected_input"
    assert counts == {"planner": 0, "answer": 0}


@pytest.fixture
def fixed_search(monkeypatch):
    # The statistics-only shared fixture has no dense retriever. Keep the
    # report-tool implementation, but provide an empty offline search backend.
    monkeypatch.setattr(tl.Tools, "_search", lambda self, query, k: ([], {}, {}, {}, {}))


def test_fixed_pipeline_has_one_extraction_and_fixed_search(shared, monkeypatch, fixed_search):
    counts = _script(monkeypatch, [_plan(calls=[_call()])], [_answer("abstained", reason="x")])
    result = g.run_agent("q", shared, g.AgentConfig(control_flow="fixed"), save_trace=False)
    assert counts == {"planner": 1, "answer": 1}
    assert result["rounds"] == 1 and result["tool_calls"] == 2
    events = [e["detail"] for e in result["trace"] if e["node"] == "execute_tool"]
    assert [e["tool"] for e in events] == ["search_reports", "get_series"]
    assert events[0]["args"] == {"query": "q", "k": 8}
    assert result["config"].endswith("|control=fixed")


def test_fixed_pipeline_does_not_research_again_after_bad_lookup(shared, monkeypatch, fixed_search):
    counts = _script(monkeypatch, [_plan(calls=[_call(source_id="unknown")])], [_answer("abstained", reason="x")])
    result = g.run_agent("q", shared, g.AgentConfig(control_flow="fixed"), save_trace=False)
    assert counts["planner"] == 1 and result["rounds"] == 1
    assert any(e["event"] == "error" for e in result["trace"] if e["node"] == "execute_tool")


def test_fixed_search_is_mandatory_even_without_statistics(shared, monkeypatch, fixed_search):
    counts = _script(monkeypatch, [_plan("finish")], [_answer("abstained", reason="x")])
    result = g.run_agent("q", shared, g.AgentConfig(control_flow="fixed"), save_trace=False)
    assert counts == {"planner": 1, "answer": 1}
    assert result["tool_calls"] == 1
    assert g.fixed_calls("q", [_call(tool="calculate_change"), _call(), _call()]) == [
        {"tool": "search_reports", "query": "q", "k": 8}, _call()]


def test_fixed_extraction_schema_and_answer_settings(shared, monkeypatch, fixed_search):
    seen = []

    def chat(model, messages, max_completion_tokens=6000, extra=None, schema=None, schema_name="answer"):
        seen.append((model, max_completion_tokens, schema, messages))
        content = json.dumps(_plan("finish")) if schema_name == "plan" else _answer("abstained", reason="x")
        return llm.LLMResult(content, 10, 5, 0, .01)

    monkeypatch.setattr(llm, "chat", chat)
    g.run_agent("q", shared, g.AgentConfig(control_flow="fixed"), save_trace=False)
    assert seen[0][2]["properties"]["calls"]["items"]["properties"]["tool"]["enum"] == ["get_series"]
    assert seen[0][2]["properties"]["calls"]["maxItems"] == 1
    assert [(r[0], r[1]) for r in seen] == [("gpt-6-luna", 1500), ("gpt-6-luna", 6000)]
    assert seen[1][3][0]["content"] == g.load_prompt("answer_v3")[0]


def test_fixed_answer_repair_is_identical_and_not_research(shared, monkeypatch, fixed_search):
    bad = _answer("answered", claims=[{"text": "x", "citations": [{"label": "P9", "quote": "q"}]}])
    counts = _script(monkeypatch, [_plan("finish")], [bad, _answer("abstained", reason="x")])
    result = g.run_agent("q", shared, g.AgentConfig(control_flow="fixed"), save_trace=False)
    assert counts == {"planner": 1, "answer": 2}
    assert result["outcome"] == "abstained"
