"""Synthetic-only deterministic, planner-schema and real stdio tests. No model or paid API."""
import asyncio
import importlib.util
import inspect
import json
from pathlib import Path

import pandas as pd
import pytest

from labourlens.agent.graph import ARGS, REQUIRED, AgentConfig, parse_tool_call, plan_schema, tool_definitions
from labourlens.agent.tools import Shared, StatsData, Tools, offered_tools
from labourlens.mcp.client import ALLOWED_SERVERS, McpClientError, McpStatsClient, SyncStatsBackend
from labourlens.mcp.models import RESULT_MODELS
from labourlens.mcp.server import ALL_TOOLS

FIXTURE = Path(__file__).with_name("annual_fixture.py")
spec = importlib.util.spec_from_file_location("annual_fixture", FIXTURE)
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
ARGS_ANNUAL = dict(year=2025, source_id="resident_unemployment_rate", indicator_id="rate", population="resident", adjustment="seasonally_adjusted", dimension=None)


def shared(stats=None):
    return Shared(world=(None, {}, {}), stats=stats or fixture.statistics())


def test_decimal_half_up_and_derived_c_evidence():
    stats = fixture.statistics()
    out, err = stats.annual_average(**ARGS_ANNUAL)
    assert err is None and out["value"] == "2.24"  # 2.235, half-up, not binary float rounding
    assert out["unit"] == "percent" and len(out["inputs"]) == 4
    tools = Tools(shared(stats))
    result = tools.annual_average(**ARGS_ANNUAL)
    assert result.ok and result.items[0].label == "C1" and result.items[0].stage == "calculated"
    text = result.items[0].text
    assert "not an official published annual estimate" in text
    assert "(2.1 + 2.2 + 2.3 + 2.34) / 4 = 2.24 percent" in text
    for row in out["inputs"]:
        assert row["observation_id"] in text and row["period"] in text
    assert tools.annual_average(**ARGS_ANNUAL).items == []


@pytest.mark.parametrize("change,kind", [({"year": 2026}, "not_found"), ({"year": 2019}, "invalid_arguments"),
    ({"year": True}, "invalid_arguments"), ({"year": "2025"}, "invalid_arguments"),
    ({"population": None}, "invalid_arguments"), ({"adjustment": None}, "invalid_arguments"),
    ({"indicator_id": "absent"}, "not_found"), ({"population": "overall"}, "not_found"),
    ({"dimension": []}, "invalid_arguments"), ({"source_id": "absent"}, "not_found")])
def test_argument_and_incomplete_year_refusals(change, kind):
    out, err = fixture.statistics().annual_average(**{**ARGS_ANNUAL, **change})
    assert out is None and err.error_kind == kind


@pytest.mark.parametrize("mode,kind", [("missing", "not_found"), ("null", "not_found"), ("infinity", "not_found"),
    ("duplicate", "not_found"), ("mixed", "invalid_arguments"), ("persons", "invalid_arguments"), ("ratio", "invalid_arguments")])
def test_never_averages_incomplete_mixed_or_nonrate_series(mode, kind):
    frame = fixture.statistics().obs.copy()
    if mode == "missing":
        frame = frame[frame.period != "2025-Q4"]
    elif mode in ("null", "infinity"):
        frame.loc[frame.period == "2025-Q4", "value"] = None if mode == "null" else float("inf")
    elif mode in ("duplicate", "mixed"):
        extra = frame.iloc[[0]].copy()
        if mode == "mixed":
            extra["dimension"] = "other"
        frame = pd.concat([frame, extra], ignore_index=True)
    else:
        frame["unit"] = mode
    out, err = StatsData(frame).annual_average(**ARGS_ANNUAL)
    assert out is None and err.error_kind == kind


def test_explicit_dimension_selects_one_series():
    frame = fixture.statistics().obs
    frame = pd.concat([frame.assign(dimension="A"), frame.assign(dimension="B")], ignore_index=True)
    stats = StatsData(frame)
    assert stats.annual_average(**ARGS_ANNUAL)[1].error_kind == "invalid_arguments"
    out, err = stats.annual_average(**{**ARGS_ANNUAL, "dimension": "a"})
    assert err is None and out["dimension"] == "A" and out["value"] == "2.24"


def test_start_year_and_seasonal_adjustment_selection():
    frame = fixture.statistics().obs.copy()
    frame["period"] = frame.period.str.replace("2025", "2020")
    unadjusted = frame.assign(adjustment="not_adjusted", value=4.0)
    stats = StatsData(pd.concat([frame, unadjusted], ignore_index=True))
    args = {**ARGS_ANNUAL, "year": 2020}
    assert stats.annual_average(**args)[0]["value"] == "2.24"
    assert stats.annual_average(**{**args, "adjustment": "not_adjusted"})[0]["value"] == "4.00"
    _, error = stats.annual_average(**{**args, "year": 2026})
    assert error.error_kind == "not_found" and "2026-Q3" in error.message and "2026-Q4" in error.message


def test_native_schema_args_and_legacy_defaults():
    sh = shared()
    base = list(offered_tools(sh))
    assert base == ["search_reports", "get_series", "calculate_change"]
    assert offered_tools(sh, "v2") == base + ["calculate_from_text_values"]
    assert offered_tools(sh, "annual") == base + ["annual_average"]
    assert AgentConfig().tool_set == "base" and AgentConfig().planner_mode == "structured"
    conf = AgentConfig(tool_set="annual", planner_mode="tools", planner_prompt="planner_v6", answer_prompt="answer_v8")
    assert "tools=annual" in conf.key()
    with pytest.raises(ValueError):
        AgentConfig(tool_set="annual")
    for name, definitions in (("base", tool_definitions(sh)), ("v2", tool_definitions(sh, "v2")), ("annual", tool_definitions(sh, "annual"))):
        assert [d["function"]["name"] for d in definitions] == offered_tools(sh, name)
    fn = tool_definitions(sh, "annual")[-1]["function"]
    assert fn["strict"] and not fn["parameters"]["additionalProperties"]
    assert fn["parameters"]["required"] == list(ARGS["annual_average"])
    assert set(fn["parameters"]["properties"]) == set(ARGS["annual_average"])
    assert list(inspect.signature(Tools.annual_average).parameters)[1:] == list(ARGS["annual_average"])
    assert "annual_average" in ALL_TOOLS and "annual_average" in RESULT_MODELS
    assert "year" not in plan_schema(sh)["properties"]["calls"]["items"]["properties"]
    parsed = parse_tool_call(dict(name="annual_average", arguments=json.dumps(ARGS_ANNUAL)), offered_tools(sh, "annual"))
    assert "_error" not in parsed and parsed["year"] == 2025
    bad = parse_tool_call(dict(name="annual_average", arguments=json.dumps({**ARGS_ANNUAL, "year": True})), offered_tools(sh, "annual"))
    assert bad["_error"][0] == "invalid_arguments"


@pytest.fixture
def backend(monkeypatch):
    name = "annual-offline-fixture"
    monkeypatch.setitem(ALLOWED_SERVERS, name, {**ALLOWED_SERVERS["labourlens-stats"], "args": [str(FIXTURE)]})
    backend = SyncStatsBackend(name)
    try:
        yield backend
    finally:
        backend.close()


def test_stdio_annual_follows_same_stats_backend_and_matches_direct(backend):
    sh = shared()
    direct = Tools(sh)
    sh_mcp = shared()
    sh_mcp.stats_backend = backend
    remote = Tools(sh_mcp)
    assert remote.routed("annual_average") and remote.routed("get_series")
    for args in (ARGS_ANNUAL, {**ARGS_ANNUAL, "year": 2026}, {**ARGS_ANNUAL, "population": "overall"}):
        a, b = direct.annual_average(**args), remote.annual_average(**args)
        assert (a.ok, a.error_kind, a.message, [x.text for x in a.items]) == (b.ok, b.error_kind, b.message, [x.text for x in b.items])
        assert b.transport == "mcp" and a.transport is None
    assert {c["tool"] for c in backend.calls} == {"annual_average"}
    async def schema_check():
        async with McpStatsClient(backend.server) as client:
            schema = client.schemas["annual_average"]
            assert set(schema["properties"]) == set(ARGS["annual_average"])
            assert set(schema["required"]) == set(REQUIRED["annual_average"])
            result = await client.annual_average(**ARGS_ANNUAL)
            assert result.result.value == "2.24" and len(result.result.inputs) == 4
            with pytest.raises(McpClientError) as exc:
                await client.annual_average(**{**ARGS_ANNUAL, "year": True})
            assert exc.value.kind == "invalid_arguments"
    asyncio.run(schema_check())


def test_native_planner_executes_annual_and_supplies_cited_inputs(monkeypatch):
    from labourlens.agent.graph import run_agent
    from labourlens.answer import llm

    seen = []
    turns = [[dict(id="annual_1", name="annual_average", arguments=json.dumps(ARGS_ANNUAL))], []]

    def chat(model, messages, max_completion_tokens=6000, **kwargs):
        if "tools" in kwargs:
            seen.append(messages)
            return llm.LLMResult("", 10, 5, 0, 0.01, tool_calls=turns.pop(0))
        payload = dict(status="abstained", summary="", claims=[], caveats=[], clarification_question="",
                       reason="Synthetic test declines to answer.")
        return llm.LLMResult(json.dumps(payload), 10, 5, 0, 0.01)

    monkeypatch.setattr(llm, "chat", chat)
    cfg = AgentConfig(tool_set="annual", planner_mode="tools", planner_prompt="planner_v6", answer_prompt="answer_v8")
    result = run_agent("Find the simple mean of four quarterly resident rates in 2025.", shared(), cfg, save_trace=False)
    calls = [e for e in result["trace"] if e["node"] == "execute_tool"]
    assert len(calls) == 1 and calls[0]["event"] == "ok" and calls[0]["detail"]["tool"] == "annual_average"
    assert result["evidence"][0]["label"] == "C1"
    message = next(m["content"] for m in seen[1] if m["role"] == "tool")
    assert "Untrusted tool output" in message and "C1:" in message and "2025-Q4" in message
