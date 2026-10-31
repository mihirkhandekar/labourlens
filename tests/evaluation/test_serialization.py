import json
from types import SimpleNamespace

from labourlens.evaluation import harness as h


def test_run_writes_fingerprints_and_scored_population(tmp_path, monkeypatch):
    data, experiments = tmp_path / "data", tmp_path / "experiments"
    raw = data / "runs" / "test"
    raw.mkdir(parents=True)
    rec = {"case_id": "current", "question": "question", "answer": None,
           "config": "planner=model|answer=model|planner_v2|answer_v3|retrieval=r3"}
    (raw / "model.jsonl").write_text(json.dumps(rec) + "\n")
    monkeypatch.setattr(h, "paths", SimpleNamespace(DATA=data, EXPERIMENTS=experiments, ROOT=h.paths.ROOT))
    monkeypatch.setattr(h.ev, "load_cases", lambda split, path=None: [
        {"case_id": "current", "question": "question", "reference_facts": [], "expected_behavior": "abstain"},
        {"case_id": "not-run", "question": "other", "reference_facts": [], "expected_behavior": "abstain"}])
    monkeypatch.setattr(h, "case_metrics", lambda *args: {"case_id": "current"})
    monkeypatch.setattr(h, "aggregate", lambda rows: {"n_cases": len(rows)})
    monkeypatch.setattr(h, "by_family", lambda rows: {})
    h.run("test", judge=False)
    metrics = json.loads((experiments / "eval" / "test" / "model.metrics.json").read_text())
    p = metrics["provenance"]
    assert p["eligible_n"] == 1 and p["available_n"] == 2
    assert p["agent_config"] == rec["config"]
    assert p["prompt_sha256"]["planner"] and p["gold_sha256"]
    assert metrics["metric_definitions"]["answers_with_ungrounded_numbers"].endswith("all scored cases")


def test_agent_summary_uses_actual_configuration(tmp_path, monkeypatch):
    from labourlens.agent import experiments as agx

    data, experiments = tmp_path / "data", tmp_path / "experiments"
    monkeypatch.setattr(agx, "paths", SimpleNamespace(DATA=data, EXPERIMENTS=experiments))
    monkeypatch.setattr(agx.ev, "load_cases", lambda split, path=None: [{"case_id": "case", "question": "question"}])
    monkeypatch.setattr(agx, "Shared", lambda: None)
    monkeypatch.setattr(agx, "run_agent", lambda q, shared, cfg: {"config": cfg.key()})
    monkeypatch.setattr(agx, "score_run", lambda c, r: {"case_id": c["case_id"]})
    monkeypatch.setattr(agx, "aggregate", lambda scores: {"n": len(scores), **{k: 0 for k in agx.COLS}})
    agx.run(pairs=["gpt-6-luna"], answer_prompt="answer_v3", planner_prompt="planner_v2", retrieval="r3", tag="test")
    summary = (experiments / "runs" / "agent-dev-test-SUMMARY.md").read_text()
    assert "`planner_v2` and `answer_v3`; retrieval `r3`" in summary
    assert "available n=1" in summary and "gpt-6-luna=1" in summary
    score = json.loads((experiments / "runs" / "agent-dev-test" / "gpt-6-luna.scores.jsonl").read_text())
    assert score["provenance"]["agent_config"].endswith("planner_v2|answer_v3|retrieval=r3")
    assert score["provenance"]["gold_sha256"]
