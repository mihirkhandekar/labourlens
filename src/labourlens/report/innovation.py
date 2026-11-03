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
    if set(content) != {"title", "scope", "abstract", "approach", "sections", "limitations", "components"}:
        raise ValueError("Unexpected innovation content fields")
    text = json.dumps(content, ensure_ascii=False)
    if any(term in text.lower() for term in ("held-out", "gpt-5.6", "\u2014", "\u2013")):
        raise ValueError("Innovation content contains forbidden presentation copy")
    if len(content["sections"]) != 3:
        raise ValueError("Innovation must have three sections")
    for section in content["sections"]:
        if set(section) != {"id", "title", "summary", "paragraphs", "subsections", "proposals"}:
            raise ValueError("Unexpected assessment section fields")
        if not all(isinstance(paragraph, str) for paragraph in section["paragraphs"]):
            raise ValueError("Section paragraphs must be plain text")
        for sub in section["subsections"]:
            if set(sub) != {"id", "title", "paragraphs", "tables"}:
                raise ValueError("Unexpected assessment subsection fields")
        for item in section["proposals"]:
            if set(item) != {"title", "gap", "measure", "threshold", "status"} or item["status"] != "proposal":
                raise ValueError("Assessment additions must remain explicit proposals")
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
                         "latency": metrics.get("latency_p50_s"), "cost": metrics.get("cost_per_case_usd"),
                         "p95_runs": [arm.get(key, {}).get("latency_p95_s") for key in ("first_run_metrics", "second_run_metrics")]})
        splits.append({"id": split["id"], "n": split["n"], "arms": arms,
                       "paired": split.get("paired", {}).get("gpt-6-luna", {})})
    scanner = report.get("security", {}).get("scanner", {})
    mcp = report.get("mcp", {}).get("metrics", {})
    return {"content": content, "measurements": {"retrieval": {"n": ladder.get("n_cases"), **retrieval},
             "retrieval_intervals": {key: configs.get(key, {}).get("hit@8_ci95") for key in ("R0", "R3")},
             "splits": splits, "scanner": {key: scanner.get(key, {}).get("recall", {}).get("count") for key in ("before", "after")},
             "mcp": {key: mcp.get(key) for key in ("compared_datasets", "different_outputs", "identical_datasets", "matching_refusals")}},
            "source": {"path": CONTENT, "sha256": hashlib.sha256(raw).hexdigest(),
                       "evidence_commit": report.get("provenance", {}).get("commit")}}
