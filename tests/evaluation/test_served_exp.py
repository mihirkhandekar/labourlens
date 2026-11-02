"""Offline served-chain tests: stub provider and MCP, no key or corpus required."""
import json
from collections import deque
from types import SimpleNamespace

import pytest

from labourlens import paths
from labourlens.agent import graph, smalltalk
from labourlens.agent.graph import AgentConfig
from labourlens.answer import llm
from labourlens.evaluation import served_exp as sx


def case(question="What was resident unemployment last year?", **extra):
    return {"case_id": "S-1", "question": question, "family": "factual_lookup", "expected_behavior": "answer",
            "evidence_text": [], "evidence_data": [], "reference_facts": [], "calculation": None, **extra}


def result():
    return {"run_id": "stub", "answer": {"status": "answered", "summary": "A result.", "claims": [], "caveats": [],
                                         "reason": "", "clarification_question": ""},
            "question": "question", "outcome": "answered", "trace": [], "errors": [], "rounds": 1, "tool_calls": 1,
            "evidence": [], "evidence_text": {}, "cited_ids": [], "seconds": .01,
            "usage": {"cost_usd": .001, "calls": 1, "prompt_tokens": 3, "completion_tokens": 2, "llm_seconds": .01}}


class StubMCP:
    def __init__(self, events):
        self.events, self.calls = events, deque()

    def query(self, *args, **kwargs):
        self.events.append("mcp")
        self.calls.append({"ok": False, "attempt": 0})
        self.calls.append({"ok": True, "attempt": 1})
        return [{"observation_id": "o1", "period": "2025-Q1", "unit": "percent", "value": 2.0}], None


def install(monkeypatch, route="in_scope"):
    events = []
    original = smalltalk.run_smalltalk

    def quick(*args, **kwargs):
        events.append("smalltalk")
        return original(*args, **kwargs)

    def chat(model, messages, **kwargs):
        step = kwargs["schema_name"]
        events.append(step)
        content = {"question": "What was resident unemployment in 2025?"} if step == "contextualise" else {
            "route": route, "reply": "Please ask about labour statistics." if route != "in_scope" else ""}
        return SimpleNamespace(content=json.dumps(content), refusal=None, prompt_tokens=10, completion_tokens=5, seconds=.01)

    def agent(question, shared, config, **kwargs):
        events.append("agent")
        shared.stats_backend.query("resident_unemployment_rate", "2025-Q1", "2025-Q1")
        return result()

    monkeypatch.setattr(smalltalk, "run_smalltalk", quick)
    monkeypatch.setattr(llm, "chat", chat)
    monkeypatch.setattr(graph, "run_agent", agent)
    backend = StubMCP(events)
    shared = SimpleNamespace(stats_backend=sx.RecordingBackend(backend), corpus={})
    return events, shared


def test_actual_web_step_order_and_mcp_attempts(monkeypatch):
    events, shared = install(monkeypatch)
    row = sx.evaluate_case(case(), shared, AgentConfig())
    assert events == ["smalltalk", "contextualise", "triage", "agent", "mcp"]
    assert row["served"]["mcp_calls"] == 2
    assert row["served"]["mcp_errors"] == 1
    assert row["served"]["statistics_calls"][0]["rows"][0]["value"] == 2.0
    assert row["served"]["steps"]["triage"]["cost_usd"] > 0
    assert row["served"]["steps"]["agent"]["cost_usd"] == .001
    assert row["usage"]["cost_usd"] > .001
    assert not sx.score_case(case(), row)["false_diversion"]


@pytest.mark.parametrize("question,route,expected", [("hi", "in_scope", ["smalltalk"]),
    ("What was resident unemployment last year?", "out_of_scope", ["smalltalk", "contextualise", "triage"])])
def test_diversion_denominator_is_answerable_gold(monkeypatch, question, route, expected):
    events, shared = install(monkeypatch, route)
    c = case(question)
    row = sx.evaluate_case(c, shared, AgentConfig())
    score = sx.score_case(c, row)
    assert events == expected
    assert score["false_diversion"]
    metrics = sx.aggregate([score])
    assert metrics["false_diversion_rate"] == 1
    probe = sx.score_case({**c, "not_part_of_gold": True, "expected_behavior": "clarify"}, row)
    assert not probe["false_diversion"]
    assert sx.aggregate([probe])["false_diversion_rate"] is None


def test_web_off_skips_all_front_steps(monkeypatch):
    events, shared = install(monkeypatch)
    row = sx.evaluate_case(case(), shared, AgentConfig(), web_steps=False)
    assert events == ["agent", "mcp"]
    assert not row["served"]["steps"]["triage"]["executed"]
    assert row["served"]["steps"]["contextualise"]["seconds"] >= 0


@pytest.mark.parametrize("existing", ["data", "experiments"])
def test_id_collision_raises_before_loading_or_spending(monkeypatch, tmp_path, existing):
    monkeypatch.setattr(paths, "DATA", tmp_path / "data")
    monkeypatch.setattr(paths, "EXPERIMENTS", tmp_path / "experiments")
    (tmp_path / existing / "runs/served-dev-collision").mkdir(parents=True)
    monkeypatch.setattr(sx, "load_cases", lambda *args: pytest.fail("collision must be checked first"))
    with pytest.raises(FileExistsError):
        sx.run(tag="collision")


def test_selection_rejects_unknown_duplicate_and_empty():
    with pytest.raises(ValueError):
        sx.select_cases([case()], case_ids=["missing"])
    with pytest.raises(ValueError):
        sx.select_cases([case(), case()])
    with pytest.raises(ValueError):
        sx.select_cases([], limit=0)


def test_statistics_parity_uses_same_case_and_arguments(tmp_path):
    def write(name, value, source="source"):
        path = tmp_path / name
        path.write_text(json.dumps({"case_id": "S-1", "served": {"statistics_calls": [
            {"arguments": {"source_id": source}, "rows": [{"observation_id": "o", "value": value}], "error": None}]}}) + "\n")
        return path
    left = write("left.jsonl", 2)
    assert sx.compare_statistics(left, write("right.jsonl", 2))["verdict"] == "pass"
    assert sx.compare_statistics(left, write("different.jsonl", 3))["verdict"] == "fail"
    assert sx.compare_statistics(left, write("unmatched.jsonl", 2, "other"))["verdict"] == "unevaluable"


def test_cli_options_forward_without_paid_calls(monkeypatch):
    from labourlens.cli import main
    captured = []
    monkeypatch.setattr(sx, "run", lambda *args: captured.append(args))
    assert main(["served-exp", "--tag", "sample", "--pairs", "gpt-6-luna", "gpt-5.6-luna",
                 "--route", "direct", "--web-steps", "off", "--limit", "2", "--case-ids", "DEV-001"]) == 0
    assert captured == [("dev", None, ["gpt-6-luna", "gpt-5.6-luna"], "sample", "r3", "direct", "off", 2, ["DEV-001"])]


def test_fin_comparison_uses_gold_subset_and_no_match_is_not_pass(tmp_path):
    candidate, baseline = tmp_path / "served.jsonl", tmp_path / "fin.jsonl"
    candidate.write_text(json.dumps({"case_id": "a", "behavior_ok": True, "is_probe": False, "false_diversion": False}) + "\n"
                         + json.dumps({"case_id": "probe", "behavior_ok": False, "is_probe": True}) + "\n")
    baseline.write_text(json.dumps({"case_id": "a", "behavior_ok": True}) + "\n"
                        + json.dumps({"case_id": "unused", "behavior_ok": False}) + "\n")
    assert sx.compare_fin(candidate, baseline)["verdict"] == "pass"
    assert sx.compare_fin(candidate, baseline)["n"] == 1
    baseline.write_text("")
    assert sx.compare_fin(candidate, baseline)["verdict"] == "unevaluable"


def test_registered_sample_is_reproducible_and_gold_labels_unchanged():
    from collections import defaultdict
    import random
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    gold = [json.loads(line) for line in (root / "experiments/gold/gold_v3.7.jsonl").read_text().splitlines()]
    dev = [c for c in gold if c["split"] == "dev"]
    assert len(dev) == 237
    families = defaultdict(list)
    for c in dev:
        families[c["family"]].append(c)
    allocation = {f: 51 * len(rows) // 237 for f, rows in families.items()}
    remainder = sorted(families, key=lambda f: (-(51 * len(families[f]) % 237), f))
    for f in remainder[:51 - sum(allocation.values())]:
        allocation[f] += 1
    rng = random.Random(20261102)
    selected = []
    for f in sorted(families):
        selected.extend(rng.sample(sorted(families[f], key=lambda c: c["case_id"]), allocation[f]))
    selected.sort(key=lambda c: c["case_id"])
    fixture = root / "experiments/served"
    registered = [json.loads(line) for line in (fixture / "gold-sample.jsonl").read_text().splitlines()]
    probes = [json.loads(line) for line in (fixture / "probes.jsonl").read_text().splitlines()]
    mixed = [json.loads(line) for line in (fixture / "mixed-sample.jsonl").read_text().splitlines()]
    assert registered == selected
    assert len(probes) == 14 and all(p["not_part_of_gold"] for p in probes)
    assert mixed == registered + probes and len(mixed) == 65


def test_unlogged_mcp_timeout_is_counted_without_changing_failure():
    class TimeoutBackend:
        calls = deque()
        def query(self, *args, **kwargs):
            raise TimeoutError("stub")

    recorder = sx.RecordingBackend(TimeoutBackend())
    with pytest.raises(TimeoutError):
        recorder.query("source", "2025-Q1", "2025-Q1")
    assert len(recorder.unlogged_failures) == 1
    assert recorder.unlogged_failures[0]["ok"] is False
    assert recorder.records[0]["error"] == "TimeoutError"
