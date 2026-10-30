"""`labourlens trace <id>`: observation_id / passage_id -> source cell/page -> snapshot -> URL."""

from __future__ import annotations

import csv
import io
import json
import re
import sys

import pandas as pd

from labourlens import paths
from labourlens.data import raw_store


def _csv_line(raw_path: str, row_no: int) -> list[str]:
    text = (paths.ROOT / raw_path).read_text(encoding="utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    return rows[row_no - 1]


def observation_provenance(o: dict, m) -> dict:
    """Provenance of one observation row `o` (a dict from observations.parquet) given its manifest entry `m`: the same facts `run`
    prints for an observation. Observations only; it never touches report passages. Used by the MCP get_provenance tool."""
    rm = re.search(r"csv_row=(\d+)", o["source_locator"] or "")
    return {"observation_id": o["observation_id"], "source_id": m.source_id, "title": m.title, "publisher": m.publisher,
            "canonical_url": m.canonical_url, "publication_date": m.publication_date, "retrieved_utc": m.retrieval_utc,
            "snapshot_id": m.snapshot_id, "sha256": m.sha256, "file": m.raw_path, "licence_id": m.licence_id, "licence_url": m.licence_url,
            "source_locator": o["source_locator"], "raw_csv_line": int(rm.group(1)) if rm else None,
            "source_period_raw": o["source_period_raw"], "raw_value": o["raw_value"], "missing_reason": o["missing_reason"],
            "transformation_version": o["transformation_version"]}


def run(ident: str) -> int:
    manifest = raw_store.load_manifest()
    obs_path = paths.PROCESSED / "observations.parquet"
    if obs_path.exists():
        obs = pd.read_parquet(obs_path)
        hit = obs[obs.observation_id == ident]
        if len(hit):
            o = hit.iloc[0].to_dict()
            m = manifest[o["source_id"]]
            print("OBSERVATION")
            for k in ("observation_id", "indicator_id", "period", "value", "raw_value", "missing_reason", "unit", "population",
                      "adjustment", "dimension", "sector_path", "in_answer_scope", "transformation_version"):
                print(f"  {k}: {o[k]}")
            print("SOURCE")
            print(f"  source_id: {m.source_id}\n  title: {m.title}\n  publisher: {m.publisher}\n  canonical_url: {m.canonical_url}")
            print(f"  dataset last updated (publisher): {m.publication_date}\n  retrieved_utc: {m.retrieval_utc}")
            print(f"  snapshot_id: {m.snapshot_id}\n  sha256: {m.sha256}\n  file: {m.raw_path}\n  licence: {m.licence_id} ({m.licence_url})")
            rm = re.search(r"csv_row=(\d+)", o["source_locator"])
            if rm:
                row = _csv_line(m.raw_path, int(rm.group(1)))
                print(f"LINEAGE\n  locator: {o['source_locator']}\n  raw CSV line {rm.group(1)}: {row[:6]}{' ...' if len(row) > 6 else ''}")
            return 0
    for f in sorted(paths.PASSAGES.glob("*.jsonl")) if paths.PASSAGES.exists() else []:
        for line in f.read_text().splitlines():
            if ident in line[:200]:
                p = json.loads(line)
                if p["passage_id"] != ident:
                    continue
                m = manifest[p["source_id"]]
                print("PASSAGE")
                for k in ("passage_id", "document_title", "publication_date", "release_stage", "locator", "section_heading",
                          "quality_flag", "quality_note", "extraction_method", "parser_version", "rights_status", "text_sha256"):
                    print(f"  {k}: {p[k]}")
                print(f"  text (local only; rights={p['rights_status']}): {p['text'][:300]!r}")
                print(f"SOURCE\n  canonical_url: {m.canonical_url}\n  snapshot_id: {m.snapshot_id}\n  sha256: {m.sha256}\n  file: {m.raw_path}")
                return 0
    print(f"id not found: {ident}", file=sys.stderr)
    return 1
