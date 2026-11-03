"""Offline v2 tuning, budget, freeze and contemporaneous control tests."""
import json
from pathlib import Path

import httpx
import pytest

from labourlens.agent import decisions
from labourlens.answer import llm
from labourlens.evaluation import decisions_v2 as v2


CASE = {"case_id": "F2-001", "question": "A synthetic research question", "expected_route": "in_scope", "family": "factual", "kind": "legitimate"}


def test_dev_threshold_selection_is_safety_first():
    rows = [{**CASE, "raw_route": "out_of_scope", "confidence": .52, "error": None},
            {**CASE, "case_id": "off", "expected_route": "out_of_scope", "raw_route": "out_of_scope", "confidence": .55, "error": None}]
    low, high = v2.dev_metrics(rows, .5), v2.dev_metrics(rows, .7)
    assert low["diversions"] == 1 and high["diversions"] == 0
    assert min((low, high), key=v2.rank) == high
    assert v2.rank({**high, "threshold": .7}, 1) < v2.rank({**high, "threshold": .9}, 1)


def test_confidence_boundary_and_errors():
    row = {"raw_route": "out_of_scope", "confidence": .7, "error": None}
    assert v2.effective(row, .7) == "out_of_scope"
    assert v2.effective({**row, "error": "refusal"}, 0) == "in_scope"


def test_incremental_tuning_cap_also_charges_global(tmp_path, monkeypatch):
    monkeypatch.setattr(v2, "GLOBAL_BUDGET", tmp_path / "shared.json")
    monkeypatch.setattr(v2, "TUNE_BUDGET", tmp_path / "tune.json")
    b = v2.TuningBudget()
    r = b.reserve({"input": "test"})
    b.settle(r, {"cost_usd": .00001})
    assert json.loads(b.global_budget.path.read_text())["charged_usd"] == pytest.approx(.00001)
    assert json.loads(b.phase_budget.path.read_text())["charged_usd"] == pytest.approx(.00001)
    b.phase_budget._update(.99999)
    with pytest.raises(decisions.BudgetExceeded):
        b.reserve({"input": "test"})
    assert json.loads(b.global_budget.path.read_text())["charged_usd"] == pytest.approx(.00001)


def test_chat_control_uses_frozen_prompt_and_bounded_existing_client(tmp_path):
    seen = {}
    def fake(model, messages, **kwargs):
        seen.update(model=model, messages=messages, **kwargs)
        return llm.LLMResult(json.dumps({"route": "in_scope", "reply": ""}), 100, 10, 0, .01, attempts=1)
    r = v2.chat_call(decisions.Budget(tmp_path / "budget.json"), CASE, chat=fake)
    assert r["route"] == "in_scope" and r["error"] is None
    assert r["usage"]["complete"] and r["usage"]["cost_usd"] > 0
    assert seen["max_attempts"] == 2 and seen["retry_backoff_s"] == .5 and seen["retry_all_5xx"]
    assert seen["schema_name"] == "triage" and seen["max_completion_tokens"] == 1500
    assert "question" not in r and "messages" not in r


def test_chat_refusal_and_retry_cost_are_not_free(tmp_path):
    def fake(*args, **kwargs):
        return llm.LLMResult("", 100, 10, 0, .01, refusal="private message", attempts=2)
    r = v2.chat_call(decisions.Budget(tmp_path / "budget.json"), CASE, chat=fake)
    assert r["route"] == "in_scope" and r["error"] == "refusal"
    assert r["attempts"] == 2 and r["usage"]["cost_usd"] is None
    assert not r["usage"]["complete"] and "private message" not in json.dumps(r)


def test_chat_provider_error_redaction(tmp_path):
    def fake(*args, **kwargs):
        raise llm.LLMError("sk-private provider passage", attempts=2)
    r = v2.chat_call(decisions.Budget(tmp_path / "budget.json"), CASE, chat=fake)
    assert r["error"] == "chat_provider_error" and r["attempts"] == 2
    assert "sk-private" not in json.dumps(r) and r["usage"]["cost_usd"] is None


def test_execute_immutable_and_budget_stop(tmp_path):
    schedule = [{**CASE, "case_id": str(i), "arm": "D", "repeat": 0} for i in range(10)]
    def fake(c):
        return {k: v for k, v in {**c, "error": "shared_dollar_cap", "stop": True}.items() if k != "question"}
    out = tmp_path / "fresh"
    rr, status = v2.execute(out, {}, schedule, fake, prompt="frozen instructions")
    assert len(rr) == 6 and status["status"] == "incomplete" and len(status["missing"]) == 4
    assert (out / "prompt.md").read_text() == "frozen instructions"
    assert "research question" not in (out / "raw.jsonl").read_text()
    with pytest.raises(FileExistsError):
        v2.execute(out, {}, schedule, fake)


def test_tune_limits_and_freeze_closes_tuning(tmp_path, monkeypatch):
    monkeypatch.setattr(v2.paths, "EXPERIMENTS", tmp_path)
    selection = tmp_path / "selection.json"
    monkeypatch.setattr(v2, "SELECTION", selection)
    selection.write_text("{}")
    with pytest.raises(ValueError, match="Tuning is closed"):
        v2.tune(1, Path("unused"))
    with pytest.raises(ValueError, match="five"):
        v2.tune(6, Path("unused"))
    with pytest.raises(FileExistsError):
        v2.freeze(selection)
    with pytest.raises(ValueError):
        v2.score("../bad")


def test_new_chat_options_do_not_change_default_retry_count(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    attempts, sleeps = [], []
    monkeypatch.setattr(llm.httpx, "post", lambda *a, **k: attempts.append(1) or httpx.Response(500, text="no"))
    monkeypatch.setattr(llm.time, "sleep", sleeps.append)
    with pytest.raises(llm.LLMError) as e:
        llm.chat("gpt-6-luna", [])
    assert len(attempts) == 3 and sleeps == [1, 2, 4] and e.value.attempts == 3
    attempts.clear()
    sleeps.clear()
    with pytest.raises(llm.LLMError):
        llm.chat("gpt-6-luna", [], max_attempts=2, retry_backoff_s=.5, retry_all_5xx=True)
    assert len(attempts) == 2 and sleeps == [.5]


def test_v2_cli_is_dry_by_default(monkeypatch):
    from labourlens.cli import main
    seen = []
    monkeypatch.setattr(v2, "tune", lambda *args: seen.append(args) or 0)
    assert main(["decisions-triage-tune", "--iteration", "1", "--prompt", "p.md"]) == 0
    assert seen == [(1, Path("p.md"), False)]
