"""The model-free floors and run-to-run flips come from committed gold and score rows; no model calls."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load():
    spec = importlib.util.spec_from_file_location("floors_and_noise", ROOT / "scripts" / "floors_and_noise.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_floors_match_the_documented_class_balance():
    sets = load().build()["sets"]
    assert {k: (v["n"], v["always_answer"]["correct"], v["always_abstain"]["correct"]) for k, v in sets.items()} == {
        "dev": (237, 182, 25), "registered": (31, 24, 2), "fresh": (65, 48, 8)}


def test_committed_output_is_what_the_script_computes():
    assert json.loads((ROOT / "experiments/eval/floors-and-noise.json").read_text()) == load().build()


def test_fresh_set_flips_are_one_to_three_cases_per_arm():
    flips = load().build()["sets"]["fresh"]["flips"]
    assert sorted(v["flipped"] for v in flips.values()) == [1, 2, 3, 3]
