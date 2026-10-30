"""MCP client for the statistics server, with the trust-boundary controls the assessment asks for.

Controls (each is exercised by tests/mcp and the threat suite)
- Server allow-listing: only servers registered in ALLOWED_SERVERS can be started; the command is fixed in code.
- Minimal environment: the subprocess gets the SDK's safe default environment only (no OPENAI_API_KEY or other secrets).
- Capability check: server name, server version and the exact tool allow-list are verified after connecting; unexpected
  tools are ignored and reported, a missing tool is an error.
- Argument validation before sending: arguments are checked against the tool's advertised JSON schema.
- Timeouts: connect, per-call (SDK read timeout plus a hard anyio deadline) and a response size cap.
- Response validation: structured content must parse as StatisticResult; anything else is a malformed response, never a
  silent fallback to made-up or direct data.
- Untrusted content: strings are sanitised; rows whose text matches injection heuristics are quarantined and counted.
- Failure taxonomy: invalid_arguments / not_found / too_large (caller can correct) versus timeout, unavailable, malformed,
  oversized (operational: reported as a failure, never as missing evidence).
"""

from __future__ import annotations

import asyncio
import json
import sys
import threading
import time
from dataclasses import dataclass, field

import anyio
import jsonschema
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import MCPError
from pydantic import ValidationError

from labourlens.agent.tools import ToolResult, TransientToolError
from labourlens.mcp.server import SERVER_NAME, SERVER_VERSION, TOOL_NAME, StatisticResult
from labourlens.security.guards import injection_flags, sanitize_text

ALLOWED_SERVERS: dict[str, dict] = {
    "labourlens-stats": {"command": sys.executable, "args": ["-m", "labourlens.mcp.server"], "expected_name": SERVER_NAME,
                         "allowed_versions": {SERVER_VERSION}, "allowed_tools": {TOOL_NAME}},
}
CONNECT_TIMEOUT_S, CALL_TIMEOUT_S, MAX_RESPONSE_BYTES = 20.0, 8.0, 200_000


def register_test_server(name: str, mode: str) -> str:
    """Test/threat-suite only: allow-list the hostile fixture server under `name` in the given mode. It claims the real server's identity
    so that the handshake checks pass and the behaviour AFTER the handshake is what is tested."""
    ALLOWED_SERVERS[name] = {**ALLOWED_SERVERS["labourlens-stats"], "args": ["-m", "labourlens.mcp.evil"], "env": {"LABOURLENS_EVIL": mode}}
    return name



class McpClientError(Exception):
    """kind: timeout | unavailable | malformed | oversized | not_allowed | capability_missing | version_mismatch"""

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


class McpStatsClient:
    def __init__(self, server: str = "labourlens-stats", call_timeout_s: float = CALL_TIMEOUT_S, connect_timeout_s: float = CONNECT_TIMEOUT_S) -> None:
        if server not in ALLOWED_SERVERS:
            raise McpClientError("not_allowed", f"server {server!r} is not on the allow-list")
        self.spec, self.call_timeout_s, self.connect_timeout_s = ALLOWED_SERVERS[server], call_timeout_s, connect_timeout_s
        self.session: ClientSession | None = None
        self.schema: dict | None = None
        self.ignored_tools: list[str] = []
        self.transcript: list[dict] = []  # protocol-level activity for the demo (no secrets: names, sizes, timings)
        self._stack = None

    async def __aenter__(self) -> "McpStatsClient":
        from contextlib import AsyncExitStack

        self._stack = AsyncExitStack()
        try:
            params = StdioServerParameters(command=self.spec["command"], args=self.spec["args"], env=self.spec.get("env"))
            r, w = await self._stack.enter_async_context(stdio_client(params))
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
        except BaseException as e:  # server missing, crashed on start, closed pipe
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
                                "protocol": s.protocol_version})
        if info is None or info.name != self.spec["expected_name"]:
            raise McpClientError("not_allowed", f"unexpected server name {getattr(info, 'name', None)!r}")
        if info.version not in self.spec["allowed_versions"]:
            raise McpClientError("version_mismatch", f"server version {info.version!r} not in {sorted(self.spec['allowed_versions'])}")
        tools = (await s.list_tools()).tools
        names = {t.name for t in tools}
        self.transcript.append({"step": "tools/list", "tools": sorted(names)})
        self.ignored_tools = sorted(names - self.spec["allowed_tools"])
        missing = self.spec["allowed_tools"] - names
        if missing:
            raise McpClientError("capability_missing", f"missing tools {sorted(missing)}")
        self.schema = next(t.input_schema for t in tools if t.name == TOOL_NAME)

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

    async def get_statistic(self, **args) -> StatsReply:
        if self.session is None:
            raise McpClientError("unavailable", "not connected")
        args = {k: v for k, v in args.items() if v is not None}
        try:  # validate before sending: a bad call should not cost a round trip
            jsonschema.validate(args, self.schema)
        except jsonschema.ValidationError as e:
            raise McpClientError("invalid_arguments", e.message[:200]) from e
        t0 = time.perf_counter()
        try:
            with anyio.fail_after(self.call_timeout_s + 1):
                res = await self.session.call_tool(TOOL_NAME, args, read_timeout_seconds=self.call_timeout_s)
        except (TimeoutError, MCPError) as e:
            if isinstance(e, MCPError) and e.code != -32001:
                kind = "unavailable"
            else:
                kind = "timeout"
            self.transcript.append({"step": "tools/call", "tool": TOOL_NAME, "arg_names": sorted(args), "outcome": kind})
            raise McpClientError(kind, TOOL_NAME) from e
        except BaseException as e:  # closed pipe, crashed server
            self.transcript.append({"step": "tools/call", "tool": TOOL_NAME, "arg_names": sorted(args), "outcome": "unavailable"})
            raise McpClientError("unavailable", type(e).__name__) from e
        dt = time.perf_counter() - t0
        raw = json.dumps(res.structured_content if res.structured_content is not None else [c.model_dump() for c in res.content], default=str)
        if len(raw.encode()) > MAX_RESPONSE_BYTES:
            self.transcript.append({"step": "tools/call", "tool": TOOL_NAME, "outcome": "oversized", "bytes": len(raw)})
            raise McpClientError("oversized", f"response of {len(raw)} bytes exceeds {MAX_RESPONSE_BYTES}")
        if res.is_error:
            text = " ".join(getattr(c, "text", "") for c in res.content)
            try:  # the SDK prefixes anticipated ToolError messages with "Error executing tool ...: "
                d = json.loads(text[text.index("{"):])
                kind, msg = d.get("error_kind", "tool_error"), str(d.get("message", ""))
            except (ValueError, AttributeError):
                kind, msg = "tool_error", text
            msg = sanitize_text(msg)[:600]
            self.transcript.append({"step": "tools/call", "tool": TOOL_NAME, "arg_names": sorted(args), "outcome": f"rejected:{kind}", "seconds": round(dt, 3)})
            raise McpClientError(kind if kind in ("invalid_arguments", "not_found", "too_large") else "tool_error", msg)
        try:
            parsed = StatisticResult.model_validate(res.structured_content)
        except (ValidationError, TypeError) as e:
            self.transcript.append({"step": "tools/call", "tool": TOOL_NAME, "outcome": "malformed", "seconds": round(dt, 3)})
            raise McpClientError("malformed", "response does not match the advertised output schema") from e
        rows, quarantined = [], 0
        for row in parsed.rows:
            d = row.model_dump()
            for k, v in d.items():
                if isinstance(v, str):
                    d[k] = sanitize_text(v)
            if any(injection_flags(v) for v in d.values() if isinstance(v, str)):
                quarantined += 1  # a statistic row whose text addresses the model is not trusted evidence
                continue
            rows.append(d)
        self.transcript.append({"step": "tools/call", "tool": TOOL_NAME, "arg_names": sorted(args), "outcome": "ok", "rows": len(rows),
                                "quarantined": quarantined, "bytes": len(raw), "seconds": round(dt, 3)})
        return StatsReply(rows, quarantined, self.ignored_tools, dt, len(raw))


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

    async def _connect(self) -> None:
        c = McpStatsClient(self.server, self.call_timeout_s)
        await c.__aenter__()
        self.client = c

    def close(self) -> None:
        if self.client is not None:
            try:
                self._run(self.client.__aexit__(None, None, None), 10)
            except Exception:  # noqa: BLE001
                pass
            self.client = None
        self.loop.call_soon_threadsafe(self.loop.stop)

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
                    self.client = None  # lost connection: reconnect once
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
