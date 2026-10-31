"""Offline web-to-shared-audit acceptance tests; no graph execution or paid calls."""

import asyncio
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace

import httpx
import pandas as pd
import pytest

from labourlens.agent import graph
from labourlens.audit import log
from labourlens.report import audit as web_audit
from labourlens.report.app import COOKIE, create_app
from test_app import (
    ACCESS_CODE,
    QUESTION,
    SESSION_SECRET,
    agent_result,
    client_for,
    isolated_environment,
    login,
    settings,
)


@asynccontextmanager
async def default_client(settings):
    shared = SimpleNamespace(obs=pd.DataFrame(), passages_by_id={})
    app = create_app(settings=settings, shared_factory=lambda: shared)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://testserver"
        ) as client:
            yield app, client, shared


def events():
    return [
        json.loads(line)
        for path in sorted(log.AUDIT_DIR.glob("events-*.jsonl"))
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def session_id(client):
    return client.cookies.get(COOKIE).rsplit(".", 1)[0].rsplit(":", 1)[0]


def assert_private(record, sid):
    assert record["session"] == log.salted_hash(sid)
    assert record["client"] == log.salted_hash("127.0.0.1")
    serialized = json.dumps(record)
    for secret in (sid, "127.0.0.1", ACCESS_CODE, SESSION_SECRET):
        assert secret not in serialized


def test_default_runner_passes_context_and_writes_one_shared_run(settings, monkeypatch):
    calls = []

    def fake_run_agent(question, shared, cfg=None, *, save_trace, audit):
        calls.append((question, shared, save_trace, audit))
        result = agent_result(question)
        result.update(config={"fixture": True}, rounds=1)
        log.log_run(result, **audit)
        return result

    monkeypatch.setattr(graph, "run_agent", fake_run_agent)

    async def scenario():
        async with default_client(settings) as (_, client, shared):
            await login(client)
            sid = session_id(client)
            response = await client.post("/api/ask", json={"question": QUESTION})
            assert response.status_code == 200, response.text
            assert len(calls) == 1
            question, resources, save_trace, context = calls[0]
            assert question == QUESTION
            assert resources is shared
            assert save_trace is True
            assert context == {"channel": "web", "session": sid, "ip": "127.0.0.1", "extra": {}}
            records = log.read_runs()
            assert len(records) == 1  # No duplicate fallback record for the real runner.
            record = records[0]
            assert record["run_id"] == response.json()["run_id"]
            assert record["channel"] == "web"
            assert record["question"] == QUESTION
            assert record["outcome"] == "answered"
            assert record["usage"]["cost_usd"] == pytest.approx(0.01)
            assert_private(record, sid)

    asyncio.run(scenario())


def test_two_argument_injected_runner_gets_normalized_shared_audit(settings):
    calls = []

    def runner(question, shared):
        calls.append(question)
        # Existing lightweight runners deliberately omit config and rounds.
        return agent_result(question)

    async def scenario():
        async with client_for(settings, runner=runner) as (_, client):
            await login(client)
            sid = session_id(client)
            response = await client.post("/api/ask", json={"question": QUESTION})
            assert response.status_code == 200, response.text
            assert calls == [QUESTION]
            records = log.read_runs()
            assert len(records) == 1
            record = records[0]
            assert record["run_id"] == response.json()["run_id"]
            assert record["channel"] == "web"
            assert isinstance(record["config"], dict)
            assert isinstance(record["rounds"], int)
            assert record["question"] == QUESTION
            assert_private(record, sid)

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "rejection,status",
    [("session_limit", 429), ("ip_limit", 429), ("budget", 429),
     ("bad_input", 422), ("malformed", 400), ("kill_switch", 503)],
)
def test_rejections_write_private_events_without_research(settings, monkeypatch, rejection, status):
    calls = []
    if rejection in {"session_limit", "ip_limit"}:
        setattr(settings, rejection, 0)

    def runner(question, shared):
        calls.append(question)
        return agent_result(question)

    async def scenario():
        async with client_for(settings, runner=runner) as (app, client):
            await login(client)
            sid = session_id(client)
            if rejection == "budget":
                app.state.spent_usd = settings.daily_budget_usd
            elif rejection == "kill_switch":
                monkeypatch.setenv("LABOURLENS_DEMO_ENABLED", "false")
            if rejection == "malformed":
                response = await client.post("/api/ask", content=b"not-json")
            else:
                question = " " if rejection == "bad_input" else QUESTION
                response = await client.post("/api/ask", json={"question": question})
            assert response.status_code == status, response.text
            assert calls == []
            assert not log.read_runs()
            records = events()
            assert len(records) == 1
            record = records[0]
            assert record["kind"] == "request_rejected"
            assert record["channel"] == "web"
            assert record["detail"]["route"] == "/api/ask"
            assert record["detail"]["status"] == status
            assert record["detail"]["reason"] == response.json()["detail"]
            assert QUESTION not in json.dumps(record)
            assert_private(record, sid)

    asyncio.run(scenario())


@pytest.mark.parametrize("tag", ["wrong_number", "wrong_source", "missing_info", "other"])
def test_feedback_tags_join_shared_run_without_parallel_feedback_file(settings, tag):
    async def scenario():
        async with client_for(settings) as (_, client):
            await login(client)
            sid = session_id(client)
            answer = await client.post("/api/ask", json={"question": QUESTION})
            assert answer.status_code == 200
            run_id = answer.json()["run_id"]
            response = await client.post("/api/feedback", json={
                "run_id": run_id, "rating": "down", "comment": "Review this result.", "tags": [tag],
            })
            assert response.status_code == 200, response.text
            assert response.json()["saved"] is True
            records = log.read_feedback()
            assert len(records) == 1
            record = records[0]
            assert record["run_id"] == log.read_runs()[0]["run_id"] == run_id
            assert record["tags"] == [tag]
            assert record["session"] == log.salted_hash(sid)
            assert sid not in json.dumps(record)
            assert not (settings.feedback_dir / "feedback.jsonl").exists()

    asyncio.run(scenario())


@pytest.mark.parametrize("tags", [["unknown"], ["wrong_number", "unknown"], "wrong_source", [1], None, {}])
def test_invalid_feedback_tags_are_rejected_without_feedback_write(settings, tags):
    async def scenario():
        async with client_for(settings) as (_, client):
            await login(client)
            response = await client.post("/api/feedback", json={
                "run_id": "a1b2c3d4e5f6", "rating": "down", "comment": "", "tags": tags,
            })
            assert response.status_code == 422, response.text
            assert not log.read_feedback()

    asyncio.run(scenario())


@pytest.mark.parametrize("run_id", ["../outside", "test-run-001", "a1b2c3d4e5f", "a1b2c3d4e5f60", "zzzzzzzzzzzz", 123, None])
def test_invalid_feedback_run_identifiers_are_rejected(settings, run_id):
    async def scenario():
        async with client_for(settings) as (_, client):
            await login(client)
            response = await client.post("/api/feedback", json={
                "run_id": run_id, "rating": "up", "comment": "",
            })
            assert response.status_code == 422, response.text
            assert not log.read_feedback()

    asyncio.run(scenario())


def test_unwritable_shared_audit_directory_does_not_break_requests(settings, monkeypatch, tmp_path):
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("Synthetic audit I/O failure fixture.")
    monkeypatch.setattr(log, "AUDIT_DIR", blocked)
    before = log.failures()

    async def scenario():
        async with client_for(settings) as (_, client):
            await login(client)
            answer = await client.post("/api/ask", json={"question": QUESTION})
            assert answer.status_code == 200, answer.text
            feedback = await client.post("/api/feedback", json={
                "run_id": answer.json()["run_id"], "rating": "up", "comment": "",
            })
            assert feedback.status_code == 200, feedback.text
            invalid = await client.post("/api/ask", json={"question": ""})
            assert invalid.status_code == 422, invalid.text

    asyncio.run(scenario())
    assert log.failures() >= before + 3


@pytest.mark.parametrize("target", ["run", "feedback", "event"])
def test_unexpected_audit_exceptions_never_replace_http_outcome(settings, monkeypatch, target):
    def broken(*args, **kwargs):
        raise RuntimeError("private-audit-failure")

    if target == "run":
        monkeypatch.setattr(log, "log_run", broken)
    elif target == "feedback":
        monkeypatch.setattr(log, "log_feedback", broken)
    else:
        monkeypatch.setattr(web_audit, "log_event", broken)

    async def scenario():
        async with client_for(settings) as (_, client):
            await login(client)
            if target == "feedback":
                await client.post("/api/ask", json={"question": QUESTION})  # feedback is accepted only for the session's own runs
            if target == "run":
                response = await client.post("/api/ask", json={"question": QUESTION})
                expected = 200
            elif target == "feedback":
                response = await client.post("/api/feedback", json={
                    "run_id": "a1b2c3d4e5f6", "rating": "up", "comment": "",
                })
                expected = 200
            else:
                response = await client.post("/api/ask", json={"question": ""})
                expected = 422
            assert response.status_code == expected, response.text
            assert "private-audit-failure" not in response.text

    asyncio.run(scenario())
