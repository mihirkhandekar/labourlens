"""Protocol-level tests: a real MCP server subprocess over stdio, a real client, hostile and faulty fixture servers."""

import asyncio
import json

import pytest

from labourlens.agent.tools import StatsData, Tools, Shared
from labourlens.mcp.server import ALL_TOOLS
from labourlens.mcp.client import McpClientError, McpStatsClient, SyncStatsBackend, register_test_server

ARGS = dict(source_id="retrenched_employees", period_from="2026-Q1", period_to="2026-Q2")


def run(coro):
    return asyncio.run(coro)


def test_discovery_exposes_only_read_only_tools_and_resources():
    async def go():
        async with McpStatsClient() as c:
            tools = (await c.session.list_tools()).tools
            assert sorted(t.name for t in tools) == sorted(ALL_TOOLS) and c.ignored_tools == []
            for t in tools:
                ann = t.annotations
                assert ann.read_only_hint and ann.idempotent_hint and not ann.destructive_hint and not ann.open_world_hint, t.name
            stat = next(t for t in tools if t.name == "get_statistic")
            assert "source_id" in stat.input_schema["properties"]
            assert await c.list_resources() == ["labourlens://sources"]
            cat = await c.read_resource("labourlens://sources")
            assert len(cat["datasets"]) >= 30 and cat["trust"] == "untrusted_data"
            assert all(d["text_served_by_this_server"] is False for d in cat["documents"])  # no MOM report text over MCP
            assert "licence" in cat["datasets"][0]
            one = await c.read_resource("labourlens://source/retrenched_employees")
            assert one["entry"]["source_id"] == "retrenched_employees"
            with pytest.raises(McpClientError) as e:
                await c.read_resource("labourlens://source/does_not_exist")
            assert e.value.kind == "not_found"
    run(go())


def test_mcp_result_equals_direct_query():
    direct, _ = StatsData().query(**ARGS)

    async def go():
        async with McpStatsClient() as c:
            return (await c.get_statistic(**ARGS)).rows
    assert run(go()) == direct


@pytest.mark.parametrize("bad,kind", [
    (dict(ARGS, source_id="nope"), "invalid_arguments"),            # enum: caught by the client's schema check
    (dict(ARGS, period_from="Q1 2026"), "invalid_arguments"),       # pattern
    (dict(ARGS, period_from="2023-Q1"), "invalid_arguments"),       # out of scope: caught by the server
    (dict(source_id="retrenched_by_industry", period_from="2026-Q1", period_to="2026-Q2"), "too_large"),
    (dict(ARGS, dimension="x" * 500), "invalid_arguments"),         # max_length
])
def test_invalid_arguments_are_rejected_with_a_correctable_kind(bad, kind):
    async def go():
        async with McpStatsClient() as c:
            with pytest.raises(McpClientError) as e:
                await c.get_statistic(**bad)
            assert e.value.kind == kind
    run(go())


def test_server_rejects_bad_arguments_even_if_the_client_check_is_bypassed():
    async def go():
        async with McpStatsClient() as c:
            res = await c.session.call_tool("get_statistic", dict(ARGS, source_id="nope"))
            assert res.is_error
            res = await c.session.call_tool("get_statistic", dict(ARGS, period_to="2030-Q1"))
            assert res.is_error and "supported periods" in res.content[0].text
    run(go())


def _hostile(mode, call_t=2.0):
    name = register_test_server(f"evil-{mode}", mode)

    async def go():
        async with McpStatsClient(name, call_timeout_s=call_t, connect_timeout_s=20) as c:
            return await c.get_statistic(**ARGS), c
    return go()


def test_instruction_in_result_row_is_quarantined_not_passed_on():
    reply, _ = run(_hostile("inject"))
    assert reply.quarantined == 1 and len(reply.rows) == 2
    assert "PWNED" not in json.dumps(reply.rows)


def test_instruction_the_heuristics_miss_is_passed_on_and_must_be_handled_downstream():
    # Documents a known limit: regex heuristics are not complete. The prompt rules, flags and quote checks are the next layers,
    # measured end to end in the threat suite.
    reply, _ = run(_hostile("subtle_inject"))
    assert reply.quarantined == 0 and any("PWNED" in r["dimension"] for r in reply.rows)


@pytest.mark.parametrize("mode,kind", [("oversized", "oversized"), ("malformed", "malformed"), ("schema_drift", "malformed"),
                                       ("slow", "timeout"), ("crash", "unavailable"), ("wrong_version", "version_mismatch"),
                                       ("bad_name", "not_allowed")])
def test_faulty_or_hostile_server_fails_closed_with_a_specific_error(mode, kind):
    with pytest.raises(McpClientError) as e:
        run(_hostile(mode, call_t=1.0))
    assert e.value.kind == kind


def test_unexpected_tools_are_ignored_and_reported():
    reply, c = run(_hostile("extra_tool"))
    assert reply.ignored_tools == ["run_shell"] and len(reply.rows) == 2


def test_server_environment_has_no_secrets(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key-123456789")
    name = register_test_server("evil-env", "env_probe")

    async def go():
        async with McpStatsClient(name) as c:
            res = await c.session.call_tool("get_statistic", ARGS)
            return res.structured_content["note"]
    assert run(go()) == "OPENAI_API_KEY=ABSENT"


def test_unlisted_server_and_missing_binary_are_refused():
    with pytest.raises(McpClientError) as e:
        McpStatsClient("some-other-server")
    assert e.value.kind == "not_allowed"
    from labourlens.mcp import client as C
    C.ALLOWED_SERVERS["ghost"] = {**C.ALLOWED_SERVERS["labourlens-stats"], "command": "/nonexistent/python"}

    async def go():
        async with McpStatsClient("ghost"):
            pass
    with pytest.raises(McpClientError) as e:
        run(go())
    assert e.value.kind == "unavailable"


def test_sync_backend_drives_agent_get_series_through_mcp_and_maps_errors():
    backend = SyncStatsBackend()
    try:
        sh = Shared(world=(None, {}, {}), observations=None)
        sh.stats_backend = backend
        t = Tools(sh)
        r = t.get_series(**ARGS)
        assert r.ok and len(r.items) == 2 and len(backend.calls) == 1
        assert t.get_series("retrenched_employees", "2023-Q1", "2026-Q2").error_kind == "invalid_arguments"
        assert t.get_series("retrenched_by_industry", "2026-Q1", "2026-Q2").error_kind == "too_large"
    finally:
        backend.close()


def test_sync_backend_reports_a_crashing_server_as_an_exception_not_as_missing_data():
    name = register_test_server("evil-crash2", "crash")
    backend = SyncStatsBackend(name, call_timeout_s=2.0)
    try:
        with pytest.raises(RuntimeError, match="unavailable"):
            backend.query(**ARGS)
    finally:
        backend.close()
