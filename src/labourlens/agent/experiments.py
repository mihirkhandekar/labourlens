"""End-to-end agent experiments (D-016, D-022, D-026). One factor at a time, dev split until the freeze.

A1 model pair for planner and answer step (same prompts, tools, bounds)
Raw runs (they contain MOM quotes) go to data/runs/; committed files hold metrics and per-case scores only.
"""

from __future__ import annotations

import json
import hashlib
import re
from decimal import Decimal
import statistics
from concurrent.futures import ThreadPoolExecutor

from labourlens import paths
from labourlens.agent.graph import AgentConfig, run_agent
from labourlens.agent.tools import Shared, compute_change
from labourlens.answer import experiments as ae
from labourlens.retrieval import evaluate as ev
from labourlens.evaluation.provenance import snapshot

WORKERS = 3
MODEL_PAIRS = {"gpt-6-luna": ("gpt-6-luna", "gpt-6-luna"), "gpt-5.6-luna": ("gpt-5.6-luna", "gpt-5.6-luna"), "gpt-4.1-mini": ("gpt-4.1-mini", "gpt-4.1-mini")}


def _calc_correct(case: dict, res: dict) -> bool | None:
    """Require a cited deterministic record, correct operands/order, operation, unit and signed result.

    A matching incidental number or unsigned magnitude in prose is not calculation evidence.
    """
    calc = case.get("calculation")
    if not calc or not res["answer"]:
        return None if not calc else False
    periods = {oid: e["period"] for e in case.get("evidence_data", []) for oid in e.get("observation_ids", [])}
    inputs = calc["inputs"]
    if len(inputs) != 2 or any(i not in periods for i in inputs):
        return False
    ia, ib = sorted(inputs, key=lambda i: periods[i])
    kind = "percent_change" if "relative percent change" in calc["formula"].replace("not relative percent change", "") else "difference"
    cid = "calc:" + hashlib.sha256(f"{ia}|{ib}|{kind}".encode()).hexdigest()[:12]
    items = {e["label"]: e for e in res.get("evidence", [])}
    texts = res.get("evidence_text", {})
    cited = {c["label"] for claim in res["answer"]["claims"] for c in claim["citations"]}
    number = r"-?\d+(?:\.\d+)?"
    for label in cited:
        if items.get(label, {}).get("id") != cid:
            continue
        text = texts.get(label, "")
        if not text.startswith(f"Calculated {kind.replace('_', ' ')} of "):
            continue
        match = re.search(r"from (\d{4}-Q[1-4]) to (\d{4}-Q[1-4]): (.*?) = (" + number + r") (.*?)\. Inputs (\w+) \((.*?)\) and (\w+) \((.*?)\)\.", text)
        if not match:
            continue
        pa, pb, formula, value, unit, la, ipa, lb, ipb = match.groups()
        if (pa, pb, ipa, ipb) != (periods[ia], periods[ib], periods[ia], periods[ib]):
            continue
        if items.get(la, {}).get("id") != ia or items.get(lb, {}).get("id") != ib:
            continue
        values = []
        for lab in (la, lb):
            parts = texts.get(lab, "").split(" | ")
            if len(parts) < 3:
                break
            m = re.fullmatch(r"(-?[\d,]+(?:\.\d+)?)(%| persons| vacancies| \(ratio\))", parts[-2])
            if not m:
                break
            values.append((m[1].replace(",", ""), {"%": "percent", " (ratio)": "ratio"}.get(m[2], m[2].strip())))
        if len(values) != 2 or values[0][1] != values[1][1]:
            continue
        expected, _, expected_unit, expected_formula = compute_change(values[0][0], values[1][0], kind, values[0][1])
        if formula != expected_formula or unit != expected_unit or Decimal(value) != expected or abs(expected - Decimal(str(calc["expected_value"]))) >= Decimal("0.005"):
            continue
        # Legacy gold has descriptive aliases for ratio units; do not conflate counts or percent.
        aliases = {"ratio": "vacancies per unemployed person"}
        if aliases.get(unit, unit) != aliases.get(calc["unit"], calc["unit"]):
            continue
        claims = [c["text"] for c in res["answer"]["claims"] if any(x["label"] == label for x in c["citations"])]
        down = r"(?:decreas\w*|declin\w*|fell|fall\w*|drop\w*|lower|fewer|reduc\w*|down)"
        up = r"(?:increas\w*|rose|ris\w*|grew|growth|higher|more|up)"
        for prose in claims:
            prose = re.sub(r"(?<=\d),(?=\d)", "", prose)
            magnitude = abs(expected)
            tokens = [(m.start(), Decimal(m.group())) for m in re.finditer(r"\d+(?:\.\d+)?", prose)]
            hits = [pos for pos, v in tokens if abs(v - magnitude) < Decimal("0.005")]
            if not hits:
                continue
            # Unit wording is free (people/persons, % / percent); the cited record carries the unit.
            # Direction must agree with the sign of the deterministic result.
            signed_down = bool(re.search(r"(?:change\w*|difference|delta)[^.;]{0,80}?[-\u2212]\s*$", prose[:max(hits)], re.I))
            has_down = bool(re.search(down, prose, re.I)) or signed_down
            has_up = bool(re.search(up, prose, re.I))
            if expected < 0 and has_down and not has_up:
                return True
            if expected > 0 and not has_down:
                return True
            if expected == 0:
                return True
    return False


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


def run(split: str = "dev", pairs: list[str] | None = None, answer_prompt: str = "answer_v3", tag: str = "A1",
        retrieval: str = "hybrid", planner_prompt: str = "planner_v1", gold_path=None) -> None:
    cases = ev.load_cases(split, gold_path)
    shared = Shared()
    exp = f"agent-{split}-{tag}"
    rows = {}
    for label in pairs or MODEL_PAIRS:
        pm, am = MODEL_PAIRS[label]
        cfg = AgentConfig(planner_model=pm, answer_model=am, answer_prompt=answer_prompt, retrieval=retrieval, planner_prompt=planner_prompt)
        provenance = snapshot(cfg.key(), len(cases), len(cases), gold_path=gold_path)
        print(f"[agent] {label} on {len(cases)} cases", flush=True)
        with ThreadPoolExecutor(WORKERS) as ex:
            results = list(ex.map(lambda c: (c, run_agent(c["question"], shared, cfg)), cases))
        raw = paths.DATA / "runs" / exp
        raw.mkdir(parents=True, exist_ok=True)
        (raw / f"{label}.jsonl").write_text("\n".join(json.dumps({"case_id": c["case_id"], **r, "generation_provenance": provenance}, default=str) for c, r in results) + "\n")
        scores = [{**score_run(c, r), "provenance": provenance} for c, r in results]
        pub = paths.EXPERIMENTS / "runs" / exp
        pub.mkdir(parents=True, exist_ok=True)
        (pub / f"{label}.scores.jsonl").write_text("\n".join(json.dumps(s) for s in scores) + "\n")
        rows[label] = aggregate(scores)
        (pub / f"{label}.metrics.json").write_text(json.dumps({"label": label, "config": cfg.key(), "provenance": provenance, "metrics": rows[label]}, indent=1))
    lines = [f"# Agent end-to-end, split `{split}`, {tag} (available n={len(cases)})", "",
             f"Draft gold labels. Planner and answer step use the same model. Prompts `{planner_prompt}` and `{answer_prompt}`; retrieval `{retrieval}`. Rates are over scored cases.", "",
             "Scored n by configuration: " + ", ".join(f"{label}={m['n']}" for label, m in rows.items()) + ".", "",
             "| config | " + " | ".join(COLS) + " |", "|---|" + "---|" * len(COLS)]
    lines += [f"| {k} | " + " | ".join(str(m[c]) for c in COLS) + " |" for k, m in rows.items()]
    text = "\n".join(lines) + "\n"
    (paths.EXPERIMENTS / "runs" / f"{exp}-SUMMARY.md").write_text(text)
    print(text)
