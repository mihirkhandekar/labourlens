"""Repeatable build: snapshots -> observations (Parquet) + passages (JSONL) + quality evidence.

Deterministic: same snapshots in, byte-identical Parquet/JSONL out (IDs derive from snapshot + content,
rows are sorted, timestamps are never written into data files).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from labourlens import paths
from labourlens.data import catalog, derived, html_extract, normalize, pdf_extract, raw_store, reconcile, validate
from labourlens.models import DocumentPassage, StatisticalObservation


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def build_observations() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    obs: list[dict] = []
    quarantine: list[dict] = []
    per_source: dict[str, dict] = {}
    for d in catalog.datasets():
        sid = d["source_id"]
        try:
            r = normalize.normalize(sid)
        except normalize.SpecViolation as e:
            per_source[sid] = {"status": "spec_violation", "detail": str(e)}
            _log(f"[build] {sid}: SPEC VIOLATION {e}")
            continue
        obs.extend(o.model_dump(mode="json") for o in r.observations)
        quarantine.extend(q.__dict__ for q in r.quarantined)
        per_source[sid] = {"status": "ok", "snapshot_id": r.snapshot_id, "rows_read": r.rows_read,
                           "observations": len(r.observations), "quarantined": len(r.quarantined)}
    df = pd.DataFrame(obs)
    key = ["indicator_id", "population", "adjustment", "dimension", "sector_path", "period", "source_id"]
    df = df.sort_values(key, kind="stable").reset_index(drop=True)
    q = pd.DataFrame(quarantine, columns=["source_id", "snapshot_id", "locator", "raw_value", "reason"])
    return df, q, per_source


def build_passages() -> tuple[list[DocumentPassage], list[dict]]:
    manifest = raw_store.load_manifest()
    out: list[DocumentPassage] = []
    stats: list[dict] = []
    for d in catalog.documents():
        sid = d["source_id"]
        m = manifest.get(sid)
        if not m or m.retrieval_status != "ok" or not m.raw_path:
            stats.append({"source_id": sid, "status": "not_available"})
            continue
        path = paths.ROOT / m.raw_path
        # Passage text is committed only if rights explicitly allow it. No MOM source qualifies today.
        commit_text = m.rights_status == "verified_open_licence"
        common = dict(source_id=sid, snapshot_id=m.snapshot_id, original_url=m.canonical_url, title=m.title,
                      publication_date=m.publication_date, release_stage=m.release_stage,
                      rights_status=m.rights_status, commit_text=commit_text)
        if m.source_type == "report_pdf":
            ps, st = pdf_extract.extract_pdf(path, **common)
        else:
            ps, st = html_extract.extract_html(path, **common)
        pdf_extract.write_passages(ps, paths.PASSAGES / f"{sid}.jsonl")
        st["status"] = "ok"
        stats.append(st)
        out.extend(ps)
    return out, stats


def run() -> int:
    paths.PROCESSED.mkdir(parents=True, exist_ok=True)
    paths.ARTIFACTS.mkdir(parents=True, exist_ok=True)
    _log("[build] normalizing datasets")
    obs, quarantine, per_source = build_observations()
    obs.to_parquet(paths.PROCESSED / "observations.parquet", index=False)
    quarantine.to_parquet(paths.PROCESSED / "quarantine.parquet", index=False)
    _log(f"[build] observations={len(obs)} quarantined={len(quarantine)}")

    _log("[build] derived indicators")
    der = derived.compute(obs)
    der["table"].to_parquet(paths.PROCESSED / "derived_indicators.parquet", index=False)

    _log("[build] extracting passages")
    passages, pstats = build_passages()

    _log("[build] reconciliation")
    rec = reconcile.build(obs, passages)
    (paths.ARTIFACTS / "reconciliation.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False, sort_keys=True) + "\n")

    _log("[build] validating")
    report = validate.run_all(obs, quarantine, passages, pstats, per_source, der, rec)
    (paths.ARTIFACTS / "validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    (paths.ARTIFACTS / "extraction_stats.json").write_text(json.dumps(pstats, indent=2, sort_keys=True) + "\n")
    validate.write_markdown(report, paths.ARTIFACTS / "quality-report.md")
    failed = [c for c in report["checks"] if c["status"] == "fail"]
    _log(f"[build] checks: {len(report['checks'])} total, {len(failed)} failed")
    for c in failed:
        _log(f"  FAIL {c['name']}: {c['detail']}")
    return 1 if failed else 0
