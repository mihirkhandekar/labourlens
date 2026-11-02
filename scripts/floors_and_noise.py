"""Model-free floors and run-to-run flips for the final evaluation, from committed gold labels and committed score rows only.
No model calls. Writes experiments/eval/floors-and-noise.json; changes no frozen result.

Floor: a classifier that never looks at the question. The scorer counts `ignore_injection_and_answer` as an answered case,
so "always answer" is right for `answer` plus `ignore_injection_and_answer`; "always abstain" is right for `abstain` only.
Flips: cases whose behaviour verdict differs between two identical-configuration runs (FIN and FIN2) of the same arm and model."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "experiments" / "eval"
GOLD = {"dev": (ROOT / "experiments/gold/gold_v3.7.jsonl", "dev"), "registered": (ROOT / "experiments/gold/gold_v3.7.jsonl", "heldout"),
        "fresh": (ROOT / "experiments/gold/heldout_v2_v1.jsonl", None)}
RUNS = {"dev": ("agent-dev-FIN-{a}", "agent-dev-FIN2-{a}"), "registered": ("agent-heldout-FIN-{a}", "agent-heldout-FIN2-{a}"),
        "fresh": ("agent-heldout-FINV2-{a}", "agent-heldout-FIN2V2-{a}")}
MODELS = ("gpt-6-luna", "gpt-5.6-luna")
ANSWERING = {"answer", "ignore_injection_and_answer"}


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def verdicts(experiment, model):
    return {r["case_id"]: bool(r["behavior_ok"]) for r in lines(EVAL / experiment / f"{model}.cases.jsonl")}


def build():
    out = {"note": "Computed by scripts/floors_and_noise.py from committed gold and score rows; no model calls.", "sets": {}}
    for name, (path, split) in GOLD.items():
        cases = [c for c in lines(path) if split is None or c["split"] == split]
        n = len(cases)
        answer = sum(c["expected_behavior"] in ANSWERING for c in cases)
        abstain = sum(c["expected_behavior"] == "abstain" for c in cases)
        entry = {"n": n, "always_answer": {"correct": answer, "rate": round(answer / n, 4)}, "always_abstain": {"correct": abstain, "rate": round(abstain / n, 4)}, "flips": {}}
        for model in MODELS:
            for arm in ("r3", "hybrid"):
                first, second = (verdicts(run.format(a=arm), model) for run in RUNS[name])
                assert set(first) == set(second) and len(first) == n, (name, model, arm)
                entry["flips"][f"{model}/{arm}"] = {"flipped": sum(first[i] != second[i] for i in first), "n": n,
                                                  "correct_in_both": sum(first[i] and second[i] for i in first), "wrong_in_both": sum(not first[i] and not second[i] for i in first)}
        out["sets"][name] = entry
    return out


if __name__ == "__main__":
    result = build()
    (EVAL / "floors-and-noise.json").write_text(json.dumps(result, indent=1) + "\n")
    for name, entry in result["sets"].items():
        print(name, entry["n"], "always answer", entry["always_answer"], "always abstain", entry["always_abstain"])
        for key, value in entry["flips"].items():
            print("  flips", key, value)
