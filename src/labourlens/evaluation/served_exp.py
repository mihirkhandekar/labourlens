"""Evaluate the actual served chain without modifying frozen agent experiments."""
from __future__ import annotations

import json
import math
import re
import statistics
import time
from pathlib import Path

from labourlens import paths
from labourlens.agent import experiments as agx
from labourlens.agent.graph import AgentConfig
from labourlens.agent.served import make_runner, make_shared
from labourlens.agent.contextualise import singapore_today
from labourlens.evaluation.provenance import file_hash, sampling_block, snapshot
from labourlens.retrieval.evaluate import load_cases

STEPS = ("smalltalk", "contextualise", "triage", "agent")
QUERY_KEYS = ("source_id", "period_from", "period_to", "dimension", "adjustment", "indicator_id")
ROW_KEYS = ("observation_id", "period", "unit", "value")


class RecordingBackend:
    """Transparent statistics recorder; preserves backend bounds, errors and quarantined rows."""
    def __init__(self, backend):
        self.backend = backend
        self.records = []
        self.unlogged_failures = []

    def __getattr__(self, name):
        return getattr(self.backend, name)

    def query(self, *args, **kwargs):
        arguments = {**dict(zip(QUERY_KEYS, args)), **kwargs}
        record = {"arguments": {k: arguments.get(k) for k in QUERY_KEYS}, "rows": None, "error": None}
        attempts = getattr(self.backend, "calls", None)
        previous = attempts[-1] if attempts else None
        try:
            rows, error = self.backend.query(*args, **kwargs)
            record["rows"] = None if rows is None else sorted(
                [{k: row[k] for k in ROW_KEYS} for row in rows], key=lambda r: r["observation_id"])
            record["error"] = error.error_kind if error is not None else None
            return rows, error
        except Exception as exc:
            record["error"] = type(exc).__name__
            # SyncStatsBackend's FutureTimeout branch raises without adding a log row.
            # Count that failed invocation too, without double-counting logged retries.
            if attempts is not None and (attempts[-1] if attempts else None) is previous:
                self.unlogged_failures.append({"tool": "get_statistic", "arguments": record["arguments"],
                                               "ok": False, "kind": type(exc).__name__, "unlogged_backend_failure": True})
            raise
        finally:
            self.records.append(record)


def evaluate_case(case, shared, config, *, route="mcp", web_steps=True):
    steps = {s: {"seconds": 0.0, "cost_usd": 0.0, "executed": False} for s in STEPS}

    def observe(step, info):
        steps[step] = {**info, "executed": True}

    recorder = shared.stats_backend if route == "mcp" else shared.stats
    if isinstance(recorder, RecordingBackend):
        recorder.records.clear()
        recorder.unlogged_failures.clear()
    backend = getattr(shared, "stats_backend", None)
    if route == "mcp":
        backend.calls.clear()
    runner = make_runner(config, web_steps=web_steps, save_trace=False, observer=observe)
    start = time.perf_counter()
    result = runner(case["question"], shared, history=case.get("history"))
    # Scorers match the original case question and require a single arm config.
    # Preserve the actual rewritten question and early-exit config separately.
    result["effective_question"] = result.get("question")
    result["executed_config"] = result.get("config")
    result["question"] = case["question"]
    result["config"] = config.key()
    result["seconds"] = round(time.perf_counter() - start, 6)
    calls = list(backend.calls) if route == "mcp" else []
    if route == "mcp" and isinstance(recorder, RecordingBackend):
        calls.extend(recorder.unlogged_failures)
    diverted = any(steps[s].get("diverted", False) for s in ("smalltalk", "triage"))
    result["served"] = {"route": route, "web_steps": web_steps, "steps": steps, "diverted": diverted,
                        "agent_called": steps["agent"]["executed"], "mcp_calls": len(calls),
                        "mcp_errors": sum(not c["ok"] for c in calls), "mcp_attempts": calls,
                        "statistics_calls": list(recorder.records) if isinstance(recorder, RecordingBackend) else []}
    return result


def score_case(case, result):
    score = agx.score_run(case, result)
    served = result["served"]
    answerable_gold = not case.get("not_part_of_gold", False) and score["expected"] == "answered"
    score.update(served=served, is_probe=bool(case.get("not_part_of_gold", False)),
                 answerable_gold=answerable_gold, false_diversion=answerable_gold and served["diverted"])
    if "expected_agent_called" in case:
        score["probe_route_ok"] = served["agent_called"] == case["expected_agent_called"]
    return score


def aggregate(scores):
    metrics = agx.aggregate(scores)
    eligible = [s for s in scores if s["answerable_gold"]]
    metrics["false_diversions"] = sum(s["false_diversion"] for s in scores)
    metrics["answerable_gold_n"] = len(eligible)
    metrics["false_diversion_rate"] = sum(s["false_diversion"] for s in eligible) / len(eligible) if eligible else None
    metrics["mcp_call_count"] = sum(s["served"]["mcp_calls"] for s in scores)
    metrics["mcp_error_count"] = sum(s["served"]["mcp_errors"] for s in scores)
    metrics["latency_p50_s"] = statistics.median(s["seconds"] for s in scores)
    metrics["latency_p95_s"] = sorted(s["seconds"] for s in scores)[math.ceil(.95 * len(scores)) - 1]
    metrics["steps"] = {step: {
        "executed_n": sum(s["served"]["steps"][step]["executed"] for s in scores),
        "latency_mean_s": statistics.mean(s["served"]["steps"][step]["seconds"] for s in scores),
        "cost_mean_usd": statistics.mean(s["served"]["steps"][step]["cost_usd"] for s in scores),
        "failure_n": sum(bool(s["served"]["steps"][step].get("error")) for s in scores),
    } for step in STEPS}
    probes = [s for s in scores if s["is_probe"]]
    metrics["probe_failures"] = [s["case_id"] for s in probes if not s["behavior_ok"] or not s.get("probe_route_ok", True)
                                 or any(s["served"]["steps"][step].get("error") for step in ("contextualise", "triage"))]
    return metrics


def select_cases(cases, limit=None, case_ids=None):
    if limit is not None and limit < 1:
        raise ValueError("--limit must be positive")
    if case_ids:
        wanted = set(case_ids)
        unknown = wanted - {c["case_id"] for c in cases}
        if unknown:
            raise ValueError(f"Unknown case ids: {sorted(unknown)}")
        cases = [c for c in cases if c["case_id"] in wanted]
    cases = cases[:limit] if limit is not None else cases
    if not cases:
        raise ValueError("No cases selected")
    if len({c["case_id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate case ids")
    return cases


def run(split="dev", gold_path=None, pairs=None, tag=None, retrieval="r3", route="mcp", web_steps="on", limit=None, case_ids=None):
    if not tag or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", tag):
        raise ValueError("--tag must be a new path-safe experiment label")
    labels = pairs or list(agx.MODEL_PAIRS)
    if len(set(labels)) != len(labels) or any(label not in agx.MODEL_PAIRS for label in labels):
        raise ValueError("--pairs must contain distinct agent-exp model labels")
    exp = f"served-{split}-{tag}"
    pub, raw = paths.EXPERIMENTS / "runs" / exp, paths.DATA / "runs" / exp
    if pub.exists() or raw.exists():
        raise FileExistsError(f"{exp} already exists; choose a new --tag")
    available = load_cases(split, gold_path)
    cases = select_cases(available, limit, case_ids)
    today = str(singapore_today())
    if any(c.get("fixture_date", today) != today for c in cases):
        raise ValueError("Registered probes have a different Singapore date; use a newly registered fixture")
    pub.mkdir(parents=True, exist_ok=False)  # reserve id before startup or paid calls
    raw.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    shared = make_shared(route == "mcp")
    startup = time.perf_counter() - started
    backend = getattr(shared, "stats_backend", None)
    if route == "mcp":
        shared.stats_backend = RecordingBackend(backend)
    else:
        shared.stats = RecordingBackend(shared.stats)
    try:
        for label in labels:
            pm, am = agx.MODEL_PAIRS[label]
            cfg = AgentConfig(planner_model=pm, answer_model=am, retrieval=retrieval, run_deadline_s=80.0)
            provenance = {**snapshot(cfg.key(), len(cases), len(available), gold_path=gold_path), "sampling": sampling_block(cfg),
                          "served": {"route": route, "web_steps": web_steps, "order": list(STEPS), "singapore_date": today,
                                     "shared_startup_seconds": startup, "case_ids": [c["case_id"] for c in cases],
                                     "contextualise_model": "gpt-6-luna", "triage_model": "gpt-6-luna",
                                     "contextualise_prompt_sha256": file_hash(paths.ROOT / "prompts/contextualise_v1.md"),
                                     "triage_prompt_sha256": file_hash(paths.ROOT / "prompts/triage_v1.md")}}
            scores = []
            with (raw / f"{label}.jsonl").open("x") as output:
                for case in cases:
                    result = evaluate_case(case, shared, cfg, route=route, web_steps=web_steps == "on")
                    output.write(json.dumps({"case_id": case["case_id"], **result, "generation_provenance": provenance}, default=str) + "\n")
                    output.flush()
                    scores.append({**score_case(case, result), "provenance": provenance})
            (pub / f"{label}.scores.jsonl").write_text("\n".join(json.dumps(s) for s in scores) + "\n")
            metrics = {"all": aggregate(scores)}
            for name, subset in (("gold", [s for s in scores if not s["is_probe"]]), ("probes", [s for s in scores if s["is_probe"]])):
                metrics[name] = aggregate(subset) if subset else None
            (pub / f"{label}.metrics.json").write_text(json.dumps({"label": label, "config": cfg.key(), "provenance": provenance,
                                                                              "metrics": metrics}, indent=2) + "\n")
            print(f"{exp} {label}: {len(scores)} cases, behaviour={metrics['all']['behavior_accuracy']}", flush=True)
    finally:
        if backend is not None:
            backend.close()


def compare_statistics(candidate: Path, baseline: Path):
    """Offline matched-call parity audit of two raw model JSONLs. No match is not a pass."""
    def calls(path):
        result = {}
        for line in path.read_text().splitlines():
            row = json.loads(line)
            for call in row["served"]["statistics_calls"]:
                if call["error"] is None:
                    key = (row["case_id"], json.dumps(call["arguments"], sort_keys=True))
                    result.setdefault(key, []).append(call["rows"])
        return result
    left, right = calls(candidate), calls(baseline)
    shared = sorted(left.keys() & right.keys())
    mismatches = [{"case_id": k[0], "arguments": json.loads(k[1])} for k in shared if any(a != b for a in left[k] for b in right[k])]
    return {"matched_signatures": len(shared), "candidate_only": len(left.keys() - right.keys()),
            "baseline_only": len(right.keys() - left.keys()), "mismatches": mismatches,
            "verdict": "fail" if mismatches else ("pass" if shared else "unevaluable")}


def compare_fin(candidate: Path, baseline: Path):
    """H1 on exactly the served run's selected gold ids; frozen FIN rows are read only."""
    served = [json.loads(line) for line in candidate.read_text().splitlines() if line.strip()]
    served = [s for s in served if not s["is_probe"]]
    fin = {s["case_id"]: s for s in (json.loads(line) for line in baseline.read_text().splitlines() if line.strip())}
    missing = sorted({s["case_id"] for s in served} - fin.keys())
    if missing or not served:
        return {"verdict": "unevaluable", "missing_fin_ids": missing, "n": len(served)}
    n = len(served)
    candidate_accuracy = sum(s["behavior_ok"] for s in served) / n
    baseline_accuracy = sum(fin[s["case_id"]]["behavior_ok"] for s in served) / n
    diversions = sum(s["false_diversion"] for s in served)
    return {"n": n, "served_accuracy": candidate_accuracy, "fin_accuracy": baseline_accuracy,
            "difference": candidate_accuracy - baseline_accuracy, "false_diversions": diversions,
            "verdict": "pass" if abs(candidate_accuracy - baseline_accuracy) <= .03 and not diversions else "fail"}
