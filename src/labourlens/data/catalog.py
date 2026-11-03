"""Loads the source inventory (specs/sources.yaml + specs/sources.d/*.yaml) and dataset adapter specs (specs/datasets/*.yaml)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from labourlens import paths

# D-077 (3 Nov 2026) widened the answer scope from 2024-Q1 to 2020-Q1. Every module that needs the window reads these constants.
ANSWER_SCOPE_START = "2020-Q1"
ANSWER_SCOPE_END = "2026-Q2"
# The evaluation gold set (D-031 to D-076) was written and measured on the earlier 2024-Q1 to 2026-Q2 window; 2020-Q1 to 2023-Q4 answers are unevaluated.
EVALUATED_WINDOW = ("2024-Q1", "2026-Q2")


def quarter_words(period: str) -> str:
    """'2020-Q1' -> 'Q1 2020'."""
    return f"{period[-2:]} {period[:4]}"


def scope_words() -> str:
    """The answer window in plain words, for user-facing text: 'Q1 2020 to Q2 2026'."""
    return f"{quarter_words(ANSWER_SCOPE_START)} to {quarter_words(ANSWER_SCOPE_END)}"


@lru_cache(maxsize=1)
def sources() -> dict[str, list[dict[str, Any]]]:
    """specs/sources.yaml plus every specs/sources.d/*.yaml (expansion batches, D-019). Lists are concatenated."""
    merged = yaml.safe_load((paths.SPECS / "sources.yaml").read_text())
    for extra in sorted((paths.SPECS / "sources.d").glob("*.yaml")):
        part = yaml.safe_load(extra.read_text()) or {}
        for key, items in part.items():
            merged.setdefault(key, []).extend(items)
    ids = [e["source_id"] for k in ("datasets", "documents") for e in merged.get(k, [])]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        raise ValueError(f"duplicate source_id across catalog files: {sorted(dup)}")
    return merged


def datasets() -> list[dict[str, Any]]:
    return sources()["datasets"]


def documents() -> list[dict[str, Any]]:
    return sources()["documents"]


def adapter_spec(source_id: str) -> dict[str, Any]:
    p = paths.SPECS / "datasets" / f"{source_id}.yaml"
    return yaml.safe_load(p.read_text())
