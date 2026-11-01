"""Measure the conversation-context rewrite (D-054).

Two parts. (1) Free and deterministic: every gold, held-out v2, threat and off-topic question with no history must reach the agent
unchanged without a model call, except the few that contain a relative date or a layoff verb (listed in the output; those get a paid
check that the rewrite keeps every number of the original). (2) Paid: 30 hand-written conversation cases (24 ordinary, 6 with
instructions planted in the history) scored by deterministic string features, not by a model judge. Raw outputs hold our own question
text and the model's one-line rewrites only, never MOM/MTI text. Each run gets a new experiment id and never overwrites (D-016)."""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from labourlens import paths
from labourlens.agent import contextualise as cx
from labourlens.evaluation import triage_check
from labourlens.security.guards import injection_flags

OUT = paths.EXPERIMENTS / "context"
CASES = OUT / "cases.jsonl"
MAX_WORKERS = 6
_NUMBER = re.compile(r"\d+")


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_cases() -> list[dict]:
    return _rows(CASES)


def standalone_questions() -> list[dict]:
    """Every gold, v2, threat and off-topic question (reuses the triage-check loader)."""
    return [{"case_id": c["case_id"], "set": c["set"], "question": c["question"]} for c in triage_check.load_cases()]


def passthrough_audit() -> dict:
    """Deterministic and free: with empty history, which standalone questions would trigger a call? Never calls the model."""
    qs = standalone_questions()
    triggered = [q for q in qs if cx.needs_rewrite(q["question"], [])]
    return {"n": len(qs), "unchanged_without_call": len(qs) - len(triggered), "triggered": [{"case_id": q["case_id"], "set": q["set"], "match": cx.TRIGGER.search(q["question"]).group(0)} for q in triggered]}


def triggered_questions() -> list[dict]:
    keep = {t["case_id"] for t in passthrough_audit()["triggered"]}
    return [q for q in standalone_questions() if q["case_id"] in keep and q["set"] != "offtopic"]


def check_features(case: dict, rewritten: str) -> dict:
    low = rewritten.lower()
    feats = {"single_line_max_300": "\n" not in rewritten and 0 < len(rewritten) <= cx.MAX_REWRITE_CHARS,
             "contains_all": all(s.lower() in low for s in case["must_contain"]),
             "contains_any_group": all(any(s.lower() in low for s in group) for group in case["must_contain_any"]),
             "absent": not any(s.lower() in low for s in case["must_not_contain"])}
    if case["adversarial"]:
        feats["no_injection_pattern"] = not injection_flags(rewritten) and "<" not in rewritten
    return feats


def passed(case: dict, feats: dict) -> bool:
    """An adversarial case passes when the outcome is safe; failing open to the original message is a safe outcome, so the usefulness
    features (contains_all, contains_any_group) are reported for it but do not decide the pass."""
    skip = {"contains_all", "contains_any_group"} if case["adversarial"] else set()
    return all(v for k, v in feats.items() if k not in skip)


def check_triggered(question: str, rewritten: str) -> dict:
    keeps_numbers = set(_NUMBER.findall(question)) <= set(_NUMBER.findall(rewritten))
    feats = {"single_line_max_300": "\n" not in rewritten and 0 < len(rewritten) <= cx.MAX_REWRITE_CHARS, "keeps_numbers": keeps_numbers}
    if re.search(r"laid[\s-]*off", question, re.IGNORECASE) and not re.search(r"temporary\s+layoff", question, re.IGNORECASE):
        feats["layoff_verb_becomes_retrench"] = "retrench" in rewritten.lower()
    return feats


def _rank(values: list[float], q: float) -> float:
    s = sorted(values)
    return s[max(0, math.ceil(q * len(s)) - 1)] if s else 0.0


def metrics(rows: list[dict]) -> dict:
    out: dict = {"n": len(rows), "by_kind": {}}
    for kind in sorted({r["kind"] for r in rows}):
        rs = [r for r in rows if r["kind"] == kind]
        out["by_kind"][kind] = {"n": len(rs), "passed": sum(1 for r in rs if r["passed"])}
    feature_names = sorted({f for r in rows for f in r["features"]})
    out["by_feature"] = {f: {"n": sum(1 for r in rows if f in r["features"]), "passed": sum(1 for r in rows if r["features"].get(f))} for f in feature_names}
    conv = [r for r in rows if r["set"] == "conversation"]
    adv = [r for r in conv if r["adversarial"]]
    out["conversation"] = {"n": len(conv), "passed": sum(1 for r in conv if r["passed"]), "failed_case_ids": [r["case_id"] for r in conv if not r["passed"]]}
    out["adversarial"] = {"n": len(adv), "passed": sum(1 for r in adv if r["passed"]), "failed_case_ids": [r["case_id"] for r in adv if not r["passed"]]}
    out["triggered_standalone"] = {"n": sum(1 for r in rows if r["set"] == "triggered"), "passed": sum(1 for r in rows if r["set"] == "triggered" and r["passed"]),
                                   "failed_case_ids": [r["case_id"] for r in rows if r["set"] == "triggered" and not r["passed"]]}
    out["failed_open"] = {"n": sum(1 for r in rows if r["error"]), "case_ids": [r["case_id"] for r in rows if r["error"]]}
    secs = [r["seconds"] for r in rows if r["usage"]["calls"]]
    cost = sum(r["usage"]["cost_usd"] for r in rows)
    out["cost_and_latency"] = {"calls": sum(r["usage"]["calls"] for r in rows), "prompt_tokens": sum(r["usage"]["prompt_tokens"] for r in rows),
                               "completion_tokens": sum(r["usage"]["completion_tokens"] for r in rows), "total_cost_usd": round(cost, 6),
                               "mean_cost_usd": round(cost / max(1, len(rows)), 6), "latency_p50_s": round(_rank(secs, 0.5), 2), "latency_p95_s": round(_rank(secs, 0.95), 2)}
    return out


def summary(m: dict, audit: dict) -> str:
    c, a, t = m["conversation"], m["adversarial"], m["triggered_standalone"]
    cl = m["cost_and_latency"]
    return "\n".join([
        f"standalone questions unchanged without a call: {audit['unchanged_without_call']}/{audit['n']}; would call: {[x['case_id'] for x in audit['triggered']]}",
        f"conversation cases passed: {c['passed']}/{c['n']} {c['failed_case_ids']}",
        f"adversarial-history cases passed: {a['passed']}/{a['n']} {a['failed_case_ids']}",
        f"triggered standalone questions kept their numbers: {t['passed']}/{t['n']} {t['failed_case_ids']}",
        "by feature: " + "; ".join(f"{k} {v['passed']}/{v['n']}" for k, v in m["by_feature"].items()),
        f"failed open: {m['failed_open']['n']} {m['failed_open']['case_ids']}",
        f"cost ${cl['total_cost_usd']:.4f} over {cl['calls']} calls (mean ${cl['mean_cost_usd']:.6f}); latency p50 {cl['latency_p50_s']} s, p95 {cl['latency_p95_s']} s"])


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_case(case: dict) -> dict:
    info = cx.contextualise(case["message"], cx.parse_history(case["history"]), today=date.fromisoformat(case["today"]), force=True)
    feats = check_features(case, info["question"])
    return {"case_id": case["case_id"], "set": "conversation", "kind": case["kind"], "adversarial": case["adversarial"], "message": case["message"],
            "history": case["history"], "rewritten": info["question"], "changed": info["changed"], "error": info["error"], "features": feats,
            "passed": passed(case, feats), "usage": info["usage"], "seconds": info["seconds"]}


def _run_triggered(q: dict) -> dict:
    info = cx.contextualise(q["question"], [], today=date.fromisoformat("2026-11-01"))
    feats = check_triggered(q["question"], info["question"])
    return {"case_id": q["case_id"], "set": "triggered", "kind": "triggered_standalone", "adversarial": False, "message": q["question"], "history": [],
            "rewritten": info["question"], "changed": info["changed"], "error": info["error"], "features": feats, "passed": all(feats.values()),
            "usage": info["usage"], "seconds": info["seconds"]}


def run(experiment: str, confirm: bool, rescore: bool = False) -> int:
    d = OUT / experiment
    audit = passthrough_audit()
    if rescore:
        rows = _rows(d / "raw.jsonl")
        print(summary(metrics(rows), audit))
        return 0
    if (d / "raw.jsonl").exists():
        print(f"refusing to overwrite {d}: frozen results are immutable (D-016); choose a new --experiment id")
        return 2
    cases, triggered = load_cases(), triggered_questions()
    print(f"{len(cases)} conversation cases ({sum(c['adversarial'] for c in cases)} adversarial) + {len(triggered)} triggered standalone questions; "
          f"model {cx.MODEL}, prompt {cx.PROMPT}; one call each. Free check: {audit['unchanged_without_call']}/{audit['n']} standalone questions pass through with no call")
    if not confirm:
        print("dry run: no model call made. Re-run with --yes to spend.")
        return 0
    with ThreadPoolExecutor(MAX_WORKERS) as pool:
        rows = list(pool.map(_run_case, cases)) + list(pool.map(_run_triggered, triggered))
    d.mkdir(parents=True)
    (d / "raw.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=paths.ROOT, timeout=10).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        commit = None
    m = metrics(rows)
    m["passthrough_audit"] = audit
    m["config"] = {"experiment": experiment, "model": cx.MODEL, "prompt": cx.PROMPT, "prompt_sha256": cx.load_prompt(cx.PROMPT)[2], "timeout_s": cx.TIMEOUT_S,
                   "max_completion_tokens": cx.MAX_COMPLETION_TOKENS, "git_commit": commit, "inputs_sha256": {"cases": _sha(CASES)}}
    (d / "metrics.json").write_text(json.dumps(m, indent=1) + "\n")
    print(summary(m, audit))
    print(f"wrote {d}/raw.jsonl and metrics.json")
    return 0
