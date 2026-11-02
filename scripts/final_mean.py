"""Mean of the two final-evaluation runs (FIN and FIN2). Pre-registered in docs/experiments/fin2-replicate.md.
Reads scored case rows, writes experiments/eval/final-mean.json. Per-case outcome = mean of two runs; paired case bootstrap."""
import json, numpy as np
from pathlib import Path
R = Path(__file__).resolve().parent.parent / "experiments" / "eval"
SETS = {"dev": ("agent-dev-FIN-{a}", "agent-dev-FIN2-{a}"), "registered": ("agent-heldout-FIN-{a}", "agent-heldout-FIN2-{a}"), "fresh": ("agent-heldout-FINV2-{a}", "agent-heldout-FIN2V2-{a}")}
MODELS = ["gpt-6-luna", "gpt-5.6-luna"]
def rows(exp, m):
    return {r["case_id"]: r for r in map(json.loads, (R / exp / f"{m}.cases.jsonl").read_text().splitlines())}
def stat(rs, f):
    v = [f(r) for r in rs]; return float(np.mean(v))
out = {"preregistration": "docs/experiments/fin2-replicate.md", "n_boot": 10000, "seed": 20261030, "sets": {}}
rng = np.random.default_rng(20261030)
for s, (e1, e2) in SETS.items():
    out["sets"][s] = {}
    for m in MODELS:
        per = {}
        for arm in ("r3", "hybrid"):
            a, b = rows(e1.format(a=arm), m), rows(e2.format(a=arm), m)
            ids = sorted(set(a) & set(b)); assert len(ids) == len(a) == len(b), (s, m, arm)
            o1 = np.array([bool(a[i]["behavior_ok"]) for i in ids], float); o2 = np.array([bool(b[i]["behavior_ok"]) for i in ids], float)
            oa = lambda k: (np.mean([bool(a[i][k]) for i in ids]), np.mean([bool(b[i][k]) for i in ids]))
            per[arm] = {"ids": ids, "run1": float(o1.mean()), "run2": float(o2.mean()), "mean": float((o1.mean() + o2.mean()) / 2), "case_mean": (o1 + o2) / 2,
                        "over_abstain": [round(float(x), 4) for x in oa("over_abstain")], "false_answer": [round(float(x), 4) for x in oa("false_answer")],
                        "cost": [round(float(np.mean([a[i]["cost_usd"] for i in ids])), 5), round(float(np.mean([b[i]["cost_usd"] for i in ids])), 5)],
                        "p50_s": [round(float(np.median([a[i]["seconds"] for i in ids])), 1), round(float(np.median([b[i]["seconds"] for i in ids])), 1)]}
        d = per["r3"]["case_mean"] - per["hybrid"]["case_mean"]; n = len(d)
        boots = [d[rng.integers(0, n, n)].mean() for _ in range(10000)]
        d1 = per["r3"]["run1"] - per["hybrid"]["run1"]; d2 = per["r3"]["run2"] - per["hybrid"]["run2"]
        out["sets"][s][m] = {"n": n, "r3": {k: v for k, v in per["r3"].items() if k not in ("ids", "case_mean")}, "hybrid": {k: v for k, v in per["hybrid"].items() if k not in ("ids", "case_mean")},
                             "paired_mean_diff": round(float(d.mean()), 4), "ci95": [round(float(np.percentile(boots, 2.5)), 4), round(float(np.percentile(boots, 97.5)), 4)],
                             "run1_diff": round(d1, 4), "run2_diff": round(d2, 4), "sign_agrees": bool(d1 * d2 > 0 or (d1 == 0 and d2 == 0))}
(R / "final-mean.json").write_text(json.dumps(out, indent=1))
for s, ms in out["sets"].items():
    for m, v in ms.items():
        print(s, m, "n", v["n"], "r3 run1/run2/mean", v["r3"]["run1"], v["r3"]["run2"], v["r3"]["mean"], "| hybrid", v["hybrid"]["run1"], v["hybrid"]["run2"], v["hybrid"]["mean"], "| diff", v["paired_mean_diff"], v["ci95"], "runs", v["run1_diff"], v["run2_diff"], "agree", v["sign_agrees"], "| OA", v["r3"]["over_abstain"], v["hybrid"]["over_abstain"], "| cost", v["r3"]["cost"], v["hybrid"]["cost"], "| p50", v["r3"]["p50_s"], v["hybrid"]["p50_s"])
