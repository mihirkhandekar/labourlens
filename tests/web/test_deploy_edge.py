"""Offline tests for the deployment edge: /healthz and which client address the rate limiter sees behind Caddy."""

import asyncio
from types import SimpleNamespace

import httpx
import pandas as pd
import pytest
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from labourlens.report import serve
from labourlens.report.app import Settings, create_app

PROXY = "172.30.0.2"  # the fixed Caddy address in deploy/docker-compose.yml


def make_app(tmp_path):
    settings = Settings(access_codes=("x" * 24,), session_secret="s" * 40, login_limit=2, feedback_dir=tmp_path)
    return create_app(settings=settings, runner=lambda q, s: {}, shared_factory=lambda: SimpleNamespace(obs=pd.DataFrame(), passages_by_id={}))


async def post_logins(app, peer, forwarded_values):
    """Send one bad login per forwarded value from a fixed TCP peer; return the status codes."""
    wrapped = ProxyHeadersMiddleware(app, trusted_hosts=PROXY)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=wrapped, client=(peer, 40000))
        async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
            return [(await client.post("/api/login", json={"code": "wrong"}, headers={"X-Forwarded-For": v})).status_code
                    for v in forwarded_values]


def test_healthz_is_minimal_and_unauthenticated(tmp_path):
    async def scenario():
        app = make_app(tmp_path)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
                return await client.get("/healthz")

    response = asyncio.run(scenario())
    assert response.status_code == 200
    assert set(response.json()) == {"status", "version"}
    assert response.json()["status"] == "ok"
    assert response.headers["content-security-policy"]


def test_spoofed_forwarded_for_from_untrusted_peer_does_not_change_rate_limit_key(tmp_path):
    # Peer is not the proxy: three different spoofed addresses still share the peer's bucket (limit 2).
    codes = asyncio.run(post_logins(make_app(tmp_path), "203.0.113.50", ["198.51.100.1", "198.51.100.2", "198.51.100.3"]))
    assert codes == [401, 401, 429]


def test_forwarded_for_from_the_proxy_is_used_as_the_client_address(tmp_path):
    # Peer is the proxy: distinct real clients get distinct buckets, the same client shares one.
    distinct = asyncio.run(post_logins(make_app(tmp_path), PROXY, ["198.51.100.1", "198.51.100.2", "198.51.100.3"]))
    assert distinct == [401, 401, 401]
    same = asyncio.run(post_logins(make_app(tmp_path), PROXY, ["198.51.100.1"] * 3))
    assert same == [401, 401, 429]


def test_forwarded_allow_ips_default_env_and_wildcard_refusal(monkeypatch):
    monkeypatch.delenv("LABOURLENS_FORWARDED_ALLOW_IPS", raising=False)
    assert serve.forwarded_allow_ips() == "127.0.0.1"
    monkeypatch.setenv("LABOURLENS_FORWARDED_ALLOW_IPS", PROXY)
    assert serve.forwarded_allow_ips() == PROXY
    monkeypatch.setenv("LABOURLENS_FORWARDED_ALLOW_IPS", "*")
    with pytest.raises(SystemExit):
        serve.forwarded_allow_ips()
