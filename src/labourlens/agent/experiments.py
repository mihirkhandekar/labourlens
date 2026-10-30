"""End-to-end agent experiments (D-016, D-022, D-026). One factor at a time, dev split until the freeze.

A1 model pair for planner and answer step (same prompts, tools, bounds)
Raw runs (they contain MOM quotes) go to data/runs/; committed files hold metrics and per-case scores only.
"""

from __future__ import annotations

import json
import statistics
from concurrent.futures import ThreadPoolExecutor

from labourlens import paths
from labourlens.agent.graph import AgentConfig, run_agent
from labourlens.agent.tools import Shared
from labourlens.answer import experiments as ae
from labourlens.answer import validate as vd
from labourlens.retrieval import evaluate as ev

WORKERS = 3
MODEL_PAIRS = {"gpt-6-luna": ("gpt-6-luna", "gpt-6-luna"), "gpt-5.6-luna": ("gpt-5.6-luna", "gpt-5.6-luna"), "gpt-4.1-mini": ("gpt-4.1-mini", "gpt-4.1-mini")}


def _calc_correct(case: dict, res: dict) -> bool | None:
    calc = case.get("calculation")
    if not calc or not res["answer"]:
        return None if not calc else False
    a = res["answer"]
    text = " ".join([a["summary"]] + [c["text"] for c in a["claims"]])
    want = float(calc["expected_value"])
    got = {float(n) for n in vd.numbers(text)}
    return any(abs(g - want) < 0.005 or abs(g - abs(want)) < 0.005 for g in got)


def to_record(res: dict) -> dict:
    ungr = next((e["detail"].get("ungrounded_numbers", []) for e in reversed(res["trace"]) if e["node"] == "validate_answer"), [])
    attempts = sum(1 for e in res["trace"] if e["node"] == "generate_answer" and e["event"] == "generated")
    return {"answer": res["answer"], "valid": res["outcome"] not in ("invalid", "operational_failure", "rejected_input"),
            "operational_failure": res["outcome"] == "operational_failure", "attempts": max(attempts, 1), "errors": res["errors"],
            "ungrounded_numbers": ungr, "context_passage_ids": [e["id"] for e in res["evidence"]], "cited_passage_ids": res["cited_ids"],
            "seconds": res["seconds"], "prompt_tokens": res["usage"]["prompt_tokens"], "completion_tokens": res["usage"]["completion_tokens"]}


def score_run(case: dict, res: dict) -> dict:
    s = ae.score(case, to_record(res), include_data_gold=True)
    s.update({"outcome": res["outcome"], "tool_calls": res["tool_calls"], "rounds": res["rounds"], "cost_usd": res["usage"]["cost_usd"],
              "tools_used": sorted({e["detail"]["tool"] for e in res["trace"] if e["node"] == "execute_tool"}),
              "tool_errors": sum(1 for e in res["trace"] if e["node"] == "execute_tool" and e["event"] != "ok")})
    cc = _calc_correct(case, res)
    if cc is not None:
        s["calc_correct"] = cc
    return s


def aggregate(scores: list[dict]) -> dict:
    m = ae.aggregate(scores, "gpt-4.1-mini")  # token cost is replaced below with the exact per-run cost
    m.pop("cost_per_case_usd", None)
    n = len(scores)
    calc = [s["calc_correct"] for s in scores if "calc_correct" in s]
    m.update({
        "calc_correct_rate": round(sum(calc) / len(calc), 3) if calc else None, "n_calc_cases": len(calc),
        "tool_calls_mean": round(statistics.mean(s["tool_calls"] for s in scores), 2),
        "tool_error_rate": round(sum(1 for s in scores if s["tool_errors"]) / n, 3),
        "cost_per_case_usd": round(sum(s["cost_usd"] for s in scores) / n, 5),
        "gold_cited_any_rate": round(sum(1 for s in scores if s.get("gold_cited")) / max(1, sum(1 for s in scores if "gold_cited" in s)), 3),
    })
    return m


COLS = ["valid_rate", "behavior_accuracy", "over_abstention_rate", "false_answer_rate", "numbers_complete_rate", "calc_correct_rate",
        "gold_cited_any_rate", "tool_calls_mean", "tool_error_rate", "operational_failures", "latency_p50_s", "cost_per_case_usd"]


def run(split: str = "dev", pairs: list[str] | None = None) -> None:
    cases = ev.load_cases(split)
    shared = Shared()
    exp = f"agent-{split}-A1"
    rows = {}
    for label in pairs or MODEL_PAIRS:
        pm, am = MODEL_PAIRS[label]
        cfg = AgentConfig(planner_model=pm, answer_model=am)
        print(f"[agent] {label} on {len(cases)} cases", flush=True)
        with ThreadPoolExecutor(WORKERS) as ex:
            results = list(ex.map(lambda c: (c, run_agent(c["question"], shared, cfg)), cases))
        raw = paths.DATA / "runs" / exp
        raw.mkdir(parents=True, exist_ok=True)
        (raw / f"{label}.jsonl").write_text("\n".join(json.dumps({"case_id": c["case_id"], **r}, default=str) for c, r in results) + "\n")
        scores = [score_run(c, r) for c, r in results]
        pub = paths.EXPERIMENTS / "runs" / exp
        pub.mkdir(parents=True, exist_ok=True)
        (pub / f"{label}.scores.jsonl").write_text("\n".join(json.dumps(s) for s in scores) + "\n")
        rows[label] = aggregate(scores)
        (pub / f"{label}.metrics.json").write_text(json.dumps({"label": label, "config": cfg.key(), "metrics": rows[label]}, indent=1))
    lines = [f"# Agent end-to-end, split `{split}`, A1 model pair (n={len(cases)} cases)", "",
             "Draft gold labels. Planner and answer step use the same model. Prompts planner_v1 and answer_v2. Rates are over cases.", "",
             "| config | " + " | ".join(COLS) + " |", "|---|" + "---|" * len(COLS)]
    lines += [f"| {k} | " + " | ".join(str(m[c]) for c in COLS) + " |" for k, m in rows.items()]
    text = "\n".join(lines) + "\n"
    (paths.EXPERIMENTS / "runs" / f"{exp}-SUMMARY.md").write_text(text)
    print(text)
