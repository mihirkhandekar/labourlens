"""The presentation reads the retrieval ladder and the paired held-out differences from report.json."""

import json
from pathlib import Path

from labourlens.report.build import _Artifacts, _ladder, _paired


class SyntheticArtifacts:
    def __init__(self, files):
        self.files = files
        self.paths = sorted(files)

    def mapping(self, path):
        value = self.load(path)
        return value if isinstance(value, dict) else {}

    def load(self, path):
        return self.files.get(path)


REPO = Path(__file__).resolve().parents[2]


def test_paired_projection_parses_numbers_only():
    text = (
        "Paired held-out difference in behaviour accuracy, r3 minus hybrid, n=31, 10000 case-bootstrap "
        "resamples, seed 20261030, GOLD v3.4\n"
        "gpt-6-luna diff 0.161 95% CI [0.000, 0.323] better 6 worse 1\n"
        "gpt-5.6-luna diff 0.097 95% CI [-0.032, 0.226] better 4 worse 1\n"
    )
    entries = _paired(SyntheticArtifacts({"experiments/heldout/paired.txt": text}))
    assert entries == [{
        "gold_version": "v3.4", "n": 31, "resamples": 10000, "seed": 20261030,
        "models": {
            "gpt-6-luna": {"diff": 0.161, "ci95": [0.0, 0.323], "better": 6, "worse": 1},
            "gpt-5.6-luna": {"diff": 0.097, "ci95": [-0.032, 0.226], "better": 4, "worse": 1},
        },
        "provenance": ["experiments/heldout/paired.txt"],
    }]


def test_paired_text_files_are_allowlisted_and_nothing_else():
    assert _Artifacts._allowed("experiments/heldout/paired.txt")
    assert _Artifacts._allowed("experiments/heldout/paired-v3.3.txt")
    assert not _Artifacts._allowed("experiments/heldout/notes.txt")
    assert not _Artifacts._allowed("experiments/heldout/paired-v9.9.txt")


def test_ladder_projection_keeps_numbers_and_drops_text():
    summary = {
        "n_cases": 128, "gold_file_sha256": "a" * 64, "corpus_hash": "b" * 64,
        "metrics": {"R0": {"n_cases": 128, "hit@8": 0.57, "hit@8_ci95": [0.49, 0.65], "note": "PRIVATE_TEXT",
                           "by_family_hit@8": {"factual_lookup": {"n": 50, "hit@8": 0.72}}}},
        "hint_coverage": {"any_hint": 96},
        "end_to_end_context_coverage": [{"config": "R0", "n": 128, "gold_in_context_of_top8_chunks": 0.57,
                                         "gold_in_first8_context_passages": 0.41, "secret": "PRIVATE_TEXT"}],
        "first_relevant_rank_histogram": {"R0": {"0": 53, "1": 27}},
    }
    ladder = _ladder(SyntheticArtifacts({"experiments/runs/dev-R-summary.json": summary}))
    assert ladder["n_cases"] == 128
    assert ladder["configs"]["R0"]["hit@8"] == 0.57
    assert ladder["configs"]["R0"]["by_family_hit@8"]["factual_lookup"] == {"n": 50, "hit@8": 0.72}
    assert ladder["end_to_end_context"]["R0"] == {"n": 128, "gold_in_context_of_top8_chunks": 0.57, "gold_in_first8_context_passages": 0.41}
    assert ladder["first_relevant_rank_histogram"] == {"R0": {"0": 53, "1": 27}}
    assert "PRIVATE_TEXT" not in json.dumps(ladder)
    assert "gold_file_sha256" not in ladder
    assert _ladder(SyntheticArtifacts({})) == {}


def test_committed_report_carries_ladder_and_paired():
    report = json.loads((REPO / "web/static/data/report.json").read_text())
    assert set(report["retrieval"]["ladder"]["configs"]) >= {"R0", "R1a", "R1b", "R2", "R3"}
    current = report["evaluation"]["paired"][0]
    assert current["gold_version"] == "v3.5" and current["n"] == 31
    assert current["models"]["gpt-6-luna"]["ci95"][0] == 0.0
    assert current["models"]["gpt-5.6-luna"]["ci95"][0] < 0
