"""Drift guard: what the agent's get_series tool and planner accept must match what the live server advertises for get_statistic.

The planner prompt and tool list are fixed code (D-016, D-048); this test connects to the real stdio server and fails when the two sides diverge."""

import asyncio
import inspect
import re

from labourlens.agent.graph import ARGS, REQUIRED, plan_schema
from labourlens.agent.tools import ADJUSTMENTS, Shared, Tools
from labourlens.mcp.client import McpStatsClient, SyncStatsBackend
from labourlens.mcp.server import SCOPE_HI, SCOPE_LO, TOOL_NAME


def enum_values(schema: dict) -> set:
    """All enum members anywhere inside one property schema (a Literal, or an optional Literal expressed as anyOf)."""
    found = set(v for v in schema.get("enum", []) if v is not None)
    for key in ("anyOf", "oneOf", "allOf"):
        for sub in schema.get(key, []):
            found |= enum_values(sub)
    return found


def advertised() -> dict:
    async def go():
        async with McpStatsClient() as c:
            return c.schemas[TOOL_NAME]
    return asyncio.run(go())


def test_planner_and_tool_arguments_match_the_servers_advertised_get_statistic_input_schema():
    schema, props = advertised(), advertised()["properties"]
    assert set(ARGS["get_series"]) == set(props)                                 # same argument names, none missing, none extra
    assert set(REQUIRED["get_series"]) == set(schema["required"])                # same required set
    assert list(inspect.signature(Tools.get_series).parameters)[1:] == list(ARGS["get_series"])  # the tool passes them in the order the planner emits
    assert list(inspect.signature(SyncStatsBackend.query).parameters)[1:] == list(ARGS["get_series"])


def test_planner_source_ids_and_adjustments_are_accepted_by_the_server():
    schema, props = advertised(), advertised()["properties"]
    shared = Shared(world=(None, {}, {}), observations=None)
    planner = plan_schema(shared)["properties"]["calls"]["items"]["properties"]
    planner_sources = {v for v in planner["source_id"]["enum"] if v is not None}
    server_sources = enum_values(props["source_id"])
    assert planner_sources and planner_sources <= server_sources, sorted(planner_sources - server_sources)
    assert {v for v in planner["adjustment"]["enum"] if v is not None} == enum_values(props["adjustment"]) == set(ADJUSTMENTS)
    for period in (SCOPE_LO, SCOPE_HI):
        for name in ("period_from", "period_to"):
            assert re.match(props[name]["pattern"], period), (name, period)
    assert schema.get("additionalProperties") in (None, False) or "additionalProperties" not in schema
