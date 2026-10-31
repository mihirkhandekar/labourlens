"""Synthetic offline regression fixtures for the public numeric report projection."""

import json
from pathlib import Path

import pytest

from labourlens.report.build import _Artifacts, _agent_trace, _experiments, _paired, _paired_corpus_v2


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


def test_error_panel_counts_only_rescored_case_files():
    stale = [{"case_id": "A", "behavior_ok": False, "valid": False, "tool_errors": 2, "tool_calls": 1, "rounds": 1, "tools_used": ["get_series"]},
             {"case_id": "B", "behavior_ok": False, "valid": True, "tool_errors": 0, "tool_calls": 1, "rounds": 1, "tools_used": []},
             {"case_id": "DROPPED", "behavior_ok": False, "valid": True, "tool_errors": 0}]
    rescored = [{"case_id": "A", "behavior_ok": True, "valid": True, "tool_errors": 0, "operational_failure": False, "ungrounded_numbers": 1},
                {"case_id": "B", "behavior_ok": False, "valid": True, "tool_errors": 1, "operational_failure": False, "ungrounded_numbers": 0}]
    orphan = [{"case_id": "A", "behavior_ok": False, "valid": True, "tool_errors": 9}]
    trace, paths, errors = _agent_trace(SyntheticArtifacts({
        "experiments/runs/agent-dev-A1/m.scores.jsonl": stale,
        "experiments/eval/agent-dev-A1/m.cases.jsonl": rescored,
        "experiments/runs/agent-dev-A2/m.scores.jsonl": orphan,  # no current case file: excluded entirely
    }))
    assert [r["case_id"] for r in trace] == ["A", "B"]
    assert errors == {"tool_errors": 1, "operational_failure": 0, "n_ungrounded_numbers": 1, "behavior_mismatch": 1}
    assert paths == ["experiments/runs/agent-dev-A1/m.scores.jsonl", "experiments/eval/agent-dev-A1/m.cases.jsonl"]


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


def test_evaluation_copy_distinguishes_postrun_gold_from_generation_freeze():
    script = (
        Path(__file__).resolve().parents[2] / "web/static/evaluation.js"
    ).read_text()
    assert "historical development plots use gold v3.2" in script
    assert "historical held-out plots use gold v3.4" in script
    assert "original generation-time v3.2 freeze" in script
    assert "after held-out execution and before human review" in script
    assert "HO-029 from refuse to ignore_injection_and_answer" in script
    assert "source passages and reference facts were added" in script
    assert "without new generation or AI judge calls" in script
    assert "not a pristine frozen-gold estimate" in script
    assert "has not been human reviewed" not in script
    assert "experiments/heldout/FREEZE.md remain unchanged" in script
    assert "experiments/heldout/paired-v3.2.txt" in script


@pytest.mark.parametrize("comparison", [
    "r3 / gpt-6-luna 0.839 → 0.839 → 0.839 → 0.871",
    "r3 / gpt-5.6-luna 0.871 → 0.839 → 0.806 → 0.839",
    "hybrid / gpt-6-luna 0.677 → 0.677 → 0.677 → 0.710",
    "hybrid / gpt-5.6-luna 0.742 → 0.710 → 0.710 → 0.742",
])
def test_evaluation_copy_preserves_gold_version_behaviour_comparison(comparison):
    script = (
        Path(__file__).resolve().parents[2] / "web/static/evaluation.js"
    ).read_text()
    assert comparison in script
    assert "gold v3.2 → v3.3 → v3.4 → v3.5 (n=31 each)" in script
    assert "three v3.4 post-run edits lower or leave scores unchanged" in script


def test_evaluation_copy_discloses_v34_edits_and_historical_paired_sensitivity():
    script = (
        Path(__file__).resolve().parents[2] / "web/static/evaluation.js"
    ).read_text()
    for disclosure in (
        "HO-027 changes from ignore_injection_and_answer to clarify",
        "question omits the year; the question is unchanged",
        "prior facts/evidence are context only",
        "HO-023 adds the non-primary cohort-definition passage",
        "mom-2026-q2-final:p053:b015:85d629c9",
        "HO-004 marks its truncated PDF passage non-primary",
        "the complete release remains primary",
        "HO-027 lowers r3 / gpt-5.6-luna behaviour accuracy by 1/31",
        "the evidence edits leave behaviour accuracy unchanged",
        "Historical v3.4 paired behaviour differences",
        "gpt-6-luna +0.161, 95% CI [0, 0.323]",
        "gpt-5.6-luna +0.097, 95% CI [-0.032, 0.226]",
        "gpt-5.6-luna interval crosses zero",
        "experiments/heldout/paired-v3.3.txt",
        "clean preregistered rerun on frozen, human-reviewed gold",
        "it has not been run",
        "Historical held-out · gold v3.4 · post-run adjudication",
        "Historical development · gold v3.2",
    ):
        assert disclosure in script
    assert "paired behaviour differences are unchanged" not in script
    assert "not newly corrected gold or rerun metrics" not in script


def test_evaluation_copy_distinguishes_owner_review_from_historical_scores():
    script = (
        Path(__file__).resolve().parents[2] / "web/static/evaluation.js"
    ).read_text()
    for disclosure in (
        "owner review complete 31 Oct 2026: 125 cards decided by the owner "
        "(30 own verdicts, 95 by agreeing per card with AI suggestions or the "
        "three-pass AI tie-break), not independent inter-rater evidence",
        "45 gold cases, 40 answers, 30 source checks and 10 decisions",
        "45 are owner-reviewed and 223 remain AI-drafted",
        "25 correct, 6 partly correct and 9 incorrect",
        "19 matches and 11 minor issues",
        "HO-022 clarify → answer",
        "DEV-018 refuse → clarify",
        "private export proposed DEV-018 refuse → refuse",
        "chat takes precedence",
        "Every evidence ID is preserved",
        "Development A1–A5 v3.5 rescoring is complete",
        "commit the resulting artifacts and rebuild the report",
        "Held-out v3.5 rescoring is complete for all four registered configurations",
        "stale judge entries were rejudged against the current gold without new generation",
        "all four configurations gain 1/31",
        "awaiting a regenerated snapshot",
        "A3 behaviour accuracy 0.903",
        "A5 0.911 and 0.916",
        "small gains of 0.008 and 0.013 are inconclusive",
        "v3.5 rescore complete; snapshot rebuild pending",
        "gold v3.5 · post-run owner adjudication",
        "every(usesGoldV35)",
        "row.scoring_provenance?.gold_sha256 === GOLD_V35_SHA256",
        "aac4b405b51c7cebf019c3b3629509ecb711be32fb830a8e78c4c7b902219e09",
        "Current v3.5 paired behaviour differences",
        "10000 case-bootstrap resamples, seed 20261030",
        "6 better / 1 worse",
        "4 better / 1 worse",
        "experiments/heldout/paired-v3.4.txt",
        "Historical second blind independent AI review",
        "preserved separately from the later owner verdicts",
    ):
        assert disclosure in script
    assert "unreviewed AI gold" not in script
    assert "Current v3.4" not in script
    assert "Held-out v3.5 rescoring remains pending" not in script
    assert "no held-out v3.5 scores are claimed" not in script


def test_paired_projection_preserves_v35_and_all_historical_gold_versions():
    paths = [
        "experiments/heldout/paired.txt",
        "experiments/heldout/paired-v3.4.txt",
        "experiments/heldout/paired-v3.3.txt",
        "experiments/heldout/paired-v3.2.txt",
    ]
    text = (
        "n=31, 10000 case-bootstrap resamples, seed 20261030\n"
        "gpt-6-luna diff 0.161 95% CI [0.000, 0.323] better 6 worse 1\n"
        "gpt-5.6-luna diff 0.097 95% CI [-0.032, 0.226] better 4 worse 1\n"
    )
    assert all(_Artifacts._allowed(path) for path in paths)
    entries = _paired(SyntheticArtifacts(dict.fromkeys(paths, text)))
    assert [entry["gold_version"] for entry in entries] == ["v3.5", "v3.4", "v3.3", "v3.2"]
    assert [entry["provenance"] for entry in entries] == [[path] for path in paths]
    for entry in entries:
        assert (entry["n"], entry["resamples"], entry["seed"]) == (31, 10000, 20261030)
        assert entry["models"]["gpt-6-luna"] == {
            "diff": 0.161, "ci95": [0.0, 0.323], "better": 6, "worse": 1,
        }
        assert entry["models"]["gpt-5.6-luna"] == {
            "diff": 0.097, "ci95": [-0.032, 0.226], "better": 4, "worse": 1,
        }


@pytest.mark.parametrize("path", [
    "experiments/eval/agent-dev-X1/gpt-6-luna.metrics.json",
    "experiments/eval/agent-dev-X1/gpt-5.6-luna.cases.jsonl",
    "experiments/eval/agent-heldout-X-r3/gpt-6-luna.metrics.json",
    "experiments/eval/agent-heldout-X-hybrid/gpt-5.6-luna.cases.jsonl",
    "experiments/runs/extraction-v2-X1/dev-R-summary.json",
    "experiments/heldout/paired-corpus-v2.txt",
])
def test_corpus_v2_artifacts_are_allowlisted(path):
    assert _Artifacts._allowed(path)


@pytest.mark.parametrize("path", [
    "experiments/eval/agent-dev-X1/gpt-4.1-mini.metrics.json",
    "experiments/eval/agent-heldout-X-r3/gpt-4.1-mini.metrics.json",
    "experiments/eval/agent-heldout-X-hybrid/gpt-4.1-mini.cases.jsonl",
    "experiments/eval/agent-dev-X1/gpt-6-luna.judgements.json",
    "experiments/eval/agent-heldout-X-other/gpt-6-luna.metrics.json",
    "experiments/runs/agent-heldout-X-r3/gpt-6-luna.scores.jsonl",
])
def test_corpus_v2_excludes_mini_judgements_and_raw_runs(path):
    assert not _Artifacts._allowed(path)


def test_rows_carry_explicit_corpus_version_labels():
    v1 = "experiments/eval/agent-heldout-H-r3/gpt-6-luna.metrics.json"
    v2 = "experiments/eval/agent-heldout-X-r3/gpt-6-luna.metrics.json"
    rows, _ = _experiments(SyntheticArtifacts({
        v1: {"metrics": {"n_cases": 31}}, v2: {"metrics": {"n_cases": 31}},
    }), "experiments/eval/")
    by_id = {row["id"]: row for row in rows}
    assert by_id[v1.removesuffix(".metrics.json")]["corpus_version"] == "v1"
    assert "gold_version" not in by_id[v1.removesuffix(".metrics.json")]
    row = by_id[v2.removesuffix(".metrics.json")]
    assert row["corpus_version"] == "v2"
    assert row["gold_version"].startswith("v3.6")


def test_ladder_labels_v1_and_v2_separately():
    from labourlens.report.build import _ladder
    v1 = "experiments/runs/dev-R-summary.json"
    v2 = "experiments/runs/extraction-v2-X1/dev-R-summary.json"
    artifacts = SyntheticArtifacts({
        v1: {"n_cases": 128, "metrics": {"R3": {"hit_at_8": 0.969}}},
        v2: {"n_cases": 128, "metrics": {"R3": {"hit_at_8": 0.953}}},
    })
    first, second = _ladder(artifacts), _ladder(artifacts, v2)
    assert (first["corpus_version"], second["corpus_version"]) == ("v1", "v2")
    assert first["provenance"] == [v1] and second["provenance"] == [v2]
    assert second["configs"]["R3"]["hit_at_8"] == 0.953


def test_paired_corpus_v2_is_a_separate_diagnostic_never_mixed_with_registered_entries():
    v2 = "experiments/heldout/paired-corpus-v2.txt"
    v1 = "experiments/heldout/paired.txt"
    body = (
        "n=31, 10000 case-bootstrap resamples, seed 20261030, GOLD {gold}\n"
        "gpt-6-luna diff 0.065 95% CI [-0.065, 0.194] better 3 worse 1\n"
        "gpt-5.6-luna diff 0.097 95% CI [-0.032, 0.226] better 4 worse 1\n"
    )
    artifacts = SyntheticArtifacts({v2: body.format(gold="v3.6"), v1: body.format(gold="v3.5")})
    registered = _paired(artifacts)
    assert [(e["corpus_version"], e["gold_version"]) for e in registered] == [("v1", "v3.5")]
    assert all("diagnostic" not in e and v2 not in e["provenance"] for e in registered)
    diagnostic = _paired_corpus_v2(artifacts)
    assert (diagnostic["corpus_version"], diagnostic["gold_version"]) == ("v2", "v3.6")
    assert diagnostic["diagnostic"] is True and diagnostic["provenance"] == [v2]
    assert _paired_corpus_v2(SyntheticArtifacts({v1: body.format(gold="v3.5")})) is None


def test_evaluation_copy_reports_corpus_v2_with_overlapping_intervals_and_no_gain():
    script = (Path(__file__).resolve().parents[2] / "web/static/evaluation.js").read_text()
    for text in (
        "reported beside, never over, the frozen corpus-v1 results",
        "gold v3.6 migrates retrieval evidence IDs only, with no label change",
        "no measurable quality change or gain",
        "diagnostic, not new held-out evidence",
        "gpt-6-luna +0.065, 95% CI [-0.065, 0.194], 3 better / 1 worse",
        "r3 remains the provisional default",
        "corpus v2 · gold v3.6 evidence-ID migration only",
    ):
        assert text in script


@pytest.mark.parametrize("path", [
    "experiments/eval/agent-dev-X2/gpt-6-luna.metrics.json",
    "experiments/eval/agent-dev-X2/gpt-5.6-luna.cases.jsonl",
    "experiments/threats/m7-e2efix-20261031/runs/gpt-6-luna.metrics.json",
    "experiments/threats/m7-e2efix-20261031/runs/gpt-5.6-luna+naive.metrics.json",
    "experiments/threats/m7-e2efix-20261031/SUMMARY.md",
])
def test_x2_and_e2efix_artifacts_are_allowlisted(path):
    assert _Artifacts._allowed(path)


@pytest.mark.parametrize("path", [
    "experiments/eval/agent-dev-X2/gpt-6-luna.judgements.json",
    "experiments/eval/agent-dev-X2/gpt-4.1-mini.metrics.json",
    "experiments/eval/agent-dev-X2-REPORT.md",
    "experiments/runs/agent-dev-X2/gpt-6-luna.scores.jsonl",
    "experiments/threats/m7-e2efix-20261031/runs/gpt-6-luna.verdicts.jsonl",
    "experiments/threats/m7-e2efix-20261031/runs/gpt-4.1-mini.metrics.json",
])
def test_x2_and_e2efix_raw_verdicts_judgements_and_extras_stay_private(path):
    assert not _Artifacts._allowed(path)


def test_x2_rows_are_labelled_v3_regression_check_and_never_v1():
    from labourlens.report.build import _x2_check
    x2 = "experiments/eval/agent-dev-X2/gpt-6-luna.metrics.json"
    a3 = "experiments/eval/agent-dev-A3/gpt-6-luna.metrics.json"
    rows, _ = _experiments(SyntheticArtifacts({x2: {"metrics": {"n_cases": 237}}, a3: {"metrics": {"n_cases": 237}}}), "experiments/eval/")
    by_id = {row["id"]: row for row in rows}
    row = by_id[x2.removesuffix(".metrics.json")]
    assert (row["corpus_version"], row["gold_version"], row["split"]) == ("v3", "v3.6", "dev")
    assert row["regression_check"] is True and row["crosscheck"] is True
    registered = by_id[a3.removesuffix(".metrics.json")]
    assert registered["corpus_version"] == "v1" and "regression_check" not in registered
    check = _x2_check([row])
    assert check["ablation"] is False and check["regression_check"] is True and check["row_ids"] == [row["id"]]
    assert _x2_check([]) is None


def test_e2efix_rows_are_a_separate_labelled_threat_run():
    from labourlens.report.build import _e2efix
    base = "experiments/threats/m7-e2efix-20261031/runs/"
    files = {base + "gpt-6-luna.metrics.json": {"model": "gpt-6-luna", "experiment": "m7-e2efix-20261031", "n_scored": 36, "passed": 36,
                                                 "by_category": {"direct_injection": {"n": 6, "passed": 6}}},
             base + "gpt-5.6-luna+naive.metrics.json": {"model": "gpt-5.6-luna+naive", "n_scored": 36, "passed": 35}}
    rows, paths = _experiments(SyntheticArtifacts(files), base)
    assert {row["label"] for row in rows} == {"gpt-6-luna", "gpt-5.6-luna+naive"}
    assert all(row["experiment"] == "m7-e2efix-20261031" and row["corpus_version"] == "v3" and row["crosscheck"] for row in rows)
    assert all(row["id"].startswith(base) for row in rows)
    block = _e2efix(rows)
    assert block["experiment"] == "m7-e2efix-20261031" and block["corpus_version"] == "v3" and block["provenance"] == sorted(paths)
    # Registered threat rows are read from a different prefix and never include the run.
    registered, _ = _experiments(SyntheticArtifacts(files), "experiments/threats/runs/")
    assert registered == []


SITE = Path(__file__).resolve().parents[2] / "web/static"


def _site_text(*names):
    return "".join((SITE / name).read_text() for name in names)


def test_site_reports_x2_and_e2efix_with_required_labels():
    evaluation = _site_text("evaluation.js", "presentation/ch5-evaluation.js")
    for text in (
        "regression check of the served system, not an ablation",
        "did not move beyond overlapping intervals",
        "for gpt-5.6-luna the X2 and A3 intervals do not overlap",
        "change in measurement as well as possibly in behaviour",
        "no held-out or evidence-disjoint evaluation",
        "corpus v3 · gold v3.6",
    ):
        assert text in evaluation
    safety = _site_text("evaluation.js", "presentation/ch6-safety.js")
    for text in (
        "T-I06 is not shown stable",
        "disclosed the planted figure in a caveat",
        "The scorer was not changed after seeing",
        "brittleness",
        "m7-e2efix-20261031",
    ):
        assert text in safety
    work = _site_text("presentation/ch-work.js")
    assert "id: 'X2'" in work and "id: 'T-e2efix'" in work and "m.e2efixRow(" in work
    model = _site_text("presentation/model.js")
    assert "e2efixRow" in model and "section('security').e2efix" in model


def test_site_states_current_serving_fact_and_drops_stale_corpus_claims():
    text = _site_text("presentation/ch-work.js", "presentation/ch8-limits.js", "presentation/index.js", "js/home.js")
    for stale in ("No experiment has run on v3", "no experiment has run on it", "No experiment has run on v3.", "no experiment has run on v3"):
        assert stale not in text
    for fact in ("c297146", "d402120f6f8f", "16,419 passages", "1,847 chunks"):
        assert fact in text
    assert "two measured evaluations" in text


def test_site_does_not_hand_type_stale_nearest_rank_p95_values():
    text = _site_text("evaluation.js", "presentation/ch5-evaluation.js", "presentation/ch-work.js", "presentation/index.js")
    for stale in ("35.6 s", "34.4 s", "37.5 s", "26.6 s", "43.3 s"):
        assert stale not in text
