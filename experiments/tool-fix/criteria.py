"""Evaluate the pre-declared X3 criteria (docs/experiments/m7-tool-fix.md section 4.1) and summarise new-tool use.

Read-only: it reads saved score files and writes experiments/tool-fix/criteria.json (counts and case ids only, no text).
Thresholds are the ones declared before the run and are constants here on purpose.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELS = ("gpt-6-luna", "gpt-5.6-luna")
MIN_CORRECT = {"gpt-6-luna": 205, "gpt-5.6-luna": 209}  # X2 interval lower bounds (0.865, 0.878) x 237
MAX_FALSE = 6  # X2 count, both models
MAX_UNGROUNDED = {"gpt-6-luna": 34, "gpt-5.6-luna": 51}  # X2 interval upper bounds (0.143, 0.215) x 237
TOOL = "calculate_from_text_values"


def scores(exp: str, model: str) -> dict:
    path = ROOT / "experiments" / "runs" / exp / f"{model}.scores.jsonl"
    return {r["case_id"]: r for r in map(json.loads, path.read_text().splitlines()) if r}


def stats(rows: dict) -> dict:
    used = sorted(c for c, r in rows.items() if TOOL in r["tools_used"])
    fam = [r for r in rows.values() if r["family"] == "numerical_comparison"]
    return {
        "n": len(rows), "correct": sum(r["behavior_ok"] for r in rows.values()),
        "false_answers": sum(r["expected"] != "answered" and r["status"] == "answered" for r in rows.values()),
        "over_abstentions": sum(r["expected"] == "answered" and r["status"] in ("abstained", "refused", "clarify") for r in rows.values()),
        "cases_with_ungrounded": sum(r["n_ungrounded_numbers"] > 0 for r in rows.values()),
        "operational_failures": sum(r["operational_failure"] for r in rows.values()),
        "new_tool_cases": len(used), "new_tool_cases_with_ungrounded": sum(rows[c]["n_ungrounded_numbers"] > 0 for c in used),
        "new_tool_case_ids_with_ungrounded": [c for c in used if rows[c]["n_ungrounded_numbers"] > 0],
        "rounds_3_cases": sum(r["rounds"] == 3 for r in rows.values()),
        "numerical_comparison_n": len(fam), "numerical_comparison_correct": sum(r["behavior_ok"] for r in fam),
    }


out = {"declared": {"min_correct": MIN_CORRECT, "max_false_answers": MAX_FALSE, "max_cases_with_ungrounded": MAX_UNGROUNDED,
                    "max_operational_failures": "X2 count"}, "dev": {}, "v2post": {}}
for model in MODELS:
    x2, x3 = scores("agent-dev-X2", model), scores("agent-dev-X3", model)
    a, b = stats(x2), stats(x3)
    crit = {
        "1_behaviour_accuracy": {"x3": b["correct"], "threshold": f">= {MIN_CORRECT[model]}", "pass": b["correct"] >= MIN_CORRECT[model]},
        "2_false_answers": {"x2": a["false_answers"], "x3": b["false_answers"], "threshold": f"<= {MAX_FALSE}", "pass": b["false_answers"] <= MAX_FALSE},
        "3a_ungrounded_in_new_tool_cases": {"x3": b["new_tool_cases_with_ungrounded"], "of_cases": b["new_tool_cases"], "threshold": "== 0", "pass": b["new_tool_cases_with_ungrounded"] == 0},
        "3b_cases_with_ungrounded": {"x2": a["cases_with_ungrounded"], "x3": b["cases_with_ungrounded"], "threshold": f"<= {MAX_UNGROUNDED[model]}", "pass": b["cases_with_ungrounded"] <= MAX_UNGROUNDED[model]},
        "4_operational_failures": {"x2": a["operational_failures"], "x3": b["operational_failures"], "threshold": f"<= {a['operational_failures']}", "pass": b["operational_failures"] <= a["operational_failures"]},
    }
    out["dev"][model] = {"x2": a, "x3": b, "criteria": crit, "all_pass": all(c["pass"] for c in crit.values()),
                         "changed_cases": sorted(c for c in x2 if x2[c]["behavior_ok"] != x3[c]["behavior_ok"])}
    out["v2post"][model] = {}
    for arm in ("r3", "hybrid"):
        pre, post = scores(f"agent-heldout-V2-{arm}", model), scores(f"agent-heldout-V2post-{arm}", model)
        out["v2post"][model][arm] = {"frozen": stats(pre), "post": stats(post)}
(ROOT / "experiments" / "tool-fix" / "criteria.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps({m: {"all_pass": v["all_pass"], **{k: c["pass"] for k, c in v["criteria"].items()}} for m, v in out["dev"].items()}, indent=1))
