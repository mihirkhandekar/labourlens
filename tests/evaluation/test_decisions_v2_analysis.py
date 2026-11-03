"""Synthetic, offline fixtures for the immutable fresh-case analysis. No paid calls."""
import hashlib
import json
from copy import deepcopy

import pytest

from labourlens.evaluation import decisions_v2_analysis as analysis

pytestmark = pytest.mark.offline


def _dump(path, value):
    path.write_text(json.dumps(value))


def _jsonl(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


@pytest.fixture
def run(tmp_path, monkeypatch):
    # Production constants remain unchanged outside these integration-shaped tests.
    monkeypatch.setattr(analysis, "N_BOOT", 100)
    cases = []
    for i in range(150):
        expected = "in_scope" if i < 90 else analysis.ROUTES[1 + i % 3]
        cases.append({"case_id": f"F2-{i + 1:03d}", "question": f"Synthetic question {i}",
                      "expected_route": expected, "family": "adversarial" if i < 20 else "lookup",
                      "kind": "injection" if i < 20 else "borderline" if i < 40 else "ordinary",
                      "drafted_by": "AI", "review_status": "AI-labelled, not human-reviewed"})
    cases_path = tmp_path / "cases.jsonl"
    _jsonl(cases_path, cases)
    directory = tmp_path / "fresh"
    directory.mkdir()
    manifest = {"expected_n": 900, "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
                "prompt_sha256": "a" * 64, "prereg_sha256": "b" * 64, "threshold": .7,
                "selected_tuning_id": "decisions-triage-tune-1", "git_commit": "c" * 40}
    rows = []
    for repeat in range(3):
        for case in cases:
            for arm in analysis.ARMS:
                rows.append({**{key: case[key] for key in ("case_id", "expected_route", "family", "kind")},
                             "arm": arm, "repeat": repeat, "route": case["expected_route"],
                             "raw_route": case["expected_route"], "confidence": .9, "error": None,
                             "seconds": 1. if arm == "D" else 2., "attempts": 1, "skipped": False,
                             "usage": {"input_tokens": 100, "output_tokens": 0 if arm == "D" else 20,
                                       "cost_usd": .0001, "complete": True}})
    status = {"status": "complete", "scheduled_n": 900, "completed_n": 900, "reason": None}

    def save():
        _dump(directory / "manifest.json", manifest)
        _dump(directory / "status.json", status)
        _jsonl(directory / "raw.jsonl", rows)

    save()
    return {"directory": directory, "cases_path": cases_path, "cases": cases,
            "rows": rows, "manifest": manifest, "status": status, "save": save,
            "out": tmp_path / "result.json"}


def analyse(run):
    run["save"]()
    return analysis.analyse(run["directory"], run["out"], cases_path=run["cases_path"])


def select(run, arm="D", repeat=0, case_id="F2-001"):
    return next(row for row in run["rows"] if (row["arm"], row["repeat"], row["case_id"])
                == (arm, repeat, case_id))


def test_complete_immutable_result(run):
    before = (run["directory"] / "raw.jsonl").read_bytes()
    result = analyse(run)
    assert result["decision"] == "adopt_web_triage"
    assert result["complete"]
    assert all(result["adoption_guards"].values())
    assert result["arms"]["D"]["each_repeat_rules"]["0"]["exact_matches_required"] == 148
    assert result["arms"]["D"]["each_repeat_rules"]["0"]["non_in_scope_recalls_required"] == 58
    assert result["latency"]["paired_n"] == 150
    assert result["latency"]["p50_ratio"] == .5
    assert result["latency"]["p95_ratio"] == .5
    assert result["latency"]["case_cluster_bootstrap"]["p95_ratio"]["percentile_95"] == [.5, .5]
    assert result["paired_accuracy"]["case_cluster_bootstrap"]["percentile_95"] == [0., 0.]
    assert result["paired_accuracy"]["exact_mcnemar"]["both_correct"] == 150
    assert result["arms"]["D"]["operational"]["tokens"]["input_tokens"] == 45000
    assert result["arms"]["D"]["operational"]["total_cost_usd"] == pytest.approx(.045)
    assert result["arms"]["D"]["three_repeat_consistency"]["numerator"] == 150
    assert json.loads(run["out"].read_text()) == result
    assert (run["directory"] / "raw.jsonl").read_bytes() == before
    with pytest.raises(FileExistsError):
        analysis.analyse(run["directory"] / "absent", run["out"])


@pytest.mark.parametrize("case_id", ["F2-001", "F2-025", "F2-070"])
def test_every_in_scope_case_including_injection_is_safety_guard(run, case_id):
    row = select(run, case_id=case_id)
    row.update(route="out_of_scope", raw_route="out_of_scope")
    result = analyse(run)
    assert result["decision"] == "do_not_adopt"
    assert result["arms"]["D"]["each_repeat_rules"]["0"]["safety"] is False
    assert result["arms"]["D"]["each_repeat_rules"]["1"]["safety"] is True
    assert result["arms"]["D"]["pooled"]["in_scope_diversions"]["identities"] == [
        {"case_id": case_id, "repeat": 0}]


def test_quality_is_each_repeat_not_pooled(run):
    for case_id in ("F2-121", "F2-122", "F2-123"):
        row = select(run, case_id=case_id)
        wrong = "small_talk" if row["expected_route"] != "small_talk" else "out_of_scope"
        row.update(route=wrong, raw_route=wrong)
    result = analyse(run)
    assert result["decision"] == "do_not_adopt"
    assert result["adoption_guards"]["D_safety"]
    rules = result["arms"]["D"]["each_repeat_rules"]
    assert not rules["0"]["quality"]
    assert rules["1"]["quality"]
    assert result["arms"]["D"]["by_repeat"]["0"]["non_in_scope_recall"]["numerator"] == 60


def test_c_safety_and_quality_are_diagnostic_not_adoption_gates(run):
    for case_id in ("F2-001", "F2-002", "F2-003"):
        select(run, arm="C", case_id=case_id).update(route="small_talk", raw_route="small_talk")
    result = analyse(run)
    assert result["decision"] == "adopt_web_triage"
    assert not result["arms"]["C"]["safety"]
    assert not result["arms"]["C"]["quality"]
    assert result["paired_accuracy"]["D_minus_C_exact_accuracy"] == pytest.approx(3 / 450)


@pytest.mark.parametrize("arm", ["D", "C"])
@pytest.mark.parametrize("failures,passes", [(4, True), (5, False)])
def test_one_percent_operational_bar_and_failed_open_accuracy(run, arm, failures, passes):
    for row in [r for r in run["rows"] if r["arm"] == arm][:failures]:
        row.update(error="refusal", route="in_scope")
    result = analyse(run)
    operational = result["arms"][arm]["operational"]
    assert operational["passes"] is passes
    assert operational["failures_or_refusals"]["numerator"] == failures
    assert operational["operational_latency"]["n"] == 450
    assert operational["successful_latency"]["n"] == 450 - failures
    assert result["decision"] == ("adopt_web_triage" if passes else "do_not_adopt")
    assert result["arms"][arm]["pooled"]["valid_only_exact_route"]["denominator"] == 450 - failures


@pytest.mark.parametrize("mutation", ["duplicate", "unknown", "missing", "label", "stratum", "repeat", "hash", "status", "count", "threshold", "prompt", "selection", "commit"])
def test_invalid_identity_metadata_and_completion_are_inconclusive(run, mutation):
    if mutation == "duplicate":
        run["rows"][-1] = deepcopy(run["rows"][0])
    elif mutation == "unknown":
        run["rows"][0]["case_id"] = "unknown"
    elif mutation == "missing":
        run["rows"].pop()
    elif mutation == "label":
        run["rows"][0]["expected_route"] = "out_of_scope"
    elif mutation == "stratum":
        run["rows"][0]["family"] = "changed"
    elif mutation == "repeat":
        run["rows"][0]["repeat"] = 3
    elif mutation == "hash":
        run["manifest"]["cases_sha256"] = "0" * 64
    elif mutation == "status":
        run["status"]["status"] = "incomplete"
    elif mutation == "count":
        run["status"]["completed_n"] = 899
    elif mutation == "threshold":
        run["manifest"]["threshold"] = .6
    elif mutation == "prompt":
        run["manifest"].pop("prompt_sha256")
    elif mutation == "selection":
        run["manifest"]["selected_tuning_id"] = "decisions-triage-tune-6"
    elif mutation == "commit":
        run["manifest"].pop("git_commit")
    result = analyse(run)
    assert result["decision"] == "inconclusive"
    assert result["validation_issues"]
    assert not result["complete"]


def test_frozen_case_cardinality_and_provenance(run):
    run["cases"].pop()
    _jsonl(run["cases_path"], run["cases"])
    run["manifest"]["cases_sha256"] = hashlib.sha256(run["cases_path"].read_bytes()).hexdigest()
    result = analyse(run)
    assert result["decision"] == "inconclusive"
    assert "frozen cases must contain exactly 150 unique identities" in result["validation_issues"]


def test_raw_thresholded_diagnostic_and_boundary(run):
    first = select(run)
    first.update(raw_route="out_of_scope", route="in_scope", confidence=.69)
    # Exactly .70 is not failed open, so keep its matching raw route.
    select(run, case_id="F2-002")["confidence"] = .7
    result = analyse(run)
    diagnostic = result["arms"]["D"]["raw_vs_thresholded"]
    assert diagnostic["changed_routes"] == 1
    assert diagnostic["exact_match_delta_thresholded_minus_raw"] == 1
    assert diagnostic["raw"]["in_scope_diversions"]["numerator"] == 1
    assert result["decision"] == "adopt_web_triage"


def test_threshold_rule_mismatch_is_inconclusive(run):
    select(run).update(raw_route="out_of_scope", route="in_scope", confidence=.7)
    result = analyse(run)
    assert result["decision"] == "inconclusive"
    assert "effective route disagrees with frozen threshold" in result["validation_issues"]


def test_missing_raw_routes_block_adoption_and_report_unavailable(run):
    for row in run["rows"]:
        row.pop("raw_route")
    result = analyse(run)
    assert result["decision"] == "inconclusive"
    assert "invalid raw Decisions route or confidence" in result["validation_issues"]
    assert result["arms"]["D"]["raw_vs_thresholded"]["available_n"] == 0
    assert result["arms"]["D"]["raw_vs_thresholded"]["raw"]["effective_exact_route"]["value"] is None


@pytest.mark.parametrize("seconds,expected", [(1.6, "adopt_web_triage"), (1.6001, "do_not_adopt")])
def test_speed_boundary_is_inclusive(run, seconds, expected):
    for row in run["rows"]:
        if row["arm"] == "D":
            row["seconds"] = seconds
    assert analyse(run)["decision"] == expected


def test_p95_cannot_be_replaced_by_p50(run):
    for row in run["rows"]:
        if row["arm"] == "D" and int(row["case_id"].split("-")[1]) <= 10:
            row["seconds"] = 2.
    result = analyse(run)
    assert result["latency"]["p50_ratio"] == .5
    assert result["latency"]["p95_ratio"] == 1.
    assert result["decision"] == "do_not_adopt"


@pytest.mark.parametrize("seconds", [None, 0, -1])
def test_missing_or_zero_paired_latency_is_inconclusive(run, seconds):
    select(run)["seconds"] = seconds
    result = analyse(run)
    assert result["decision"] == "inconclusive"
    assert result["latency"]["paired_n"] == 149


def test_three_repeats_use_per_case_median_and_report_ties(run):
    select(run)["seconds"] = 100.
    select(run, repeat=1).update(route="small_talk", raw_route="small_talk")
    select(run, repeat=2).update(route="out_of_scope", raw_route="out_of_scope")
    result = analyse(run)
    assert result["latency"]["case_pairs"][0]["D_median_s"] == 1.
    consistency = result["arms"]["D"]["three_repeat_consistency"]
    assert consistency["numerator"] == 149
    assert consistency["route_majority_ties"] == 1
    assert consistency["case_details"][0]["majority_route"] is None
    assert result["paired_accuracy"]["exact_mcnemar"]["C_only_correct"] == 1


def test_exact_mcnemar_is_case_majority_not_repeat_level():
    pairs = [{"D_correct_n": 3, "C_correct_n": 0}] * 5 + [{"D_correct_n": 1, "C_correct_n": 3}]
    result = analysis._mcnemar(pairs)
    assert result["D_only_correct"] == 5
    assert result["C_only_correct"] == 1
    assert result["two_sided_exact_p"] == pytest.approx(14 / 64)
    assert not result["adoption_gate"]


def test_unknown_cost_is_not_zero(run):
    select(run)["usage"].update(complete=False, cost_usd=None, input_tokens=None)
    result = analyse(run)
    operational = result["arms"]["D"]["operational"]
    assert operational["total_cost_usd"] is None
    assert operational["tokens"]["input_tokens"] is None
    assert operational["complete_observed_cost"] is False


def test_bootstrap_defaults_are_preregistered():
    assert analysis.SEED == 20261103
    assert analysis.N_BOOT == 10000
    assert analysis.N_CASES == 150
    assert analysis.N_REPEATS == 3


def test_unknown_frozen_label_cannot_become_an_analysis_label(run):
    run["cases"][0]["expected_route"] = "unknown"
    _jsonl(run["cases_path"], run["cases"])
    run["manifest"]["cases_sha256"] = hashlib.sha256(run["cases_path"].read_bytes()).hexdigest()
    result = analyse(run)
    assert result["decision"] == "inconclusive"
    assert "invalid frozen case labels or provenance" in result["validation_issues"]


def test_omitted_usage_completeness_cannot_claim_known_cost(run):
    select(run)["usage"].pop("complete")
    result = analyse(run)
    assert result["arms"]["D"]["operational"]["total_cost_usd"] is None
    assert not result["arms"]["D"]["operational"]["complete_observed_cost"]


def test_default_paths_resolve_against_experiments(run, monkeypatch, tmp_path):
    monkeypatch.setattr(analysis.paths, "EXPERIMENTS", tmp_path)
    default_cases = tmp_path / "triage/fresh_cases_v2.jsonl"
    default_cases.parent.mkdir()
    default_cases.write_bytes(run["cases_path"].read_bytes())
    result = analysis.analyse(run["directory"])
    default_output = tmp_path / "eval/decisions-api-v2-results.json"
    assert result["inputs"]["cases_path"] == str(default_cases)
    assert json.loads(default_output.read_text()) == result


@pytest.mark.parametrize("misses,passes", [(2, True), (3, False)])
def test_owner_approved_absolute_two_error_allowance(run, misses, passes):
    for i in range(misses):
        row = select(run, case_id=f"F2-{121 + i:03d}")
        row.update(route="in_scope", raw_route="in_scope")
    result = analyse(run)
    assert result["arms"]["D"]["each_repeat_rules"]["0"]["quality"] is passes
    assert result["decision"] == ("adopt_web_triage" if passes else "do_not_adopt")
