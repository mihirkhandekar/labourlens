"""The workbench MCP tab: /api/mcp and /api/mcp/try with a fake backend, no server process and no paid call."""

import asyncio
import collections
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import httpx
import pandas as pd
import pytest

from labourlens.agent.tools import CALLER_SESSION, Tools
from labourlens.mcp.client import McpClientError, RECENT_CALLS, SyncStatsBackend
from labourlens.report.app import MCP_EXAMPLES
from test_app import ACCESS_CODE, SESSION_SECRET, agent_result, client_for, login, settings  # noqa: F401  (settings is a fixture)

DESCRIBED = {
    "server": {"name": "labourlens-stats", "version": "0.1.0", "protocol_version": "2025-06-18", "capabilities": ["prompts", "resources", "tools"], "transport": "stdio"},
    "tools": [{"name": "get_statistic", "title": "Get published statistic", "description": "Return rows.", "read_only": True, "in_allow_list": True,
               "input_schema": {"properties": {"source_id": {"type": "string", "enum": ["a"], "enum_count": 1}}, "required": ["source_id"]}},
              {"name": "list_datasets", "title": "List datasets", "description": "List.", "read_only": True, "in_allow_list": True, "input_schema": {"properties": {}, "required": []}}],
    "resources": [{"uri": "labourlens://sources", "name": "source_catalogue", "description": "Catalogue."}],
    "prompts": [{"name": "compare_quarters", "description": "Compare."}],
}


class FakeBackend:
    def __init__(self, connected=True, leak=None):
        self.client = object() if connected else None
        self.calls = collections.deque(maxlen=20)
        self.seen = []
        self.leak = leak

    def describe(self):
        return DESCRIBED

    def call_tool(self, tool, **args):
        self.seen.append((tool, args))
        if tool == "get_statistic":
            raise McpClientError("invalid_arguments", self.leak or "rejected by the fake")
        entry = {"tool": tool, "arguments": args, "ms": 1.0, "ok": True, "attempt": 0, "quarantined": 0}
        if CALLER_SESSION.get():
            entry["session"] = CALLER_SESSION.get()
        self.calls.append(entry)
        return SimpleNamespace(result=SimpleNamespace(model_dump=lambda mode="json": {"dataset_count": 0} if tool == "list_datasets" else {"big": "x" * 20000}), quarantined=0)

    def query(self, source_id, period_from, period_to, dimension=None, adjustment=None, indicator_id=None):
        entry = {"tool": "get_statistic", "arguments": {"source_id": source_id}, "ms": 1.0, "ok": True, "attempt": 0, "quarantined": 0}
        if CALLER_SESSION.get():
            entry["session"] = CALLER_SESSION.get()
        self.calls.append(entry)
        return [], None


def shared_with(backend):
    return lambda: SimpleNamespace(obs=pd.DataFrame(), passages_by_id={}, stats_backend=backend)


def run_with_runner(settings, backend, runner, scenario):
    async def go():
        async with client_for(settings, runner=runner, shared_factory=shared_with(backend)) as (app, client):
            return await scenario(app, client)
    return asyncio.run(go())


def run(settings, backend, scenario):
    async def go():
        async with client_for(settings, shared_factory=shared_with(backend)) as (app, client):
            return await scenario(app, client)
    return asyncio.run(go())


def test_endpoints_need_a_session(settings):
    async def scenario(app, client):
        assert (await client.get("/api/mcp")).status_code == 401
        assert (await client.post("/api/mcp/try", json={"example": "list_datasets"})).status_code == 401
    run(settings, FakeBackend(), scenario)


@pytest.mark.parametrize("route,method", [("/api/mcp", "GET"), ("/api/mcp/try", "POST")])
def test_rejected_request_emits_sampled_private_audit(settings, tmp_path, monkeypatch, route, method):
    import json
    from labourlens.audit import log
    from labourlens.report import audit

    monkeypatch.setattr(log, "AUDIT_DIR", tmp_path)
    monkeypatch.setattr(audit, "_sample_clients", set())
    monkeypatch.setattr(audit, "_sample_minute", -1)
    monkeypatch.setattr(audit.time, "monotonic", lambda: 120.0)

    async def scenario(app, client):
        for _ in range(2):
            assert (await client.request(method, route)).status_code == 401

    run(settings, FakeBackend(), scenario)
    records = [json.loads(line) for file in tmp_path.glob("events-*.jsonl") for line in file.read_text().splitlines()]
    assert len(records) == 1
    assert records[0]["detail"]["route"] == route
    assert records[0]["detail"]["status"] == 401
    assert records[0]["client"] == log.salted_hash("127.0.0.1")
    assert "127.0.0.1" not in json.dumps(records)


def test_overview_shape_and_roles(settings):
    async def scenario(app, client):
        await login(client)
        r = await client.get("/api/mcp")
        assert r.status_code == 200
        body = r.json()
        assert body["enabled"] and body["connected"] and body["server"]["name"] == "labourlens-stats"
        assert body["used_by_agent"] == ["get_statistic", "annual_average"] and body["agent_tool_name"] == "get_series"
        assert body["agent_tools"] == {"get_statistic": "get_series", "annual_average": "annual_average"}
        assert len(body["not_given_to_agent"]) == 8 and not {"get_statistic", "annual_average"} & set(body["not_given_to_agent"])
        assert {t["name"]: t["used_by_agent"] for t in body["tools"]} == {"get_statistic": True, "list_datasets": False}
        assert body["resources"][0]["uri"] == "labourlens://sources" and body["prompts"][0]["name"] == "compare_quarters"
        assert {e["id"] for e in body["examples"]} == set(MCP_EXAMPLES)
        assert ACCESS_CODE not in r.text and SESSION_SECRET not in r.text
    run(settings, FakeBackend(), scenario)


def test_not_connected_and_disabled_return_200_with_a_message(settings):
    async def scenario(app, client):
        await login(client)
        body = (await client.get("/api/mcp")).json()
        assert (body["enabled"], body["connected"]) == (True, False) and "not connected" in body["message"] and body["tools"] == []
    run(settings, FakeBackend(connected=False), scenario)

    async def disabled(app, client):
        await login(client)
        r = await client.get("/api/mcp")
        assert r.status_code == 200 and r.json()["enabled"] is False and r.json()["message"]
        assert (await client.post("/api/mcp/try", json={"example": "list_datasets"})).status_code == 503
    run(settings, None, disabled)


def test_discovery_failure_is_not_a_500(settings):
    class Broken(FakeBackend):
        def describe(self):
            raise McpClientError("timeout", "discovery")

    async def scenario(app, client):
        await login(client)
        r = await client.get("/api/mcp")
        assert r.status_code == 200 and r.json()["connected"] is False and r.json()["message"]
    run(settings, Broken(), scenario)


@pytest.mark.parametrize("example", ["", "get_statistic", "../etc/passwd", None, 3, ["list_datasets"], {"tool": "x"}])
def test_try_rejects_anything_outside_the_allowlist(settings, example):
    backend = FakeBackend()

    async def scenario(app, client):
        await login(client)
        assert (await client.post("/api/mcp/try", json={"example": example})).status_code == 422
        assert (await client.post("/api/mcp/try", json={"example": "list_datasets", "tool": "run_shell", "arguments": {"x": 1}})).status_code == 200
    run(settings, backend, scenario)
    assert backend.seen == [("list_datasets", {})]  # extra tool or argument fields are ignored


def test_try_runs_fixed_examples_caps_reply_and_redacts(settings):
    leak = f"echo {ACCESS_CODE}"
    backend = FakeBackend(leak=leak)

    async def scenario(app, client):
        await login(client)
        ok = (await client.post("/api/mcp/try", json={"example": "list_datasets"})).json()
        assert ok["ok"] and ok["tool"] == "list_datasets" and ok["arguments"] == {} and ok["ms"] >= 0
        rejected = await client.post("/api/mcp/try", json={"example": "retrenched_2025q1_to_2026q1"})
        assert rejected.status_code == 200 and rejected.json()["ok"] is False and rejected.json()["error"]["kind"] == "invalid_arguments"
        assert ACCESS_CODE not in rejected.text
        assert backend.seen[-1] == ("get_statistic", MCP_EXAMPLES["retrenched_2025q1_to_2026q1"]["arguments"])
    run(settings, backend, scenario)


def test_try_reply_is_size_capped(settings):
    backend = FakeBackend()

    async def scenario(app, client):
        await login(client)
        r = (await client.post("/api/mcp/try", json={"example": "latest_resident_unemployment"})).json()
        assert r["reply"]["truncated"] is True and len(r["reply"]["text"]) == 8000
    run(settings, backend, scenario)


def test_try_counts_against_the_session_limit(settings):
    settings.session_limit = 2
    backend = FakeBackend()

    async def scenario(app, client):
        await login(client)
        codes = [(await client.post("/api/mcp/try", json={"example": "list_datasets"})).status_code for _ in range(3)]
        assert codes == [200, 200, 429]
    run(settings, backend, scenario)


def test_recent_calls_are_bounded_and_record_arguments():
    backend = SyncStatsBackend()
    try:
        for i in range(RECENT_CALLS + 5):
            backend._record("get_statistic", {"source_id": "s", "period_from": f"2024-Q{i % 4 + 1}", "dimension": None}, 0.0, True, 0)
        assert len(backend.calls) == RECENT_CALLS == 20
        assert backend.calls[-1]["arguments"] == {"source_id": "s", "period_from": "2024-Q1"} and backend.calls[-1]["tool"] == "get_statistic"
    finally:
        backend.close()


def test_recorded_calls_carry_the_caller_session_tag_only_when_one_is_set():
    backend = SyncStatsBackend()
    try:
        backend._record("list_datasets", {}, 0.0, True, 0)
        token = CALLER_SESSION.set("visitor-a")
        try:
            backend._record("list_datasets", {}, 0.0, True, 0)
        finally:
            CALLER_SESSION.reset(token)
        assert "session" not in backend.calls[0] and backend.calls[1]["session"] == "visitor-a"
    finally:
        backend.close()


def test_overview_shows_each_visitor_only_their_own_calls_and_never_the_session_tag(settings):
    backend = FakeBackend()
    settings.session_limit = 20

    def agent_runner(question, shared):  # like the agent graph: the tool runs in a pool thread that does not inherit the request context
        tools = Tools(shared)
        with ThreadPoolExecutor(1) as pool:
            pool.submit(tools.get_series, "visitor_marker_" + question[:1], "2024-Q1", "2024-Q1").result()
        return agent_result(question)

    async def scenario(app, client):
        await login(client)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://testserver") as other:
            await login(other)
            assert (await client.post("/api/mcp/try", json={"example": "list_datasets"})).status_code == 200
            assert (await other.post("/api/ask", json={"question": "Zebra resident unemployment rate trend?"})).status_code == 200
            mine, theirs = (await client.get("/api/mcp")).json(), (await other.get("/api/mcp")).json()
        assert [c["tool"] for c in mine["recent_calls"]] == ["list_datasets"]
        assert [c["arguments"] for c in theirs["recent_calls"]] == [{"source_id": "visitor_marker_Z"}]
        assert len(backend.calls) == 2  # the operator's log is global
        assert all("session" not in c for c in mine["recent_calls"] + theirs["recent_calls"])
    run_with_runner(settings, backend, agent_runner, scenario)


def test_workbench_shell_has_the_mcp_tab():
    from pathlib import Path
    script = (Path(__file__).resolve().parents[2] / "web/static/js/workbench.js").read_text()
    assert "['mcp', 'MCP']" in script and "role', 'tab'" in script
    assert "/api/mcp/try" in script and "Used by the agent" in script and "Not given to the agent" in script
    assert "innerHTML" not in script
