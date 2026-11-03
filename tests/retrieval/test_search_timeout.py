"""Served report search: its own timeout, one timeout retry, an honest 'timed out' label and a required disclosure (D-091). Slow stub tools, no key."""
import json
import time

import pytest
from .test_parallel_tools import GET, _cfg, _shared, script, tc

from labourlens.agent import graph as g
from labourlens.agent import tools as tl
from labourlens.answer.schema import Answer
from labourlens.answer.validate import report_search_failure_errors


def run(cfg, question="why did retrenchments rise?"):
    shared = _shared()
    tools = tl.Tools(shared, cfg.retrieval, question, cfg.tool_timeout_s)
    final = g.build_graph(shared, tools, cfg).invoke({"question": question, "round": 0, "calls_used": 0, "attempts": 0, "trace": []}, {"recursion_limit": 40})
    return tools, final, [e for e in final["trace"] if e["node"] == "execute_tool"]


def patch_search(monkeypatch, delays):
    calls = []

    def search_reports(self, query, k=8):
        calls.append(query)
        time.sleep(delays[min(len(calls), len(delays)) - 1])
        it = self._add("P", f"passage-{len(calls)}", "mom-2026-q2-final", "Report", None, "final", "p1", "stated reasons")
        return tl.ToolResult(True, [it] if it else [], "1 new passage")

    monkeypatch.setattr(tl.Tools, "search_reports", search_reports)
    return calls


SEARCH = [tc("search_reports", {"query": "reasons", "k": 8}, "s")]


def test_search_has_its_own_budget_and_statistics_keep_the_short_one(monkeypatch):
    patch_search(monkeypatch, [0.4])
    real = tl.Tools.get_series
    monkeypatch.setattr(tl.Tools, "get_series", lambda self, *a, **k: (time.sleep(0.4), real(self, *a, **k))[1])
    script(monkeypatch, [[*SEARCH, tc("get_series", GET, "g")], []])
    _, _, events = run(_cfg(tool_timeout_s=0.2, search_timeout_s=1.0))
    assert [(e["detail"]["tool"], e["event"]) for e in events] == [("search_reports", "ok"), ("get_series", "operational_failure")]


def test_a_timed_out_search_is_retried_once_inside_the_budget_and_the_retry_is_not_a_counted_call(monkeypatch):
    monkeypatch.setattr(g, "SEARCH_RETRY_TIMEOUT_S", 1.0)
    monkeypatch.setattr(g, "MIN_RETRY_S", 0.1)
    calls = patch_search(monkeypatch, [0.6, 0.0])  # the first attempt outlives 0.3 s, the retry is instant
    script(monkeypatch, [SEARCH, []])
    tools, final, events = run(_cfg(tool_timeout_s=0.2, search_timeout_s=0.3))
    assert len(calls) == 2 and [e["event"] for e in events] == ["ok"] and final["calls_used"] == 1
    assert [i.passage_id for i in tools.items] == ["passage-2"]  # the late first attempt published nothing


def test_two_timeouts_are_labelled_timed_out_not_a_generic_failure_and_a_note_is_added(monkeypatch):
    monkeypatch.setattr(g, "SEARCH_RETRY_TIMEOUT_S", 0.3)
    monkeypatch.setattr(g, "MIN_RETRY_S", 0.1)
    patch_search(monkeypatch, [0.8, 0.8])
    script(monkeypatch, [[*SEARCH, tc("get_series", GET, "g")], []])
    tools, final, events = run(_cfg(tool_timeout_s=0.2, search_timeout_s=0.3))
    bad = events[0]["detail"]
    assert events[0]["event"] == "operational_failure" and bad["error_kind"] == "timeout"
    assert "timed out after" in bad["error"] and "retried once" in bad["error"]
    assert any("Report search timed out" in n for n in tools.notes)
    tool_message = next(m["content"] for m in final["planner_messages"] if m["role"] == "tool")
    assert "timed out after" in tool_message and "not shown to be empty" in tool_message
    time.sleep(1.0)  # late workers finish into detached forks only
    assert [i.label for i in tools.items] == ["O1", "O2"]


def test_the_retry_is_skipped_when_the_run_deadline_leaves_no_room(monkeypatch):
    monkeypatch.setattr(g, "ANSWER_RESERVE_S", 100.0)
    calls = patch_search(monkeypatch, [0.6, 0.0])
    script(monkeypatch, [SEARCH, []])
    _, _, events = run(_cfg(tool_timeout_s=0.2, search_timeout_s=0.3, run_deadline_s=50.0))
    assert len(calls) == 1 and "no time left to retry" in events[0]["detail"]["error"]


@pytest.mark.parametrize("annual", [False])
def test_configurations_without_search_timeout_keep_the_old_label_and_no_retry(monkeypatch, annual):
    calls = patch_search(monkeypatch, [0.6])
    script(monkeypatch, [SEARCH, []])
    _, _, events = run(_cfg(tool_timeout_s=0.2))
    assert len(calls) == 1 and events[0]["detail"]["error"].endswith("did not complete") and "error_kind" not in events[0]["detail"]


def answered(summary="Retrenchments rose.", caveats=()):
    return Answer(status="answered", summary=summary, claims=[], caveats=list(caveats), reason="", clarification_question="")


def test_statistics_only_answer_to_a_why_question_must_say_report_search_failed():
    assert report_search_failure_errors(answered(), "Why did retrenchments rise?", "timed out")
    assert report_search_failure_errors(answered(caveats=["Report search timed out, so MOM's explanations are not covered."]), "Why did retrenchments rise?", "timed out") == []
    assert report_search_failure_errors(answered(), "How did retrenchments change?", "timed out") == []  # no reasons were asked for
    abstain = Answer(status="abstained", summary="", claims=[], caveats=[], reason="x", clarification_question="")
    assert report_search_failure_errors(abstain, "Why?", "failed") == []


def test_served_config_sets_the_search_budget():
    from labourlens.agent import served

    cfg = served.shipped_config()
    assert cfg.search_timeout_s == g.SEARCH_TIMEOUT_S == 25.0 and cfg.tool_timeout_s == g.TOOL_TIMEOUT_S == 10.0
    assert json.dumps(cfg.key())  # not part of the key
    assert "search_timeout" not in cfg.key()
