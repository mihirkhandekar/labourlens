"""Runtime fixes from the end-to-end review: run-level LLM deadline, provider-shape failures, MCP quarantine reporting."""
import json
from types import SimpleNamespace

import pandas as pd
import pytest

from labourlens.agent import graph as g
from labourlens.agent import tools as tl
from labourlens.answer import llm
from labourlens.mcp.client import _Rows


class NoSearch:
    def search(self, q, k):
        return []


def _obs(rows):
    cols = dict(source_id="retrenched_employees", indicator_id="retrenched_employees", unit="persons", population="establishments",
                adjustment="not_applicable", dimension="", release_stage="dataset_snapshot", in_answer_scope=True, missing_reason="")
    return pd.DataFrame([{**cols, "observation_id": f"obs{i}", "source_locator": f"row{i}", **r} for i, r in enumerate(rows)])


@pytest.fixture
def shared():
    return tl.Shared(world=(NoSearch(), {}, {}), observations=_obs([{"period": "2026-Q1", "value": 3830.0}, {"period": "2026-Q2", "value": 4620.0}]))


def _answer(status="abstained"):
    return json.dumps({"status": status, "summary": "", "claims": [], "caveats": [], "clarification_question": "", "reason": "x"})


def _plan(decision="gather"):
    call = dict(tool="get_series", query=None, k=None, source_id="retrenched_employees", period_from="2026-Q1", period_to="2026-Q2",
                dimension=None, adjustment=None, indicator_id="retrenched_employees", obs_a=None, obs_b=None, kind=None)
    return json.dumps({"decision": decision, "note": "n", "calls": [call] if decision == "gather" else []})


def _recording_chat(monkeypatch):
    seen = []
    plans = [_plan(), _plan("finish")]

    def chat(model, messages, max_completion_tokens=6000, extra=None, schema=None, schema_name="answer", **kwargs):
        seen.append((schema_name, kwargs))
        content = plans.pop(0) if schema_name == "plan" else _answer()
        return llm.LLMResult(content, 10, 5, 0, 0.01)

    monkeypatch.setattr(llm, "chat", chat)
    return seen


def test_run_deadline_is_passed_to_every_planner_and_answer_call(shared, monkeypatch):
    seen = _recording_chat(monkeypatch)
    r = g.run_agent("q", shared, g.AgentConfig(run_deadline_s=80.0), save_trace=False)
    assert r["outcome"] == "abstained"
    assert [name for name, _ in seen] == ["plan", "plan", "answer"]
    assert all(0 < kwargs["timeout_s"] <= 80.0 for _, kwargs in seen)
    assert [kwargs["timeout_s"] for _, kwargs in seen] == sorted((kwargs["timeout_s"] for _, kwargs in seen), reverse=True)  # budget shrinks


def test_unbounded_runs_call_chat_exactly_as_before(shared, monkeypatch):
    seen = _recording_chat(monkeypatch)
    g.run_agent("q", shared, save_trace=False)
    assert all(kwargs == {} for _, kwargs in seen)


def test_exhausted_run_deadline_stops_the_run_without_a_provider_call(shared, monkeypatch):
    async def forbidden(*a, **k):
        raise AssertionError("no provider call once the run deadline has passed")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setattr(llm, "_bounded_post", forbidden)
    r = g.run_agent("q", shared, g.AgentConfig(run_deadline_s=0.0), save_trace=False)
    assert r["outcome"] == "operational_failure"


def test_chat_retries_a_transient_status_only_while_the_deadline_allows(monkeypatch):
    replies = [SimpleNamespace(status_code=429, text="slow down"),
               SimpleNamespace(status_code=200, text="", json=lambda: {"choices": [{"message": {"content": "{}"}}], "usage": {"prompt_tokens": 1, "completion_tokens": 2}})]
    sleeps = []

    async def post(body, key, seconds):
        return replies.pop(0)

    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setattr(llm, "_bounded_post", post)
    monkeypatch.setattr(llm.time, "sleep", sleeps.append)
    assert llm.chat("m", [], timeout_s=30).content == "{}" and sleeps == [1]
    monkeypatch.setattr(llm, "_bounded_post", lambda *a: post(*a))
    replies[:] = [SimpleNamespace(status_code=429, text="slow down")]
    with pytest.raises(llm.LLMError):  # 0.5 s left: no time for the 1 s back-off
        llm.chat("m", [], timeout_s=0.5)


@pytest.mark.parametrize("body", [{}, {"choices": []}, {"choices": [{"message": {}}]}, [], {"choices": [{"message": {}}], "usage": {}}])
def test_malformed_provider_body_is_an_llm_error(monkeypatch, body):
    async def post(body_, key, seconds):
        return SimpleNamespace(status_code=200, text="", json=lambda: body)

    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setattr(llm, "_bounded_post", post)
    with pytest.raises(llm.LLMError):
        llm.chat("m", [], timeout_s=5)


@pytest.mark.parametrize("fails", ["plan", "answer"])
def test_unexpected_provider_exception_becomes_operational_failure(shared, monkeypatch, fails):
    plans = [_plan(), _plan("finish")]

    def chat(model, messages, max_completion_tokens=6000, extra=None, schema=None, schema_name="answer", **kwargs):
        if schema_name == fails:
            raise KeyError("choices")
        return llm.LLMResult(plans.pop(0) if schema_name == "plan" else _answer(), 10, 5, 0, 0.01)

    monkeypatch.setattr(llm, "chat", chat)
    assert g.run_agent("q", shared, save_trace=False)["outcome"] == "operational_failure"


def test_planner_returning_json_without_the_plan_fields_is_operational_failure(shared, monkeypatch):
    monkeypatch.setattr(llm, "chat", lambda *a, **k: llm.LLMResult("{}", 1, 1, 0, 0.01))
    assert g.run_agent("q", shared, save_trace=False)["outcome"] == "operational_failure"


def test_quarantined_mcp_rows_are_reported_as_a_service_event_not_as_missing_data(shared):
    rows, err = shared.stats.query("retrenched_employees", "2026-Q1", "2026-Q2")
    assert err is None
    shared.stats_backend = SimpleNamespace(query=lambda *a: (_Rows(rows[:1], 1), None))
    tools = tl.Tools(shared)
    result = tools.get_series("retrenched_employees", "2026-Q1", "2026-Q2")
    assert result.ok and "1 quarantined" in result.message
    notes = " ".join(tools.notes)
    assert "withheld by the MCP client" in notes and "2026-Q2" in notes
    assert "the dataset has no row" not in notes
    shared.stats_backend = SimpleNamespace(query=lambda *a: (list(rows[:1]), None))  # a plain list still reports plain absence
    plain = tl.Tools(shared)
    plain.get_series("retrenched_employees", "2026-Q1", "2026-Q2")
    assert "the dataset has no row for 2026-Q2" in " ".join(plain.notes)
