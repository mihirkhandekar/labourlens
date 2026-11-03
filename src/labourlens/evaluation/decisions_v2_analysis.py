"""Immutable, offline analysis of the fresh, paired Decisions triage screen.

AI-labelled cases are not human ground truth. Confidence intervals and McNemar
are descriptive, not additional adoption gates. No deployment is performed.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from statistics import median

import numpy as np

from labourlens import paths
from labourlens.evaluation.decisions_analysis import (
    ROUTES, _number, _proportion, _quantile, _timings, _usage,
)

SEED = 20261103
N_BOOT = 10000
N_CASES = 150
N_REPEATS = 3
ARMS = ("D", "C")
THRESHOLDS = (0, .3, .5, .7, .9)


def _rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _failed(row):
    return bool(row.get("error")) or row.get("route") not in ROUTES or row.get("skipped") is not False


def _operational(rows, scheduled_n):
    # Completeness must be explicit; absent usage metadata is not a zero bill.
    prepared = [{**r, "usage": {**r.get("usage", {}),
                  "complete": r.get("usage", {}).get("complete") is True}} for r in rows]
    result = _usage(prepared, scheduled_n)
    failures = sum(_failed(r) for r in rows)
    result["failures_or_refusals"] = _proportion(failures, scheduled_n)
    result["passes"] = failures <= scheduled_n * .01 and len(rows) == scheduled_n
    return result


def _metrics(rows, raw=False):
    confusion = {a: {b: 0 for b in (*ROUTES, "invalid")} for a in ROUTES}
    correct = valid_correct = valid_n = recall = negatives = 0
    diverted, misses = [], []
    raw_available = 0
    for row in rows:
        route = row.get("raw_route") if raw else row.get("route")
        if raw and route in ROUTES:
            raw_available += 1
        actual = route if route in ROUTES else "invalid"
        expected = row["expected_route"]
        confusion[expected][actual] += 1
        match = actual == expected
        correct += match
        if not _failed(row) and actual != "invalid":
            valid_n += 1
            valid_correct += match
        if expected != "in_scope":
            negatives += 1
            recall += actual in ROUTES and actual != "in_scope"
        elif actual != "in_scope":
            diverted.append({"case_id": row["case_id"], "repeat": row["repeat"]})
        if not match:
            misses.append({"case_id": row["case_id"], "repeat": row["repeat"]})
    result = {
        "effective_exact_route": _proportion(correct, len(rows)),
        "valid_only_exact_route": _proportion(valid_correct, valid_n),
        "non_in_scope_recall": _proportion(recall, negatives),
        "in_scope_diversions": {**_proportion(len(diverted), len(rows) - negatives), "identities": diverted},
        "confusion_matrix": confusion, "misses": misses,
    }
    if raw:
        result["raw_route_coverage"] = _proportion(raw_available, len(rows))
    return result


def _strata(rows, field):
    return {value: _metrics([r for r in rows if r[field] == value])
            for value in sorted({r[field] for r in rows})}


def _guards(rows, n, non_in_scope_n):
    metric = _metrics(rows)
    # Owner-approved v2 rule preserves v1's absolute allowance of two errors,
    # rather than scaling 407/409 and accidentally demanding 150/150.
    exact_bar = n - 2
    recall_bar = math.ceil(non_in_scope_n * 29 / 30)
    return {
        "expected_n": n, "exact_matches_required": exact_bar,
        "non_in_scope_recalls_required": recall_bar,
        "safety": metric["in_scope_diversions"]["numerator"] == 0,
        "quality": (metric["effective_exact_route"]["numerator"] >= exact_bar
                    and metric["non_in_scope_recall"]["numerator"] >= recall_bar
                    and len(rows) == n),
    }


def _interval(values):
    array = np.asarray(values, dtype=float)
    valid = array[np.isfinite(array)]
    return {"percentile_95": np.quantile(valid, [.025, .975]).tolist()
            if len(valid) >= .95 * len(array) and len(valid) else None,
            "defined_draws": int(len(valid)), "undefined_draws": int(len(array) - len(valid))}


def _mcnemar(pairs):
    # Each case contributes one paired majority-correctness outcome, not three
    # supposedly independent observations. Three repeats cannot tie in correctness.
    both = neither = d_only = c_only = 0
    for pair in pairs:
        d, c = pair["D_correct_n"] >= 2, pair["C_correct_n"] >= 2
        both += d and c
        neither += not d and not c
        d_only += d and not c
        c_only += c and not d
    discordant = d_only + c_only
    p = min(1., 2 * sum(math.comb(discordant, k) for k in range(min(d_only, c_only) + 1))
            / 2 ** discordant) if discordant else 1.
    return {"unit": "case-majority correctness across three repeats", "n": len(pairs),
            "both_correct": both, "both_incorrect": neither,
            "D_only_correct": d_only, "C_only_correct": c_only,
            "concordant_ties": both + neither, "majority_correctness_ties": 0,
            "discordant_n": discordant, "two_sided_exact_p": p,
            "adoption_gate": False}


def _paired(index, cases):
    accuracy_pairs, timed_pairs = [], []
    for case in cases:
        ident = case.get("case_id")
        grouped = {arm: [index.get((ident, arm, repeat)) for repeat in range(N_REPEATS)] for arm in ARMS}
        if any(row is None for group in grouped.values() for row in group):
            continue
        correct = {arm: sum(r.get("route") == case.get("expected_route") for r in group)
                   for arm, group in grouped.items()}
        accuracy_pairs.append({"case_id": ident, "D_correct_n": correct["D"], "C_correct_n": correct["C"],
                               "accuracy_delta": (correct["D"] - correct["C"]) / N_REPEATS})
        if any(not _number(r.get("seconds")) or r["seconds"] <= 0
               or not _number(r.get("attempts")) or r["attempts"] < 1 or r.get("skipped") is not False
               for group in grouped.values() for r in group):
            continue
        times = {arm: median(r["seconds"] for r in group) for arm, group in grouped.items()}
        timed_pairs.append({"case_id": ident, "D_median_s": times["D"], "C_median_s": times["C"],
                            "delta_s": times["D"] - times["C"], "ratio": times["D"] / times["C"]})
    accuracy = {"paired_n": len(accuracy_pairs), "case_pairs": accuracy_pairs,
                "D_minus_C_exact_accuracy": float(np.mean([p["accuracy_delta"] for p in accuracy_pairs]))
                if accuracy_pairs else None, "exact_mcnemar": _mcnemar(accuracy_pairs),
                "interpretation": "Descriptive paired non-inferiority evidence only; no significance adoption gate."}
    before = [p["C_median_s"] for p in timed_pairs]
    after = [p["D_median_s"] for p in timed_pairs]
    speed = {"paired_n": len(timed_pairs), "case_pairs": timed_pairs,
             "C_case_medians": _timings(before), "D_case_medians": _timings(after),
             "comparison": "Contemporaneous case-paired timings; not an isolated endpoint causal effect.",
             "median_paired_delta_s": median([p["delta_s"] for p in timed_pairs]) if timed_pairs else None,
             "mean_paired_delta_s": float(np.mean([p["delta_s"] for p in timed_pairs])) if timed_pairs else None,
             "median_case_ratio": median([p["ratio"] for p in timed_pairs]) if timed_pairs else None,
             "proportion_faster": _proportion(sum(p["delta_s"] < 0 for p in timed_pairs), len(timed_pairs))}
    for q, name in ((.5, "p50"), (.95, "p95")):
        speed[name + "_ratio"] = _quantile(after, q) / _quantile(before, q) if timed_pairs else None
        speed[name + "_difference_s"] = _quantile(after, q) - _quantile(before, q) if timed_pairs else None
    # The seed and complete case-cluster draws keep all six paired observations
    # together. Accuracy uses the within-case repeat mean; latency its median.
    if accuracy_pairs:
        draws = np.random.default_rng(SEED).integers(0, len(accuracy_pairs), size=(N_BOOT, len(accuracy_pairs)))
        accuracy["case_cluster_bootstrap"] = _interval(
            np.asarray([p["accuracy_delta"] for p in accuracy_pairs])[draws].mean(axis=1))
    if timed_pairs:
        draws = np.random.default_rng(SEED).integers(0, len(timed_pairs), size=(N_BOOT, len(timed_pairs)))
        d, c = np.asarray(after)[draws], np.asarray(before)[draws]
        uncertainty = {"mean_latency_delta_s": _interval((d - c).mean(axis=1)),
                       "median_latency_delta_s": _interval(np.median(d - c, axis=1))}
        d, c = np.sort(d, axis=1), np.sort(c, axis=1)
        for q, name in ((.5, "p50"), (.95, "p95")):
            rank = math.ceil(q * len(timed_pairs)) - 1
            uncertainty[name + "_difference_s"] = _interval(d[:, rank] - c[:, rank])
            uncertainty[name + "_ratio"] = _interval(d[:, rank] / c[:, rank])
        speed["case_cluster_bootstrap"] = uncertainty
    speed["faster"] = (len(timed_pairs) == N_CASES
                       and speed["p50_ratio"] <= .8 and speed["p95_ratio"] <= .8)
    return accuracy, speed


def _validate(manifest, status, rows, cases, cases_hash):
    issues = []
    if len(cases) != N_CASES or len({c.get("case_id") for c in cases}) != N_CASES:
        issues.append("frozen cases must contain exactly 150 unique identities")
    if any(not isinstance(c.get("case_id"), str) or c.get("expected_route") not in ROUTES
           or not isinstance(c.get("family"), str) or not isinstance(c.get("kind"), str)
           or c.get("drafted_by") != "AI" or c.get("review_status") != "AI-labelled, not human-reviewed"
           for c in cases):
        issues.append("invalid frozen case labels or provenance")
    if (sum(c.get("expected_route") == "in_scope" for c in cases) != 90
            or sum(c.get("expected_route") in ROUTES[1:] for c in cases) != 60):
        issues.append("frozen cases must contain 90 in_scope and 60 non_in_scope cases")
    if manifest.get("cases_sha256") != cases_hash:
        issues.append("frozen cases SHA-256 mismatch")
    if manifest.get("expected_n") != 900:
        issues.append("manifest expected_n must be 900")
    for name in ("prompt_sha256", "prereg_sha256"):
        value = manifest.get(name)
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            issues.append("missing or invalid " + name)
    if not manifest.get("git_commit"):
        issues.append("missing git_commit")
    if manifest.get("selected_tuning_id") not in {f"decisions-triage-tune-{i}" for i in range(1, 6)}:
        issues.append("invalid selected_tuning_id")
    threshold = manifest.get("threshold")
    if not _number(threshold) or threshold not in THRESHOLDS:
        issues.append("invalid frozen threshold")
    if (status.get("status") != "complete" or status.get("scheduled_n") != 900
            or status.get("completed_n") != 900 or len(rows) != 900):
        issues.append("run status or scheduled/completed coverage incomplete")
    frozen = {c.get("case_id"): c for c in cases}
    index, clean, duplicates, extra = {}, [], [], []
    for row in rows:
        ident = (row.get("case_id"), row.get("arm"), row.get("repeat"))
        if ident in index:
            duplicates.append(list(ident))
            continue
        index[ident] = row
        case = frozen.get(ident[0])
        if case is None or ident[1] not in ARMS or type(ident[2]) is not int or ident[2] not in range(N_REPEATS):
            extra.append(list(ident))
            continue
        if (any(row.get(field) != case.get(field) for field in ("expected_route", "family", "kind"))
                or row.get("expected_route") not in ROUTES
                or not all(isinstance(row.get(field), str) for field in ("family", "kind"))):
            issues.append("case label or stratum mismatch")
            continue
        clean.append(row)
        if row.get("route") not in ROUTES or row.get("skipped") is not False:
            issues.append("invalid effective route or skipped classification")
        if row.get("arm") == "D" and not _failed(row):
            conf = row.get("confidence")
            if row.get("raw_route") not in ROUTES or not _number(conf) or not 0 <= conf <= 1:
                issues.append("invalid raw Decisions route or confidence")
            elif threshold in THRESHOLDS and row["route"] != ("in_scope" if conf < threshold else row["raw_route"]):
                issues.append("effective route disagrees with frozen threshold")
    expected = {(c.get("case_id"), arm, repeat) for c in cases for arm in ARMS for repeat in range(N_REPEATS)}
    missing = sorted(expected - index.keys())
    if duplicates or extra or missing:
        issues.append("paired identities are missing, extra or duplicated")
    return list(dict.fromkeys(issues)), clean, index, {"duplicates": duplicates, "extra": extra, "missing": [list(i) for i in missing]}


def analyse(directory: Path, out: Path | None = None, *, cases_path: Path | None = None) -> dict:
    """Write a new immutable result; incomplete/mismatched runs are inconclusive.

    ``cases_path`` permits offline fixtures or an explicitly frozen case file.
    The manifest must fingerprint its exact bytes, including labels and provenance.
    Existing output paths are refused before reading inputs, then protected by x mode.
    """
    directory = Path(directory)
    out = Path(out) if out is not None else paths.EXPERIMENTS / "eval/decisions-api-v2-results.json"
    if out.exists():
        raise FileExistsError(out)
    cases_path = Path(cases_path) if cases_path is not None else paths.EXPERIMENTS / "triage/fresh_cases_v2.jsonl"
    # Read the frozen file once so the hash and decoded labels cannot disagree.
    case_bytes = cases_path.read_bytes()
    cases_hash = hashlib.sha256(case_bytes).hexdigest()
    cases = [json.loads(line) for line in case_bytes.decode().splitlines() if line.strip()]
    manifest = json.loads((directory / "manifest.json").read_text())
    status = json.loads((directory / "status.json").read_text())
    rows = _rows(directory / "raw.jsonl")
    issues, clean, _, coverage = _validate(manifest, status, rows, cases, cases_hash)
    arms = {}
    non_in_scope_n = sum(c.get("expected_route") in ROUTES[1:] for c in cases)
    for arm in ARMS:
        observed = [r for r in clean if r["arm"] == arm]
        repeats, repeat_rules = {}, {}
        for repeat in range(N_REPEATS):
            group = [r for r in observed if r["repeat"] == repeat]
            repeats[str(repeat)] = {**_metrics(group), "by_family": _strata(group, "family"),
                                    "by_kind": _strata(group, "kind"), "operational": _operational(group, N_CASES)}
            repeat_rules[str(repeat)] = _guards(group, N_CASES, non_in_scope_n)
        operational = _operational(observed, N_CASES * N_REPEATS)
        consistency = []
        for case in cases:
            group = [r for r in observed if r["case_id"] == case.get("case_id")]
            if len(group) == N_REPEATS:
                counts = Counter(r.get("route") for r in group)
                majority = [route for route, count in counts.items() if count >= 2]
                consistency.append({"case_id": case.get("case_id"), "consistent": len(counts) == 1,
                                    "routes": [r.get("route") for r in sorted(group, key=lambda r: r["repeat"])],
                                    "majority_route": majority[0] if majority else None,
                                    "route_majority_tie": not majority})
        arms[arm] = {"pooled": _metrics(observed), "by_repeat": repeats,
                     "by_family": _strata(observed, "family"), "by_kind": _strata(observed, "kind"),
                     "operational": operational, "each_repeat_rules": repeat_rules,
                     "safety": all(r["safety"] for r in repeat_rules.values()),
                     "quality": all(r["quality"] for r in repeat_rules.values()),
                     "three_repeat_consistency": {**_proportion(sum(c["consistent"] for c in consistency), len(consistency)),
                                                  "case_details": consistency,
                                                  "route_majority_ties": sum(c["route_majority_tie"] for c in consistency)}}
        confidences = [r["confidence"] for r in observed if _number(r.get("confidence")) and 0 <= r["confidence"] <= 1]
        arms[arm]["confidence_distribution"] = {
            "n": len(confidences), "p05": _quantile(confidences, .05), "p50": _quantile(confidences, .5),
            "p95": _quantile(confidences, .95), "mean": sum(confidences) / len(confidences) if confidences else None,
            "min": min(confidences) if confidences else None, "max": max(confidences) if confidences else None}
        raw = [r for r in observed if r.get("raw_route") in ROUTES]
        arms[arm]["raw_vs_thresholded"] = {
            "available_n": len(raw), "raw": _metrics(raw, raw=True), "thresholded_same_rows": _metrics(raw),
            "changed_routes": sum(r["raw_route"] != r.get("route") for r in raw),
            "exact_match_delta_thresholded_minus_raw": sum((r.get("route") == r["expected_route"])
                - (r["raw_route"] == r["expected_route"]) for r in raw),
        }
    # Only trusted labels enter paired reporting. Any validation issue still blocks adoption.
    clean_index = {(r["case_id"], r["arm"], r["repeat"]): r for r in clean}
    accuracy, latency = _paired(clean_index, cases)
    if latency["paired_n"] != N_CASES:
        issues.append("incomplete valid paired latency coverage")
    complete = not issues
    guards = {"D_safety": arms["D"]["safety"], "D_quality": arms["D"]["quality"],
              "D_operational": arms["D"]["operational"]["passes"],
              "C_operational": arms["C"]["operational"]["passes"], "faster": latency["faster"]}
    result = {"schema_version": 2, "inputs": {"directory": str(directory), "cases_path": str(cases_path),
               "cases_sha256": cases_hash, "manifest": manifest, "status": status},
              "seed": SEED, "bootstrap_draws": N_BOOT, "complete": complete,
              "validation_issues": list(dict.fromkeys(issues)), "identity_coverage": coverage,
              "arms": arms, "paired_accuracy": accuracy, "latency": latency, "adoption_guards": guards,
              "decision": "inconclusive" if not complete else "adopt_web_triage" if all(guards.values()) else "do_not_adopt",
              "interpretation": {"labels": "AI-labelled, not human-reviewed; descriptive sample evidence, not deployment safety proof.",
                 "baseline": "C safety and quality are reported, not adoption requirements; both arms require <=1% operational failures.",
                 "exact_quality": "At least 148/150 each repeat: the owner-approved absolute two-error allowance from v1, not scaled-ceiling 407/409.",
                 "recall_quality": "At least ceil(non_in_scope_n*29/30) each repeat, giving 58/60 on the frozen fresh set.",
                 "quantiles": "nearest rank ceil(q*n)",
                 "bootstrap": "10000 case-cluster resamples, seed 20261103, percentile 95%; all repeats remain together.",
                 "deployment": "No deployment is performed. No significance or McNemar adoption gate."}}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return result
