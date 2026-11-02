"""Offline statistics-store ablation: runtime catalogue, refusal, and unchanged live transport."""
import json
from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from labourlens import paths
from labourlens.agent import graph, served
from labourlens.agent.tools import BASE_TOOLS, Tools, offered_tools
from labourlens.answer import llm
from labourlens.answer.pipeline import load_prompt
from labourlens.evaluation import served_exp as sx


@pytest.fixture
def shared():
    def no_lookup(*args, **kwargs):
        pytest.fail("disabled statistics must never reach either backend")

    return SimpleNamespace(obs=pd.DataFrame({"source_id": ["s"], "indicator_id": ["i"]}),
                           stats=SimpleNamespace(query=no_lookup), stats_backend=SimpleNamespace(query=no_lookup),
                           catalogue_text=lambda: "dataset metadata", corpus={}, disabled_tools=frozenset({"get_series"}))


def test_catalogue_excludes_disabled_statistics_but_keeps_other_tools(shared):
    assert offered_tools(shared) == ["search_reports", "calculate_change"]
    schema = graph.plan_schema(shared)
    assert schema["properties"]["calls"]["items"]["properties"]["tool"]["enum"] == offered_tools(shared)
    assert graph.MAX_CALLS == 6 and graph.MAX_ROUNDS == 2 and graph.TOOL_TIMEOUT_S == 10.0


def test_forced_statistics_call_is_a_traced_tool_error_not_a_crash(shared, monkeypatch):
    seen = []
    plans = iter([{"decision": "gather", "note": "forced disabled call", "calls": [{"tool": "get_series"}]},
                  {"decision": "finish", "note": "stop", "calls": []}])

    def chat(model, messages, max_completion_tokens=6000, **kwargs):
        if kwargs.get("schema_name") == "plan":
            seen.append(messages[0]["content"])
            payload = next(plans)
        else:
            payload = {"status": "abstained", "summary": "", "claims": [], "caveats": [],
                       "reason": "Insufficient evidence.", "clarification_question": ""}
        return llm.LLMResult(json.dumps(payload), 10, 5, 0, .01)

    monkeypatch.setattr(llm, "chat", chat)
    row = graph.run_agent("What is the published figure?", shared, save_trace=False)
    events = [e for e in row["trace"] if e["node"] == "execute_tool"]
    assert len(events) == 1 and events[0]["event"] == "error"
    assert events[0]["detail"]["error_kind"] == "disabled_tool"
    assert row["tool_calls"] == 1 and row["outcome"] != "operational_failure"
    assert not row["evidence"]
    original, _, _ = load_prompt("planner_v1")
    expected = "\n".join(line for line in original.format(catalogue=shared.catalogue_text()).split("\n")
                         if not line.startswith("- get_series("))
    assert seen and all(prompt == expected for prompt in seen)
    assert "- search_reports(" in seen[0] and "- calculate_change(" in seen[0]
    score = sx.agx.score_run({"case_id": "s", "family": "factual_lookup", "question": row["question"], "expected_behavior": "abstain",
                             "evidence_text": [], "evidence_data": [], "reference_facts": [], "calculation": None}, row)
    assert score["tool_errors"] == 1


def test_direct_tool_invocation_also_rejects_statistics(shared):
    result = Tools(shared).get_series("s", "2026-Q1", "2026-Q2")
    assert not result.ok and result.error_kind == "disabled_tool" and result.transport is None


def test_default_catalogue_and_live_transports_are_unchanged(shared, monkeypatch):
    del shared.disabled_tools
    assert offered_tools(shared) == list(BASE_TOOLS)
    assert graph.plan_schema(shared)["properties"]["calls"]["items"]["properties"]["tool"]["enum"] == list(BASE_TOOLS)
    assert served.TRANSPORTS == ("direct", "mcp_stats", "mcp_all")
    assert served.DEFAULT_TRANSPORT == "mcp_stats"
    from labourlens.report.app import Settings

    monkeypatch.delenv("LABOURLENS_MCP", raising=False)
    monkeypatch.setenv("LABOURLENS_TOOL_TRANSPORT", "no-stats")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_no_stats_dry_run_has_explicit_filtered_tool_metadata(monkeypatch, tmp_path, capsys):
    sample = paths.EXPERIMENTS / "served/mixed-sample.jsonl"
    monkeypatch.setattr(paths, "EXPERIMENTS", tmp_path / "experiments")
    monkeypatch.setattr(paths, "DATA", tmp_path / "data")
    monkeypatch.setattr(sx, "singapore_today", lambda: date(2026, 11, 2))
    monkeypatch.setattr(sx, "make_shared", lambda *a, **k: pytest.fail("dry run must not load data or start MCP"))
    monkeypatch.setattr(llm, "chat", lambda *a, **k: pytest.fail("dry run must not call models"))
    plan = sx.run(gold_path=sample, pairs=["gpt-6-luna"], tag="S65-nostats", route="no-stats", dry_run=True)
    assert plan["cases"] == 65 and plan["route"] == "no-stats" and plan["tool_transport"] == "direct"
    assert plan["tool_list_filtered"] and plan["offered_tools"] == ["search_reports", "calculate_change"]
    assert list(plan["models"]) == ["gpt-6-luna"]
    assert json.loads(capsys.readouterr().out) == plan
    assert not (tmp_path / "data").exists() and not (tmp_path / "experiments").exists()
