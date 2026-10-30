"""Loads the fixed source inventory (specs/sources.yaml) and dataset adapter specs (specs/datasets/*.yaml)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from labourlens import paths

ANSWER_SCOPE_START = "2024-Q1"
ANSWER_SCOPE_END = "2026-Q2"


@lru_cache(maxsize=1)
def sources() -> dict[str, list[dict[str, Any]]]:
    return yaml.safe_load((paths.SPECS / "sources.yaml").read_text())


def datasets() -> list[dict[str, Any]]:
    return sources()["datasets"]


def documents() -> list[dict[str, Any]]:
    return sources()["documents"]


def adapter_spec(source_id: str) -> dict[str, Any]:
    p = paths.SPECS / "datasets" / f"{source_id}.yaml"
    return yaml.safe_load(p.read_text())
