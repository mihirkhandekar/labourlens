"""Deterministic synthetic comparisons; no generation or network."""
import json

import pytest

from labourlens.evaluation import fixed


def case(i):
    return {"case_id": str(i), "family": "factual_lookup", "expected_behavior": "answer", "evidence_text": [], "evidence_data": []}


def row(ok):
    return {"behavior_ok": ok, "false_answer": False, "over_abstain": not ok, "operational_failure": False,
            "seconds": 2, "cost_usd": .003, "judge_cost_usd": .001}


def test_mean_preserves_half_correct_cases_and_single_run_mcnemar():
    cases = [case(i) for i in range(4)]
    first = {str(i): row(i % 2 == 0) for i in range(4)}
    second = {str(i): row(i % 2 != 0) for i in range(4)}
    candidate = {str(i): row(True) for i in range(4)}
    result = fixed.analyse(candidate, first, second, cases, n_boot=100)
    assert result["agent_two_run_mean_comparison"]["paired_difference"] == .5
    assert result["agent_two_run_mean_comparison"]["agent_accuracy"] == .5
    assert result["agent_two_run_mean_comparison"]["mcnemar_exact_p"] is None
    assert result["agent_run_flips"] == 4
    assert result["always_answer_floor"] == 1
    assert result["arms"]["fixed"]["usage_cost_per_question_usd"] == .003
    assert result["arms"]["fixed"]["latency_p95_s"] == 2
    assert result["decision"] == "inconclusive"  # McNemar does not pass


def test_exact_case_sets_required():
    with pytest.raises(ValueError, match="case-set"):
        fixed.analyse({"0": row(True)}, {}, {}, [case(0)], n_boot=10)


def test_existing_output_refused_before_reading_inputs(tmp_path):
    out = tmp_path / "report.json"
    out.write_text("frozen")
    with pytest.raises(FileExistsError):
        fixed.run(tmp_path / "missing-gold", "candidate", out)
    assert out.read_text() == "frozen"


def test_answer_floor_includes_injection_answer_label():
    cases = [case(i) for i in range(3)]
    cases[1]["expected_behavior"] = "ignore_injection_and_answer"
    cases[2]["expected_behavior"] = "abstain"
    rows = {str(i): row(True) for i in range(3)}
    result = fixed.analyse(rows, rows, rows, cases, n_boot=20)
    assert result["always_answer_floor"] == 2 / 3
    assert result["agent_two_run_mean_comparison"]["paired_difference"] == 0
    assert result["decision"] == "inconclusive"
    json.dumps(result)


def test_preflight_checks_frozen_questions_and_corpus_before_generation(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from labourlens import paths
    from labourlens.agent.graph import AgentConfig
    from labourlens.evaluation.provenance import snapshot

    experiments, data = tmp_path / "experiments", tmp_path / "data"
    monkeypatch.setattr(paths, "EXPERIMENTS", experiments)
    monkeypatch.setattr(paths, "DATA", data)
    gold = tmp_path / "gold.jsonl"
    cases = [{**case(i), "question": f"Question {i}"} for i in range(237)]
    gold.write_text("\n".join(json.dumps(c) for c in cases))
    cfg = AgentConfig(control_flow="fixed")
    metadata = {"provenance": snapshot(cfg.key(), 237, 237, gold_path=gold)}
    corpus = {"content_sha256": "test"}
    for exp in fixed.REFERENCES:
        folder = experiments / "eval" / exp
        folder.mkdir(parents=True)
        (folder / f"{fixed.MODEL}.metrics.json").write_text(json.dumps(metadata))
        raw = data / "runs" / exp
        raw.mkdir(parents=True)
        (raw / f"{fixed.MODEL}.jsonl").write_text("\n".join(json.dumps({**c, "corpus": corpus}) for c in cases))
    assert fixed.preflight(cases, SimpleNamespace(corpus=corpus), cfg, gold)["case_count"] == 237
    with pytest.raises(ValueError, match="corpus mismatch"):
        fixed.preflight(cases, SimpleNamespace(corpus={"content_sha256": "other"}), cfg, gold)
    changed = [{**c, "question": "different"} for c in cases]
    with pytest.raises(ValueError, match="question-set mismatch"):
        fixed.preflight(changed, SimpleNamespace(corpus=corpus), cfg, gold)
