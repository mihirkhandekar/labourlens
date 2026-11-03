"""POST /api/ask/stream (D-079): event order, the final payload, mid-stream failure, and the gates it shares with /api/ask.

Offline: a fake runner stands in for the agent, so no key, corpus or network. httpx's ASGI transport hands back the whole body at once, so
these tests check what was sent and in which order, not wall-clock incrementality (that is smoked against a real server)."""
import asyncio
import json
import time

import pytest
from test_app import ACCESS_CODE, QUESTION, agent_result, client_for, isolated_environment, login, settings  # noqa: F401

from labourlens.report.app import RUN_RESERVATION_USD, public_event


def frames(text):
    """[(event name, data)] of an SSE body; comment lines (keepalives) are skipped."""
    out = []
    for block in text.split("\n\n"):
        name, data = "message", []
        for line in block.split("\n"):
            if line.startswith("event:"):
                name = line[6:].strip()
            elif line.startswith("data:"):
                data.append(line[5:].lstrip(" "))
        if data:
            out.append((name, json.loads("\n".join(data))))
    return out


def live_runner(question, shared, audit=None, history=None, emit=None):
    """Emits the same internal events the real runner and graph do, in the order they happen."""
    emit = emit or (lambda event: None)  # /api/ask passes no emit
    emit({"type": "stage", "stage": "contextualise", "state": "running"})
    emit({"type": "stage", "stage": "contextualise", "state": "done", "changed": False})
    emit({"type": "stage", "stage": "triage", "state": "running"})
    emit({"type": "stage", "stage": "triage", "state": "done", "route": "in_scope"})
    emit({"type": "node_started", "node": "validate_question"})
    emit({"type": "node_started", "node": "plan_research"})
    emit({"type": "trace", "item": {"t": 1.0, "node": "plan_research", "event": "gather", "detail": {"round": 1, "n_calls": 1, "note": "hidden", "planner_mode": "tools"}}})
    emit({"type": "node_started", "node": "execute_tool"})
    emit({"type": "tool_call_started", "tool": "get_series", "args": {"source_id": "retrenched_employees"}})
    emit({"type": "tool_call_finished", "item": {"t": 2.0, "node": "execute_tool", "event": "ok", "detail": {"tool": "get_series", "seconds": 0.1, "new_items": ["O1"], "result": "private"}}})
    emit({"type": "node_started", "node": "generate_answer"})
    emit({"type": "node_started", "node": "validate_answer"})
    emit({"type": "trace", "item": {"t": 3.0, "node": "finalize", "event": "answered", "detail": {}}})
    return agent_result(question)


async def stream(client, body=None):
    return await client.post("/api/ask/stream", json=body if body is not None else {"question": QUESTION})


def test_events_arrive_in_run_order_and_end_with_one_result(settings):  # noqa: F811
    async def scenario():
        async with client_for(settings, runner=live_runner) as (app, client):
            await login(client)
            response = await stream(client)
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            assert response.headers["x-accel-buffering"] == "no" and response.headers["cache-control"] == "no-store"
            assert "default-src 'self'" in response.headers["content-security-policy"]
            got = frames(response.text)
            names = [(n, d.get("stage") or d.get("phase") or (d.get("item") or {}).get("event")) for n, d in got]
            assert names == [("status", "accepted"), ("status", "contextualise"), ("status", "contextualise"), ("status", "triage"), ("status", "triage"),
                             ("status", "planning"), ("trace", "gather"), ("tool", "started"), ("tool", "finished"), ("status", "answering"),
                             ("status", "validating"), ("trace", "answered"), ("result", None)]
            assert [n for n, _ in got].count("result") == 1 and got[-1][0] == "result"
            assert all(isinstance(d.get("text"), str) and d["text"] for n, d in got if n == "status")
            tool_done = got[8][1]["item"]["detail"]
            assert tool_done == {"tool": "get_series", "seconds": 0.1, "new_items": ["O1"]}  # allow-listed keys only: no "result" text
            assert "note" not in got[6][1]["item"]["detail"] and got[7][1]["args"] == {"source_id": "retrenched_employees"}
            assert app.state.active == 0 and app.state.spent_usd == pytest.approx(0.01)

    asyncio.run(scenario())


def test_final_event_is_exactly_the_non_streaming_response_and_nothing_earlier_carries_answer_text(settings):  # noqa: F811
    async def scenario():
        async with client_for(settings, runner=live_runner) as (_, client):
            await login(client)
            plain = (await client.post("/api/ask", json={"question": QUESTION})).json()
            body = (await stream(client)).text
            got = frames(body)
            assert got[-1] == ("result", plain)
            assert plain["answer"]["summary"] not in "".join(json.dumps(d) for n, d in got[:-1])
            assert body.count(plain["answer"]["summary"]) == 1  # the validated answer appears once, in the result frame

    asyncio.run(scenario())


def test_runner_without_emit_still_streams_accepted_then_result(settings):  # noqa: F811
    async def scenario():
        async with client_for(settings) as (_, client):  # default runner takes (question, shared) only
            await login(client)
            got = frames((await stream(client)).text)
            assert [n for n, _ in got] == ["status", "result"] and got[-1][1]["answer"]["status"] == "answered"

    asyncio.run(scenario())


def test_failure_mid_stream_sends_an_error_event_no_result_and_releases_the_slot(settings):  # noqa: F811
    def runner(question, shared, emit=None):
        emit({"type": "stage", "stage": "triage", "state": "running"})
        raise RuntimeError("provider exploded with sk-secret-detail")

    async def scenario():
        async with client_for(settings, runner=runner) as (app, client):
            await login(client)
            response = await stream(client)
            got = frames(response.text)
            assert response.status_code == 200 and [n for n, _ in got] == ["status", "status", "error"]
            assert got[-1][1] == {"status": 503, "detail": "Agent unavailable. Please try again later."}
            assert "sk-secret-detail" not in response.text and "RuntimeError" not in response.text
            assert app.state.active == 0 and app.state.spent_usd == pytest.approx(RUN_RESERVATION_USD)  # an unfinished run keeps its reservation
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code in (200, 503)  # the slot is free again

    asyncio.run(scenario())


def test_run_that_outlives_the_request_timeout_sends_a_504_error_event(settings):  # noqa: F811
    settings.request_timeout = 0.2

    def runner(question, shared, emit=None):
        time.sleep(0.6)
        return agent_result(question)

    async def scenario():
        async with client_for(settings, runner=runner) as (app, client):
            await login(client)
            got = frames((await stream(client)).text)
            assert got[-1] == ("error", {"status": 504, "detail": "Run timed out. Please try again later."}) and "result" not in [n for n, _ in got]
        assert app.state.active == 0  # the lifespan waited for the late run; it was charged at least the reservation
        assert app.state.spent_usd >= RUN_RESERVATION_USD

    asyncio.run(scenario())


def test_same_gates_as_ask_login_origin_request_shape_budget_and_busy(settings):  # noqa: F811
    calls = []

    def runner(question, shared, emit=None):
        calls.append(question)
        return agent_result(question)

    async def scenario():
        async with client_for(settings, runner=runner) as (app, client):
            anonymous = await stream(client)
            assert anonymous.status_code == 401 and anonymous.headers["content-type"].startswith("application/json") and calls == []
            await login(client)
            assert (await client.post("/api/ask/stream", json={"question": QUESTION}, headers={"Origin": "https://evil.example"})).status_code == 403
            assert (await stream(client, {"question": ""})).status_code == 422
            assert (await stream(client, {"question": "x" * 1001})).status_code == 422
            assert (await stream(client, {"question": QUESTION, "history": "nope"})).status_code == 422
            assert (await client.post("/api/ask/stream", content=b"x" * 20000, headers={"Content-Type": "application/json"})).status_code == 413
            assert calls == []
            app.state.spent_usd = settings.daily_budget_usd
            assert (await stream(client)).status_code == 429
            app.state.spent_usd = 0.0
            app.state.active = 2
            assert (await stream(client)).status_code == 503
            app.state.active = 0
            assert calls == [] and (await stream(client)).status_code == 200 and calls == [QUESTION]

    asyncio.run(scenario())


def test_stream_requests_count_against_the_same_rate_limits(settings):  # noqa: F811
    settings.session_limit = 2
    settings.ip_limit = 50

    async def scenario():
        async with client_for(settings) as (_, client):
            await login(client)
            assert (await stream(client)).status_code == 200
            assert (await client.post("/api/ask", json={"question": QUESTION})).status_code == 200
            assert (await stream(client)).status_code == 429

    asyncio.run(scenario())


def test_secrets_never_leave_in_a_live_event(settings):  # noqa: F811
    def runner(question, shared, emit=None):
        emit({"type": "tool_call_started", "tool": "get_series", "args": {"query": f"leak {ACCESS_CODE}"}})
        return agent_result(question)

    async def scenario():
        async with client_for(settings, runner=runner) as (_, client):
            await login(client)
            text = (await stream(client)).text
            assert ACCESS_CODE not in text and "tool" in text

    asyncio.run(scenario())


def test_public_event_allow_list():
    assert public_event({"type": "stage", "stage": "triage", "state": "done", "route": "out_of_scope"})[1]["text"].startswith("The question is outside")
    assert public_event({"type": "stage", "stage": "contextualise", "state": "done", "changed": True})[1]["text"] == "Question rewritten using the earlier turns."
    assert public_event({"type": "node_started", "node": "assess_evidence"}) is None and public_event({"type": "unknown"}) is None
    assert public_event({"type": "trace", "item": "not a dict"}) is None
    args = public_event({"type": "tool_call_started", "tool": "t" * 100, "args": {"query": "q" * 1000, "k": 8}})[1]
    assert len(args["tool"]) == 64 and len(args["args"]["query"]) == 300 and args["args"]["k"] == 8


def test_app_builds_the_shipped_runner_and_the_runner_sends_stage_and_agent_events(settings, monkeypatch):  # noqa: F811
    from types import SimpleNamespace

    from labourlens.agent import contextualise, graph, served, smalltalk, triage

    built = {}
    real = served.make_runner
    monkeypatch.setattr(served, "make_runner", lambda config=None, **kw: built.update(config=config, **kw) or real(config, **kw))
    create_app_ = __import__("labourlens.report.app", fromlist=["create_app"]).create_app
    create_app_(settings)
    assert (built["config"].planner_mode, built["config"].planner_prompt, built["config"].answer_prompt) == ("tools", "planner_v4", "answer_v6")
    assert (built["triage_prompt"], built["contextualise_prompt"]) == ("triage_v2", "contextualise_v2")

    seen = {}
    info = {"question": "q", "original": "q", "changed": False, "called": True, "error": None, "usage": triage._empty_usage(), "model": "m", "prompt": "p", "prompt_sha256": "h", "seconds": 0.0}
    monkeypatch.setattr(smalltalk, "run_smalltalk", lambda *a, **k: None)
    monkeypatch.setattr(contextualise, "contextualise", lambda message, history=None, **kw: seen.setdefault("ctx", kw) and info or info)
    monkeypatch.setattr(triage, "classify", lambda message, **kw: seen.setdefault("triage", kw) and {"route": "in_scope", "reply": "", "error": None, "usage": triage._empty_usage(), "model": "m", "prompt": "p", "prompt_sha256": "h", "seconds": 0.0} or {})

    def fake_run_agent(question, shared, cfg=None, *, save_trace, audit, on_event=None):
        seen["cfg"] = cfg
        on_event({"type": "node_started", "node": "plan_research"})
        return {**agent_result(question), "usage": {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "llm_seconds": 0.0}, "trace": []}

    monkeypatch.setattr(graph, "run_agent", fake_run_agent)
    events = []
    runner = served.make_runner(served.shipped_config(), triage_prompt="triage_v2", contextualise_prompt="contextualise_v2", save_trace=False)
    result = runner("q", SimpleNamespace(), emit=events.append)
    assert seen["triage"] == {"prompt": "triage_v2"} and seen["ctx"] == {"prompt": "contextualise_v2"} and seen["cfg"].planner_mode == "tools"
    assert [(e["type"], e.get("stage") or e.get("node"), e.get("state")) for e in events] == [
        ("stage", "contextualise", "running"), ("stage", "contextualise", "done"), ("stage", "triage", "running"), ("stage", "triage", "done"), ("node_started", "plan_research", None)]
    assert result["outcome"] == "answered"
