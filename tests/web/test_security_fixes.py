"""Offline regression coverage for the independent web security review."""
import asyncio
import json
import logging
import threading
from types import SimpleNamespace

import httpx
import pandas as pd
import pytest
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from labourlens.report import audit as web_audit
from labourlens.report import serve
from labourlens.report.app import COOKIE, RIGHTS_NOTICE, RUN_RESERVATION_USD, Settings, create_app, public_result
from test_app import ACCESS_CODE, QUESTION, agent_result, client_for, isolated_environment, login, settings


def test_weak_secrets_disable_live_demo(settings, caplog):
    async def scenario():
        for codes, secret in [(("short",), "s" * 32), ((ACCESS_CODE,), "s" * 31), ((ACCESS_CODE, "short"), "s" * 32)]:
            settings.access_codes, settings.session_secret = codes, secret
            with caplog.at_level(logging.WARNING):
                async with client_for(settings) as (_, client):
                    assert (await client.get("/api/status")).json()["enabled"] is False
                    assert (await client.post("/api/login", json={"code": codes[0]})).status_code == 503
        assert "require a session secret >=32" in caplog.text
    asyncio.run(scenario())


@pytest.mark.parametrize("failure", ["exception", "bad_projection", "failure_outcome"])
def test_failed_runs_keep_durable_reservation_and_cannot_bypass_cap(settings, failure):
    settings.daily_budget_usd = RUN_RESERVATION_USD
    calls = []
    def runner(question, shared):
        calls.append(question)
        saved = json.loads((settings.feedback_dir / "budget.json").read_text())
        assert saved["spent_usd"] == RUN_RESERVATION_USD  # Must exist before any paid work.
        if failure == "exception":
            raise RuntimeError("after provider call")
        raw = agent_result()
        if failure == "bad_projection":
            raw["evidence"] = [None]
        else:
            raw["outcome"] = "operational_failure"
        return raw
    async def scenario():
        async with client_for(settings, runner=runner) as (app, client):
            await login(client)
            result = await client.post("/api/ask", json={"question": QUESTION})
            assert result.status_code == (200 if failure == "failure_outcome" else 503)
            assert app.state.spent_usd == pytest.approx(RUN_RESERVATION_USD)
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 429
        async with client_for(settings) as (app, client):
            await login(client)
            assert app.state.spent_usd == pytest.approx(RUN_RESERVATION_USD)
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 429
        assert len(calls) == 1
    asyncio.run(scenario())


def test_timeout_retains_reservation_even_after_late_success(settings):
    settings.request_timeout = .001
    async def scenario():
        release = asyncio.Event()
        async def runner(question, shared):
            await release.wait()
            return agent_result(cost=.001)
        async with client_for(settings, runner=runner) as (app, client):
            await login(client)
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 504
            assert app.state.spent_usd == RUN_RESERVATION_USD
            release.set()
        assert app.state.spent_usd == RUN_RESERVATION_USD
        assert json.loads((settings.feedback_dir / "budget.json").read_text())["spent_usd"] == RUN_RESERVATION_USD
    asyncio.run(scenario())


def test_unwritable_reservation_never_starts_runner(settings):
    settings.feedback_dir.write_text("blocked")
    async def scenario():
        def runner(*args):
            pytest.fail("reservation failed but research ran")
        async with client_for(settings, runner=runner) as (app, client):
            await login(client)
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 503
            assert app.state.spent_usd == settings.daily_budget_usd
    asyncio.run(scenario())


def test_budget_rejects_insufficient_room_before_launch(settings):
    settings.daily_budget_usd = RUN_RESERVATION_USD - .001
    async def scenario():
        def runner(*args):
            pytest.fail("run launched without room for reservation")
        async with client_for(settings, runner=runner) as (_, client):
            await login(client)
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 429
    asyncio.run(scenario())




@pytest.mark.parametrize("field", ["summary", "reason", "clarification_question", "caveats", "claim"])
def test_free_text_verbatim_overlap_is_withheld(field):
    raw = agent_result()
    copied = " ".join(f"word{i}" for i in range(13))
    raw["evidence_text"] = {"P1": "before " + copied + " after"}
    if field == "claim":
        raw["answer"]["claims"] = [{"text": copied, "citations": []}]
    elif field == "caveats":
        raw["answer"][field] = [copied]
    else:
        raw["answer"][field] = copied
    result = public_result(raw, SimpleNamespace(obs=pd.DataFrame(), passages_by_id={}))
    assert copied not in json.dumps(result)
    assert RIGHTS_NOTICE in json.dumps(result)
    assert raw["evidence_text"]["P1"].endswith("after")


def test_quote_reconstruction_limits_apply_to_answer_and_cards():
    raw = agent_result()
    quotes = [" ".join(f"q{i}w{j}" for j in range(40)) for i in range(20)]
    raw["evidence_text"] = {"P1": " ".join(quotes)}
    raw["evidence"] = [{"label": "P1", "id": "p1", "source_id": "fixture"}]
    raw["answer"]["claims"] = [{"text": "Paraphrase", "citations": [{"label": "P1", "quote": q} for q in [quotes[i], quotes[i], *quotes]]} for i in range(20)]
    result = public_result(raw, SimpleNamespace(obs=pd.DataFrame(), passages_by_id={}))
    claims = result["answer"]["claims"]
    citations = [c for claim in claims for c in claim["citations"]]
    assert len(claims) == 12
    assert all(len(claim["citations"]) <= 3 for claim in claims)
    # A quote repeated inside one claim is listed once; reuse across claims costs no extra quote budget.
    assert all(len({c["quote"] for c in claim["citations"]}) == len(claim["citations"]) for claim in claims)
    unique = {c["quote"] for c in citations}
    assert sum(len(q.split()) for q in unique) <= 120
    assert sum(len(q.split()) for q in result["evidence"][0]["quotes"]) <= 120
    assert len(result["evidence"][0]["quotes"]) == len(set(result["evidence"][0]["quotes"]))


def test_response_redaction_preserves_json_and_short_codes_not_global_substrings(settings):
    def runner(*args):
        raw = agent_result()
        raw["answer"]["summary"] = 'token=abcdefgh" path\\ demo'
        return raw
    async def scenario():
        async with client_for(settings, runner=runner) as (_, client):
            await login(client)
            response = await client.post("/api/ask", json={"question": QUESTION})
            assert response.status_code == 200
            assert '" path\\ demo' in response.json()["answer"]["summary"]
            assert "abcdefgh" not in response.text
    asyncio.run(scenario())


def test_login_lock_is_per_address_and_a_valid_code_passes_while_locked(settings):
    settings.login_limit = 1000
    settings.login_lock_per_address = 3
    async def scenario():
        app = create_app(settings, runner=lambda *args: agent_result(), shared_factory=lambda: None)
        async with app.router.lifespan_context(app):
            def client(address):
                return httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=(address, 1234)), base_url="https://testserver")
            async with client("198.51.100.1") as attacker, client("198.51.100.2") as other:
                assert [(await attacker.post("/api/login", json={"code": "wrong"})).status_code for _ in range(5)] == [401, 401, 401, 429, 429]
                # The locked address can still sign in with a valid code, and other addresses were never affected.
                assert (await attacker.post("/api/login", json={"code": ACCESS_CODE})).status_code == 200
                assert (await other.post("/api/login", json={"code": ACCESS_CODE})).status_code == 200
                assert (await other.post("/api/login", json={"code": "wrong"})).status_code == 401
    asyncio.run(scenario())


def test_global_failure_threshold_refuses_invalid_codes_from_any_address_but_not_valid_ones(settings):
    settings.login_lock_global = 5
    async def scenario():
        app = create_app(settings, runner=lambda *args: agent_result(), shared_factory=lambda: None)
        async with app.router.lifespan_context(app):
            for i in range(7):
                transport = httpx.ASGITransport(app=app, client=(f"198.51.100.{i}", 1234))
                async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
                    assert (await client.post("/api/login", json={"code": "wrong"})).status_code == (401 if i < 5 else 429)
            transport = httpx.ASGITransport(app=app, client=("198.51.100.99", 1234))
            async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
                assert (await client.post("/api/login", json={"code": ACCESS_CODE})).status_code == 200
    asyncio.run(scenario())


def test_login_origin_missing_client_logout_revocation_and_relogin_limits(settings):
    settings.session_limit = 1
    async def scenario():
        async with client_for(settings) as (app, client):
            assert (await client.post("/api/login", json={"code": ACCESS_CODE}, headers={"origin": "https://evil.example"})).status_code == 403
            await login(client)
            stolen = client.cookies.get(COOKIE)
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 200
            assert (await client.post("/api/logout")).status_code == 200
            assert not client.cookies.get(COOKIE)
            client.cookies.set(COOKIE, stolen)
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 401
            client.cookies.clear()
            await login(client)
            assert client.cookies.get(COOKIE) != stolen
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 429
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=None), base_url="https://testserver") as missing_client:
                assert (await missing_client.post("/api/login", json={"code": ACCESS_CODE})).status_code == 200
    asyncio.run(scenario())


@pytest.mark.parametrize("peer,forwarded,secure", [("127.0.0.1", "https", True), ("203.0.113.1", "https", False), ("127.0.0.1", "http", False)])
def test_secure_cookie_trusts_only_proxy_proto(settings, peer, forwarded, secure):
    async def scenario():
        app = create_app(settings, runner=lambda *args: agent_result(), shared_factory=lambda: None)
        wrapped = ProxyHeadersMiddleware(app, trusted_hosts="127.0.0.1")
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=wrapped, client=(peer, 1234)), base_url="http://testserver") as client:
                response = await client.post("/api/login", json={"code": ACCESS_CODE}, headers={"X-Forwarded-Proto": forwarded})
                assert response.status_code == 200
                assert ("; secure" in response.headers["set-cookie"].lower()) is secure
    asyncio.run(scenario())


def test_event_writes_do_not_run_on_event_loop(settings, monkeypatch):
    loop_thread, writers = threading.get_ident(), []
    monkeypatch.setattr(web_audit, "log_event", lambda *args: writers.append(threading.get_ident()))
    async def scenario():
        async with client_for(settings) as (_, client):
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 401
    asyncio.run(scenario())
    assert writers and all(writer != loop_thread for writer in writers)


def test_server_announces_trusted_proxy_without_secrets(monkeypatch, caplog):
    import uvicorn
    monkeypatch.setenv("LABOURLENS_FORWARDED_ALLOW_IPS", "127.0.0.1")
    monkeypatch.setattr("labourlens.report.app.create_app", lambda: object())
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: None)
    with caplog.at_level(logging.WARNING):
        serve.run()
    assert "Trusted proxy headers enabled for: 127.0.0.1" in caplog.text
    assert ACCESS_CODE not in caplog.text

def test_trace_redactor_filters_each_configured_access_code(monkeypatch):
    from labourlens.mcp.redact import redact
    monkeypatch.setenv("LABOURLENS_ACCESS_CODES", ACCESS_CODE + ", second-test-access-code")
    result = redact("question repeats " + ACCESS_CODE + " and second-test-access-code")
    assert ACCESS_CODE not in result
    assert "second-test-access-code" not in result
