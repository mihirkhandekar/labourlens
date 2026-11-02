"""Offline scanner-only experiment. Public outputs never include private passage text."""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone

from labourlens import paths
from labourlens.security import guards

FREEZE = paths.EXPERIMENTS / "scanner" / "freeze.json"


def sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interval(k: int, n: int) -> dict:
    """Wilson two-sided 95% score interval, including boundary observations."""
    if not n:
        return {"count": k, "n": n, "rate": None, "wilson95": None}
    z = 1.959963984540054
    p = k / n
    den = 1 + z*z/n
    centre = (p + z*z/(2*n))/den
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return {"count": k, "n": n, "rate": p, "wilson95": [max(0, centre-half), min(1, centre+half)]}


def load_cases(split: str, freeze_path=None) -> tuple[list[dict], dict]:
    if split not in {"dev", "test"}:
        raise ValueError("split must be dev or test")
    freeze_path = freeze_path or FREEZE
    manifest = json.loads(freeze_path.read_text())
    rows = []
    for kind in ("public", "private"):
        p = paths.ROOT / manifest[f"{kind}_path"]
        if not p.exists():
            raise FileNotFoundError(f"frozen {kind} input missing: {p}; no denominator reduction permitted")
        if sha(p) != manifest[f"{kind}_sha256"]:
            raise ValueError(f"frozen {kind} input hash mismatch")
        rows.extend(json.loads(line) for line in p.read_text().splitlines() if line.strip())
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("duplicate case identifiers")
    chosen = [r for r in rows if r["split"] == split]
    expected = manifest["counts"][split]
    counts = Counter("malicious" if r["malicious"] else "private_benign" if r["class"] == "private_corpus" else "synthetic_benign" for r in chosen)
    if dict(counts) != expected:
        raise ValueError(f"frozen counts differ: {dict(counts)} versus {expected}")
    return chosen, manifest


def metrics(rows: list[dict]) -> dict:
    def group(items):
        bad = [r for r in items if r["malicious"]]
        good = [r for r in items if not r["malicious"]]
        return {"recall": interval(sum(bool(r["flags"]) for r in bad), len(bad)),
                "false_positive_rate": interval(sum(bool(r["flags"]) for r in good), len(good))}
    return {**group(rows), "by_class": {c: group([r for r in rows if r["class"] == c]) for c in sorted({r["class"] for r in rows})},
            "false_negative_ids": [r["id"] for r in rows if r["malicious"] and not r["flags"]],
            "false_positive_ids": [r["id"] for r in rows if not r["malicious"] and r["flags"]]}


def run(split: str, experiment: str, profile: str | None = None) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", experiment):
        raise ValueError("experiment must be a simple new identifier")
    if not guards.guards_on():
        raise ValueError("scanner evaluation requires guards enabled")
    out = paths.EXPERIMENTS / "scanner" / experiment
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    cases, manifest = load_cases(split)
    rows = [{"id": c["id"], "malicious": c["malicious"], "class": c["class"],
             "flags": guards.injection_flags(c["text"], **({"profile": profile} if profile else {}))} for c in cases]
    result = {"config": {"split": split, "experiment": experiment, "profile": profile or "current", "guards_sha256": sha(paths.ROOT / "src/labourlens/security/guards.py"),
                         "public_sha256": manifest["public_sha256"], "private_sha256": manifest["private_sha256"],
                         "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "offline": True}, "metrics": metrics(rows)}
    out.mkdir(parents=True, exist_ok=False)
    (out / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
    # Private negatives contribute only to aggregate metrics: no source IDs, hashes or texts per passage.
    (out / "predictions.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows if r["class"] != "private_corpus"))
    print(json.dumps({"output": str(out), "recall": result["metrics"]["recall"], "false_positive_rate": result["metrics"]["false_positive_rate"]}, indent=2))
    return result
