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
import collections
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

from labourlens.agent.tools import CALLER_SESSION, ToolResult, TransientToolError
from labourlens.mcp.http_server import MIN_TOKEN_CHARS, TOKEN_ENV, is_loopback
from labourlens.mcp.models import (AGENT_RESULT_MODELS, RESULT_MODELS, ComparePeriodsResult, DescribeDatasetResult, DimensionValuesResult, LatestValueResult,
                                   ListDatasetsResult, ProvenanceResult, RevisionsResult, SeriesSummaryResult)
from labourlens.mcp.server import AGENT_TOOLS, ALL_TOOLS, SERVER_NAME, SERVER_VERSION, SOURCE_IDS, TOOL_NAME
from labourlens.security.guards import injection_flags, sanitize_text

_COMMON = {"expected_name": SERVER_NAME, "allowed_versions": {SERVER_VERSION}, "required_tools": {TOOL_NAME}, "allowed_tools": set(ALL_TOOLS)}
ALLOWED_SERVERS: dict[str, dict] = {
    "labourlens-stats": {"transport": "stdio", "command": sys.executable, "args": ["-m", "labourlens.mcp.server"], **_COMMON},
    # Same server over loopback streamable HTTP. Start it yourself (see docs/deploy.md); the token is read from LABOURLENS_MCP_TOKEN.
    "labourlens-stats-http": {"transport": "http", "url": "http://127.0.0.1:8765/mcp", "token_env": TOKEN_ENV, **_COMMON},
    # The live app's server (D-066): the same server started with --agent-tools, so the agent's three tools all run over MCP. It loads the
    # report corpus (a few seconds), hence the longer connect timeout, and it serves report text, which the resource check must allow.
    "labourlens-stats-agent": {"transport": "stdio", "command": sys.executable, "args": ["-m", "labourlens.mcp.server", "--agent-tools"], **_COMMON,
                               "required_tools": {TOOL_NAME, *AGENT_TOOLS}, "allowed_tools": set(ALL_TOOLS) | set(AGENT_TOOLS),
                               "connect_timeout_s": 60.0, "serves_report_text": True},
}
CONNECT_TIMEOUT_S, CALL_TIMEOUT_S, MAX_RESPONSE_BYTES = 20.0, 8.0, 200_000
RECENT_CALLS = 20
CORRECTABLE = ("invalid_arguments", "not_found", "too_large")
PROMPTS = {"compare_quarters": {"type": "object", "additionalProperties": False, "required": ["source_id", "quarter_a", "quarter_b"],
                                 "properties": {"source_id": {"enum": list(SOURCE_IDS)}, "quarter_a": {"type": "string", "pattern": r"^\d{4}-Q[1-4]$"},
                                                "quarter_b": {"type": "string", "pattern": r"^\d{4}-Q[1-4]$"}}}}  # prompt allow-list: name -> argument schema
# CALLER_SESSION (defined in agent.tools) tags every call recorded while a visitor's request is running, so the workbench shows a visitor only their own calls.


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


def _resource_schema(uri: str, serves_text: bool = False) -> dict:
    def entry(fields, extra):
        props = {k: {"type": "string"} for k in fields}
        props.update({k: {"type": ["string", "null"]} for k in ("publisher", "canonical_url")})
        props.update(extra)
        return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}

    dataset = entry(("source_id", "title", "licence"), {
        "periods_in_scope": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 2},
        "series": {"type": "array", "items": {"type": "string"}}})
    document = entry(("source_id", "title"), {
        **{k: {"type": ["string", "null"]} for k in ("publication_date", "release_stage", "rights_status")},
        "text_served_by_this_server": {"type": "boolean"} if serves_text else {"const": False}})
    props = {"trust": {"const": "untrusted_data"}}
    if uri == "labourlens://sources":
        props.update(note={"type": "string"}, datasets={"type": "array", "items": dataset},
                     documents={"type": "array", "items": document})
    elif uri.startswith("labourlens://source/") and uri.removeprefix("labourlens://source/"):
        props["entry"] = {"oneOf": [dataset, document]}
    else:
        raise McpClientError("not_allowed", "unknown resource URI")
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def _check_http_url(url: str) -> None:
    u = urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname or u.username or u.password:
        raise McpClientError("not_allowed", "http server URL must be http(s)://host:port/path without credentials")
    if not is_loopback(u.hostname):
        raise McpClientError("not_allowed", f"refusing non-loopback host {u.hostname!r}: the bearer token is only sent to loopback servers")


def _error_payload(res) -> dict | None:
    """The {error_kind, message} object of a failed tool result. Prefers structuredContent; otherwise looks for a JSON object with an
    `error_kind` inside the text blocks (the SDK wraps a ToolError message as "Error executing tool X: <message>"), without relying on a prefix."""
    sc = getattr(res, "structured_content", None)
    if isinstance(sc, dict) and isinstance(sc.get("error_kind"), str):
        return sc
    decoder = json.JSONDecoder()
    for block in getattr(res, "content", None) or []:
        text = getattr(block, "text", None)
        if not isinstance(text, str):
            continue
        text = text[:20_000]
        start = text.find("{")
        for _ in range(20):
            if start < 0:
                break
            try:
                obj, _end = decoder.raw_decode(text, start)
            except ValueError:
                obj = None
            if isinstance(obj, dict) and isinstance(obj.get("error_kind"), str):
                return obj
            start = text.find("{", start + 1)
    return None


class McpStatsClient:
    def __init__(self, server: str = "labourlens-stats", call_timeout_s: float = CALL_TIMEOUT_S, connect_timeout_s: float | None = None) -> None:
        if server not in ALLOWED_SERVERS:
            raise McpClientError("not_allowed", f"server {server!r} is not on the allow-list")
        self.spec, self.call_timeout_s = ALLOWED_SERVERS[server], call_timeout_s
        self.connect_timeout_s = connect_timeout_s if connect_timeout_s is not None else self.spec.get("connect_timeout_s", CONNECT_TIMEOUT_S)
        if self.spec.get("transport", "stdio") == "http":
            _check_http_url(self.spec["url"])
        self.session: ClientSession | None = None
        self.protocol_version: str | None = None  # the version the server and client actually negotiated
        self.capabilities: dict = {}  # server capabilities declared at initialize (empty = none declared)
        self.output_schemas: dict[str, dict] = {}
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
        caps = s.server_capabilities
        self.protocol_version = str(s.protocol_version) if s.protocol_version else None
        self.capabilities = caps.model_dump(exclude_none=True, mode="json") if caps is not None else {}
        self.transcript.append({"step": "initialize", "server": getattr(info, "name", None), "version": getattr(info, "version", None),
                                "protocol": self.protocol_version, "transport": self.spec.get("transport", "stdio"), "capabilities": sorted(self.capabilities)})
        if info is None or info.name != self.spec["expected_name"]:
            raise McpClientError("not_allowed", f"unexpected server name {getattr(info, 'name', None)!r}")
        if info.version not in self.spec["allowed_versions"]:
            raise McpClientError("version_mismatch", f"server version {info.version!r} not in {sorted(self.spec['allowed_versions'])}")
        if "tools" not in self.capabilities:
            raise McpClientError("capability_missing", "server did not declare the tools capability")
        tools = (await s.list_tools()).tools
        names = {t.name for t in tools}
        self.transcript.append({"step": "tools/list", "tools": sorted(names)})
        self.ignored_tools = sorted(names - self.spec["allowed_tools"])
        missing = self.spec["required_tools"] - names
        if missing:
            raise McpClientError("capability_missing", f"missing tools {sorted(missing)}")
        self.schemas = {t.name: t.input_schema for t in tools if t.name in self.spec["allowed_tools"]}
        self.output_schemas = {t.name: t.output_schema for t in tools if t.name in self.spec["allowed_tools"] and t.output_schema}

    def has_capability(self, name: str) -> bool:
        return name in self.capabilities

    def _require(self, capability: str) -> None:
        """Only use a server feature the server declared at initialize."""
        if self.session is None:
            raise McpClientError("unavailable", "not connected")
        if not self.has_capability(capability):
            raise McpClientError("capability_missing", f"server did not declare the {capability} capability")

    async def list_resources(self) -> list[str]:
        self._require("resources")
        res = await self.session.list_resources()
        self.transcript.append({"step": "resources/list", "uris": [r.uri for r in res.resources]})
        return [r.uri for r in res.resources]

    async def get_prompt(self, name: str, **args) -> dict:
        """Fetch one allow-listed prompt template ('prompts/get'). Arguments are validated before sending; the returned text is
        sanitised, size-capped and refused when it looks like an instruction aimed at the model beyond the template. The host decides whether to use it."""
        self._require("prompts")
        if name not in PROMPTS:
            raise McpClientError("not_allowed", f"prompt {name!r} is not on the allow-list")
        try:
            jsonschema.validate(args, PROMPTS[name])
        except jsonschema.ValidationError as e:
            raise McpClientError("invalid_arguments", e.message[:200]) from e
        try:
            with anyio.fail_after(self.call_timeout_s):
                out = await self.session.get_prompt(name, args)
        except TimeoutError as e:
            raise McpClientError("timeout", f"prompt {name}") from e
        except MCPError as e:
            raise McpClientError("invalid_arguments" if e.code == -32602 else "unavailable", f"prompt {name}: code {e.code}") from e
        except Exception as e:
            raise McpClientError("unavailable", f"getting prompt: {type(e).__name__}") from e
        texts = [getattr(m.content, "text", None) for m in getattr(out, "messages", [])]
        if not texts or any(not isinstance(t, str) for t in texts):
            raise McpClientError("malformed", "prompt must contain text messages")
        text = sanitize_text("\n".join(texts))
        if len(text.encode()) > MAX_RESPONSE_BYTES:
            raise McpClientError("oversized", f"prompt is {len(text)} characters")
        if injection_flags(text):
            raise McpClientError("quarantined", "prompt text contains instruction-like text")
        self.transcript.append({"step": "prompts/get", "name": name, "arg_names": sorted(args), "bytes": len(text.encode())})
        return {"name": name, "text": text}

    async def read_resource(self, uri: str) -> dict:
        schema = _resource_schema(uri, bool(self.spec.get("serves_report_text")))
        self._require("resources")
        t0 = time.perf_counter()
        try:
            with anyio.fail_after(self.call_timeout_s):
                out = await self.session.read_resource(uri)
        except TimeoutError as e:
            raise McpClientError("timeout", f"reading {uri}") from e
        except MCPError as e:
            raise McpClientError("not_found" if e.code == -32602 else "unavailable", f"resource {uri}: code {e.code}") from e
        except Exception as e:
            raise McpClientError("unavailable", f"reading resource: {type(e).__name__}") from e
        if len(json.dumps(out.model_dump(), default=str).encode()) > MAX_RESPONSE_BYTES:
            raise McpClientError("oversized", "resource response exceeds size cap")
        if not out.contents or any(not hasattr(c, "text") for c in out.contents):
            raise McpClientError("malformed", "resource must contain JSON text")
        text = "".join(c.text for c in out.contents if hasattr(c, "text"))
        if len(text.encode()) > MAX_RESPONSE_BYTES:
            raise McpClientError("oversized", f"resource {uri} is {len(text)} characters")
        try:
            doc = json.loads(text)
        except json.JSONDecodeError as e:
            raise McpClientError("malformed", f"resource {uri} is not JSON") from e
        try:
            jsonschema.validate(doc, schema)
        except jsonschema.ValidationError as e:
            raise McpClientError("malformed", "resource shape does not match its schema") from e
        clean = _sanitize(doc)
        quarantined = 0
        for key, value in list(clean.items()):
            if isinstance(value, list):
                clean[key] = [item for item in value if not _flagged(item)]
                quarantined += len(value) - len(clean[key])
        if _flagged(clean):
            raise McpClientError("quarantined", "resource contains instruction-like text outside a list")
        self.transcript.append({"step": "resources/read", "uri": uri, "bytes": len(text.encode()),
                                "seconds": round(time.perf_counter() - t0, 3), "quarantined": quarantined})
        return clean

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
        except RuntimeError as e:
            if "structured content" not in str(e):  # the SDK itself checks structuredContent against the tool's advertised outputSchema and raises this
                self.transcript.append({"step": "tools/call", "tool": tool, "arg_names": sorted(args), "outcome": "unavailable"})
                raise McpClientError("unavailable", type(e).__name__) from e
            self.transcript.append({"step": "tools/call", "tool": tool, "outcome": "malformed", "seconds": round(time.perf_counter() - t0, 3)})
            raise McpClientError("malformed", "response does not match the advertised output schema") from e
        except BaseException as e:  # closed pipe, crashed server
            self.transcript.append({"step": "tools/call", "tool": tool, "arg_names": sorted(args), "outcome": "unavailable"})
            raise McpClientError("unavailable", type(e).__name__) from e
        dt = time.perf_counter() - t0
        raw = json.dumps(res.structured_content if res.structured_content is not None else [c.model_dump() for c in res.content], default=str)
        if len(raw.encode()) > MAX_RESPONSE_BYTES:
            self.transcript.append({"step": "tools/call", "tool": tool, "outcome": "oversized", "bytes": len(raw)})
            raise McpClientError("oversized", f"response of {len(raw)} bytes exceeds {MAX_RESPONSE_BYTES}")
        if res.is_error:
            d = _error_payload(res) or {}
            kind = d.get("error_kind") if isinstance(d.get("error_kind"), str) else "tool_error"
            msg = d.get("message") if "message" in d else " ".join(getattr(c, "text", "") or "" for c in res.content)
            msg = sanitize_text(str(msg))[:600]
            self.transcript.append({"step": "tools/call", "tool": tool, "arg_names": sorted(args), "outcome": f"rejected:{kind}", "seconds": round(dt, 3)})
            raise McpClientError(kind if kind in CORRECTABLE else "tool_error", msg)
        model_cls = RESULT_MODELS.get(tool) or AGENT_RESULT_MODELS[tool]
        out_schema = self.output_schemas.get(tool)
        try:
            if out_schema is not None:  # the server's own advertised contract, then the client's typed model
                jsonschema.validate(res.structured_content, out_schema)
            parsed = model_cls.model_validate(res.structured_content)
        except (ValidationError, TypeError, jsonschema.ValidationError, jsonschema.SchemaError) as e:
            self.transcript.append({"step": "tools/call", "tool": tool, "outcome": "malformed", "seconds": round(dt, 3)})
            raise McpClientError("malformed", "response does not match the advertised output schema or the client's model") from e
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


class _Rows(list):
    """Rows of one statistics reply plus the number of rows the client quarantined, so the agent can report an
    operational/security event instead of 'the dataset has no row'. A plain list everywhere else."""

    def __init__(self, rows, quarantined: int = 0) -> None:
        super().__init__(rows)
        self.quarantined = int(quarantined or 0)


class SyncStatsBackend:
    """Same contract as StatsData.query, backed by a persistent MCP session on a private event-loop thread.

    Plugged into Shared.stats_backend so the agent's get_series goes through the MCP protocol. Reconnects once after a lost
    connection; a second failure is an operational failure."""

    def __init__(self, server: str = "labourlens-stats", call_timeout_s: float = CALL_TIMEOUT_S) -> None:
        self.server, self.call_timeout_s = server, call_timeout_s
        self.connect_timeout_s = ALLOWED_SERVERS[server].get("connect_timeout_s", CONNECT_TIMEOUT_S) if server in ALLOWED_SERVERS else CONNECT_TIMEOUT_S
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True, name="mcp-client")
        self.thread.start()
        self.client: McpStatsClient | None = None
        self.calls: collections.deque[dict] = collections.deque(maxlen=RECENT_CALLS)  # bounded: the newest RECENT_CALLS lookups
        self._described: dict | None = None
        self._calls_lock = threading.Lock()
        self._connect_lock = asyncio.Lock()  # used only on the private event loop
        self._task: asyncio.Task | None = None
        self._stop: asyncio.Event | None = None
        self._closed = False

    def _run(self, coro, timeout: float):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)

    async def _serve(self, ready: "asyncio.Future", stop: asyncio.Event) -> None:
        """Own the connection and its anyio cancel scopes in one task."""
        c = None
        try:
            async with McpStatsClient(self.server, self.call_timeout_s) as c:
                self.client = c
                if not ready.done():
                    ready.set_result(c)
                await stop.wait()
        except BaseException as e:  # noqa: BLE001
            if not ready.done():
                ready.set_exception(e)
        finally:
            if self.client is c:
                self.client = None

    async def _stop_session(self) -> None:
        if self._task is not None:
            self._stop.set()
            await self._task
            self._task = None
            self._stop = None

    async def _connect(self) -> McpStatsClient:
        async with self._connect_lock:
            if self._closed:
                raise McpClientError("unavailable", TOOL_NAME)
            if self.client is not None:
                return self.client
            await self._stop_session()
            ready = self.loop.create_future()
            self._stop = asyncio.Event()
            self._task = self.loop.create_task(self._serve(ready, self._stop))
            try:
                return await asyncio.wait_for(ready, self.connect_timeout_s)
            except BaseException:
                self._task.cancel()
                await self._stop_session()
                raise

    async def _disconnect(self, expected=None, closing: bool = False) -> None:
        async with self._connect_lock:
            if closing:
                self._closed = True
            if expected is not None and self.client is not expected:
                return
            await self._stop_session()

    def close(self) -> None:
        try:
            self._run(self._disconnect(closing=True), 12)
        finally:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(timeout=12)

    def _drop(self, expected=None) -> None:
        self._run(self._disconnect(expected), self.connect_timeout_s + 5)

    def _record(self, tool: str, args: dict, t0: float, ok: bool, attempt: int, quarantined: int = 0, kind: str | None = None) -> None:
        entry = {"tool": tool, "arguments": _loggable(args), "ms": round((time.perf_counter() - t0) * 1000, 1), "ok": ok,
                 "attempt": attempt, "quarantined": quarantined}
        if kind:
            entry["kind"] = kind
        caller = CALLER_SESSION.get()
        if caller:
            entry["session"] = caller  # internal tag for per-visitor filtering; never returned by the web API
        with self._calls_lock:
            self.calls.append(entry)

    def call_tool(self, tool: str, **args) -> ToolReply:
        """Run one allow-listed tool call through the same client checks as the agent path (validation, size cap, quarantine).
        Same reconnect-once rule as `query`; raises McpClientError for a rejected or failed call."""
        t0 = time.perf_counter()
        for attempt in range(2):
            c = None
            try:
                c = self._run(self._connect(), self.connect_timeout_s + 5)
                reply = self._run(c.call(tool, **args), self.call_timeout_s + 5)
                self._record(tool, args, t0, True, attempt, reply.quarantined)
                return reply
            except McpClientError as e:
                self._record(tool, args, t0, False, attempt, kind=e.kind)
                if e.kind == "unavailable" and attempt == 0:
                    if c is not None:
                        self._drop(c)
                    continue
                raise
            except (TimeoutError, FutureTimeoutError) as e:
                self._record(tool, args, t0, False, attempt, kind="timeout")
                raise McpClientError("timeout", tool) from e
        raise McpClientError("unavailable", tool)

    def describe(self) -> dict:
        """What the connected server offers: identity, tools (with annotations and trimmed input schemas), resources, templates, prompts.
        Discovered once through the live session and cached; raises McpClientError / TimeoutError when not reachable."""
        if self._described is not None:
            return self._described
        c = self._run(self._connect(), self.connect_timeout_s + 5)
        self._described = self._run(self._discover(c), self.call_timeout_s + 5)
        return self._described

    @staticmethod
    async def _discover(c: "McpStatsClient") -> dict:
        s = c.session
        info = s.server_info
        tools = (await s.list_tools()).tools
        resources = (await s.list_resources()).resources if c.has_capability("resources") else []
        templates = (await s.list_resource_templates()).resource_templates if c.has_capability("resources") else []
        prompts = (await s.list_prompts()).prompts if c.has_capability("prompts") else []
        return {
            "server": {"name": getattr(info, "name", None), "version": getattr(info, "version", None), "protocol_version": c.protocol_version,
                       "capabilities": sorted(c.capabilities), "transport": c.spec.get("transport", "stdio")},
            "tools": [{"name": t.name, "title": getattr(t.annotations, "title", None) or getattr(t, "title", None) or t.name,
                       "description": sanitize_text(t.description or "")[:600], "read_only": bool(getattr(t.annotations, "read_only_hint", False)),
                       "in_allow_list": t.name in c.spec["allowed_tools"], "input_schema": _trim_schema(t.input_schema)} for t in tools],
            "resources": [{"uri": str(r.uri), "name": r.name, "description": sanitize_text(r.description or "")[:400]} for r in resources]
                         + [{"uri": str(r.uri_template), "name": r.name, "description": sanitize_text(r.description or "")[:400]} for r in templates],
            "prompts": [{"name": p.name, "description": sanitize_text(p.description or "")[:400]} for p in prompts],
        }

    def _guarded(self, tool: str, args: dict, call):
        """One tool call with the agent's failure rules. `call(client)` builds the coroutine. Returns (reply, None), or (None, ToolResult) for a
        problem the caller can correct (invalid_arguments, not_found, too_large). A lost connection is retried once on a fresh session; a
        first timeout raises TransientToolError (the graph retries the tool once); anything else raises RuntimeError, which the graph reports
        as an operational failure, never as missing evidence. There is no fallback to the in-process tools: it would hide the failure."""
        t0 = time.perf_counter()
        for attempt in range(2):
            c = None
            try:
                c = self._run(self._connect(), self.connect_timeout_s + 5)
                reply = self._run(call(c), self.call_timeout_s + 5)
                self._record(tool, args, t0, True, attempt, reply.quarantined)
                return reply, None
            except McpClientError as e:
                self._record(tool, args, t0, False, attempt, kind=e.kind)
                if e.kind in ("invalid_arguments", "not_found", "too_large"):
                    return None, ToolResult(False, message=e.message or e.kind, error_kind=e.kind)
                if e.kind == "unavailable" and attempt == 0:
                    if c is not None:
                        self._drop(c)  # only drop the session this call used
                    continue
                if e.kind == "timeout" and attempt == 0:
                    raise TransientToolError(e.kind) from e
                raise RuntimeError(f"mcp {e.kind}") from e
            except (TimeoutError, FutureTimeoutError) as e:
                raise TransientToolError("timeout") from e
        raise RuntimeError("mcp unavailable")

    def invoke(self, tool: str, **args):
        """An agent tool on the MCP server (search_reports, calculate_change, calculate_from_text_values): (ToolReply, None) or (None, ToolResult)."""
        return self._guarded(tool, args, lambda c: c.call(tool, **args))

    def query(self, source_id, period_from, period_to, dimension=None, adjustment=None, indicator_id=None):
        args = dict(source_id=source_id, period_from=period_from, period_to=period_to, dimension=dimension, adjustment=adjustment, indicator_id=indicator_id)
        reply, err = self._guarded(TOOL_NAME, args, lambda c: c.get_statistic(**args))
        return (None, err) if err is not None else (_Rows(reply.rows, reply.quarantined), None)


def _loggable(args: dict) -> dict:
    """Arguments as the visitor's call log shows them: no None values, no embedding vector (16 KB of base64), long strings cut."""
    out = {}
    for k, v in args.items():
        if v is None:
            continue
        out[k] = "[omitted]" if k == "query_vector_b64" else (v[:300] + "…" if isinstance(v, str) and len(v) > 300 else v)
    return out


def _trim_schema(schema: dict | None) -> dict:
    """Only what a reader needs: property name -> type, enum (capped), pattern, description, plus which are required."""
    out = {}
    for name, prop in ((schema or {}).get("properties") or {}).items():
        variants = [prop] + list(prop.get("anyOf") or [])
        types = sorted({v.get("type") for v in variants if isinstance(v.get("type"), str) and v.get("type") != "null"})
        enum = next((v["enum"] for v in variants if isinstance(v.get("enum"), list)), None)
        entry = {"type": " or ".join(types) or "any"}
        if enum:
            entry["enum"] = [str(x) for x in enum[:12]] + (["..."] if len(enum) > 12 else [])
            entry["enum_count"] = len(enum)
        for k in ("pattern", "description"):
            v = next((x[k] for x in variants if isinstance(x.get(k), str)), None)
            if v:
                entry[k] = sanitize_text(v)[:300]
        out[name] = entry
    return {"properties": out, "required": [r for r in (schema or {}).get("required", []) if isinstance(r, str)]}


try:  # concurrent.futures.TimeoutError is an alias of TimeoutError on Python 3.11+, kept explicit for clarity
    from concurrent.futures import TimeoutError as FutureTimeoutError
except ImportError:  # pragma: no cover
    FutureTimeoutError = TimeoutError
