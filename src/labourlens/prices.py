"""Cost from measured tokens and the verified price table in specs/prices.yaml (D-022)."""

from __future__ import annotations

from functools import cache

import yaml

from labourlens import paths


@cache
def table() -> dict:
    return yaml.safe_load((paths.SPECS / "prices.yaml").read_text())


def chat_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    p = table()["chat"][model]
    return (prompt_tokens * p["input"] + completion_tokens * p["output"]) / 1e6


def embedding_cost(model: str, tokens: int) -> float:
    return tokens * table()["embedding"][model]["input"] / 1e6
