"""MCP client for the LabourLens statistics server, with the trust-boundary controls the assessment asks for.

Controls (each is exercised by tests/mcp and the threat suite)
- Server allow-listing: only servers registered in ALLOWED_SERVERS can be started or contacted. A stdio server's command is fixed in
  code. An http server is a fixed loopback URL; the client refuses any non-loopback host and sends the bearer token (read from the
  environment variable named in the entry) only to that URL.
- Minimal environment: a stdio subprocess gets the SDK's safe default environment only (no OPENAI_API_KEY or other secrets).
- Capability check: server name, server version and the tool allow-list are verified after connecting. Required tools must exist;
  tools outside the allow-list are ignored and reported, never callable.
- Argument validation before sending: arguments are checked against that tool's advertised JSON schema.
- Timeouts: connect, per-call (SDK read timeout plus a hard anyio deadline) and a response size cap.
- Response validation: structured content must parse as the tool's result model; anything else is a malformed response, never a
  silent fallback to made-up or direct data.
- Untrusted content: every string in every result is sanitised and scanned with the injection heuristics. List items that match are
  quarantined and counted; a match anywhere else in the result refuses the whole result.
- Failure taxonomy: invalid_arguments / not_found / too_large (caller can correct) versus timeout, unavailable, malformed,
  oversized, quarantined (operational: reported as a failure, never as missing evidence).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar
from urllib.parse import urlparse

import anyio
import jsonschema
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client
from mcp.shared.exceptions import MCPError
from pydantic import BaseModel, ValidationError

from labourlens.agent.tools import ToolResult, TransientToolError
from labourlens.mcp.http_server import MIN_TOKEN_CHARS, TOKEN_ENV, is_loopback
from labourlens.mcp.models import (RESULT_MODELS, ComparePeriodsResult, DescribeDatasetResult, DimensionValuesResult, LatestValueResult, ListDatasetsResult,
                                   ProvenanceResult, RevisionsResult, SeriesSummaryResult, StatisticResult)
from labourlens.mcp.server import ALL_TOOLS, SERVER_NAME, SERVER_VERSION, TOOL_NAME
from labourlens.security.guards import injection_flags, sanitize_text

_COMMON = {"expected_name": SERVER_NAME, "allowed_versions": {SERVER_VERSION}, "required_tools": {TOOL_NAME}, "allowed_tools": set(ALL_TOOLS)}
ALLOWED_SERVERS: dict[str, dict] = {
    "labourlens-stats": {"transport": "stdio", "command": sys.executable, "args": ["-m", "labourlens.mcp.server"], **_COMMON},
    # Same server over loopback streamable HTTP. Start it yourself (see docs/deploy.md); the token is read from LABOURLENS_MCP_TOKEN.
    "labourlens-stats-http": {"transport": "http", "url": "http://127.0.0.1:8765/mcp", "token_env": TOKEN_ENV, **_COMMON},
}
CONNECT_TIMEOUT_S, CALL_TIMEOUT_S, MAX_RESPONSE_BYTES = 20.0, 8.0, 200_000
CORRECTABLE = ("invalid_arguments", "not_found", "too_large")


def register_test_server(name: str, mode: str) -> str:
    """Test/threat-suite only: allow-list the hostile fixture server under `name` in the given mode. It claims the real server's identity
    so that the handshake checks pass and the behaviour AFTER the handshake is what is tested."""
    ALLOWED_SERVERS[name] = {**ALLOWED_SERVERS["labourlens-stats"], "args": ["-m", "labourlens.mcp.evil"], "env": {"LABOURLENS_EVIL": mode}}
    return name


def register_http_server(name: str, url: str, token_env: str = TOKEN_ENV) -> str:
    """Test/demo only: allow-list an http server at `url` (still subject to the loopback rule, which is checked on connect)."""
    ALLOWED_SERVERS[name] = {**ALLOWED_SERVERS["labourlens-stats-http"], "url": url, "token_env": token_env}
    return name


class McpClientError(Exception):
    """kind: timeout | unavailable | malformed | oversized | quarantined | not_allowed | capability_missing | version_mismatch
    plus the correctable kinds invalid_arguments | not_found | too_large | tool_error"""

    def __init__(self, kind: str, message: str = "") -> None:
        super().__init__(f"{kind}: {message}")
        self.kind, self.message = kind, message


@dataclass
class StatsReply:
    rows: list[dict]
    quarantined: int = 0
    ignored_tools: list[str] = field(default_factory=list)
    seconds: float = 0.0
    bytes: int = 0


T = TypeVar("T", bound=BaseModel)


@dataclass
class ToolReply(Generic[T]):
    """A validated, sanitised tool result. `quarantined` counts list items dropped because their text looked like an instruction."""
    result: T
    quarantined: int = 0
    ignored_tools: list[str] = field(default_factory=list)
    seconds: float = 0.0
    bytes: int = 0


def _sanitize(v: Any) -> Any:
    if isinstance(v, str):
        return sanitize_text(v)
    if isinstance(v, list):
        return [_sanitize(x) for x in v]
    if isinstance(v, dict):
        return {k: _sanitize(x) for k, x in v.items()}
    return v


def _flagged(v: Any) -> bool:
    """True if any string anywhere inside `v` (including dict keys) matches the injection heuristics."""
    if isinstance(v, str):
        return bool(injection_flags(v))
    if isinstance(v, list):
        return any(_flagged(x) for x in v)
    if isinstance(v, dict):
        return any(_flagged(k) or _flagged(x) for k, x in v.items())
    return False


def screen_result(model: BaseModel) -> tuple[dict, int]:
    """Sanitise every string of a result and quarantine suspicious list items. Returns (clean dict, quarantined count).
    Raises McpClientError("quarantined") when instruction-like text sits outside a list, since there is no item to drop."""
    d = _sanitize(model.model_dump())
    quarantined = 0
    for k, v in list(d.items()):
        if isinstance(v, list):
            keep = [x for x in v if not _flagged(x)]
            quarantined += len(v) - len(keep)
            d[k] = keep
    if _flagged({k: v for k, v in d.items() if not isinstance(v, list)}):
        raise McpClientError("quarantined", "a non-list field of the result contains instruction-like text")
    return d, quarantined


def _check_http_url(url: str) -> None:
    u = urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname or u.username or u.password:
        raise McpClientError("not_allowed", "http server URL must be http(s)://host:port/path without credentials")
    if not is_loopback(u.hostname):
        raise McpClientError("not_allowed", f"refusing non-loopback host {u.hostname!r}: the bearer token is only sent to loopback servers")


class McpStatsClient:
    def __init__(self, server: str = "labourlens-stats", call_timeout_s: float = CALL_TIMEOUT_S, connect_timeout_s: float = CONNECT_TIMEOUT_S) -> None:
        if server not in ALLOWED_SERVERS:
            raise McpClientError("not_allowed", f"server {server!r} is not on the allow-list")
        self.spec, self.call_timeout_s, self.connect_timeout_s = ALLOWED_SERVERS[server], call_timeout_s, connect_timeout_s
        if self.spec.get("transport", "stdio") == "http":
            _check_http_url(self.spec["url"])
        self.session: ClientSession | None = None
        self.schemas: dict[str, dict] = {}
        self.ignored_tools: list[str] = []
        self.transcript: list[dict] = []  # protocol-level activity for the demo (no secrets: names, sizes, timings)
        self._stack = None

    @property
    def schema(self) -> dict | None:
        return self.schemas.get(TOOL_NAME)

    async def _open_transport(self):
        if self.spec.get("transport", "stdio") == "http":
            token = os.environ.get(self.spec["token_env"], "")
            if len(token) < MIN_TOKEN_CHARS:
                raise McpClientError("not_allowed", f"environment variable {self.spec['token_env']} is not set to a token of at least {MIN_TOKEN_CHARS} characters")
            http = create_mcp_http_client(headers={"Authorization": f"Bearer {token}"})
            await self._stack.enter_async_context(http)
            return await self._stack.enter_async_context(streamable_http_client(self.spec["url"], http_client=http))
        params = StdioServerParameters(command=self.spec["command"], args=self.spec["args"], env=self.spec.get("env"))
        return await self._stack.enter_async_context(stdio_client(params))

    async def __aenter__(self) -> "McpStatsClient":
        from contextlib import AsyncExitStack

        self._stack = AsyncExitStack()
        try:
            r, w = await self._open_transport()
            self.session = await self._stack.enter_async_context(ClientSession(r, w, read_timeout_seconds=self.connect_timeout_s))
            with anyio.fail_after(self.connect_timeout_s):  # the scope must not span the transport context managers
                await self.session.initialize()
                await self._verify()
        except TimeoutError as e:
            await self._close()
            raise McpClientError("timeout", "connecting to the MCP server") from e
        except McpClientError:
            await self._close()
            raise
        except BaseException as e:  # server missing, crashed on start, closed pipe, HTTP refusal (for example 401)
            await self._close()
            raise McpClientError("unavailable", type(e).__name__) from e
        return self

    async def _close(self) -> None:
        if self._stack is not None:
            try:
                await self._stack.aclose()
            except BaseException:  # noqa: BLE001 - shutting down a broken transport must not raise
                pass
            self._stack = None
        self.session = None

    async def __aexit__(self, *exc) -> None:
        await self._close()

    async def _verify(self) -> None:
        s = self.session
        info = s.server_info
        self.transcript.append({"step": "initialize", "server": getattr(info, "name", None), "version": getattr(info, "version", None),
                                "protocol": s.protocol_version, "transport": self.spec.get("transport", "stdio")})
        if info is None or info.name != self.spec["expected_name"]:
            raise McpClientError("not_allowed", f"unexpected server name {getattr(info, 'name', None)!r}")
        if info.version not in self.spec["allowed_versions"]:
            raise McpClientError("version_mismatch", f"server version {info.version!r} not in {sorted(self.spec['allowed_versions'])}")
        tools = (await s.list_tools()).tools
        names = {t.name for t in tools}
        self.transcript.append({"step": "tools/list", "tools": sorted(names)})
        self.ignored_tools = sorted(names - self.spec["allowed_tools"])
        missing = self.spec["required_tools"] - names
        if missing:
            raise McpClientError("capability_missing", f"missing tools {sorted(missing)}")
        self.schemas = {t.name: t.input_schema for t in tools if t.name in self.spec["allowed_tools"]}

    async def list_resources(self) -> list[str]:
        res = await self.session.list_resources()
        self.transcript.append({"step": "resources/list", "uris": [r.uri for r in res.resources]})
        return [r.uri for r in res.resources]

    async def read_resource(self, uri: str) -> dict:
        t0 = time.perf_counter()
        try:
            with anyio.fail_after(self.call_timeout_s):
                out = await self.session.read_resource(uri)
        except TimeoutError as e:
            raise McpClientError("timeout", f"reading {uri}") from e
        except MCPError as e:
            raise McpClientError("not_found" if e.code == -32602 else "unavailable", f"resource {uri}: code {e.code}") from e
        text = "".join(c.text for c in out.contents if hasattr(c, "text"))
        if len(text.encode()) > MAX_RESPONSE_BYTES:
            raise McpClientError("oversized", f"resource {uri} is {len(text)} characters")
        try:
            doc = json.loads(text)
        except json.JSONDecodeError as e:
            raise McpClientError("malformed", f"resource {uri} is not JSON") from e
        self.transcript.append({"step": "resources/read", "uri": uri, "bytes": len(text), "seconds": round(time.perf_counter() - t0, 3)})
        return doc

    async def call(self, tool: str, **args) -> ToolReply:
        """Call one allow-listed tool and return its validated, sanitised result model."""
        if tool not in self.spec["allowed_tools"]:
            raise McpClientError("not_allowed", f"tool {tool!r} is not on the allow-list")
        if self.session is None:
            raise McpClientError("unavailable", "not connected")
        if tool not in self.schemas:
            raise McpClientError("capability_missing", f"server does not advertise {tool!r}")
        args = {k: v for k, v in args.items() if v is not None}
        try:  # validate before sending: a bad call should not cost a round trip
            jsonschema.validate(args, self.schemas[tool])
        except jsonschema.ValidationError as e:
            raise McpClientError("invalid_arguments", e.message[:200]) from e
        t0 = time.perf_counter()
        try:
            with anyio.fail_after(self.call_timeout_s + 1):
                res = await self.session.call_tool(tool, args, read_timeout_seconds=self.call_timeout_s)
        except (TimeoutError, MCPError) as e:
            if isinstance(e, MCPError) and e.code != -32001:
                kind = "unavailable"
            else:
                kind = "timeout"
            self.transcript.append({"step": "tools/call", "tool": tool, "arg_names": sorted(args), "outcome": kind})
            raise McpClientError(kind, tool) from e
        except BaseException as e:  # closed pipe, crashed server
            self.transcript.append({"step": "tools/call", "tool": tool, "arg_names": sorted(args), "outcome": "unavailable"})
            raise McpClientError("unavailable", type(e).__name__) from e
        dt = time.perf_counter() - t0
        raw = json.dumps(res.structured_content if res.structured_content is not None else [c.model_dump() for c in res.content], default=str)
        if len(raw.encode()) > MAX_RESPONSE_BYTES:
            self.transcript.append({"step": "tools/call", "tool": tool, "outcome": "oversized", "bytes": len(raw)})
            raise McpClientError("oversized", f"response of {len(raw)} bytes exceeds {MAX_RESPONSE_BYTES}")
        if res.is_error:
            text = " ".join(getattr(c, "text", "") for c in res.content)
            try:  # the SDK prefixes anticipated ToolError messages with "Error executing tool ...: "
                d = json.loads(text[text.index("{"):])
                kind, msg = d.get("error_kind", "tool_error"), str(d.get("message", ""))
            except (ValueError, AttributeError):
                kind, msg = "tool_error", text
            msg = sanitize_text(msg)[:600]
            self.transcript.append({"step": "tools/call", "tool": tool, "arg_names": sorted(args), "outcome": f"rejected:{kind}", "seconds": round(dt, 3)})
            raise McpClientError(kind if kind in CORRECTABLE else "tool_error", msg)
        model_cls = RESULT_MODELS[tool]
        try:
            parsed = model_cls.model_validate(res.structured_content)
        except (ValidationError, TypeError) as e:
            self.transcript.append({"step": "tools/call", "tool": tool, "outcome": "malformed", "seconds": round(dt, 3)})
            raise McpClientError("malformed", "response does not match the advertised output schema") from e
        try:
            clean, quarantined = screen_result(parsed)
        except McpClientError:
            self.transcript.append({"step": "tools/call", "tool": tool, "outcome": "quarantined", "seconds": round(dt, 3)})
            raise
        self.transcript.append({"step": "tools/call", "tool": tool, "arg_names": sorted(args), "outcome": "ok", "quarantined": quarantined,
                                "bytes": len(raw), "seconds": round(dt, 3)})
        return ToolReply(model_cls.model_validate(clean), quarantined, self.ignored_tools, dt, len(raw))

    async def get_statistic(self, **args) -> StatsReply:
        r = await self.call(TOOL_NAME, **args)
        rows = [x.model_dump() for x in r.result.rows]
        self.transcript[-1]["rows"] = len(rows)
        return StatsReply(rows, r.quarantined, r.ignored_tools, r.seconds, r.bytes)

    # ---- typed convenience methods: one per tool, same checks as `call` -----------------------------------------------------
    async def list_datasets(self, topic: str | None = None) -> ToolReply[ListDatasetsResult]:
        return await self.call("list_datasets", topic=topic)

    async def describe_dataset(self, source_id: str) -> ToolReply[DescribeDatasetResult]:
        return await self.call("describe_dataset", source_id=source_id)

    async def get_dimension_values(self, source_id: str) -> ToolReply[DimensionValuesResult]:
        return await self.call("get_dimension_values", source_id=source_id)

    async def latest_value(self, source_id: str, dimension: str | None = None, adjustment: str | None = None,
                           indicator_id: str | None = None) -> ToolReply[LatestValueResult]:
        return await self.call("latest_value", source_id=source_id, dimension=dimension, adjustment=adjustment, indicator_id=indicator_id)

    async def compare_periods(self, source_id: str, period_a: str, period_b: str, dimension: str | None = None, adjustment: str | None = None,
                              indicator_id: str | None = None) -> ToolReply[ComparePeriodsResult]:
        return await self.call("compare_periods", source_id=source_id, period_a=period_a, period_b=period_b, dimension=dimension,
                               adjustment=adjustment, indicator_id=indicator_id)

    async def series_summary(self, source_id: str, period_from: str, period_to: str, dimension: str | None = None, adjustment: str | None = None,
                             indicator_id: str | None = None) -> ToolReply[SeriesSummaryResult]:
        return await self.call("series_summary", source_id=source_id, period_from=period_from, period_to=period_to, dimension=dimension,
                               adjustment=adjustment, indicator_id=indicator_id)

    async def get_revisions(self, source_id: str | None = None, period: str | None = None) -> ToolReply[RevisionsResult]:
        return await self.call("get_revisions", source_id=source_id, period=period)

    async def get_provenance(self, observation_id: str) -> ToolReply[ProvenanceResult]:
        return await self.call("get_provenance", observation_id=observation_id)


class SyncStatsBackend:
    """Same contract as StatsData.query, backed by a persistent MCP session on a private event-loop thread.

    Plugged into Shared.stats_backend so the agent's get_series goes through the MCP protocol. Reconnects once after a lost
    connection; a second failure is an operational failure."""

    def __init__(self, server: str = "labourlens-stats", call_timeout_s: float = CALL_TIMEOUT_S) -> None:
        self.server, self.call_timeout_s = server, call_timeout_s
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True, name="mcp-client")
        self.thread.start()
        self.client: McpStatsClient | None = None
        self.calls: list[dict] = []

    def _run(self, coro, timeout: float):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)

    async def _serve(self, ready: "asyncio.Future") -> None:
        """Owns the MCP connection for its whole life in ONE task: anyio cancel scopes must be entered and exited by the same task."""
        self._stop = asyncio.Event()
        try:
            async with McpStatsClient(self.server, self.call_timeout_s) as c:
                self.client = c
                ready.set_result(None)
                await self._stop.wait()
        except BaseException as e:  # noqa: BLE001
            if not ready.done():
                ready.set_exception(e)
        finally:
            self.client = None

    async def _connect(self) -> None:
        ready = self.loop.create_future()
        self._task = self.loop.create_task(self._serve(ready))
        await asyncio.wait_for(ready, CONNECT_TIMEOUT_S + 5)

    def close(self) -> None:
        task = getattr(self, "_task", None)
        if task is not None:
            try:
                self.loop.call_soon_threadsafe(self._stop.set)
                self._run(asyncio.wait_for(asyncio.shield(task), 10), 12)
            except Exception:  # noqa: BLE001
                pass
        self.loop.call_soon_threadsafe(self.loop.stop)

    def _drop(self) -> None:
        task = getattr(self, "_task", None)
        if task is not None:
            self.loop.call_soon_threadsafe(self._stop.set)
        self.client = None

    def query(self, source_id, period_from, period_to, dimension=None, adjustment=None, indicator_id=None):
        args = dict(source_id=source_id, period_from=period_from, period_to=period_to, dimension=dimension, adjustment=adjustment, indicator_id=indicator_id)
        t0 = time.perf_counter()
        for attempt in range(2):
            try:
                if self.client is None:
                    self._run(self._connect(), CONNECT_TIMEOUT_S + 5)
                reply = self._run(self.client.get_statistic(**args), self.call_timeout_s + 5)
                self.calls.append({"ms": round((time.perf_counter() - t0) * 1000, 1), "ok": True, "attempt": attempt})
                return reply.rows, None
            except McpClientError as e:
                self.calls.append({"ms": round((time.perf_counter() - t0) * 1000, 1), "ok": False, "kind": e.kind, "attempt": attempt})
                if e.kind in ("invalid_arguments", "not_found", "too_large"):
                    return None, ToolResult(False, message=e.message or e.kind, error_kind=e.kind)
                if e.kind == "unavailable" and attempt == 0:
                    self._drop()  # lost connection: reconnect once
                    continue
                if e.kind == "timeout" and attempt == 0:
                    raise TransientToolError(e.kind) from e
                raise RuntimeError(f"mcp {e.kind}") from e
            except (TimeoutError, FutureTimeoutError) as e:
                raise TransientToolError("timeout") from e
        raise RuntimeError("mcp unavailable")


try:  # concurrent.futures.TimeoutError is an alias of TimeoutError on Python 3.11+, kept explicit for clarity
    from concurrent.futures import TimeoutError as FutureTimeoutError
except ImportError:  # pragma: no cover
    FutureTimeoutError = TimeoutError
