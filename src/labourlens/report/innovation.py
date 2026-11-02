"""Curated editorial content plus aggregate, committed report measurements only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

CONTENT = "docs/innovation-page.json"


def project_innovation(root: Path, report: dict) -> dict:
    """Never open raw runs, answers, private files or source passages for this page."""
    raw = (root / CONTENT).read_bytes()
    content = json.loads(raw)
    if set(content) != {"title", "intro", "contribution_intro", "contributions", "roadmap_title", "roadmap_intro", "roadmap", "limits"}:
        raise ValueError("Unexpected innovation content fields")
    text = json.dumps(content, ensure_ascii=False)
    if any(term in text.lower() for term in ("held-out", "gpt-5.6", "\u2014", "\u2013")):
        raise ValueError("Innovation content contains forbidden presentation copy")
    for group in content["roadmap"]:
        if set(group) != {"name", "purpose", "items"}:
            raise ValueError("Unexpected roadmap group fields")
        for item in group["items"]:
            if set(item) != {"title", "why", "status"} or item["status"] != "proposal":
                raise ValueError("Roadmap items must remain explicit proposals")
    ladder = report.get("retrieval", {}).get("ladder", {})
    configs = ladder.get("configs", {})
    retrieval = {key: configs.get(key, {}).get("hit@8") for key in ("R0", "R3")}
    splits = []
    for split in report.get("final_evaluation", {}).get("splits", []):
        arms = []
        for arm in split.get("arms", []):
            if arm.get("model") != "gpt-6-luna":
                continue
            metrics = arm.get("metrics", {})
            arms.append({"arm": arm["arm"], "accuracy": metrics.get("behaviour_accuracy", {}).get("rate"),
                         "latency": metrics.get("latency_p50_s"), "cost": metrics.get("cost_per_case_usd")})
        splits.append({"id": split["id"], "n": split["n"], "arms": arms})
    scanner = report.get("security", {}).get("scanner", {})
    mcp = report.get("mcp", {}).get("metrics", {})
    return {"content": content, "measurements": {"retrieval": {"n": ladder.get("n_cases"), **retrieval},
             "splits": splits, "scanner": {key: scanner.get(key, {}).get("recall", {}).get("count") for key in ("before", "after")},
             "mcp": {key: mcp.get(key) for key in ("compared_datasets", "different_outputs", "identical_datasets", "matching_refusals")}},
            "source": {"path": CONTENT, "sha256": hashlib.sha256(raw).hexdigest(),
                       "evidence_commit": report.get("provenance", {}).get("commit")}}
