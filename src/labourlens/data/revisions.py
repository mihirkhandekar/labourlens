"""Revision tracker: which already-published values changed between two snapshots of the same dataset.

Snapshots are immutable, so refetching later (for example after the yearly seasonal-adjustment revision of
unemployment series) yields a new snapshot_id. `diff_csv` compares two raw CSV files cell by cell on their key
columns; `run` applies it to every source that has two or more snapshots on disk. With one snapshot the report
says so explicitly (baseline established); it never invents a revision.
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from labourlens import paths


def _read(path: Path) -> tuple[list[str], list[list[str]]]:
    rows = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8-sig"))))
    return rows[0], rows[1:]


def diff_csv(old: Path, new: Path, key_cols: list[str]) -> dict:
    h0, r0 = _read(old)
    h1, r1 = _read(new)
    if h0 != h1:
        added_cols = [c for c in h1 if c not in h0]
        removed_cols = [c for c in h0 if c not in h1]
    else:
        added_cols = removed_cols = []
    i0 = [h0.index(k) for k in key_cols]
    i1 = [h1.index(k) for k in key_cols]
    m0 = {tuple(r[i] for i in i0): dict(zip(h0, r)) for r in r0}
    m1 = {tuple(r[i] for i in i1): dict(zip(h1, r)) for r in r1}
    changed = []
    for k in sorted(set(m0) & set(m1)):
        for c in h0:
            if c in h1 and m0[k][c] != m1[k][c] and c not in key_cols:
                changed.append({"key": list(k), "column": c, "old": m0[k][c], "new": m1[k][c]})
    return {"added_rows": [list(k) for k in sorted(set(m1) - set(m0))], "removed_rows": [list(k) for k in sorted(set(m0) - set(m1))],
            "changed_cells": changed, "added_columns": added_cols, "removed_columns": removed_cols}


def compute() -> dict:
    """Per-source revision report from the snapshots on disk (pure: reads files, writes nothing). Used by `run` and the MCP server."""
    out = {}
    from labourlens.data import catalog

    for d in catalog.datasets():
        sid = d["source_id"]
        spec = catalog.adapter_spec(sid)
        snaps = sorted((paths.SNAPSHOTS / sid).glob("*/*.csv")) if (paths.SNAPSHOTS / sid).exists() else []
        if len(snaps) < 2:
            out[sid] = {"snapshots": len(snaps), "status": "baseline_only_no_earlier_snapshot"}
            continue
        key_cols = [spec.get("period_col") or spec["label_col"]] + ([spec["dimension_col"]] if spec.get("dimension_col") else [])
        if spec["adapter"] == "quarter_end_month":
            key_cols = [spec["period_col"]]
        out[sid] = {"snapshots": len(snaps), "old": snaps[-2].parent.name, "new": snaps[-1].parent.name, **diff_csv(snaps[-2], snaps[-1], key_cols)}
    return out


def run() -> int:
    out = compute()
    paths.ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (paths.ARTIFACTS / "revisions.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v.get("status") or f"{len(v['changed_cells'])} changed cells" for k, v in out.items()}, indent=1))
    return 0
