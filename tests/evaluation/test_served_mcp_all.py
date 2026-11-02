"""served-exp --route mcp-all (D-066): dry-run, the new arm's recording and provenance. Stubs only: no key, no corpus, no server process, no paid call."""
import json
from collections import deque
from datetime import date
from types import SimpleNamespace

import pytest

from labourlens import paths
from labourlens.agent import graph, served, smalltalk
from labourlens.agent.graph import AgentConfig
from labourlens.answer import llm
from labourlens.evaluation import served_exp as sx

SAMPLE = paths.EXPERIMENTS / "served" / "mixed-sample.jsonl"


@pytest.fixture
def sandbox(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "DATA", tmp_path / "data")
    monkeypatch.setattr(paths, "EXPERIMENTS", tmp_path / "experiments")
    monkeypatch.setattr(sx, "singapore_today", lambda: date(2026, 11, 2))  # the registered probes' date, whatever day the test runs
    return tmp_path


def test_dry_run_makes_no_call_and_creates_nothing(sandbox, monkeypatch, capsys):
    monkeypatch.setattr(sx, "make_shared", lambda *a, **k: pytest.fail("a dry run must not start the MCP server or load the corpus"))
    monkeypatch.setattr(llm, "chat", lambda *a, **k: pytest.fail("a dry run must not call a model"))
    plan = sx.run(gold_path=SAMPLE, pairs=["gpt-6-luna", "gpt-5.6-luna"], tag="S65-mcpall", route="mcp-all", dry_run=True)
    assert plan["dry_run"] and plan["experiment"] == "served-dev-S65-mcpall" and plan["tool_transport"] == "mcp_all" and plan["cases"] == 65 and plan["probes"] == 14
    assert not (sandbox / "data").exists() and not (sandbox / "experiments").exists()
    assert json.loads(capsys.readouterr().out)["experiment"] == "served-dev-S65-mcpall"
    with pytest.raises(FileExistsError):  # an id that exists is refused even in a dry run
        (sandbox / "experiments/runs/served-dev-S65-mcpall").mkdir(parents=True)
        sx.run(gold_path=SAMPLE, tag="S65-mcpall", route="mcp-all", dry_run=True)


def test_dry_run_estimates_cost_from_a_measured_arm_or_says_it_cannot(sandbox):
    assert sx.estimate_cost(["gpt-6-luna"], 65)["total_estimate_usd"] is None  # reference arm not in the sandbox
    ref = sandbox / "experiments/runs" / sx.REFERENCE_ARM
    ref.mkdir(parents=True)
    for label, cost in (("gpt-6-luna", 0.002), ("gpt-5.6-luna", 0.004)):
        (ref / f"{label}.metrics.json").write_text(json.dumps({"metrics": {"all": {"cost_per_case_usd": cost}}}))
    est = sx.estimate_cost(["gpt-6-luna", "gpt-5.6-luna"], 65)
    assert est["gpt-6-luna"]["estimate_usd"] == 0.13 and est["total_estimate_usd"] == 0.39


def test_routes_map_to_the_agent_transports_and_unknown_routes_are_refused(sandbox):
    assert sx.ROUTES == {"mcp": "mcp_stats", "direct": "direct", "mcp-all": "mcp_all"} and set(sx.ROUTES.values()) == set(served.TRANSPORTS)
    with pytest.raises(ValueError):
        sx.run(gold_path=SAMPLE, tag="X", route="mcp-everything", dry_run=True)


def test_the_cli_exposes_the_new_route_and_the_dry_run_flag(monkeypatch):
    from labourlens.cli import main

    captured = []
    monkeypatch.setattr(sx, "run", lambda *args, **kwargs: captured.append((args, kwargs)))
    assert main(["served-exp", "--tag", "T", "--route", "mcp-all", "--dry-run"]) == 0
    assert captured[0][0][5] == "mcp-all" and captured[0][1] == {"dry_run": True}


class StubBackend:
    """What SyncStatsBackend offers the agent: the statistics query, `invoke` for the other tools, and a bounded call log."""

    def __init__(self):
        self.calls = deque(maxlen=20)

    def close(self):
        pass

    def query(self, *args, **kwargs):
        self.calls.append({"tool": "get_statistic", "ok": True, "attempt": 0})
        return [], None

    def invoke(self, tool, **args):
        self.calls.append({"tool": tool, "ok": True, "attempt": 0})
        if tool == "calculate_change":
            return SimpleNamespace(result=SimpleNamespace(value="0.2", unit="percentage points", formula="2.9 - 2.7"), quarantined=0), None
        r = SimpleNamespace(chunks=[SimpleNamespace(chunk_id="c1")], passages=[SimpleNamespace(passage_id="p1")])
        return SimpleNamespace(result=r, quarantined=0), None


def test_the_new_arm_records_every_tool_call_and_its_transport(sandbox, monkeypatch):
    def agent(question, shared, config, **kwargs):
        shared.stats_backend.invoke("search_reports", query="q", question=question, query_vector_b64="A" * 16384)
        shared.stats_backend.query("s", "2025-Q1", "2025-Q1")
        shared.stats_backend.invoke("calculate_change", observation_id_a="a" * 16, observation_id_b="b" * 16)
        return {"run_id": "stub", "answer": None, "question": question, "outcome": "answered", "trace": [], "errors": [], "rounds": 1, "tool_calls": 3, "evidence": [],
                "evidence_text": {}, "cited_ids": [], "seconds": .01, "usage": {"cost_usd": .001, "calls": 1, "prompt_tokens": 3, "completion_tokens": 2, "llm_seconds": .01}}

    monkeypatch.setattr(smalltalk, "run_smalltalk", lambda *a, **k: None)
    monkeypatch.setattr(graph, "run_agent", agent)
    shared = SimpleNamespace(stats_backend=sx.RecordingBackend(StubBackend()), corpus={})
    row = sx.evaluate_case({"case_id": "S-1", "question": "What was it?", "family": "factual_lookup", "expected_behavior": "answer", "evidence_text": [],
                            "evidence_data": [], "reference_facts": [], "calculation": None}, shared, AgentConfig(), route="mcp-all", web_steps=False)
    served_block = row["served"]
    assert served_block["route"] == "mcp-all" and served_block["mcp_calls"] == 3 and served_block["mcp_errors"] == 0
    tools = served_block["tool_calls"]
    assert [t["tool"] for t in tools] == ["search_reports", "calculate_change"]
    assert tools[0]["arguments"]["query_vector_b64"] == "[omitted]" and tools[0]["summary"] == {"chunk_ids": ["c1"], "passage_ids": ["p1"], "quarantined": 0}
    assert tools[1]["summary"] == {"value": "0.2", "unit": "percentage points", "formula": "2.9 - 2.7"}
    assert len(served_block["statistics_calls"]) == 1


@pytest.mark.parametrize("route,transport", [("mcp-all", "mcp_all"), ("mcp", "mcp_stats"), ("direct", "direct")])
def test_every_new_run_records_its_tool_transport_in_provenance(sandbox, monkeypatch, route, transport):
    seen = []

    def make_shared(t):
        seen.append(t)
        return SimpleNamespace(stats_backend=None if route == "direct" else StubBackend(), stats=SimpleNamespace(), corpus={})

    case = {"case_id": "S-1", "question": "q", "family": "factual_lookup", "expected_behavior": "answer", "evidence_text": [], "evidence_data": [],
            "reference_facts": [], "calculation": None}
    monkeypatch.setattr(sx, "make_shared", make_shared)
    monkeypatch.setattr(sx, "load_cases", lambda split, gold: [case])
    monkeypatch.setattr(sx, "snapshot", lambda *a, **k: {})
    monkeypatch.setattr(sx, "sampling_block", lambda cfg: {})
    monkeypatch.setattr(sx, "evaluate_case", lambda *a, **k: {"served": {"route": route}})
    monkeypatch.setattr(sx, "score_case", lambda case, result: {"is_probe": False, "answerable_gold": False})
    monkeypatch.setattr(sx, "aggregate", lambda scores: {"behavior_accuracy": 1.0})
    sx.run(pairs=["gpt-6-luna"], tag="T", route=route)
    meta = json.loads((paths.EXPERIMENTS / "runs/served-dev-T/gpt-6-luna.metrics.json").read_text())
    assert seen == [transport] and meta["provenance"]["served"]["tool_transport"] == transport and meta["provenance"]["served"]["route"] == route
