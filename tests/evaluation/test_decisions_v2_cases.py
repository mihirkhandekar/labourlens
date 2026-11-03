"""Own-text lexical screening fixtures, with no network or model outputs."""
import hashlib
import json

import pytest

from labourlens.evaluation import decisions_v2_cases as cases


FROZEN_SHA256 = "fc431214c64643b5d8e63f76e4ad39a9fd31c6d61566613d9ab372d7016f8a7d"


def row(identity, question):
    return {"case_id": identity, "question": question, "expected_route": "in_scope",
            "family": "factual", "kind": "research", "drafted_by": "AI",
            "review_status": "AI-labelled, not human-reviewed"}


def save(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def test_frozen_own_text_distribution_and_freshness():
    result = cases.audit()
    assert result["n"] == 150
    assert result["sha256"] == FROZEN_SHA256
    assert result["counts"] == {"in_scope": 90, "out_of_scope": 40,
                                "small_talk": 10, "unsafe_or_sensitive": 10}
    assert result["max_similarity"]["jaccard"]["value"] < 0.35
    assert result["max_similarity"]["sequence_ratio"]["value"] < 0.80
    assert result["reference_unique_questions"] >= 409
    assert result["reference_sha256"]


def test_word_normalisation_and_short_exact_duplicates():
    assert cases.normalise("  CAFÉ, quarterly! ") == "café quarterly"
    assert cases.trigrams("one two three four") == {("one", "two", "three"), ("two", "three", "four")}
    assert cases.similarity("Hello!", " hello ") == (0.0, 1.0)


def test_hash_and_maxima_recomputed_from_own_fixture(tmp_path):
    fresh = save(tmp_path / "fresh.jsonl", [row("new", "violet lanterns beside quiet pools")])
    prior = save(tmp_path / "prior.jsonl", [row("old", "bronze kettles above misty hills")])
    result = cases.audit(fresh, [prior], enforce_distribution=False)
    assert result["sha256"] == hashlib.sha256(fresh.read_bytes()).hexdigest()
    assert result["reference_sha256"][str(prior)] == hashlib.sha256(prior.read_bytes()).hexdigest()
    assert result["max_similarity"]["sequence_ratio"]["value"] == cases.similarity(
        "violet lanterns beside quiet pools", "bronze kettles above misty hills")[1]


def test_reference_near_duplicate_raises(tmp_path):
    fresh = save(tmp_path / "fresh.jsonl", [row("new", "Inspect the bright orange lantern beside the garden gate")])
    prior = save(tmp_path / "prior.jsonl", [row("old", "Inspect the bright orange lantern beside the garden gates")])
    with pytest.raises(ValueError, match="Near duplicate"):
        cases.audit(fresh, [prior], enforce_distribution=False)


def test_intrafresh_duplicate_is_not_ignored(tmp_path):
    fresh = save(tmp_path / "fresh.jsonl", [row("a", "Good morning!"), row("b", "GOOD morning")])
    with pytest.raises(ValueError, match="Near duplicate"):
        cases.audit(fresh, [], enforce_distribution=False)


@pytest.mark.parametrize("scores", [(0.35, 0.1), (0.1, 0.80)])
def test_either_threshold_is_inclusive(tmp_path, monkeypatch, scores):
    fresh = save(tmp_path / "fresh.jsonl", [row("new", "Violet lanterns")])
    prior = save(tmp_path / "prior.jsonl", [row("old", "Bronze kettles")])
    monkeypatch.setattr(cases, "similarity", lambda left, right: scores)
    with pytest.raises(ValueError, match="Near duplicate"):
        cases.audit(fresh, [prior], enforce_distribution=False)


def test_missing_reference_fails_closed(tmp_path):
    fresh = save(tmp_path / "fresh.jsonl", [row("new", "Violet lanterns")])
    with pytest.raises(FileNotFoundError):
        cases.audit(fresh, [tmp_path / "absent.jsonl"], enforce_distribution=False)


@pytest.mark.parametrize("field,value,match", [
    ("drafted_by", "human", "provenance"),
    ("review_status", "human-reviewed", "provenance"),
    ("question", "", "Empty question"),
    ("question", "a" * 1001, "would be skipped"),
    ("expected_route", "invented", "Unknown route"),
    ("family", "", "Missing stratum"),
])
def test_malformed_authorship_and_route_rejected(tmp_path, field, value, match):
    item = {**row("new", "Violet lanterns"), field: value}
    fresh = save(tmp_path / "fresh.jsonl", [item])
    with pytest.raises(ValueError, match=match):
        cases.audit(fresh, [], enforce_distribution=False)


def test_identity_duplicates_rejected_before_similarity(tmp_path):
    fresh = save(tmp_path / "fresh.jsonl", [row("same", "Violet lanterns"), row("same", "Bronze kettles")])
    with pytest.raises(ValueError, match="Duplicate case identity"):
        cases.audit(fresh, [], enforce_distribution=False)


def test_full_distribution_required_by_default(tmp_path):
    fresh = save(tmp_path / "fresh.jsonl", [row("F2-001", "Violet lanterns")])
    with pytest.raises(ValueError, match="distribution"):
        cases.audit(fresh, [])
