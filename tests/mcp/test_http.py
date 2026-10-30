"""Loopback streamable-HTTP transport: a real server subprocess on a free port with a random per-run token."""

import asyncio
import json
import os
import secrets
import socket
import subprocess
import sys
import time

import httpx
import pytest

from labourlens.mcp import http_server
from labourlens.mcp.client import McpClientError, McpStatsClient, register_http_server
from labourlens.mcp.http_server import MIN_TOKEN_CHARS, TOKEN_ENV, StartupRefused, validate_config
from labourlens.mcp.server import ALL_TOOLS

ARGS = dict(source_id="retrenched_employees", period_from="2026-Q1", period_to="2026-Q2")
INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                                                                       "clientInfo": {"name": "t", "version": "0"}}}
HDRS = {"content-type": "application/json", "accept": "application/json, text/event-stream"}


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start(args: list[str], env_extra: dict) -> subprocess.Popen:
    env = {k: v for k, v in os.environ.items() if k != TOKEN_ENV}
    return subprocess.Popen([sys.executable, "-m", "labourlens.mcp.server", *args], env={**env, **env_extra}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


@pytest.fixture(scope="module")
def server():
    token, port = secrets.token_urlsafe(32), free_port()
    p = start(["--transport", "http", "--host", "127.0.0.1", "--port", str(port)], {TOKEN_ENV: token})
    deadline = time.time() + 60
    while time.time() < deadline:
        if p.poll() is not None:
            raise RuntimeError(f"server exited early: {p.stderr.read()}")
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.5).close()
            break
        except OSError:
            time.sleep(0.3)
    else:
        p.kill()
        raise RuntimeError("server did not start")
    info = {"token": token, "port": port, "url": f"http://127.0.0.1:{port}/mcp", "proc": p}
    yield info
    p.terminate()
    try:
        info["stderr"] = p.communicate(timeout=15)[1]
    except subprocess.TimeoutExpired:
        p.kill()
        info["stderr"] = p.communicate()[1]


def post(server, headers=None, content=None, token="valid"):
    h = dict(HDRS)
    if token == "valid":
        h["authorization"] = f"Bearer {server['token']}"
    elif token:
        h["authorization"] = f"Bearer {token}"
    h.update(headers or {})
    return httpx.post(server["url"], headers=h, content=content if content is not None else json.dumps(INIT), timeout=10)


def client_for(server, monkeypatch, token=None):
    monkeypatch.setenv(TOKEN_ENV, token or server["token"])
    return register_http_server("http-test", server["url"])


def test_http_discovery_and_a_call_succeed(server, monkeypatch):
    name = client_for(server, monkeypatch)

    async def go():
        async with McpStatsClient(name) as c:
            reply = await c.get_statistic(**ARGS)
            cmp = await c.compare_periods(source_id="retrenched_employees", period_a="2026-Q1", period_b="2026-Q2")
            return sorted(c.schemas), reply.rows, cmp.result.difference.value, c.transcript[0]["transport"]
    tools, rows, diff, transport = asyncio.run(go())
    assert tools == sorted(ALL_TOOLS) and len(rows) == 2 and diff == "790" and transport == "http"


def test_missing_and_wrong_token_get_a_bare_401(server):
    for token in (None, "wrong-token-" + secrets.token_hex(16), ""):
        r = post(server, token=token)
        assert r.status_code == 401 and r.content == b"" and r.headers.get("www-authenticate") == "Bearer"
    assert post(server, headers={"authorization": f"Basic {server['token']}"}, token=None).status_code == 401  # wrong scheme
    assert post(server).status_code == 200  # the valid token reaches the MCP handler


def test_wrong_token_fails_the_client_closed(server, monkeypatch):
    name = client_for(server, monkeypatch, token=secrets.token_urlsafe(32))

    async def go():
        async with McpStatsClient(name):
            pass
    with pytest.raises(McpClientError) as e:
        asyncio.run(go())
    assert e.value.kind == "unavailable"


def test_client_requires_the_token_in_its_environment(server, monkeypatch):
    monkeypatch.delenv(TOKEN_ENV, raising=False)
    name = register_http_server("http-notoken", server["url"])

    async def go():
        async with McpStatsClient(name):
            pass
    with pytest.raises(McpClientError) as e:
        asyncio.run(go())
    assert e.value.kind == "not_allowed"


def test_bad_host_and_origin_are_rejected_even_with_a_valid_token(server):
    r = post(server, headers={"host": "evil.example.com"})
    assert r.status_code == 421
    assert post(server, headers={"host": f"localhost:{server['port']}"}).status_code == 200  # the loopback names are accepted
    assert post(server, headers={"origin": "http://evil.example.com"}).status_code == 403


def test_no_cors_headers_and_preflight_is_not_answered(server):
    r = httpx.options(server["url"], headers={"origin": "http://evil.example.com", "access-control-request-method": "POST",
                                                "authorization": f"Bearer {server['token']}"}, timeout=10)
    assert r.status_code >= 400 and not any(k.lower().startswith("access-control-") for k in r.headers)
    assert not any(k.lower().startswith("access-control-") for k in post(server).headers)


def test_oversized_request_body_is_rejected(server):
    r = post(server, content=json.dumps({**INIT, "pad": "x" * 200_000}))
    assert r.status_code == 413


def test_stdio_and_http_return_identical_rows(server, monkeypatch):
    name = client_for(server, monkeypatch)
    queries = [ARGS, dict(source_id="resident_unemployment_rate", period_from="2024-Q1", period_to="2026-Q2", adjustment="not_adjusted"),
               dict(source_id="retrenched_by_occupation", period_from="2026-Q1", period_to="2026-Q2", dimension="professionals, managers, executives and technicians")]

    async def collect(server_name):
        async with McpStatsClient(server_name) as c:
            return [(await c.get_statistic(**q)).rows for q in queries], (await c.latest_value("resident_unemployment_rate")).result.model_dump()
    assert asyncio.run(collect("labourlens-stats")) == asyncio.run(collect(name))


def test_token_never_appears_in_server_logs(server, monkeypatch):
    wrong = "wrong-token-" + secrets.token_hex(16)
    post(server, token=wrong)
    name = client_for(server, monkeypatch)

    async def go():
        async with McpStatsClient(name) as c:
            await c.get_statistic(**ARGS)
    asyncio.run(go())
    server["proc"].terminate()
    err = server["proc"].communicate(timeout=20)[1]
    server["stderr"] = err
    assert server["token"] not in err and wrong not in err and "Authorization" not in err
    assert "serving read-only statistics" in err and "get_statistic ok" in err  # logging worked, and was clean


# ---- startup refusals (separate processes, no listening) ---------------------------------------------------------------------
def test_server_refuses_to_start_without_a_long_enough_token():
    for env in ({}, {TOKEN_ENV: "short"}, {TOKEN_ENV: "x" * (MIN_TOKEN_CHARS - 1)}):
        p = start(["--transport", "http", "--port", str(free_port())], env)
        _, err = p.communicate(timeout=60)
        assert p.returncode == 2 and "refusing to start" in err and TOKEN_ENV in err
        if env.get(TOKEN_ENV):  # the message names the variable, never its value
            assert env[TOKEN_ENV] not in err.replace(TOKEN_ENV, "")


def test_server_refuses_a_non_loopback_host_at_start():
    token = secrets.token_urlsafe(32)
    for host in ("0.0.0.0", "192.0.2.10", "example.com"):
        p = start(["--transport", "http", "--host", host, "--port", str(free_port())], {TOKEN_ENV: token})
        _, err = p.communicate(timeout=60)
        assert p.returncode == 2 and "only loopback" in err and token not in err


def test_allow_nonloopback_flag_warns_instead_of_refusing():
    token = secrets.token_urlsafe(32)
    warnings = validate_config("0.0.0.0", 8765, token, allow_nonloopback=True)
    assert len(warnings) == 1 and "TLS" in warnings[0] and "authentication" in warnings[0]
    assert validate_config("127.0.0.1", 8765, token, allow_nonloopback=False) == [] and validate_config("localhost", 8765, token, False) == []
    assert validate_config("::1", 8765, token, False) == []
    with pytest.raises(StartupRefused):
        validate_config("0.0.0.0", 8765, token, allow_nonloopback=False)
    with pytest.raises(StartupRefused):
        validate_config("127.0.0.1", 0, token, False)
    assert http_server.allowed_hosts("127.0.0.1", 9) == ["127.0.0.1:9", "localhost:9", "[::1]:9"]


@pytest.mark.parametrize("url", ["http://192.0.2.1:8765/mcp", "http://example.com/mcp", "http://localhost.evil.com:8765/mcp", "https://10.0.0.5/mcp",
                                 "http://127.0.0.1.evil.com/mcp", "http://user:pw@127.0.0.1:8765/mcp", "ftp://127.0.0.1/mcp"])
def test_client_refuses_non_loopback_or_odd_urls(url, monkeypatch):
    monkeypatch.setenv(TOKEN_ENV, secrets.token_urlsafe(32))
    name = register_http_server("http-bad", url)
    with pytest.raises(McpClientError) as e:
        McpStatsClient(name)
    assert e.value.kind == "not_allowed"
