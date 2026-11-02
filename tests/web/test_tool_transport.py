"""D-066: the live app's tool transport setting and the MCP tab's account of which tools run over MCP. No server process, no paid call."""

import asyncio
import collections
from types import SimpleNamespace

import pandas as pd
import pytest

from labourlens.agent.served import DEFAULT_TRANSPORT, MCP_ALL_ROUTED, TRANSPORTS
from labourlens.report.app import Settings
from test_app import client_for, login, settings  # noqa: F401  (settings is a fixture)
from test_mcp_panel import DESCRIBED, FakeBackend


def test_the_live_default_is_mcp_all_and_the_flag_values_are_validated(monkeypatch):
    assert DEFAULT_TRANSPORT == "mcp_all" and TRANSPORTS == ("direct", "mcp_stats", "mcp_all")
    monkeypatch.delenv("LABOURLENS_MCP", raising=False)
    monkeypatch.delenv("LABOURLENS_TOOL_TRANSPORT", raising=False)
    assert Settings.from_env().tool_transport == "mcp_all" and Settings.from_env().mcp_enabled
    for value in TRANSPORTS:
        monkeypatch.setenv("LABOURLENS_TOOL_TRANSPORT", value)
        assert Settings.from_env().tool_transport == value and Settings.from_env().mcp_enabled == (value != "direct")
    monkeypatch.setenv("LABOURLENS_TOOL_TRANSPORT", "mcp-everywhere")
    with pytest.raises(ValueError):
        Settings.from_env()
    monkeypatch.setenv("LABOURLENS_MCP", "false")  # the D-053 switch still wins: direct calls
    monkeypatch.setenv("LABOURLENS_TOOL_TRANSPORT", "mcp_all")
    assert Settings.from_env().tool_transport == "direct"


def test_the_app_builds_its_shared_state_with_the_configured_transport(monkeypatch, settings):  # noqa: F811
    from labourlens.agent import served

    seen = []
    monkeypatch.setattr(served, "make_shared", lambda transport="x": seen.append(transport) or SimpleNamespace(obs=pd.DataFrame(), passages_by_id={}, stats_backend=None))

    async def go(transport):
        from labourlens.report.app import create_app

        app = create_app(settings=Settings(**{**settings.__dict__, "tool_transport": transport}), runner=lambda question, shared: {})  # no shared_factory: the default one
        async with app.router.lifespan_context(app):
            pass

    for transport in ("mcp_all", "mcp_stats", "direct"):
        asyncio.run(go(transport))
    assert seen == ["mcp_all", "mcp_stats", "direct"]


def described_all():
    names = ["search_reports", "calculate_change", "calculate_from_text_values", "describe_corpus"]
    extra = [{"name": n, "title": n, "description": n, "read_only": True, "in_allow_list": True, "input_schema": {"properties": {}, "required": []}} for n in names]
    return {**DESCRIBED, "tools": DESCRIBED["tools"] + extra}


def test_the_mcp_tab_lists_the_tools_that_really_run_over_mcp(settings):  # noqa: F811
    class Backend(FakeBackend):
        def describe(self):
            return described_all()

    shared = lambda: SimpleNamespace(obs=pd.DataFrame(), passages_by_id={}, stats_backend=Backend(), mcp_routed=MCP_ALL_ROUTED)

    async def go():
        async with client_for(settings, shared_factory=shared) as (app, client):
            await login(client)
            return (await client.get("/api/mcp")).json()

    body = asyncio.run(go())
    assert body["used_by_agent"] == ["get_statistic", "search_reports", "calculate_change"] and body["agent_tool_name"] == "get_series"
    assert body["agent_tools"] == {"get_statistic": "get_series", "search_reports": "search_reports", "calculate_change": "calculate_change"}
    assert set(body["not_given_to_agent"]) >= {"calculate_from_text_values", "describe_corpus", "list_datasets"} and "search_reports" not in body["not_given_to_agent"]
    assert {t["name"]: t["used_by_agent"] for t in body["tools"]}["search_reports"] is True
    assert {t["name"]: t["used_by_agent"] for t in body["tools"]}["describe_corpus"] is False
