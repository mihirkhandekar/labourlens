"""Offline synthetic analysis tests. No provider or restricted source dependency."""
import hashlib
import json
from copy import deepcopy

import pytest

from labourlens.evaluation import decisions_analysis as analysis

pytestmark = pytest.mark.offline


def choice(case_id, **updates):
    row = {"case_id": case_id, "set": "gold", "kind": "factual_lookup", "expected_route": "in_scope",
           "repeat": 0, "route": "in_scope", "route70": "in_scope", "confidence": .9,
           "probabilities": {route: .25 for route in analysis.ROUTES}, "error": None, "seconds": .5,
           "attempts": 1, "usage": {"input_tokens": 100, "output_tokens": 0, "cost_usd": .00001}, "skipped": False}
    return {**row, **updates}


def claim(case_id, probability=.9, label="supported", **updates):
    row = {"case_id": case_id, "model": "generator", "set": "dev", "arm": "r3", "family": "lookup",
           "claim_index": 0, "label": label, "original_label": label, "probability": probability, "error": None,
           "seconds": .2, "attempts": 1, "usage": {"input_tokens": 100, "output_tokens": 0, "cost_usd": .00001},
           "original_answer_cost_usd": .02, "second_answer_cost_usd": .04, "answer_claim_count": 1}
    return {**row, **updates}


@pytest.fixture
def frozen(tmp_path, monkeypatch):
    monkeypatch.setattr(analysis.paths, "EXPERIMENTS", tmp_path)
    # Full denominators exercise fixed adoption rules, without real experiment data.
    base = []
    for i in range(409):
        set_name = "gold" if i < 268 else "v2" if i < 333 else "threats" if i < 369 else "offtopic"
        expected = "out_of_scope" if 369 <= i < 399 else "in_scope"
        kind = "borderline_inscope" if i >= 399 else "factual_lookup"
        base.append({"case_id": f"case-{i}", "set": set_name, "kind": kind, "expected_route": expected,
                     "route": expected, "seconds": 2., "usage": {"cost_usd": .001}})
    baseline = tmp_path / "triage/triage-v1-luna/raw.jsonl"
    baseline.parent.mkdir(parents=True)
    baseline.write_text("".join(json.dumps(r) + "\n" for r in base))
    monkeypatch.setattr(analysis, "BASELINE_SHA256", hashlib.sha256(baseline.read_bytes()).hexdigest())
    labels, support = [], []
    for i in range(441):
        label = "supported" if i < 383 else "partial"
        row = claim(f"answer-{i // 2}", .9 if label == "supported" else .1, label,
                    arm="r3" if i % 2 == 0 else "hybrid")
        support.append(row)
        labels.append({**{k: row[k] for k in ("case_id", "model", "set", "arm", "family")}, "status": "valid",
                       "original": {"claims": [label]}, "second": {"claims": [label]},
                       "attempts": [{"cached": True, "status": "valid", "list_price_usd": .04}]})
    label_path = tmp_path / "xjudge/sonnet55-FIN-s60-b-20261102/labels.json"
    label_path.parent.mkdir(parents=True)
    label_path.write_text(json.dumps(labels))
    monkeypatch.setattr(analysis, "LABELS_SHA256", hashlib.sha256(label_path.read_bytes()).hexdigest())
    triage = [choice(r["case_id"], **{k: r[k] for k in ("set", "kind", "expected_route", "route")},
                     repeat=repeat, route70=r["route"]) for repeat in range(3) for r in base]
    # Reduced draws in integration-shaped tests only. Production constant is tested separately.
    monkeypatch.setattr(analysis, "N_BOOT", 100)
    return base, triage, labels, support


def write_run(folder, task, rows, status="complete"):
    folder.mkdir()
    n = 1227 if task == "triage" else 441
    (folder / "manifest.json").write_text(json.dumps({"task": task, "expected_n": n, "inputs_sha256": {"input": "hash"},
                                                       "prompt_sha256": "prompt-hash", "config": {}}))
    (folder / "status.json").write_text(json.dumps({"status": status, "reason": None, "scheduled_n": n, "completed_n": len(rows)}))
    (folder / "raw.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_full_immutable_analysis(frozen, tmp_path):
    _, triage, _, support = frozen
    a, b, out = tmp_path / "new-a", tmp_path / "new-b", tmp_path / "result.json"
    write_run(a, "triage", triage)
    write_run(b, "support", support)
    before = (a / "raw.jsonl").read_bytes()
    result = analysis.analyse(a, b, out)
    assert result["triage"]["decision"] == "candidate_for_later_integration_decision"
    assert result["support"]["decision"] == "candidate_for_further_verifier_evaluation"
    assert result["triage"]["latency"]["paired_n"] == 409
    assert result["triage"]["latency"]["median_case_ratio"] == .25
    assert result["support"]["metrics"]["primary"]["overall"]["auroc"] == 1
    assert result["support"]["metrics"]["primary"]["cluster_bootstrap"]["clusters"] == 221
    assert result["support"]["historical_judge_latency"]["available"] is False
    assert json.loads(out.read_text()) == result
    assert (a / "raw.jsonl").read_bytes() == before
    with pytest.raises(FileExistsError):
        analysis.analyse(tmp_path / "absent", tmp_path / "absent", out)


def test_per_repeat_guards_cannot_be_pooled(frozen):
    base, rows, _, _ = frozen
    row = rows[0]
    row.update(route="out_of_scope", route70="out_of_scope")
    result = analysis._triage(rows, base, [])
    assert result["decision"] == "failed_screen"
    assert result["rules"]["each_repeat"]["0"]["safe"] is False
    assert result["rules"]["each_repeat"]["1"]["safe"] is True
    assert result["arms"]["A70"]["pooled"]["legitimate_diversions"]["numerator"] == 1


def test_threat_identity_guard_not_just_count(frozen):
    base, rows, _, _ = frozen
    rows[333].update(route="small_talk", route70="small_talk")
    result = analysis._triage(rows, base, [])
    assert result["rules"]["each_repeat"]["0"]["safe"] is False
    assert result["rules"]["each_repeat"]["0"]["route_quality"] is True


def test_quality_and_operational_guardrails(frozen):
    base, rows, _, _ = frozen
    for r in rows:
        if r["expected_route"] != "in_scope":
            r.update(route="in_scope", route70="in_scope")
    assert analysis._triage(rows, base, [])["rules"]["route_quality"] is False
    _, rows, _, _ = deepcopy(frozen)
    for r in rows[:13]:
        r.update(error="refusal", route="in_scope", route70="in_scope")
    result = analysis._triage(rows, base, [])
    assert result["rules"]["operational_failure_at_most_one_percent"] is False
    assert result["arms"]["A70"]["pooled"]["valid_only_exact_route"]["denominator"] == 1214
    assert result["operational"]["operational_latency"]["n"] == 1227
    assert result["operational"]["successful_latency"]["n"] == 1214


def test_duplicate_and_missing_identity_runs_inconclusive(frozen):
    base, triage, labels, support = frozen
    triage[-1] = deepcopy(triage[0])
    support[-1] = deepcopy(support[0])
    a = analysis._triage(triage, base, [])
    b = analysis._support(support, labels, [])
    assert a["decision"] == b["decision"] == "inconclusive"
    assert a["duplicates"] and a["missing"]
    assert b["duplicates"] and b["missing"]
    assert a["rules"]["faster"] is None


def test_label_mismatch_and_incomplete_status_never_pass(frozen, tmp_path):
    _, triage, _, support = frozen
    support[0]["label"] = "partial"
    a, b = tmp_path / "a", tmp_path / "b"
    write_run(a, "triage", triage, "incomplete")
    write_run(b, "support", support)
    result = analysis.analyse(a, b, tmp_path / "result.json")
    assert result["triage"]["decision"] == "inconclusive"
    assert result["support"]["decision"] == "inconclusive"


def test_frozen_fingerprints_block_screen(frozen, tmp_path, monkeypatch):
    _, triage, _, support = frozen
    a, b = tmp_path / "a", tmp_path / "b"
    write_run(a, "triage", triage)
    write_run(b, "support", support)
    monkeypatch.setattr(analysis, "BASELINE_SHA256", "wrong")
    monkeypatch.setattr(analysis, "LABELS_SHA256", "wrong")
    result = analysis.analyse(a, b, tmp_path / "result.json")
    assert result["triage"]["decision"] == result["support"]["decision"] == "inconclusive"


def test_confidence_separate_threshold_and_fail_open():
    row = choice("case", route="out_of_scope", confidence=.70)
    assert analysis._route(row, "A70") == "out_of_scope"
    row["confidence"] = .699999
    assert analysis._route(row, "A0") == "out_of_scope"
    assert analysis._route(row, "A70") == "in_scope"
    for invalid in (None, float("nan"), float("inf"), -.1, 1.1, True):
        row["confidence"] = invalid
        assert analysis._route(row, "A0") == "in_scope"
    row["confidence"] = .9
    row["probabilities"]["in_scope"] = None
    assert not analysis._triage_valid(row)


def test_nearest_rank_and_case_median_not_pooled(frozen):
    assert analysis._quantile([1, 2, 3, 100], .5) == 2
    assert analysis._quantile(list(range(1, 21)), .95) == 19
    base, rows, _, _ = frozen
    for r in rows:
        r["seconds"] = (.5, .6, 20)[r["repeat"]]
    result = analysis._triage(rows, base, [])
    assert result["latency"]["case_medians"]["p95_s"] == .6
    assert result["operational"]["operational_latency"]["p95_s"] == 20
    assert result["rules"]["faster"] is True
    interval = result["paired_accuracy_case_cluster_bootstrap"]["A70"]["interval"]
    assert interval["percentile_95"] == [0., 0.]
    rows[0].update(skipped=True, attempts=0, seconds=0)
    result = analysis._triage(rows, base, [])
    assert result["latency"]["paired_n"] == 408
    assert result["rules"]["faster"] is None
    assert result["decision"] == "inconclusive"
    assert result["paired_accuracy_case_cluster_bootstrap"]["A70"]["paired_cases"] == 409


def test_binary_metrics_ties_threshold_missing_and_single_class():
    rows = [claim("p", .5), claim("n", .5, "partial"), claim("missing", None, "supported", error="refusal")]
    result = analysis._binary_metrics(rows)
    assert result["auroc"] == .5
    assert result["confusion_matrix"] == {"tp": 1, "tn": 0, "fp": 1, "fn": 0}
    assert result["accuracy"] == .5
    assert result["all_scheduled_accuracy"] == 1 / 3
    assert result["coverage"] == 2 / 3
    assert result["brier_score"] == .25
    assert result["false_support_rate"] == 1
    assert analysis._binary_metrics([claim("p")])["auroc"] is None
    assert analysis._binary_metrics([])["auroc"] is None
    json.dumps(analysis._binary_metrics([]), allow_nan=False)


def test_bootstrap_defaults_reproducibility_cluster_retention_and_undefined_draws():
    assert analysis.N_BOOT == 10000
    assert analysis.SEED == 20261103
    # Both labels in each cluster: resampling the cluster preserves perfect separation.
    rows = [claim("a", .8), claim("a", .2, "partial", arm="hybrid"),
            claim("b", .9), claim("b", .1, "partial", arm="hybrid")]
    first = analysis._support_bootstrap(rows, "label")
    assert first == analysis._support_bootstrap(rows, "label")
    assert first["clusters"] == 2
    assert first["metrics"]["auroc"]["defined_draws"] == 10000
    assert first["metrics"]["auroc"]["percentile_95"] == [1., 1.]
    single = analysis._support_bootstrap([claim("a")], "label")
    assert single["metrics"]["auroc"]["undefined_draws"] == 10000
    assert single["metrics"]["auroc"]["percentile_95"] is None
    uncertain = analysis._support_bootstrap([claim("a"), claim("b", .1, "partial")], "label")
    assert uncertain["metrics"]["auroc"]["percentile_95"] is None
    assert uncertain["metrics"]["auroc"]["undefined_draws"] > 500


def test_original_judge_sensitivity_and_failed_coverage(frozen):
    _, _, labels, rows = frozen
    rows[0]["original_label"] = "partial"
    labels[0]["original"]["claims"][0] = "partial"
    rows[1].update(probability=None, error="malformed")
    result = analysis._support(rows, labels, [])
    assert result["decision"] == "failed_screen"
    assert result["rules"]["valid_coverage_100_percent"] is False
    m = result["metrics"]
    assert m["primary"]["overall"]["valid_n"] == 440
    assert m["primary"]["overall"]["all_scheduled_accuracy"] == 440 / 441
    assert m["original_judge_sensitivity"]["overall"]["false_support_rate"] > 0


def test_judge_costs_count_once_and_equal_answer_amortisation():
    rows = [claim("a", original_answer_cost_usd=.06, answer_claim_count=2),
            claim("a", original_answer_cost_usd=.06, answer_claim_count=2, claim_index=1),
            claim("b", original_answer_cost_usd=.09)]
    result = analysis._judge_costs(rows, "original_answer_cost_usd")
    assert result["total_cost_usd"] == pytest.approx(.15)
    assert result["total_cost_per_total_claims_usd"] == pytest.approx(.05)
    assert result["equal_answer_mean_amortised_per_claim_usd"] == pytest.approx(.06)
    rows[0]["original_answer_cost_usd"] = None
    assert analysis._judge_costs(rows, "original_answer_cost_usd")["total_cost_usd"] is None


def test_unknown_cost_not_zero_and_attempt_denominator_includes_retries():
    rows = [claim("a", attempts=2), claim("b")]
    result = analysis._usage(rows, 2)
    assert result["http_attempts"] == 3
    assert result["mean_cost_per_http_attempt_usd"] == pytest.approx(.00002 / 3)
    rows[0]["usage"]["cost_usd"] = None
    result = analysis._usage(rows, 2)
    assert result["total_cost_usd"] is None
    assert result["mean_cost_per_scheduled_case_usd"] is None


def test_wilson_limits_and_unavailable_interval():
    assert analysis._proportion(0, 0)["wilson_95"] is None
    assert analysis._proportion(0, 100)["wilson_95"][0] == 0
    interval = analysis._interval([1.] * 9400 + [float("nan")] * 600)
    assert interval["percentile_95"] is None
    interval = analysis._interval([1.] * 9500 + [float("nan")] * 500)
    assert interval["percentile_95"] == [1., 1.]


def test_incomplete_attempt_usage_never_reports_zero_tokens_as_complete():
    rows = [claim("a")]
    rows[0]["usage"].update(input_tokens=0, output_tokens=0, cached_tokens=0, cost_usd=0, complete=False)
    result = analysis._usage(rows, 1)
    assert result["tokens"]["input_tokens"] is None
    assert result["tokens"]["cached_tokens"] is None
    assert result["total_cost_usd"] is None
    assert result["complete_observed_cost"] is False
    rows[0]["usage"].update(input_tokens=100, cached_tokens=40, complete=True)
    result = analysis._usage(rows, 1)
    assert result["tokens"]["input_tokens"] == 100
    assert result["tokens"]["cached_tokens"] == 40
