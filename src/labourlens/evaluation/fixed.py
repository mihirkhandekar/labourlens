"""Offline fixed-policy comparison with two frozen agent replicates. No model calls."""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

import numpy as np

from labourlens import paths
from labourlens.evaluation import paired
from labourlens.retrieval.evaluate import load_cases

MODEL = "gpt-6-luna"
REFERENCES = ("agent-dev-FIN-r3", "agent-dev-FIN2-r3")
CONFIG = "planner=gpt-6-luna|answer=gpt-6-luna|planner_v1|answer_v3|retrieval=r3"


def describe(rows: dict[str, dict], cases: list[dict]) -> dict:
    values = list(rows.values())
    seconds = sorted(float(r["seconds"]) for r in values)
    return {
        "n": len(values), "behaviour_accuracy": statistics.mean(bool(r["behavior_ok"]) for r in values),
        "false_answers": sum(bool(r["false_answer"]) for r in values),
        "over_abstentions": sum(bool(r["over_abstain"]) for r in values),
        "operational_failures": sum(bool(r["operational_failure"]) for r in values),
        "latency_median_s": statistics.median(seconds),
        "latency_p95_s": seconds[math.ceil(.95 * len(seconds)) - 1],
        "usage_cost_per_question_usd": statistics.mean(float(r["cost_usd"]) for r in values),
        "judge_cost_per_question_usd": statistics.mean(float(r.get("judge_cost_usd", 0)) for r in values),
        "per_question": [{"case_id": i, "seconds": r["seconds"], "cost_usd": r["cost_usd"],
                          "judge_cost_usd": r.get("judge_cost_usd", 0)} for i, r in sorted(rows.items())],
        "by_family": {f: {"n": len(ids), "behaviour_accuracy": statistics.mean(bool(rows[i]["behavior_ok"]) for i in ids)}
                      for f in sorted({c["family"] for c in cases})
                      for ids in [[c["case_id"] for c in cases if c["family"] == f]]},
    }


def analyse(candidate: dict, first: dict, second: dict, cases: list[dict], *, n_boot=10000, seed=20261030) -> dict:
    expected = {c["case_id"] for c in cases}
    if not cases or any(set(r) != expected for r in (candidate, first, second)):
        raise ValueError("Exact non-empty case-set equality is required for all three arms")
    comparisons = [paired.compare(candidate, r, cases, n_boot=n_boot, seed=seed, level=.95) for r in (first, second)]
    ids = sorted(expected)
    agent_mean = np.array([(bool(first[i]["behavior_ok"]) + bool(second[i]["behavior_ok"])) / 2 for i in ids])
    fixed = np.array([float(bool(candidate[i]["behavior_ok"])) for i in ids])
    diffs = fixed - agent_mean
    components = paired.components(cases)
    mean = {"agent_accuracy": float(agent_mean.mean()), "fixed_accuracy": float(fixed.mean()),
            "paired_difference": float(diffs.mean()),
            "case_bootstrap_interval": paired._interval(diffs, np.array(ids), n_boot, seed, .95),
            "component_bootstrap_interval": paired._interval(diffs, np.array([components[i] for i in ids]), n_boot, seed, .95),
            "mcnemar_exact_p": None, "mcnemar_note": "Not defined for fractional replicate means"}
    positive = all(c["case_bootstrap_interval"][0] > 0 and c["component_bootstrap_interval"][0] > 0 for c in comparisons)
    negative = all(c["case_bootstrap_interval"][1] < 0 and c["component_bootstrap_interval"][1] < 0 for c in comparisons)
    significant = all(c["mcnemar_exact_p"] <= .05 for c in comparisons)
    fixed_false = sum(bool(r["false_answer"]) for r in candidate.values())
    agent_false = [sum(bool(r["false_answer"]) for r in arm.values()) for arm in (first, second)]
    verdict = "inconclusive"
    if positive and significant and mean["paired_difference"] > 0 and all(fixed_false <= n for n in agent_false):
        verdict = "fixed development advantage"
    if negative and significant and mean["paired_difference"] < 0 and all(n <= fixed_false for n in agent_false):
        verdict = "agent development advantage"
    floor = sum(c["expected_behavior"] in ("answer", "ignore_injection_and_answer") for c in cases) / len(cases)
    return {"n": len(cases), "always_answer_floor": floor, "single_run_comparisons": dict(zip(REFERENCES, comparisons)),
            "agent_two_run_mean_comparison": mean, "decision": verdict,
            "agent_run_flips": sum(first[i]["behavior_ok"] != second[i]["behavior_ok"] for i in ids),
            "arms": {k: describe(r, cases) for k, r in zip(("fixed", *REFERENCES), (candidate, first, second))},
            "agent_mean_by_family": {f: statistics.mean((bool(first[c["case_id"]]["behavior_ok"]) + bool(second[c["case_id"]]["behavior_ok"])) / 2
                                                       for c in cases if c["family"] == f) for f in sorted({c["family"] for c in cases})}}


def preflight(cases: list[dict], shared, cfg, gold: Path) -> dict:
    """Check frozen case text, prompts and report corpus before any paid call."""
    import os

    from labourlens.evaluation.provenance import snapshot

    if cfg.key() != CONFIG + "|control=fixed":
        raise ValueError("Registered fixed experiment requires primary model, base tools, R3 and frozen prompts")
    if any(os.environ.get(key) == "off" for key in ("LABOURLENS_GUARDS", "LABOURLENS_CROSSCHECK")):
        raise ValueError("Registered fixed experiment requires guards and cross-check enabled")
    root = paths.EXPERIMENTS / "eval"
    metrics_paths = {e: root / e / f"{MODEL}.metrics.json" for e in REFERENCES}
    paired.check_gold(gold, metrics_paths)
    expected = {c["case_id"]: c["question"] for c in cases}
    if len(expected) != 237:
        raise ValueError("Registered fixed experiment requires exactly 237 development cases")
    current = snapshot(cfg.key(), len(cases), len(cases), gold_path=gold)
    for exp, p in metrics_paths.items():
        metadata = json.loads(p.read_text())
        if metadata["provenance"]["prompt_sha256"] != current["prompt_sha256"]:
            raise ValueError(f"Frozen/current prompt mismatch: {exp}")
        raw = paired.load_rows(paths.DATA / "runs" / exp / f"{MODEL}.jsonl")
        if {i: r["question"] for i, r in raw.items()} != expected:
            raise ValueError(f"Frozen/current question-set mismatch: {exp}")
        if not shared.corpus or any(r.get("corpus") != shared.corpus for r in raw.values()):
            raise ValueError(f"Frozen/current report corpus mismatch: {exp}")
    return {"case_count": len(expected), "corpus": shared.corpus, "prompt_sha256": current["prompt_sha256"]}


def run(gold: Path, candidate: str, out: Path) -> dict:
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite {out}")
    experiments = (candidate, *REFERENCES)
    root = paths.EXPERIMENTS / "eval"
    metrics_paths = {exp: root / exp / f"{MODEL}.metrics.json" for exp in experiments}
    paired.check_gold(gold, metrics_paths)
    metrics = {exp: json.loads(p.read_text()) for exp, p in metrics_paths.items()}
    reference = metrics[REFERENCES[0]]
    rows = {exp: paired.load_rows(root / exp / f"{MODEL}.cases.jsonl") for exp in experiments}
    cases = load_cases("dev", gold)
    corpus = None
    for exp in experiments:
        m = metrics[exp]
        expected_config = CONFIG + ("|control=fixed" if exp == candidate else "")
        if m["judge"] != "gpt-6.1-terra" or m["provenance"]["agent_config"] != expected_config:
            raise ValueError(f"Model, judge or configuration mismatch: {exp}")
        if m["provenance"]["prompt_sha256"] != reference["provenance"]["prompt_sha256"]:
            raise ValueError(f"Prompt fingerprint mismatch: {exp}")
        raw_path = paths.DATA / "runs" / exp / f"{MODEL}.jsonl"
        raw = paired.load_rows(raw_path)
        if set(raw) != set(rows[exp]):
            raise ValueError(f"Raw/scored case-set mismatch: {exp}")
        expected_questions = {c["case_id"]: c["question"] for c in cases}
        if {i: r["question"] for i, r in raw.items()} != expected_questions:
            raise ValueError(f"Raw/gold question-set mismatch: {exp}")
        for r in raw.values():
            if r.get("crosscheck_enabled") is not True:
                raise ValueError(f"Generation cross-check mismatch: {exp}")
            if not r.get("corpus"):
                raise ValueError(f"Missing generation corpus identity: {exp}")
            if corpus is None:
                corpus = r["corpus"]
            if r["corpus"] != corpus:
                raise ValueError(f"Generation corpus mismatch: {exp}")
            if r["config"] != expected_config:
                raise ValueError(f"Generation configuration mismatch: {exp}")
            if r.get("generation_provenance", {}).get("prompt_sha256") != reference["provenance"]["prompt_sha256"]:
                raise ValueError(f"Generation prompt fingerprint mismatch: {exp}")
    result = {"candidate": candidate, "references": REFERENCES, "gold": str(gold), "corpus": corpus,
              "scoring_provenance": {e: metrics[e]["provenance"] for e in experiments},
              "scorer_limit": "Scoring functions unchanged between frozen scoring commits and preparation; wrapper changes add provenance and overwrite protection. Historical runtime drift remains possible.",
              **analyse(rows[candidate], rows[REFERENCES[0]], rows[REFERENCES[1]], cases)}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1) + "\n")
    return result
