"""Measure the scope-triage prompt (D-051) on every evaluation question plus a hand-written off-topic set.

Acceptance criterion: the triage step must not divert any gold, held-out v2 or threat question (all of them concern the workbench or
must reach the agent's own defences). The off-topic set is our own text with an expected route. Raw outputs hold questions and the
model's short replies only, never MOM/MTI text. Each run gets a new experiment id and refuses to overwrite (D-016)."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from labourlens import paths
from labourlens.agent import triage

OUT = paths.EXPERIMENTS / "triage"
GOLD = paths.EXPERIMENTS / "gold" / "gold_v3.7.jsonl"
V2 = paths.EXPERIMENTS / "gold" / "heldout_v2_v1.jsonl"
THREATS = paths.EXPERIMENTS / "threats" / "cases.jsonl"
OFFTOPIC = OUT / "offtopic_cases.jsonl"
SETS = (("gold", GOLD), ("v2", V2), ("threats", THREATS), ("offtopic", OFFTOPIC))
MAX_WORKERS = 6


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_cases() -> list[dict]:
    cases = []
    for name, path in SETS:
        for r in _rows(path):
            cases.append({"case_id": r["case_id"], "set": name, "kind": r.get("kind", r.get("family", r.get("category", ""))),
                          "expected_route": r.get("expected_route", "in_scope"), "question": r["question"]})
    return cases


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rank(values: list[float], q: float) -> float:
    s = sorted(values)
    return s[max(0, math.ceil(q * len(s)) - 1)] if s else 0.0


def metrics(rows: list[dict]) -> dict:
    by_set = {name: [r for r in rows if r["set"] == name] for name, _ in SETS}
    out: dict = {"n": len(rows), "sets": {}}
    for name, rs in by_set.items():
        counts = {k: sum(1 for r in rs if r["route"] == k) for k in triage.ROUTES}
        out["sets"][name] = {"n": len(rs), "routes": counts, "failed_open": sum(1 for r in rs if r["error"] and not r["error"].startswith("skipped"))}

    def false_rate(names: tuple[str, ...]) -> dict:
        rs = [r for n in names for r in by_set[n]]
        bad = [r for r in rs if r["route"] != "in_scope"]
        return {"n": len(rs), "false_out_of_scope": sum(1 for r in rs if r["route"] == "out_of_scope"), "false_diverted_any_route": len(bad),
                "failed_open": sum(1 for r in rs if r["error"] and not r["error"].startswith("skipped")), "diverted_case_ids": [r["case_id"] for r in bad]}

    out["false_out_of_scope_gold_v2"] = false_rate(("gold", "v2"))
    out["false_out_of_scope_threats"] = false_rate(("threats",))
    off = by_set["offtopic"]
    clear = [r for r in off if r["expected_route"] != "in_scope"]
    out["offtopic"] = {
        "n": len(off), "expected_not_in_scope": len(clear),
        "recall_not_in_scope": sum(1 for r in clear if r["route"] != "in_scope"),
        "exact_route_matches": sum(1 for r in clear if r["route"] == r["expected_route"]),
        "by_kind": {k: {"n": sum(1 for r in off if r["kind"] == k), "correct": sum(1 for r in off if r["kind"] == k and r["route"] == r["expected_route"])}
                    for k in sorted({r["kind"] for r in off})},
        "misrouted_case_ids": [r["case_id"] for r in off if r["route"] != r["expected_route"]]}
    secs = [r["seconds"] for r in rows if r["usage"]["calls"]]
    cost = sum(r["usage"]["cost_usd"] for r in rows)
    out["cost_and_latency"] = {
        "calls": sum(r["usage"]["calls"] for r in rows), "prompt_tokens": sum(r["usage"]["prompt_tokens"] for r in rows),
        "completion_tokens": sum(r["usage"]["completion_tokens"] for r in rows), "total_cost_usd": round(cost, 6),
        "mean_cost_usd": round(cost / max(1, len(rows)), 6), "latency_p50_s": round(_rank(secs, 0.5), 2), "latency_p95_s": round(_rank(secs, 0.95), 2)}
    return out


def summary(m: dict) -> str:
    g, t, o, c = m["false_out_of_scope_gold_v2"], m["false_out_of_scope_threats"], m["offtopic"], m["cost_and_latency"]
    bk = o["by_kind"]
    return "\n".join([
        f"false out_of_scope gold+v2: {g['false_out_of_scope']}/{g['n']} (any diversion {g['false_diverted_any_route']}, failed open {g['failed_open']})",
        f"false out_of_scope threats: {t['false_out_of_scope']}/{t['n']} (any diversion {t['false_diverted_any_route']}, failed open {t['failed_open']})",
        f"off-topic recall (not in_scope): {o['recall_not_in_scope']}/{o['expected_not_in_scope']}; exact route {o['exact_route_matches']}/{o['expected_not_in_scope']}",
        "by kind: " + "; ".join(f"{k} {v['correct']}/{v['n']}" for k, v in bk.items()),
        f"cost ${c['total_cost_usd']:.4f} over {c['calls']} calls (mean ${c['mean_cost_usd']:.6f}); latency p50 {c['latency_p50_s']} s, p95 {c['latency_p95_s']} s"])


def run(experiment: str, confirm: bool, rescore: bool = False) -> int:
    d = OUT / experiment
    cases = load_cases()
    if rescore:
        rows = _rows(d / "raw.jsonl")
        m = metrics(rows)
        print(summary(m))
        return 0
    if (d / "raw.jsonl").exists():
        print(f"refusing to overwrite {d}: frozen results are immutable (D-016); choose a new --experiment id")
        return 2
    print(f"{len(cases)} questions ({', '.join(f'{n} {sum(1 for c in cases if c['set'] == n)}' for n, _ in SETS)}); model {triage.MODEL}, prompt {triage.PROMPT}; one call each")
    if not confirm:
        print("dry run: no model call made. Re-run with --yes to spend.")
        return 0
    with ThreadPoolExecutor(MAX_WORKERS) as pool:
        infos = list(pool.map(lambda c: triage.classify(c["question"]), cases))
    rows = [{**c, "route": i["route"], "reply": i["reply"], "error": i["error"], "usage": i["usage"], "seconds": i["seconds"]} for c, i in zip(cases, infos)]
    d.mkdir(parents=True)
    (d / "raw.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=paths.ROOT, timeout=10).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        commit = None
    m = metrics(rows)
    m["config"] = {"experiment": experiment, "model": triage.MODEL, "prompt": triage.PROMPT, "prompt_sha256": infos[0]["prompt_sha256"], "timeout_s": triage.TIMEOUT_S,
                   "max_completion_tokens": triage.MAX_COMPLETION_TOKENS, "git_commit": commit, "inputs_sha256": {name: _sha(path) for name, path in SETS}}
    (d / "metrics.json").write_text(json.dumps(m, indent=1) + "\n")
    print(summary(m))
    print(f"wrote {d}/raw.jsonl and metrics.json")
    return 0
