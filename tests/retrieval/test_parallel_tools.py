"""Served annual rounds run planned tool calls concurrently (deterministic fakes: no key, network or corpus).

Overlap is proved with a Barrier that only opens if every call of the round is inside its tool at the same time; a sequential executor breaks it."""
import json
import threading
import time

import pandas as pd

from labourlens.agent import graph as g
from labourlens.agent import tools as tl
from labourlens.answer import llm


class NoSearch:
    def search(self, q, k):
        return []


def _shared():
    cols = dict(source_id="retrenched_employees", indicator_id="retrenched_employees", unit="persons", population="establishments",
                adjustment="not_applicable", dimension="", release_stage="dataset_snapshot", in_answer_scope=True, missing_reason="")
    rows = [{"period": "2026-Q1", "value": 3830.0}, {"period": "2026-Q2", "value": 4620.0}]
    df = pd.DataFrame([{**cols, "observation_id": f"obs{i}", "source_locator": f"row{i}", **r} for i, r in enumerate(rows)])
    return tl.Shared(world=(NoSearch(), {}, {}), observations=df)


def _cfg(annual=True, **kw):
    if annual:
        return g.AgentConfig(planner_mode="tools", planner_prompt="planner_v6", answer_prompt="answer_v8", tool_set="annual", **kw)
    return g.AgentConfig(planner_mode="tools", planner_prompt="planner_v5", answer_prompt="answer_v7", **kw)


GET = dict(source_id="retrenched_employees", period_from="2026-Q1", period_to="2026-Q2", dimension=None, adjustment=None, indicator_id="retrenched_employees")


def tc(name, args, id):
    return {"id": id, "name": name, "arguments": json.dumps(args)}


def script(monkeypatch, turns):
    pending = list(turns)

    def chat(model, messages, max_completion_tokens=6000, extra=None, schema=None, schema_name="answer", **kw):
        if "tools" in kw:
            return llm.LLMResult("", 10, 5, 0, 0.01, tool_calls=pending.pop(0))
        return llm.LLMResult(json.dumps({"status": "abstained", "summary": "", "claims": [], "caveats": [], "clarification_question": "", "reason": "x"}), 10, 5, 0, 0.01)

    monkeypatch.setattr(llm, "chat", chat)


class Probe:
    def __init__(self, parties, delays=None):
        self.barrier = threading.Barrier(parties, timeout=2) if parties else None
        self.delays, self.active, self.max_active, self.lock = delays or {}, 0, 0, threading.Lock()

    def enter(self, key):
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            if self.barrier:
                self.barrier.wait()
            time.sleep(self.delays.get(key, 0))
        finally:
            with self.lock:
                self.active -= 1


def patch_tools(monkeypatch, probe):
    real_get = tl.Tools.get_series

    def search_reports(self, query, k=8):
        probe.enter(query)
        it = self._add("P", f"passage-{query}", "mom-2026-q1-final", "Report", None, "final", "p1", f"text {query}")
        return tl.ToolResult(True, [it] if it else [], f"1 new passages: {it.label}" if it else "none")

    def get_series(self, *a, **kw):
        probe.enter("series")
        return real_get(self, *a, **kw)

    monkeypatch.setattr(tl.Tools, "search_reports", search_reports)
    monkeypatch.setattr(tl.Tools, "get_series", get_series)


def execute(cfg, shared):
    tools = tl.Tools(shared, cfg.retrieval, "q", cfg.tool_timeout_s)
    graph = g.build_graph(shared, tools, cfg)
    final = graph.invoke({"question": "q", "round": 0, "calls_used": 0, "attempts": 0, "trace": []}, {"recursion_limit": 40})
    return tools, final


def events(final):
    return [e for e in final["trace"] if e["node"] == "execute_tool"]


def test_annual_round_overlaps_and_labels_follow_planned_order_not_completion_order(monkeypatch):
    # The first planned search is the slowest: completion order is the reverse of planned order.
    probe = Probe(3, {"A": 0.3, "series": 0.1})
    patch_tools(monkeypatch, probe)
    script(monkeypatch, [[tc("search_reports", {"query": "A", "k": 4}, "a"), tc("get_series", GET, "s"), tc("search_reports", {"query": "B", "k": 4}, "b")],
                         [tc("calculate_change", dict(obs_a="O1", obs_b="O2", kind="difference"), "c")]])
    tools, final = execute(_cfg(), _shared())
    assert probe.max_active == 3  # the barrier would have raised (operational failure) had the calls run one after another
    assert [e["event"] for e in events(final)] == ["ok"] * 4
    assert [(i.label, i.passage_id) for i in tools.items][:4] == [("P1", "passage-A"), ("O1", "obs0"), ("O2", "obs1"), ("P2", "passage-B")]
    assert events(final)[0]["detail"]["new_items"] == ["P1"] and events(final)[1]["detail"]["new_items"] == ["O1", "O2"]
    assert events(final)[2]["detail"]["new_items"] == ["P2"]
    # The round-two calculation bound to the observations the round-one get_series produced.
    assert tools.items[-1].label == "C1" and events(final)[3]["detail"]["new_items"] == ["C1"]
    assert set(tools._obs) == {"O1", "O2"} and [i.label for i in tools.items] == ["P1", "O1", "O2", "P2", "C1"]
    assert [e["detail"]["tool"] for e in events(final)] == ["search_reports", "get_series", "search_reports", "calculate_change"]
    assert final["calls_used"] == 4 and final["round"] == 2
    planner_tool_msgs = [m for m in final["planner_messages"] if m["role"] == "tool"]
    assert "P1" in planner_tool_msgs[0]["content"] and "O1" in planner_tool_msgs[1]["content"] and "P2" in planner_tool_msgs[2]["content"]


def test_same_round_calculation_never_sees_a_sibling_get_series(monkeypatch):
    probe = Probe(1, {"series": 0.1})
    patch_tools(monkeypatch, probe)
    script(monkeypatch, [[tc("get_series", GET, "s"), tc("calculate_change", dict(obs_a="O1", obs_b="O2", kind="difference"), "c")], []])
    tools, final = execute(_cfg(), _shared())
    assert [e["event"] for e in events(final)] == ["ok", "error"]
    assert events(final)[1]["detail"]["error_kind"] == "invalid_arguments"  # O1/O2 did not exist when the round started: same result at any scheduling
    assert [i.label for i in tools.items] == ["O1", "O2"]


def test_timeout_isolates_late_worker_and_keeps_on_time_evidence(monkeypatch):
    probe = Probe(0, {"slow": 0.7})
    patch_tools(monkeypatch, probe)
    script(monkeypatch, [[tc("search_reports", {"query": "slow", "k": 4}, "a"), tc("get_series", GET, "s"), tc("search_reports", {"query": "fast", "k": 4}, "b")], []])
    tools, final = execute(_cfg(tool_timeout_s=0.2), _shared())
    assert [e["event"] for e in events(final)] == ["operational_failure", "ok", "ok"]
    assert [i.label for i in tools.items] == ["O1", "O2", "P1"]  # the timed-out call published nothing and took no label
    time.sleep(0.8)  # the late worker finishes now and writes into its detached fork only
    assert [i.passage_id for i in tools.items] == ["obs0", "obs1", "passage-fast"]
    assert tools._n == {"P": 1, "O": 2, "C": 0}


def test_legacy_sequence_is_unchanged_for_other_tool_sets(monkeypatch):
    probe = Probe(0, {"A": 0.05, "series": 0.05})
    patch_tools(monkeypatch, probe)
    script(monkeypatch, [[tc("search_reports", {"query": "A", "k": 4}, "a"), tc("get_series", GET, "s"), tc("search_reports", {"query": "B", "k": 4}, "b")], []])
    tools, final = execute(_cfg(annual=False), _shared())
    assert probe.max_active == 1  # strictly one call at a time
    assert [e["event"] for e in events(final)] == ["ok", "ok", "ok"]
    assert [i.label for i in tools.items] == ["P1", "O1", "O2", "P2"]
