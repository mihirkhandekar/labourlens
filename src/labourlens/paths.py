from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPECS = ROOT / "specs"
DATA = ROOT / "data"
RAW = DATA / "raw"  # gitignored: report PDFs and HTML (rights not cleared for redistribution)
SNAPSHOTS = DATA / "snapshots"  # committed: Open-Data-Licence CSVs (D-004)
MANIFESTS = DATA / "manifests"
PROCESSED = DATA / "processed"
PASSAGES = DATA / "passages"  # gitignored: extracted MOM text
ARTIFACTS = ROOT / "artifacts" / "data-quality"
FIGURES = ROOT / "artifacts" / "figures"


def rel(p: Path) -> str:
    return str(p.resolve().relative_to(ROOT))

INDEX = DATA / "index"  # gitignored: chunks and indexes derived from MOM text
EXPERIMENTS = ROOT / "experiments"
