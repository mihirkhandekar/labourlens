"""Offline HTTP acceptance tests: injected research only, no corpus or paid API.

The integration owner runs these with ``uv run pytest tests/web``. Tests use
HTTPS so the browser sends the deployment's Secure session cookie.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace

import httpx
import pandas as pd
import pytest

from labourlens.report.app import Settings, create_app, public_result
from labourlens.audit import log as audit_log


ACCESS_CODE = "reviewer-code-not-a-production-secret"
SESSION_SECRET = "test-only-session-signing-secret-32-bytes"
QUESTION = "What changed in resident unemployment?"


def agent_result(question=QUESTION, cost=0.01):
    return {
        "run_id": "a1b2c3d4e5f6",
        "question": question,
        "outcome": "answered",
        "answer": {
            "status": "answered",
            "summary": "Injected offline answer, not an official statistic.",
            "reason": "",
            "clarification_question": "",
            "claims": [],
            "caveats": ["Synthetic test fixture."],
        },
        "evidence": [],
        "evidence_text": {},
        "cited_ids": [],
        "trace": [{"node": "finalize", "event": "ok", "detail": {}}],
        "usage": {"calls": 1, "prompt_tokens": 10, "completion_tokens": 5, "cost_usd": cost},
        "seconds": 0.01,
        "errors": [],
        "tool_calls": 0,
    }



@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("LABOURLENS_DEMO_ENABLED", "true")
    monkeypatch.setenv("LABOURLENS_AUDIT_SALT", "offline-web-test-salt")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(audit_log, "AUDIT_DIR", tmp_path / "audit")

@pytest.fixture
def settings(tmp_path):
    return Settings(
        access_codes=(ACCESS_CODE,),
        session_secret=SESSION_SECRET,
        demo_enabled=True,
        daily_budget_usd=2.0,
        login_limit=5,
        session_limit=10,
        ip_limit=20,
        max_concurrent=2,
        feedback_dir=tmp_path / "feedback",
    )


@asynccontextmanager
async def client_for(settings, runner=None, shared_factory=None):
    def default_runner(question, shared):
        return agent_result(question)

    def default_shared():
        return SimpleNamespace(obs=pd.DataFrame(), passages_by_id={})

    app = create_app(
        settings=settings,
        runner=runner or default_runner,
        shared_factory=shared_factory or default_shared,
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://testserver"
        ) as client:
            yield app, client


async def login(client):
    response = await client.post("/api/login", json={"code": ACCESS_CODE})
    assert response.status_code == 200, response.text
    return response


def test_login_status_secure_cookie_and_tampering(settings):
    async def scenario():
        async with client_for(settings) as (_, client):
            status = await client.get("/api/status")
            assert status.status_code == 200
            assert status.json()["enabled"] is True
            assert status.json()["authenticated"] is False
            response = await login(client)
            cookie = response.headers["set-cookie"].lower()
            assert "labourlens_session=" in cookie
            assert "httponly" in cookie
            assert "secure" in cookie
            assert "samesite=lax" in cookie or "samesite=strict" in cookie
            assert ACCESS_CODE not in cookie
            assert (await client.get("/api/status")).json()["authenticated"] is True
            client.cookies.clear()
            client.cookies.set("labourlens_session", "tampered.invalid.signature")
            assert (await client.get("/api/status")).json()["authenticated"] is False
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 401

    asyncio.run(scenario())


def test_wrong_login_and_login_rate_limit(settings):
    settings.login_limit = 2

    async def scenario():
        async with client_for(settings) as (_, client):
            for _ in range(2):
                response = await client.post("/api/login", json={"code": "wrong"})
                assert response.status_code == 401
                assert "labourlens_session=" not in response.headers.get("set-cookie", "")
            limited = await client.post("/api/login", json={"code": ACCESS_CODE})
            assert limited.status_code == 429
            assert (await client.get("/api/status")).json()["authenticated"] is False

    asyncio.run(scenario())


def test_unauthenticated_requests_never_invoke_runner(settings):
    def forbidden_runner(*args):
        pytest.fail("Unauthenticated HTTP request invoked research")

    async def scenario():
        async with client_for(settings, runner=forbidden_runner) as (_, client):
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 401
            assert (await client.post("/api/feedback", json={"run_id": "x", "rating": "up", "comment": ""})).status_code == 401

    asyncio.run(scenario())


@pytest.mark.parametrize("disabled_by", ["switch", "codes", "secret"])
def test_disabled_configuration_does_not_load_research(settings, disabled_by):
    if disabled_by == "switch":
        settings.demo_enabled = False
    elif disabled_by == "codes":
        settings.access_codes = ()
    else:
        settings.session_secret = ""

    def forbidden_factory():
        pytest.fail("Disabled live demo loaded research resources")

    async def scenario():
        async with client_for(settings, shared_factory=forbidden_factory) as (_, client):
            status = await client.get("/api/status")
            assert status.status_code == 200
            assert status.json()["enabled"] is False
            assert (await client.post("/api/login", json={"code": ACCESS_CODE})).status_code == 503
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 503

    asyncio.run(scenario())


def test_injected_agent_smoke_and_budget_accounting(settings):
    calls = []
    shared = SimpleNamespace(obs=pd.DataFrame(), passages_by_id={})

    def runner(question, resources):
        assert resources is shared
        calls.append(question)
        return agent_result(question, cost=0.125)

    async def scenario():
        async with client_for(settings, runner=runner, shared_factory=lambda: shared) as (app, client):
            await login(client)
            response = await client.post("/api/ask", json={"question": QUESTION})
            assert response.status_code == 200, response.text
            result = response.json()
            assert set(result) >= {"run_id", "answer", "evidence", "chart", "trace", "usage"}
            assert result["answer"]["summary"] == agent_result()["answer"]["summary"]
            assert result["run_id"]
            assert result["usage"]["cost_usd"] == 0.125
            assert isinstance(result["trace"], list)
            assert app.state.spent_usd == pytest.approx(0.125)
            assert calls == [QUESTION]
            app.state.spent_usd = settings.daily_budget_usd
            blocked = await client.post("/api/ask", json={"question": QUESTION})
            assert blocked.status_code == 429
            assert calls == [QUESTION]

    asyncio.run(scenario())


@pytest.mark.parametrize("limit_name", ["session_limit", "ip_limit"])
def test_ask_rate_limits_prevent_extra_model_calls(settings, limit_name):
    setattr(settings, limit_name, 1)
    calls = []

    def runner(question, shared):
        calls.append(question)
        return agent_result(question)

    async def scenario():
        async with client_for(settings, runner=runner) as (_, client):
            await login(client)
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 200
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 429
            assert len(calls) == 1

    asyncio.run(scenario())


def test_concurrency_rejects_overlap_and_releases_slot(settings):
    settings.max_concurrent = 1

    async def scenario():
        entered = asyncio.Event()
        release = asyncio.Event()
        calls = []

        async def runner(question, shared):
            calls.append(question)
            entered.set()
            await release.wait()
            return agent_result(question)

        async with client_for(settings, runner=runner) as (_, client):
            await login(client)
            first = asyncio.create_task(client.post("/api/ask", json={"question": QUESTION}))
            try:
                await asyncio.wait_for(entered.wait(), timeout=3)
                second = await client.post("/api/ask", json={"question": QUESTION})
                assert second.status_code == 503
                assert len(calls) == 1
            finally:
                release.set()
                await asyncio.wait_for(first, timeout=3)
            assert first.result().status_code == 200
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 200
            assert len(calls) == 2

    asyncio.run(scenario())


def test_runner_failure_is_generic_and_releases_slot(settings):
    settings.max_concurrent = 1
    calls = []

    def runner(question, shared):
        calls.append(question)
        if len(calls) == 1:
            raise RuntimeError("secret-backend-detail-not-for-client")
        return agent_result(question)

    async def scenario():
        async with client_for(settings, runner=runner) as (_, client):
            await login(client)
            response = await client.post("/api/ask", json={"question": QUESTION})
            assert response.status_code in {500, 502, 503}
            assert "secret-backend-detail" not in response.text
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 200

    asyncio.run(scenario())


@pytest.mark.parametrize("question", ["", "   ", "x" * 1001, None, 42, [], {}])
def test_invalid_questions_do_not_invoke_runner(settings, question):
    def forbidden_runner(*args):
        pytest.fail("Invalid question reached research")

    async def scenario():
        async with client_for(settings, runner=forbidden_runner) as (_, client):
            await login(client)
            response = await client.post("/api/ask", json={"question": question})
            assert response.status_code == 422

    asyncio.run(scenario())


@pytest.mark.parametrize("streamed", [False, True])
def test_request_body_limit_applies_without_trusting_content_length(settings, streamed):
    settings.body_limit = 256

    async def scenario():
        async with client_for(settings) as (_, client):
            await login(client)
            payload = json.dumps({"question": "x" * 512}).encode()
            if streamed:
                async def chunks():
                    yield payload[:128]
                    yield payload[128:]

                content = chunks()
            else:
                content = payload
            response = await client.post("/api/ask", content=content, headers={"content-type": "application/json"})
            assert response.status_code == 413

    asyncio.run(scenario())


def test_security_headers_cover_success_and_error_responses(settings):
    async def scenario():
        async with client_for(settings) as (_, client):
            responses = [await client.get("/api/status"), await client.post("/api/ask", json={"question": QUESTION})]
            for response in responses:
                assert response.headers["x-content-type-options"].lower() == "nosniff"
                assert response.headers.get("x-frame-options", "").lower() == "deny"
                assert response.headers.get("referrer-policy") in {"no-referrer", "same-origin", "strict-origin-when-cross-origin"}
                csp = response.headers["content-security-policy"]
                assert "default-src 'self'" in csp
                assert "frame-ancestors 'none'" in csp
                assert "object-src 'none'" in csp
                assert "'unsafe-eval'" not in csp
                assert response.headers.get("cache-control") == "no-store"

    asyncio.run(scenario())


def test_feedback_is_sanitized_and_stored_as_one_json_record(settings):
    async def scenario():
        async with client_for(settings) as (_, client):
            await login(client)
            response = await client.post("/api/ask", json={"question": QUESTION})
            run_id = response.json()["run_id"]
            comment = '<script>alert(1)</script>Useful\x00\u202e\n{"rating":"up"}'
            feedback = await client.post("/api/feedback", json={"run_id": run_id, "rating": "down", "comment": comment})
            assert feedback.status_code == 200, feedback.text
            assert feedback.json()["saved"] is True
            records = (audit_log.AUDIT_DIR / "feedback.jsonl").read_text().splitlines()
            assert len(records) == 1
            saved = json.loads(records[0])
            assert saved["run_id"] == run_id
            assert saved["rating"] == "down"
            assert "Useful" in saved["comment"]
            assert "<script>" not in saved["comment"]
            assert "\x00" not in saved["comment"]
            assert "\u202e" not in saved["comment"]
            assert ACCESS_CODE not in records[0]
            assert SESSION_SECRET not in records[0]
            assert not (settings.feedback_dir / "feedback.jsonl").exists()

    asyncio.run(scenario())


@pytest.mark.parametrize("rating", ["other", "", 1, None])
def test_invalid_feedback_rating_is_rejected(settings, rating):
    async def scenario():
        async with client_for(settings) as (_, client):
            await login(client)
            response = await client.post("/api/feedback", json={"run_id": "a1b2c3d4e5f6", "rating": rating, "comment": ""})
            assert response.status_code == 422
            assert not audit_log.read_feedback()

    asyncio.run(scenario())


def test_environment_kill_switch_blocks_existing_session(settings, monkeypatch):
    async def scenario():
        async with client_for(settings) as (_, client):
            await login(client)
            monkeypatch.setenv("LABOURLENS_DEMO_ENABLED", "false")
            assert (await client.get("/api/status")).json()["enabled"] is False
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 503

    asyncio.run(scenario())


def test_cross_origin_session_requests_are_rejected(settings):
    async def scenario():
        async with client_for(settings) as (_, client):
            await login(client)
            response = await client.post(
                "/api/ask", json={"question": QUESTION},
                headers={"origin": "https://untrusted.example"},
            )
            assert response.status_code == 403

    asyncio.run(scenario())


@pytest.mark.parametrize("payload", [b"not-json", b"[]", b"null"])
def test_malformed_request_body_is_rejected(settings, payload):
    async def scenario():
        async with client_for(settings) as (_, client):
            await login(client)
            response = await client.post("/api/ask", content=payload, headers={"content-type": "application/json"})
            assert response.status_code == 400

    asyncio.run(scenario())


def test_budget_survives_app_restart_and_corrupt_ledger_fails_closed(settings):
    async def scenario():
        async with client_for(settings) as (_, client):
            await login(client)
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 200
        async with client_for(settings) as (app, _):
            assert app.state.spent_usd == pytest.approx(0.01)
        (settings.feedback_dir / "budget.json").write_text("not-json")
        async with client_for(settings) as (app, client):
            await login(client)
            assert app.state.spent_usd == settings.daily_budget_usd
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 429

    asyncio.run(scenario())


def test_timed_out_run_retains_concurrency_slot_until_finished(settings):
    settings.max_concurrent = 1
    settings.request_timeout = 0.01

    async def scenario():
        release = asyncio.Event()

        async def runner(question, shared):
            await release.wait()
            return agent_result(question)

        async with client_for(settings, runner=runner) as (_, client):
            await login(client)
            try:
                response = await client.post("/api/ask", json={"question": QUESTION})
                assert response.status_code == 504
                overlap = await client.post("/api/ask", json={"question": QUESTION})
                assert overlap.status_code == 503
            finally:
                release.set()

    asyncio.run(scenario())


def test_feedback_length_is_bounded_and_run_id_cannot_be_a_path(settings):
    async def scenario():
        async with client_for(settings) as (_, client):
            await login(client)
            response = await client.post("/api/feedback", json={"run_id": "../outside", "rating": "up", "comment": "x" * 1001})
            assert response.status_code == 422
            assert not audit_log.read_feedback()
            response = await client.post("/api/feedback", json={"run_id": "../outside", "rating": "up", "comment": "fine"})
            assert response.status_code == 422
            assert not audit_log.read_feedback()
            response = await client.post("/api/feedback", json={"run_id": "a1b2c3d4e5f6", "rating": "up", "comment": "fine"})
            assert response.status_code == 200
            assert audit_log.read_feedback()[0]["run_id"] == "a1b2c3d4e5f6"

    asyncio.run(scenario())


def test_public_result_projects_only_verified_data_and_bounded_cited_quotes(monkeypatch):
    from labourlens.data import catalog

    source_id = "synthetic-statistics"
    report_id = "synthetic-report"
    monkeypatch.setattr(catalog, "sources", lambda: {
        "datasets": [{"source_id": source_id, "title": "Synthetic quarterly fixture", "canonical_url": "https://example.org/statistics", "publisher": "Test publisher"}],
        "documents": [{"source_id": report_id, "title": "Synthetic narrative fixture", "canonical_url": "https://example.org/report", "publisher": "Test publisher"}],
    })
    quote = "Synthetic evidence explains this fixture."
    full_passage = quote + " Additional private fixture content must not be redistributed by the response."
    long_quote = " ".join(f"word{i}" for i in range(41))
    shared = SimpleNamespace(
        obs=pd.DataFrame([{
            "observation_id": "obs-fixture-1", "source_id": source_id,
            "period": "2026-Q2", "value": 2.75, "indicator_id": "fixture-rate",
            "dimension": "all", "population": "resident", "adjustment": "seasonally_adjusted",
            "unit": "percent", "publication_date": "2026-09-01", "release_stage": "final",
        }]),
        passages_by_id={"passage-fixture-1": {
            "source_id": report_id, "locator": "page 3", "publication_date": "2026-09-01",
            "release_stage": "final", "text": full_passage,
        }},
    )
    raw = agent_result()
    raw["chart"] = {"series": [{"points": [{"period": "2099-Q4", "value": 999999}]}]}
    raw["answer"]["claims"] = [{
        "text": "Synthetic claim.",
        "citations": [
            {"label": "P1", "quote": quote},
            {"label": "P1", "quote": "Invented quote not in evidence."},
            {"label": "P1", "quote": long_quote},
        ],
    }]
    raw["evidence"] = [
        {"label": "O1", "id": "obs-fixture-1", "source_id": source_id},
        {"label": "P1", "id": "passage-fixture-1", "source_id": report_id},
    ]
    raw["evidence_text"] = {"P1": full_passage + " " + long_quote}
    raw["trace"] = [{
        "node": "execute_tool", "event": "ok",
        "detail": {"tool": "get_series", "observations": 1,
                   "note": "private-planner-note", "result": "private-tool-result"},
    }]
    result = public_result(raw, shared)
    series = result["chart"]["series"]
    assert len(series) == 1
    assert series[0]["unit"] == "percent"
    assert series[0]["points"] == [{"period": "2026-Q2", "value": 2.75, "observation_id": "obs-fixture-1"}]
    assert "999999" not in json.dumps(result["chart"])
    assert result["evidence"][0]["url"] == "https://example.org/statistics"
    report = result["evidence"][1]
    assert report["url"] == "https://example.org/report"
    assert report["locator"] == "page 3"
    assert report["quotes"] == [quote]
    assert "evidence_text" not in result
    assert "Additional private fixture content" not in json.dumps(result)
    trace = result["trace"]
    assert trace[0]["detail"]["tool"] == "get_series"
    assert trace[0]["detail"]["observations"] == 1
    assert "note" not in trace[0]["detail"]
    assert "result" not in trace[0]["detail"]
    assert "private-planner-note" not in json.dumps(trace)
    assert "private-tool-result" not in json.dumps(trace)


def test_workbench_routes_are_public_static_pages_with_index_security(settings):
    from labourlens import paths

    settings.demo_enabled = False

    def forbidden(*args):
        pytest.fail("Static page request loaded or invoked research")

    async def scenario():
        async with client_for(settings, runner=forbidden, shared_factory=forbidden) as (_, client):
            index = await client.get("/")
            expected = (paths.ROOT / "web" / "workbench.html").read_bytes()
            headers = ("content-security-policy", "x-content-type-options", "referrer-policy", "x-frame-options", "permissions-policy")
            for route in ("/workbench", "/workbench.html"):
                response = await client.get(route)
                assert response.status_code == 200
                assert response.content == expected
                assert response.headers["content-type"].startswith("text/html")
                for header in headers:
                    assert response.headers[header] == index.headers[header]
                assert "set-cookie" not in response.headers
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 503

    asyncio.run(scenario())


def test_public_result_projects_observation_definitions_and_usage_without_private_fields(monkeypatch):
    from labourlens.data import catalog

    monkeypatch.setattr(catalog, "sources", lambda: {})
    record = {
        "observation_id": "fixture-obs", "source_id": "fixture-source", "period": "2026-Q2",
        "value": 2.75, "unit": "percent", "indicator_id": "fixture-rate", "population": "resident",
        "adjustment": "seasonally_adjusted", "dimension": "", "source_locator": "row=3;col=rate",
        "missing_reason": None, "raw_value": "private raw cell", "snapshot_id": "private-snapshot",
    }
    shared = SimpleNamespace(obs=pd.DataFrame([record]), passages_by_id={})
    raw = agent_result()
    raw["evidence"] = [{"label": "O1", "id": "fixture-obs", "source_id": "fixture-source"}]
    raw["usage"]["hidden_reasoning"] = "private reasoning"
    result = public_result(raw, shared)
    card = result["evidence"][0]
    for key in ("period", "value", "unit", "indicator_id", "population", "adjustment", "dimension", "source_locator"):
        assert card[key] == record[key]
    assert "raw_value" not in card
    assert "snapshot_id" not in card
    assert result["usage"] == {"cost_usd": 0.01, "seconds": 0.01, "prompt_tokens": 10, "completion_tokens": 5}
    assert "private reasoning" not in json.dumps(result)
    raw["usage"] = {}
    assert public_result(raw, shared)["usage"] == {"cost_usd": 0, "seconds": 0.01}
    shared.obs.loc[0, "value"] = float("nan")
    assert public_result(raw, shared)["evidence"][0]["value"] is None


@pytest.mark.parametrize("calculation_text, locator", [
    ("Calculated difference of fixture-rate (all; resident, seasonally_adjusted) from 2026-Q1 to 2026-Q2: 2.75 - 2.5 = 0.25 percentage_points. Inputs O1 (2026-Q1) and O2 (2026-Q2).", "O1 (2026-Q1) → O2 (2026-Q2)"),
    ("", ""),
])
def test_public_result_calculation_metadata_is_not_dataset_release(monkeypatch, calculation_text, locator):
    from labourlens.data import catalog

    monkeypatch.setattr(catalog, "sources", lambda: {"datasets": [{
        "source_id": "fixture-source", "title": "Synthetic quarterly fixture", "publisher": "Test publisher",
        "publication_date": "2026-09-01", "release_stage": "dataset_snapshot",
        "canonical_url": "https://example.org/statistics",
    }]})
    raw = agent_result()
    raw["evidence"] = [{"label": "C1", "id": "calc:fixture", "source_id": "fixture-source"}]
    raw["evidence_text"] = {"C1": calculation_text}
    result = public_result(raw, SimpleNamespace(obs=pd.DataFrame(), passages_by_id={}))
    card = result["evidence"][0]
    assert card["kind"] == "calculation"
    assert card["source_title"] == "Calculation on Synthetic quarterly fixture"
    assert card["release_stage"] == "calculated"
    assert card["date"] == ""
    assert card["locator"] == locator
    assert card["url"] == "https://example.org/statistics"
    assert "value" not in card
    assert "unit" not in card
    assert "evidence_text" not in result
