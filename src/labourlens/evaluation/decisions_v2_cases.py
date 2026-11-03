"""Offline authorship/provenance and lexical freshness screen for triage v2.

Lexical novelty is not semantic independence or human review. No model is called.
"""
from __future__ import annotations

from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from labourlens import paths

FRESH = paths.EXPERIMENTS / "triage/fresh_cases_v2.jsonl"
ROUTES = {"in_scope", "out_of_scope", "small_talk", "unsafe_or_sensitive"}
FAMILIES = ("factual", "numerical", "cross-source", "revision", "ambiguity/causal", "adversarial")
JACCARD_LIMIT = 0.35
SEQUENCE_LIMIT = 0.80


def normalise(text: str) -> str:
    """Casefold Unicode words and collapse punctuation/whitespace consistently."""
    return " ".join(re.findall(r"\w+", unicodedata.normalize("NFKC", text).casefold()))


def trigrams(text: str) -> set[tuple[str, str, str]]:
    words = normalise(text).split()
    return set(zip(words, words[1:], words[2:]))


def similarity(left: str, right: str) -> tuple[float, float]:
    a, b = trigrams(left), trigrams(right)
    union = a | b
    jaccard = len(a & b) / len(union) if union else 0.0
    ratio = SequenceMatcher(None, normalise(left), normalise(right), autojunk=False).ratio()
    return jaccard, ratio


def reference_paths() -> list[Path]:
    """Include historical gold drafts/archives as well as the full 409 baseline."""
    candidates = [*sorted((paths.EXPERIMENTS / "gold").rglob("*.jsonl")),
                  *sorted((paths.EXPERIMENTS / "threats").glob("cases*.jsonl")),
                  paths.EXPERIMENTS / "triage/offtopic_cases.jsonl",
                  paths.EXPERIMENTS / "triage/triage-v1-luna/raw.jsonl"]
    return sorted(set(candidates))


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def audit(path: Path = FRESH, references: list[Path] | None = None,
          *, enforce_distribution: bool = True) -> dict:
    """Recompute hashes, distribution and every pair; raise on either threshold.

    Compare fresh cases with each other and every question-bearing reference row.
    Explicit references support tiny offline unit fixtures. Defaults are fail-closed
    on absent sources; callers should preserve the returned input hashes in prereg.
    """
    cases_path = Path(path)
    cases = _rows(cases_path)
    seen_ids = set()
    for row in cases:
        identity = row["case_id"]
        if identity in seen_ids:
            raise ValueError(f"Duplicate case identity: {identity}")
        seen_ids.add(identity)
        if not isinstance(row["question"], str) or not normalise(row["question"]):
            raise ValueError(f"Empty question: {identity}")
        if len(row["question"]) > 1000:
            raise ValueError(f"Question would be skipped: {identity}")
        if row["expected_route"] not in ROUTES:
            raise ValueError(f"Unknown route: {identity}")
        if row.get("drafted_by") != "AI" or row.get("review_status") != "AI-labelled, not human-reviewed":
            raise ValueError(f"Invalid AI provenance: {identity}")
        if not row.get("family") or not row.get("kind"):
            raise ValueError(f"Missing stratum: {identity}")
    routes = dict(Counter(row["expected_route"] for row in cases))
    strata = Counter((row["expected_route"], row["kind"]) for row in cases)
    if enforce_distribution:
        if routes != {"in_scope": 90, "out_of_scope": 40, "small_talk": 10, "unsafe_or_sensitive": 10}:
            raise ValueError("Fresh route distribution differs from preregistered 150")
        if [row["case_id"] for row in cases] != [f"F2-{n:03d}" for n in range(1, 151)]:
            raise ValueError("Expected ordered F2-001 through F2-150 identities")
        family_counts = Counter(row["family"] for row in cases if row["kind"] == "research")
        if family_counts != Counter({family: 10 for family in FAMILIES}):
            raise ValueError("Expected ten research cases per family")
        expected = {("in_scope", "research"): 60, ("in_scope", "borderline"): 15,
                    ("in_scope", "injection"): 15, ("out_of_scope", "clear"): 20,
                    ("out_of_scope", "borderline"): 20, ("small_talk", "social"): 10,
                    ("unsafe_or_sensitive", "unrelated-harm"): 10}
        if strata != Counter(expected):
            raise ValueError("Fresh kind distribution differs from preregistration")
    reference_hashes = {}
    prior = []
    unique_questions = set()
    for path in reference_paths() if references is None else references:
        path = Path(path)
        reference_hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        for row in _rows(path):
            question = row.get("question")
            if isinstance(question, str) and question not in unique_questions:
                unique_questions.add(question)
                prior.append((f"{path.name}:{row.get('case_id', '?')}", question))
    maxima = {"jaccard": {"value": 0.0, "pair": None},
              "sequence_ratio": {"value": 0.0, "pair": None}}
    for row in cases:
        for identity, question in prior:
            jaccard, ratio = similarity(row["question"], question)
            pair = [row["case_id"], identity]
            for metric, value in (("jaccard", jaccard), ("sequence_ratio", ratio)):
                if value > maxima[metric]["value"]:
                    maxima[metric] = {"value": value, "pair": pair}
            if normalise(row["question"]) == normalise(question) or jaccard >= JACCARD_LIMIT or ratio >= SEQUENCE_LIMIT:
                raise ValueError(f"Near duplicate {pair}: Jaccard={jaccard:.6f}, sequence={ratio:.6f}")
        prior.append((row["case_id"], row["question"]))
    digest = hashlib.sha256(cases_path.read_bytes()).hexdigest()
    return {"n": len(cases), "sha256": digest, "cases_sha256": digest,
            "counts": routes, "routes": routes, "kinds": dict(Counter(row["kind"] for row in cases)),
            "reference_unique_questions": len(unique_questions), "reference_sha256": reference_hashes,
            "max_similarity": maxima, "thresholds": {"jaccard": JACCARD_LIMIT, "sequence_ratio": SEQUENCE_LIMIT},
            "provenance": "AI-authored and AI-labelled, not human-reviewed"}
