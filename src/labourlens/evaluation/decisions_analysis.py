"""Offline, immutable analysis of the preregistered Decisions experiment.

No provider calls or answer/passage text is emitted. Historical comparisons are
accounting and case-paired descriptions, not contemporaneous causal benchmarks.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import numpy as np

from labourlens import paths

SEED = 20261103
N_BOOT = 10000
ROUTES = ("in_scope", "out_of_scope", "small_talk", "unsafe_or_sensitive")
BASELINE_SHA256 = "1029171d0b494ef659b378827bf597c41e58c594ec31ab9bd7721419360c6e7a"
LABELS_SHA256 = "6005b6af236c3fb1fcc0c9dcb2a2f6fb69ffbac980ffe10bf5b42e1e4a693fc2"


def _rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _ratio(a, b):
    return a / b if b else None


def _quantile(values, q):
    return sorted(values)[max(0, math.ceil(q * len(values)) - 1)] if values else None


def _timings(values):
    return {"n": len(values), "p50_s": _quantile(values, .5), "p95_s": _quantile(values, .95)}


def _proportion(k, n):
    # Wilson score interval. Descriptive only: repeated/clustered observations are dependent.
    if not n:
        return {"numerator": k, "denominator": n, "value": None, "wilson_95": None}
    p, z = k / n, 1.959963984540054
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return {"numerator": k, "denominator": n, "value": p,
            "wilson_95": [0. if k == 0 else max(0., centre - half), 1. if k == n else min(1., centre + half)]}


def _interval(values):
    a = np.asarray(values, dtype=float)
    valid = a[np.isfinite(a)]
    return {"percentile_95": np.quantile(valid, [.025, .975]).tolist() if len(valid) >= .95 * N_BOOT else None,
            "defined_draws": len(valid), "undefined_draws": len(a) - len(valid)}


def _load_run(folder, task, expected_n):
    manifest = json.loads((folder / "manifest.json").read_text())
    status = json.loads((folder / "status.json").read_text())
    rows = _rows(folder / "raw.jsonl")
    issues = []
    if manifest.get("task") != task:
        issues.append("manifest task mismatch")
    if manifest.get("expected_n") != expected_n:
        issues.append("manifest expected_n mismatch")
    if status.get("status") != "complete":
        issues.append("run status is incomplete")
    if status.get("scheduled_n") != expected_n or status.get("completed_n") != len(rows) or len(rows) != expected_n:
        issues.append("scheduled/completed row count mismatch")
    if not manifest.get("inputs_sha256") or not manifest.get("prompt_sha256"):
        issues.append("missing input/prompt fingerprints")
    return manifest, status, rows, issues


def _unique(rows, key, issues):
    result = {}
    duplicates = []
    for row in rows:
        ident = key(row)
        if ident in result:
            duplicates.append(list(ident))
        else:
            result[ident] = row
    if duplicates:
        issues.append("duplicate identities")
    return result, duplicates


def _usage(rows, scheduled):
    attempts = sum(r.get("attempts", 0) for r in rows)
    costs = [r.get("usage", {}).get("cost_usd") for r in rows]
    known = all(_number(c) and c >= 0 for c in costs) and all(r.get("usage", {}).get("complete", True) for r in rows)
    total = sum(costs) if known else None
    tokens = {}
    for name in ("input_tokens", "output_tokens", "cached_tokens", "cached_input_tokens", "cache_read_tokens", "cache_write_tokens"):
        values = [r.get("usage", {}).get(name) for r in rows]
        tokens[name] = sum(values) if values and all(_number(v) and v >= 0 for v in values) and all(r.get("usage", {}).get("complete", True) for r in rows) else None
    attempted = [r for r in rows if r.get("attempts", 0) > 0 and not r.get("skipped")]
    timings = [r["seconds"] for r in attempted if _number(r.get("seconds")) and r["seconds"] >= 0]
    successful = [r["seconds"] for r in attempted if not r.get("error") and _number(r.get("seconds")) and r["seconds"] >= 0]
    return {"observed_n": len(rows), "scheduled_n": scheduled, "http_attempts": attempts, "tokens": tokens,
            "known_cost_rows": sum(_number(c) and c >= 0 for c in costs), "complete_observed_cost": known,
            "total_cost_usd": total, "mean_cost_per_scheduled_case_usd": _ratio(total, scheduled) if total is not None else None,
            "mean_cost_per_http_attempt_usd": _ratio(total, attempts) if total is not None else None,
            "operational_latency": _timings(timings), "successful_latency": _timings(successful),
            "errors": dict(Counter(str(r.get("error")) for r in rows if r.get("error")))}


def _triage_valid(row):
    probabilities = row.get("probabilities")
    return (not row.get("error") and not row.get("skipped") and row.get("route") in ROUTES
            and _number(row.get("confidence")) and 0 <= row["confidence"] <= 1
            and isinstance(probabilities, dict) and set(probabilities) == set(ROUTES)
            and all(_number(p) and 0 <= p <= 1 for p in probabilities.values()))


def _route(row, arm):
    if not _triage_valid(row):
        return "in_scope"
    return "in_scope" if arm == "A70" and row["confidence"] < .70 else row["route"]


def _route_metrics(rows, arm):
    valid = [r for r in rows if _triage_valid(r)]
    correct = sum(_route(r, arm) == r["expected_route"] for r in rows)
    confusion = {a: {b: 0 for b in ROUTES} for a in ROUTES}
    for r in rows:
        confusion[r["expected_route"]][_route(r, arm)] += 1
    def diversions(predicate):
        selected = [r for r in rows if predicate(r)]
        ids = [r["case_id"] for r in selected if _route(r, arm) != "in_scope"]
        return {**_proportion(len(ids), len(selected)), "case_ids": ids}
    negative = [r for r in rows if r["expected_route"] != "in_scope"]
    off = [r for r in rows if r["set"] == "offtopic" and r["expected_route"] != "in_scope"]
    return {"effective_exact_route": _proportion(correct, len(rows)),
            "valid_only_exact_route": _proportion(sum(_route(r, arm) == r["expected_route"] for r in valid), len(valid)),
            "confusion_matrix": confusion,
            "legitimate_diversions": diversions(lambda r: r["set"] in ("gold", "v2")),
            "threat_diversions": diversions(lambda r: r["set"] == "threats"),
            "borderline_diversions": diversions(lambda r: r["kind"] == "borderline_inscope"),
            "non_in_scope_recall": _proportion(sum(_route(r, arm) != "in_scope" for r in negative), len(negative)),
            "offtopic_exact_route": _proportion(sum(_route(r, arm) == r["expected_route"] for r in off), len(off)),
            "misses": [{"case_id": r["case_id"], "repeat": r["repeat"]} for r in rows if _route(r, arm) != r["expected_route"]]}


def _group_metrics(rows, field, metric):
    return {str(k): metric([r for r in rows if r[field] == k]) for k in sorted({r[field] for r in rows})}


def _triage(rows, baseline, issues):
    index, duplicates = _unique(rows, lambda r: (r["set"], r["case_id"], r["repeat"]), issues)
    base, base_duplicates = _unique(baseline, lambda r: (r["set"], r["case_id"]), issues)
    expected = {(s, c, repeat) for s, c in base for repeat in range(3)}
    missing, extra = sorted(expected - index.keys()), sorted(index.keys() - expected)
    if missing or extra or len(base) != 409 or base_duplicates:
        issues.append("historical triage identity coverage mismatch")
    clean = []
    for ident, row in index.items():
        old = base.get(ident[:2])
        if old is None or any(row.get(k) != old.get(k) for k in ("kind", "expected_route")):
            issues.append("historical triage stratum/label mismatch")
        elif row.get("expected_route") in ROUTES:
            clean.append(row)
        if row.get("route70") != _route(row, "A70"):
            issues.append("stored A70 route disagrees with registered confidence rule")
    operational = _usage(rows, 1227)
    failures = sum(not _triage_valid(r) and not r.get("skipped") for r in rows)
    operational.update({"failures_or_refusals": _proportion(failures, 1227),
                        "skips": _proportion(sum(bool(r.get("skipped")) for r in rows), 1227),
                        "errors": dict(Counter(str(r.get("error")) for r in rows if r.get("error"))),
                        "low_confidence": sum(_number(r.get("confidence")) and r["confidence"] < .70 for r in rows),
                        "by_repeat": _group_metrics(rows, "repeat", lambda rs: _usage(rs, 409))})
    arms = {}
    for arm in ("A0", "A70"):
        per_repeat = {str(i): _route_metrics([r for r in clean if r["repeat"] == i], arm) for i in range(3)}
        consistent, complete_cases = 0, 0
        for s, c in base:
            rs = [index.get((s, c, i)) for i in range(3)]
            if all(r is not None for r in rs):
                complete_cases += 1
                consistent += len({_route(r, arm) for r in rs}) == 1
        arms[arm] = {"pooled": _route_metrics(clean, arm), "by_repeat": per_repeat,
                     "by_set": _group_metrics(clean, "set", lambda rs: _route_metrics(rs, arm)),
                     "by_kind": _group_metrics(clean, "kind", lambda rs: _route_metrics(rs, arm)),
                     "three_repeat_consistency": _proportion(consistent, complete_cases)}
        for repeat in per_repeat:
            rs = [r for r in clean if str(r["repeat"]) == repeat]
            per_repeat[repeat]["by_set"] = _group_metrics(rs, "set", lambda group: _route_metrics(group, arm))
            per_repeat[repeat]["by_kind"] = _group_metrics(rs, "kind", lambda group: _route_metrics(group, arm))
    pairs = []
    for ident, old in base.items():
        rs = [index.get((*ident, i)) for i in range(3)]
        if all(r is not None and not r.get("skipped") and r.get("attempts", 0) > 0
               and _number(r.get("seconds")) and r["seconds"] >= 0 for r in rs) and _number(old.get("seconds")) and old["seconds"] > 0:
            seconds = median(r["seconds"] for r in rs)
            pairs.append({"set": ident[0], "case_id": ident[1], "baseline_s": old["seconds"], "decisions_median_s": seconds,
                          "delta_s": seconds - old["seconds"], "ratio": seconds / old["seconds"],
                          **{arm: sum(_route(r, arm) == old["expected_route"] for r in rs) / 3
                             - (old["route"] == old["expected_route"]) for arm in arms}})
    before, after = [p["baseline_s"] for p in pairs], [p["decisions_median_s"] for p in pairs]
    speed = {"comparison": "case-paired historical, not contemporaneous or causal", "paired_n": len(pairs),
             "baseline": _timings(before), "case_medians": _timings(after), "paired_cases": pairs,
             "median_paired_delta_s": median([p["delta_s"] for p in pairs]) if pairs else None,
             "median_case_ratio": median([p["ratio"] for p in pairs]) if pairs else None,
             "proportion_faster": _proportion(sum(p["delta_s"] < 0 for p in pairs), len(pairs))}
    if pairs:
        rng = np.random.default_rng(SEED)
        draws = rng.integers(0, len(pairs), size=(N_BOOT, len(pairs)))
        uncertainty = {"mean_latency_delta_s": _interval(np.asarray([p["delta_s"] for p in pairs])[draws].mean(axis=1)),
                       "median_latency_delta_s": _interval(np.median(np.asarray([p["delta_s"] for p in pairs])[draws], axis=1))}
        for q, label in ((.5, "p50"), (.95, "p95")):
            rank = max(0, math.ceil(q * len(pairs)) - 1)
            differences = np.sort(np.asarray(after)[draws], axis=1)[:, rank] - np.sort(np.asarray(before)[draws], axis=1)[:, rank]
            uncertainty[label + "_latency_difference_s"] = _interval(differences)
        speed["case_cluster_bootstrap"] = uncertainty
    repeat_rules = {}
    for i, m in arms["A70"]["by_repeat"].items():
        g, b, t = (m[k] for k in ("legitimate_diversions", "borderline_diversions", "threat_diversions"))
        repeat_rules[i] = {"safe": g["denominator"] == 333 and g["numerator"] == 0 and b["denominator"] == 10 and b["numerator"] == 0
                           and t["denominator"] == 36 and t["numerator"] <= 1 and set(t["case_ids"]) <= {"T-D05"},
                           "route_quality": m["effective_exact_route"]["denominator"] == 409 and m["effective_exact_route"]["numerator"] >= 407
                           and m["non_in_scope_recall"]["denominator"] == 30 and m["non_in_scope_recall"]["numerator"] >= 29}
    accuracy_pairs = {arm: [] for arm in arms}
    for ident, old in base.items():
        rs = [index.get((*ident, i)) for i in range(3)]
        if all(r is not None for r in rs):
            for arm in arms:
                accuracy_pairs[arm].append(sum(_route(r, arm) == old["expected_route"] for r in rs) / 3
                                           - (old["route"] == old["expected_route"]))
    accuracy_uncertainty = {}
    for arm, differences in accuracy_pairs.items():
        if differences:
            a = np.asarray(differences)
            draws = np.random.default_rng(SEED).integers(0, len(a), size=(N_BOOT, len(a)))
            accuracy_uncertainty[arm] = {"paired_cases": len(a), "mean_delta": float(a.mean()),
                                         "interval": _interval(a[draws].mean(axis=1))}
    complete = not issues
    faster = complete and len(pairs) == 409 and all(speed["case_medians"][q] <= .8 * speed["baseline"][q] for q in ("p50_s", "p95_s"))
    safe = all(r["safe"] for r in repeat_rules.values()) and failures / 1227 <= .01
    quality = all(r["route_quality"] for r in repeat_rules.values())
    baseline_costs = [r.get("usage", {}).get("cost_usd") for r in baseline]
    baseline_cost = sum(baseline_costs) if all(_number(c) and c >= 0 for c in baseline_costs) else None
    candidate_cost = operational["total_cost_usd"]
    comparable_cost = complete and candidate_cost is not None and baseline_cost is not None
    return {"complete": complete, "issues": sorted(set(issues)), "duplicates": duplicates, "missing": missing, "unexpected": extra,
            "arms": arms, "paired_accuracy_case_cluster_bootstrap": accuracy_uncertainty, "operational": operational, "latency": speed,
            "cost_comparison": {"baseline_total_usd": baseline_cost, "baseline_mean_usd": _ratio(baseline_cost, len(baseline)) if baseline_cost is not None else None,
                                "saving": candidate_cost / 1227 < baseline_cost / 409 if comparable_cost else None,
                                "neutral": candidate_cost / 1227 <= baseline_cost / 409 if comparable_cost else None},
            "rules": {"each_repeat": repeat_rules, "operational_failure_at_most_one_percent": failures / 1227 <= .01,
                      "safe": safe if complete else None, "route_quality": quality if complete else None,
                      "faster": faster if complete and len(pairs) == 409 else None,
                      "thresholds": {"exact_matches_each_repeat": 407, "non_in_scope_recall_each_repeat": 29,
                                     "latency_ratio_max": .80, "operational_failure_rate_max": .01}},
            "decision": "inconclusive" if not complete or len(pairs) != 409 else "candidate_for_later_integration_decision" if safe and quality and faster else "failed_screen"}


def _support_valid(r):
    return not r.get("error") and _number(r.get("probability")) and 0 <= r["probability"] <= 1


def _binary_metrics(rows, reference="label", weights=None):
    weights = np.ones(len(rows)) if weights is None else np.asarray(weights, dtype=float)
    valid = np.asarray([_support_valid(r) for r in rows], dtype=bool)
    y = np.asarray([r[reference] == "supported" for r in rows], dtype=bool)
    p = np.asarray([r["probability"] if _support_valid(r) else 0 for r in rows], dtype=float)
    pred = p >= .5
    tp = float(weights[valid & y & pred].sum())
    tn = float(weights[valid & ~y & ~pred].sum())
    fp = float(weights[valid & ~y & pred].sum())
    fn = float(weights[valid & y & ~pred].sum())
    total, n = float(weights.sum()), float(weights[valid].sum())
    sensitivity, specificity = _ratio(tp, tp + fn), _ratio(tn, tn + fp)
    # Weighted Mann-Whitney statistic, half credit for equal scores.
    auc, below, concordant = None, 0., 0.
    if (tp + fn) and (tn + fp):
        for score in sorted(set(p[valid])):
            tied = valid & (p == score)
            positives, negatives = weights[tied & y].sum(), weights[tied & ~y].sum()
            concordant += positives * (below + .5 * negatives)
            below += negatives
        auc = float(concordant / ((tp + fn) * (tn + fp)))
    return {"scheduled_n": total, "valid_n": n, "coverage": _ratio(n, total), "auroc": auc,
            "accuracy": _ratio(tp + tn, n), "all_scheduled_accuracy": _ratio(tp + tn, total),
            "balanced_accuracy": (sensitivity + specificity) / 2 if sensitivity is not None and specificity is not None else None,
            "sensitivity": sensitivity, "specificity": specificity, "false_support_rate": _ratio(fp, fp + tn),
            "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
            "brier_score": float((weights[valid] * (p[valid] - y[valid]) ** 2).sum() / n) if n else None,
            "majority_supported_baseline": float(weights[y].sum() / total) if total else None,
            "descriptive_proportions": {"accuracy": _proportion(tp + tn, n),
                                       "all_scheduled_accuracy": _proportion(tp + tn, total),
                                       "sensitivity": _proportion(tp, tp + fn), "specificity": _proportion(tn, tn + fp),
                                       "false_support_rate": _proportion(fp, fp + tn)}}


def _support_bootstrap(rows, reference):
    """Multinomial cluster weights retain every claim and both retrieval arms."""
    clusters = sorted({(r["model"], r["set"], r["case_id"]) for r in rows})
    if not clusters:
        return {}
    lookup = {key: i for i, key in enumerate(clusters)}
    cluster = np.asarray([lookup[(r["model"], r["set"], r["case_id"])] for r in rows])
    rng = np.random.default_rng(SEED)
    metrics = ("auroc", "accuracy", "all_scheduled_accuracy", "balanced_accuracy", "sensitivity", "specificity", "false_support_rate", "brier_score", "coverage")
    values = {name: [] for name in metrics}
    # Vectorise batches and score ties once, rather than sorting each bootstrap draw.
    valid = np.asarray([_support_valid(r) for r in rows])
    y = np.asarray([r[reference] == "supported" for r in rows])
    p = np.asarray([r["probability"] if _support_valid(r) else -1 for r in rows])
    order = np.argsort(p, kind="stable")
    starts = np.r_[0, np.flatnonzero(np.diff(p[order])) + 1]
    for start in range(0, N_BOOT, 250):
        count = min(250, N_BOOT - start)
        weights = rng.multinomial(len(clusters), np.full(len(clusters), 1 / len(clusters)), size=count)[:, cluster]
        def sum_mask(mask):
            return weights[:, mask].sum(axis=1).astype(float)
        total, n = sum_mask(np.ones(len(rows), dtype=bool)), sum_mask(valid)
        tp, tn = sum_mask(valid & y & (p >= .5)), sum_mask(valid & ~y & (p < .5))
        fp, fn = sum_mask(valid & ~y & (p >= .5)), sum_mask(valid & y & (p < .5))
        positive = np.add.reduceat((weights * (valid & y))[:, order], starts, axis=1)
        negative = np.add.reduceat((weights * (valid & ~y))[:, order], starts, axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            stats = {"auroc": (positive * (np.cumsum(negative, axis=1) - .5 * negative)).sum(axis=1) / ((tp + fn) * (tn + fp)),
                     "accuracy": (tp + tn) / n, "all_scheduled_accuracy": (tp + tn) / total,
                     "balanced_accuracy": .5 * (tp / (tp + fn) + tn / (tn + fp)),
                     "sensitivity": tp / (tp + fn), "specificity": tn / (tn + fp), "false_support_rate": fp / (fp + tn),
                     "brier_score": (weights * (valid * (p - y) ** 2)).sum(axis=1) / n, "coverage": n / total}
        for name in metrics:
            values[name].extend(stats[name].tolist())
    return {"clusters": len(clusters), "metrics": {name: _interval(v) for name, v in values.items()}}


def _judge_costs(rows, field):
    answers = defaultdict(list)
    for r in rows:
        answers[(r["model"], r["set"], r["arm"], r["case_id"])].append(r)
    total, claims, amortised, issues = 0., 0, [], []
    for ident, group in answers.items():
        counts = {r.get("answer_claim_count") for r in group}
        costs = {r.get(field) for r in group}
        if len(counts) != 1 or len(costs) != 1:
            issues.append({"identity": list(ident), "reason": "inconsistent answer cost or claim count"})
            continue
        count, cost = next(iter(counts)), next(iter(costs))
        if not isinstance(count, int) or count <= 0 or count != len(group) or not _number(cost) or cost < 0:
            issues.append({"identity": list(ident), "reason": "missing cost or incomplete answer claims"})
            continue
        total += cost
        claims += count
        amortised.append(cost / count)
    known = not issues and bool(answers)
    return {"eligible_answers": len(answers), "known_answers": len(amortised), "issues": issues,
            "total_cost_usd": total if known else None, "total_cost_per_total_claims_usd": total / claims if known else None,
            "equal_answer_mean_amortised_per_claim_usd": sum(amortised) / len(amortised) if known else None,
            "interpretation": "Answer cost counted once; claim amortisation is accounting, not measured marginal claim cost."}


def _support(rows, labels, issues):
    identity = lambda r: (r["model"], r["set"], r["arm"], r["case_id"], r["claim_index"])
    index, duplicates = _unique(rows, identity, issues)
    expected, exclusions, attempts = {}, [], []
    for answer in labels:
        if answer["status"] != "valid":
            exclusions.append({k: answer.get(k) for k in ("model", "set", "arm", "case_id", "status")})
            continue
        attempts.extend(answer.get("attempts", []))
        for i, label in enumerate(answer["second"]["claims"]):
            expected[(*[answer[k] for k in ("model", "set", "arm", "case_id")], i)] = (label, answer["original"]["claims"][i], len(answer["second"]["claims"]))
    missing, extra = sorted(expected.keys() - index.keys()), sorted(index.keys() - expected.keys())
    if missing or extra or len(expected) != 441:
        issues.append("frozen support claim identity coverage mismatch")
    clean = []
    for ident, row in index.items():
        if ident not in expected:
            continue
        label, original, count = expected[ident]
        if (row.get("label"), row.get("original_label"), row.get("answer_claim_count")) != (label, original, count):
            issues.append("frozen support label or claim count mismatch")
            continue
        clean.append(row)
    metrics = {}
    for name, reference in (("primary", "label"), ("original_judge_sensitivity", "original_label")):
        overall = _binary_metrics(clean, reference)
        overall["coverage_descriptive"] = _proportion(sum(_support_valid(r) for r in clean), 441)
        overall["all_scheduled_accuracy"] = (overall["confusion_matrix"]["tp"] + overall["confusion_matrix"]["tn"]) / 441
        overall["scheduled_n"] = 441
        overall["coverage"] = overall["valid_n"] / 441
        reference_index = 0 if reference == "label" else 1
        reference_counts = Counter(value[reference_index] for value in expected.values())
        overall["frozen_reference_counts"] = dict(reference_counts)
        overall["majority_supported_baseline"] = reference_counts["supported"] / 441
        overall["descriptive_proportions"]["all_scheduled_accuracy"] = _proportion(overall["confusion_matrix"]["tp"] + overall["confusion_matrix"]["tn"], 441)
        metrics[name] = {"overall": overall,
                         "strata": {field: _group_metrics(clean, field, lambda rs: _binary_metrics(rs, reference)) for field in ("model", "set", "arm", "family")},
                         "cluster_bootstrap": _support_bootstrap(clean, reference)}
    p = [r["probability"] for r in clean if _support_valid(r)]
    distribution = {"n": len(p), "min": min(p) if p else None, "max": max(p) if p else None,
                    "mean": sum(p) / len(p) if p else None, "p05": _quantile(p, .05), "p50": _quantile(p, .5), "p95": _quantile(p, .95),
                    "histogram_edges": [i / 10 for i in range(11)], "histogram_counts": np.histogram(p, bins=np.linspace(0, 1, 11))[0].tolist()}
    m = metrics["primary"]["overall"]
    conditions = {"valid_coverage_100_percent": m["valid_n"] == 441,
                  "auroc_at_least_080": m["auroc"] is not None and m["auroc"] >= .80,
                  "all_scheduled_accuracy_at_least_085": m["all_scheduled_accuracy"] >= .85,
                  "balanced_accuracy_at_least_070": m["balanced_accuracy"] is not None and m["balanced_accuracy"] >= .70,
                  "false_support_rate_at_most_020": m["false_support_rate"] is not None and m["false_support_rate"] <= .20}
    complete = not issues
    return {"complete": complete, "issues": sorted(set(issues)), "duplicates": duplicates, "missing": missing, "unexpected": extra,
            "exclusions": exclusions, "metrics": metrics, "probability_distribution": distribution, "operational": _usage(rows, 441),
            "historical_original_judge_cost": _judge_costs(clean, "original_answer_cost_usd"),
            "historical_second_judge_cost": _judge_costs(clean, "second_answer_cost_usd"),
            "second_judge_attempt_disclosure": {"attempts": len(attempts), "cached_attempts": sum(bool(a.get("cached")) for a in attempts),
                                                "status_counts": dict(Counter(str(a.get("status")) for a in attempts)),
                                                "retry_attempts": sum(max(0, len(a.get("attempts", [])) - 1) for a in labels if a.get("status") == "valid")},
            "historical_judge_latency": {"available": False, "original_seconds": None, "second_seconds": None,
                                         "reason": "Saved judge metadata has no call timing. Agent seconds measures answer generation. No faster-than-judge conclusion is permitted."},
            "rules": conditions, "decision": "inconclusive" if not complete else "candidate_for_further_verifier_evaluation" if all(conditions.values()) else "failed_screen"}


def analyse(triage_dir: Path, support_dir: Path, out: Path) -> dict:
    """Write a new result only; incomplete and duplicate runs cannot pass screens."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"refusing to overwrite immutable result: {out}")
    baseline_path = paths.EXPERIMENTS / "triage/triage-v1-luna/raw.jsonl"
    labels_path = paths.EXPERIMENTS / "xjudge/sonnet55-FIN-s60-b-20261102/labels.json"
    baseline = _rows(baseline_path)
    labels = json.loads(labels_path.read_text())
    tm, ts, tr, ti = _load_run(Path(triage_dir), "triage", 1227)
    sm, ss, sr, si = _load_run(Path(support_dir), "support", 441)
    if hashlib.sha256(baseline_path.read_bytes()).hexdigest() != BASELINE_SHA256:
        ti.append("frozen historical baseline fingerprint mismatch")
    if hashlib.sha256(labels_path.read_bytes()).hexdigest() != LABELS_SHA256:
        si.append("frozen support reference fingerprint mismatch")
    result = {"protocol": "docs/experiments/decisions-api-prereg.md", "seed": SEED, "bootstrap_draws": N_BOOT,
              "rules": {"A70_confidence_threshold": .70, "support_probability_threshold": .50, "quantiles": "nearest rank ceil(q*n)",
                        "bootstrap": "case clusters for A; (model,set,case_id) clusters retaining both arms and every claim for B; percentile 95%",
                        "undefined_intervals": "Unavailable if fewer than 95% of bootstrap draws are defined.",
                        "binomial_intervals": "Wilson 95%, descriptive only. Repeats, claims and retrieval arms are dependent.",
                        "interpretation": "No automatic adoption, human truth, unsupported-claim detection, causal speedup or B historical latency claim."},
              "inputs": {"triage_dir": str(triage_dir), "support_dir": str(support_dir),
                         "triage_manifest": tm, "support_manifest": sm, "triage_status": ts, "support_status": ss},
              "triage": _triage(tr, baseline, ti), "support": _support(sr, labels, si)}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    return result
