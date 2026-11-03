"""Offline HTTP and frozen-run adapter tests. Never uses a real key or network."""
import json

import httpx
import pytest

from labourlens.agent import decisions as d
from labourlens.evaluation import decisions_exp as exp


def question(kind="choice"):
    q = {"type": kind, "name": "q", "instructions": "classify"}
    if kind == "choice":
        q["choices"] = [{"value": r, "description": r} for r in ("in_scope", "out_of_scope")]
    return {"model": d.MODEL, "input": "untrusted", "questions": [q]}


def response(kind="choice"):
    answer = {"name": "q", "type": kind}
    answer.update({"choice": "out_of_scope", "confidence": 0.7, "probabilities": [
        {"value": "in_scope", "probability": 0.2}, {"value": "out_of_scope", "probability": 0.8}]} if kind == "choice" else {"probability": 0.5})
    return {"answers": [answer], "usage": {"input_tokens": 100, "output_tokens": 2}}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-secret")
    return d.Client(d.Budget(tmp_path / "budget.json"))


def test_choice_and_billing(client):
    client.post = lambda body, timeout: httpx.Response(200, json=response())
    result = client.call(question())
    assert result["choice"] == "out_of_scope" and result["confidence"] == 0.7
    assert result["attempts"] == 1 and result["error"] is None
    assert result["usage"]["cost_usd"] == pytest.approx(0.00001)
    assert json.loads(client.budget.path.read_text())["charged_usd"] == pytest.approx(0.00001)
    assert "fake-secret" not in json.dumps(result)


@pytest.mark.parametrize("status,retries", [(429, 2), (500, 2), (599, 2), (400, 1), (401, 1)])
def test_retry_policy(client, monkeypatch, status, retries):
    monkeypatch.setattr(d.time, "sleep", lambda _: None)
    client.post = lambda body, timeout: httpx.Response(status, text="fake-secret provider passage")
    r = client.call(question())
    assert r["attempts"] == retries
    assert r["error"] == f"http_{status}"
    assert r["usage"]["cost_usd"] is None
    assert "provider passage" not in json.dumps(r)


def test_timeout_no_retry(client):
    def fail(*args):
        raise httpx.ReadTimeout("fake-secret")
    client.post = fail
    r = client.call(question())
    assert r["attempts"] == 1 and r["error"] == "transport_timeout"
    assert r["usage"]["cost_usd"] is None


@pytest.mark.parametrize("value", [-0.1, 1.1, float("nan"), float("inf"), True, "0.5"])
def test_invalid_probabilities(value):
    raw = response("predicate")
    raw["answers"][0]["probability"] = value
    with pytest.raises(d.DecisionError):
        d.parse_answer(raw, question("predicate")["questions"][0])


def test_refusal_and_bad_distribution(client):
    raw = response()
    raw["answers"][0] = {"type": "refusal", "name": "q", "refusal": "secret"}
    client.post = lambda *args: httpx.Response(200, json=raw)
    assert client.call(question())["error"] == "refusal"
    raw = response()
    raw["answers"][0]["probabilities"][0]["value"] = "out_of_scope"
    with pytest.raises(d.DecisionError):
        d.parse_answer(raw, question()["questions"][0])


def test_cache_rates_and_unknown_write():
    raw = response()
    raw["usage"]["input_tokens_details"] = {"cached_tokens": 80}
    assert d.usage_info(raw)["cost_usd"] == pytest.approx((20 * .1 + 80 * .01) / 1e6)
    raw["usage"]["input_tokens_details"] = {"cache_write_tokens": 80}
    assert d.usage_info(raw)["cost_usd"] is None


def test_shared_budget_and_ambiguous_reservation(tmp_path):
    a = d.Budget(tmp_path / "budget.json", maximum=0.002)
    b = d.Budget(a.path, maximum=0.002)
    a.reserve(question())
    with pytest.raises(d.BudgetExceeded):
        b.reserve(question())
    assert json.loads(a.path.read_text())["charged_usd"] > 0


def test_unknown_write_stops(client):
    raw = response()
    raw["usage"]["input_tokens_details"] = {"cache_write_tokens": 10}
    client.post = lambda *args: httpx.Response(200, json=raw)
    assert client.call(question())["error"] == "unknown_cost_stop"


def test_confidence_separate_from_max_probability(client):
    raw = response()
    raw["answers"][0]["confidence"] = 0.69
    client.post = lambda *args: httpx.Response(200, json=raw)
    case = {"case_id": "x", "skipped": False}
    r = exp.classify(client, question(), case)
    assert r["route"] == "out_of_scope" and r["route70"] == "in_scope"
    raw["answers"][0]["confidence"] = 0.70
    assert exp.classify(client, question(), case)["route70"] == "out_of_scope"


def test_no_key_fails_open(client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY")
    r = exp.classify(client, question(), {"skipped": False})
    assert r["route"] == r["route70"] == "in_scope"
    assert r["attempts"] == 0 and r["error"] == "missing_api_key"


def test_skip_no_call(client):
    client.post = lambda *args: pytest.fail("must skip")
    assert exp.classify(client, question(), {"skipped": True})["attempts"] == 0


def test_dry_run_and_immutability(tmp_path, monkeypatch):
    monkeypatch.setattr(exp.paths, "EXPERIMENTS", tmp_path)
    monkeypatch.setattr(exp, "prepare_triage", lambda: ([{"_input": "hello", "skipped": False}], {}))
    assert exp.run("triage", "new-id") == 0
    assert not (tmp_path / "triage/new-id").exists()
    (tmp_path / "triage/new-id").mkdir(parents=True)
    with pytest.raises(FileExistsError):
        exp.run("triage", "new-id")
    with pytest.raises(ValueError):
        exp.run("triage", "../escape")


def test_support_public_row_contains_no_input(client):
    raw = response("predicate")
    client.post = lambda *args: httpx.Response(200, json=raw)
    r = exp.classify(client, question("predicate"), {"case_id": "x", "_input": "restricted passage", "skipped": False})
    assert "restricted passage" not in json.dumps(r)
    assert r["probability"] == .5


def test_cli_guard(monkeypatch):
    from labourlens.cli import main
    calls = []
    monkeypatch.setattr(exp, "run", lambda *args: calls.append(args) or 0)
    assert main(["decisions-triage-check", "--experiment", "dry"]) == 0
    assert calls[-1] == ("triage", "dry", False)
    assert main(["decisions-support-check", "--experiment", "paid", "--yes"]) == 0
    assert calls[-1] == ("support", "paid", True)

def test_deadline_includes_provider_time(client, monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(d.time, "perf_counter", lambda: clock[0])
    def slow(*args):
        clock[0] = 8.1
        return httpx.Response(200, json=response())
    client.post = slow
    r = client.call(question())
    assert r["error"] == "deadline" and r["attempts"] == 1
    assert r["usage"]["cost_usd"] is not None


def test_malformed_usage_is_unknown_not_free(client):
    raw = response()
    raw.pop("usage")
    client.post = lambda *args: httpx.Response(200, json=raw)
    r = client.call(question())
    assert r["error"] == "invalid_usage"
    assert r["usage"]["cost_usd"] is None


def test_paid_fake_run_preserves_incomplete_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(exp.paths, "EXPERIMENTS", tmp_path)
    monkeypatch.setattr(exp, "registration_commit", lambda: "registered")
    cases = [{"case_id": str(i), "set": "gold", "repeat": 0, "skipped": False, "_input": "secret passage"} for i in range(8)]
    monkeypatch.setattr(exp, "prepare_triage", lambda: (cases, {}))
    class Fake:
        def call(self, body):
            return {"error": "shared_dollar_cap", "stop": True, "seconds": .1, "attempts": 0,
                    "usage": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0}}
    assert exp.run("triage", "fake", True, client=Fake()) == 1
    folder = tmp_path / "triage/fake"
    status = json.loads((folder / "status.json").read_text())
    assert status["completed_n"] == 6 and len(status["missing"]) == 2
    assert "secret passage" not in (folder / "raw.jsonl").read_text()

def test_frozen_route_descriptions_preserved():
    prompt = (exp.paths.ROOT / "prompts/triage_decisions_v1.md").read_text()
    original = (exp.paths.ROOT / "prompts/triage_v1.md").read_text()
    body = exp.body_for("triage", "<user_message>hello</user_message>", prompt)
    assert [c["value"] for c in body["questions"][0]["choices"]] == list(exp.triage.ROUTES)
    for c in body["questions"][0]["choices"]:
        assert c["value"] + ": " + c["description"] in original.splitlines()


def test_predicate_exact_boundary_and_invalid_name():
    raw = response("predicate")
    assert d.parse_answer(raw, question("predicate")["questions"][0])["probability"] == .5
    raw["answers"][0]["name"] = "wrong"
    with pytest.raises(d.DecisionError, match="invalid_answer_name"):
        d.parse_answer(raw, question("predicate")["questions"][0])
