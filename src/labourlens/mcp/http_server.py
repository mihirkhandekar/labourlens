"""Loopback streamable-HTTP transport for the LabourLens MCP server, protected by a bearer token.

Start: LABOURLENS_MCP_TOKEN=<24+ chars> uv run python -m labourlens.mcp.server --transport http --host 127.0.0.1 --port 8765

Controls (each exercised in tests/mcp/test_http.py)
- The token comes from the environment only, must be at least 24 characters, and the server refuses to start without it.
- Constant-time comparison (hmac.compare_digest); a missing or wrong token gets a bare 401 with no detail and no body.
  The auth check is the outermost layer, so an unauthenticated caller reaches neither the MCP code nor the Host check.
- Loopback only: a non-loopback --host is refused unless --allow-nonloopback is given, which prints a warning that TLS and a real
  authentication layer are then required (this server provides neither; see docs/deploy.md).
- Host and Origin validation (DNS-rebinding protection) with the SDK's TransportSecuritySettings: only the bound address and
  `localhost` on the bound port are accepted as Host; any browser Origin is rejected. No CORS headers are ever sent.
- Request bodies are capped at 64 KiB (the SDK default is 4 MiB; our requests are a few hundred bytes).
- The uvicorn access log is off (it would record paths and peer addresses for no benefit) and error logs pass through the redaction
  filter. The token is never logged: it is not in any log call, and redaction replaces it by value should it ever appear.
- The server is read-only and has no CORS, OAuth, or TLS: OAuth and TLS termination are NOT built (documented gap).
"""

from __future__ import annotations

import hmac
import ipaddress
import os
import sys

from starlette.types import ASGIApp, Receive, Scope, Send

TOKEN_ENV = "LABOURLENS_MCP_TOKEN"
MIN_TOKEN_CHARS = 24
MAX_BODY_BYTES = 64 * 1024
MCP_PATH = "/mcp"


class StartupRefused(Exception):
    """The configuration is unsafe; the server must not start."""


def is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def validate_config(host: str, port: int, token: str | None, allow_nonloopback: bool) -> list[str]:
    """Raise StartupRefused for an unsafe configuration; return warnings for a risky but explicitly allowed one."""
    if not token or len(token) < MIN_TOKEN_CHARS:
        raise StartupRefused(f"{TOKEN_ENV} must be set to a random secret of at least {MIN_TOKEN_CHARS} characters")
    if not 1 <= port <= 65535:
        raise StartupRefused("port must be 1 to 65535")
    warnings = []
    if not is_loopback(host):
        if not allow_nonloopback:
            raise StartupRefused(f"refusing to bind {host!r}: only loopback addresses are allowed (use --allow-nonloopback to override)")
        warnings.append(f"WARNING: binding {host!r}, which is not loopback. This server has no TLS and only a static bearer token; "
                        "put it behind a TLS-terminating proxy with a real authentication layer. See docs/deploy.md.")
    return warnings


def allowed_hosts(host: str, port: int) -> list[str]:
    if is_loopback(host):
        return [f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"]
    return [f"{host}:{port}"]


class BearerTokenMiddleware:
    """Pure ASGI middleware: every HTTP request must carry `Authorization: Bearer <token>`; anything else gets a bare 401."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        self.app, self._token = app, token.encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await self.app(scope, receive, send)
            return
        if scope["type"] != "http":  # no websocket or other protocol is served
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1008})
            return
        supplied = b""
        for k, v in scope["headers"]:
            if k == b"authorization":
                scheme, _, value = v.partition(b" ")
                if scheme.lower() == b"bearer":
                    supplied = value.strip()
                break
        if not hmac.compare_digest(supplied, self._token):  # constant-time compare; only the token length can leak through timing
            await send({"type": "http.response.start", "status": 401, "headers": [(b"www-authenticate", b"Bearer"), (b"content-length", b"0")]})
            await send({"type": "http.response.body", "body": b""})
            return
        await self.app(scope, receive, send)


def build_app(mcp, host: str, port: int, token: str) -> ASGIApp:
    from mcp.server.transport_security import TransportSecuritySettings

    inner = mcp.streamable_http_app(
        streamable_http_path=MCP_PATH, host=host, max_request_body_size=MAX_BODY_BYTES,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True, allowed_hosts=allowed_hosts(host, port), allowed_origins=[]))
    return BearerTokenMiddleware(inner, token)


def serve(mcp, host: str, port: int, *, allow_nonloopback: bool = False) -> None:
    import uvicorn

    try:
        warnings = validate_config(host, port, os.environ.get(TOKEN_ENV), allow_nonloopback)
    except StartupRefused as e:
        print(f"labourlens-mcp: refusing to start: {e}", file=sys.stderr)
        raise SystemExit(2) from None
    for w in warnings:
        print(f"labourlens-mcp: {w}", file=sys.stderr)
    app = build_app(mcp, host, port, os.environ[TOKEN_ENV])
    print(f"labourlens-mcp: serving read-only statistics on http://{host}:{port}{MCP_PATH} (bearer token required)", file=sys.stderr, flush=True)
    # log_config=None keeps the redacting handler installed by the server; the access log stays off.
    uvicorn.run(app, host=host.strip("[]"), port=port, log_config=None, access_log=False, server_header=False, timeout_keep_alive=5)
