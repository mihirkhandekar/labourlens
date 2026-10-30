"""Synthetic offline regression fixtures for the public numeric report projection."""

import json
from pathlib import Path

import pytest

from labourlens.report.build import _Artifacts, _experiments


class SyntheticArtifacts:
    def __init__(self, files):
        self.files = files
        self.paths = sorted(files)

    def mapping(self, path):
        value = self.load(path)
        return value if isinstance(value, dict) else {}

    def load(self, path):
        return self.files.get(path)


@pytest.mark.parametrize("n_cases", [7, 61])
def test_evaluation_projects_current_counts_intervals_and_strata(n_cases):
    path = "experiments/eval/synthetic-run/synthetic-model.metrics.json"
    cases_path = path.removesuffix(".metrics.json") + ".cases.jsonl"
    artifacts = SyntheticArtifacts({
        path: {
            "label": "synthetic-model",
            "judge": "synthetic-judge",
            "metrics": {
                "n_cases": n_cases,
                "behaviour_accuracy": {"rate": 0.75, "ci95": [0.4, 0.9], "n": n_cases},
                "claim_supported_rate": 0.8,
                "claims_judged": n_cases * 2,
                "fact_coverage": 0.5,
                "cost_per_case_usd": 0.0012,
                "latency_p50_s": 2.5,
                "raw_answer": "PRIVATE_ANSWER_TEXT",
            },
            "by_family": {
                "factual_lookup": {"n": n_cases, "behaviour_accuracy": 0.75},
            },
        },
        cases_path: [
            {"claims_supported": 1, "facts_total": 2, "judge_notes": ["PRIVATE_JUDGE_NOTES"]},
            {"claims_supported": 0, "facts_total": 3, "raw_text": "PRIVATE_PASSAGE"},
            # An unjudged response must not enlarge the reference-fact denominator.
            {"facts_total": 100},
        ],
    })

    rows, paths = _experiments(artifacts, "experiments/eval/")

    assert len(rows) == 1
    row = rows[0]
    assert row["judge"] == "synthetic-judge"
    assert row["metrics"]["n_cases"] == n_cases
    assert row["metrics"]["behaviour_accuracy"] == {
        "rate": 0.75, "ci95": [0.4, 0.9], "n": n_cases,
    }
    assert row["strata"]["factual_lookup"]["n"] == n_cases
    assert row["metrics"]["claims_judged"] == n_cases * 2
    assert row["denominators"] == {"fact_coverage": 5}
    assert set(row["provenance"]) == {path, cases_path}
    assert set(paths) == {path, cases_path}
    projected = json.dumps(row)
    for private in ("PRIVATE_ANSWER_TEXT", "PRIVATE_JUDGE_NOTES", "PRIVATE_PASSAGE"):
        assert private not in projected


def test_legacy_aggregate_without_case_file_remains_available():
    path = "experiments/eval/legacy/model.metrics.json"
    rows, paths = _experiments(SyntheticArtifacts({path: {
        "label": "model",
        "metrics": {"n_cases": 9, "fact_coverage": 0.25},
    }}), "experiments/eval/")

    assert rows[0]["metrics"]["n_cases"] == 9
    assert "denominators" not in rows[0]
    assert "judge" not in rows[0]
    assert paths == [path]


def test_security_keeps_pass_intervals_and_category_counts():
    path = "experiments/threats/runs/synthetic+naive.metrics.json"
    rows, _ = _experiments(SyntheticArtifacts({path: {
        "model": "synthetic+naive",
        "n_cases": 11,
        "n_scored": 10,
        "passed": 8,
        "pass_rate": 0.8,
        "pass_rate_ci95": [0.5, 0.95],
        "by_category": {"direct_injection": {"n": 10, "passed": 8, "not_exercised": 1}},
    }}), "experiments/threats/runs/")

    assert rows[0]["metrics"]["pass_rate_ci95"] == [0.5, 0.95]
    assert rows[0]["metrics"]["n_scored"] == 10
    assert rows[0]["strata"]["direct_injection"] == {
        "n": 10, "passed": 8, "not_exercised": 1,
    }


def test_artifact_reader_uses_commit_snapshot_not_working_tree(monkeypatch, tmp_path):
    path = "experiments/eval/agent-dev-A3/model.metrics.json"
    working = tmp_path / path
    working.parent.mkdir(parents=True)
    working.write_text('{"metrics": {"n_cases": 999}}')
    snapshot = {"commit": "first", "count": 5}
    calls = []

    def git(self, *args):
        calls.append(args)
        if args == ("rev-parse", "HEAD"):
            return snapshot["commit"].encode()
        if args[0] == "ls-files":
            return (path + "\0").encode()
        assert args == ("show", f'{snapshot["commit"]}:{path}')
        return json.dumps({"metrics": {"n_cases": snapshot["count"]}}).encode()

    monkeypatch.setattr(_Artifacts, "_git", git)
    first = _Artifacts(Path(tmp_path))
    assert first.mapping(path)["metrics"]["n_cases"] == 5
    assert first.provenance[path]["status"] == "available"
    assert len(first.provenance[path]["sha256"]) == 64
    snapshot.update(commit="second", count=17)
    second = _Artifacts(Path(tmp_path))
    assert second.mapping(path)["metrics"]["n_cases"] == 17
    assert ("show", "first:" + path) in calls
    assert ("show", "second:" + path) in calls


@pytest.mark.parametrize("retriever", ["r3", "hybrid"])
@pytest.mark.parametrize("model", ["gpt-6-luna", "gpt-5.6-luna"])
def test_registered_heldout_projection_includes_safe_fingerprints(retriever, model):
    path = f"experiments/eval/agent-heldout-H-{retriever}/{model}.metrics.json"
    source = {
        "gold_sha256": "a" * 64,
        "prompt_sha256": {"planner": "b" * 64, "answer": "c" * 64,
                          "raw_prompt": "PRIVATE_PROMPT"},
        "git_head": "d" * 40,
        "price_table_sha256": "e" * 64,
        "eligible_n": 31,
        "available_n": 30,
        "raw_answer": "PRIVATE_ANSWER",
    }
    rows, _ = _experiments(SyntheticArtifacts({path: {
        "label": model, "provenance": source,
        "metrics": {"n_cases": 30, "answers_with_ungrounded_numbers": {
            "rate": 0.1, "n": 30, "ci95": [0, 0.2],
        }},
    }}), "experiments/eval/")
    assert _Artifacts._allowed(path)
    assert _Artifacts._allowed(path.replace(".metrics.json", ".cases.jsonl"))
    assert rows[0]["split"] == "heldout"
    fingerprint = rows[0]["scoring_provenance"]
    assert fingerprint["gold_sha256"] == source["gold_sha256"]
    assert fingerprint["git_head"] == source["git_head"]
    assert fingerprint["eligible_n"] == 31
    assert fingerprint["available_n"] == 30
    assert fingerprint["prompt_sha256"] == {"planner": "b" * 64, "answer": "c" * 64}
    metrics = rows[0]["metrics"]
    assert metrics["cases_with_ungrounded_numbers"] == metrics["answers_with_ungrounded_numbers"]
    assert metrics["cases_with_ungrounded_numbers"]["n"] == metrics["n_cases"]
    assert "PRIVATE_" not in json.dumps(rows)


@pytest.mark.parametrize("path", [
    "experiments/eval/agent-heldout-H-r3/gpt-4.1-mini.metrics.json",
    "experiments/eval/agent-heldout-H-hybrid/gpt-4.1-mini.cases.jsonl",
    "experiments/eval/agent-heldout-H-other/gpt-6-luna.metrics.json",
    "experiments/eval/agent-heldout-H-r3/gpt-6-luna.raw.json",
    "experiments/runs/agent-heldout-H-r3/gpt-6-luna.scores.jsonl",
])
def test_unregistered_heldout_and_raw_runs_are_excluded(path):
    assert not _Artifacts._allowed(path)
    if path.endswith(".metrics.json"):
        rows, paths = _experiments(SyntheticArtifacts({
            path: {"metrics": {"n_cases": 31}},
        }), "experiments/eval/")
        assert rows == []
        assert paths == []
