"""Immutable snapshot storage and the source manifest.

Layout
  data/snapshots/<source_id>/<snapshot_id>/<file>   committed (Open Data Licence CSVs, D-004)
  data/raw/<source_id>/<snapshot_id>/<file>         gitignored (MOM PDFs/HTML, all rights reserved)
  data/manifests/manifest.json                      latest entry per source (committed)
  data/manifests/manifest_history.jsonl             append-only, one line per new snapshot (committed)

snapshot_id = <retrieval date UTC>-<first 12 hex of SHA-256 of the exact bytes>. A file whose hash
already exists for the source is never written twice.
"""

from __future__ import annotations

import json
from pathlib import Path

from labourlens import paths
from labourlens.models import SourceManifestEntry, sha256_hex


def snapshot_id_for(content: bytes, retrieval_utc: str) -> str:
    return f"{retrieval_utc[:10].replace('-', '')}-{sha256_hex(content)[:12]}"


def _primary_file(snapshot_dir: Path) -> Path | None:
    """The data file of a snapshot dir, chosen deterministically: the only non-metadata file, preferring a CSV.

    Dataset snapshot dirs also hold `<dataset_id>.metadata.json`; directory listing order must never decide `raw_path`.
    """
    files = sorted(f for f in snapshot_dir.iterdir() if f.is_file())
    data_files = [f for f in files if not f.name.endswith(".metadata.json")]
    csvs = [f for f in data_files if f.suffix.lower() == ".csv"]
    chosen = csvs or data_files
    return chosen[0] if chosen else None


def store_snapshot(
    source_id: str, content: bytes, filename: str, retrieval_utc: str, *, committed: bool
) -> tuple[str, Path, bool]:
    """Write bytes once. Returns (snapshot_id, path, newly_written).

    If any existing snapshot of this source (in either store) has the same SHA-256, that snapshot is reused so
    repeated fetches of unchanged data produce no new snapshot.
    """
    primary, other = (paths.SNAPSHOTS, paths.RAW) if committed else (paths.RAW, paths.SNAPSHOTS)
    digest12 = sha256_hex(content)[:12]
    for store in (primary, other):
        root = store / source_id
        if root.exists():
            for existing in sorted(root.iterdir()):
                if existing.is_dir() and existing.name.endswith(f"-{digest12}"):
                    found = _primary_file(existing)
                    if found:
                        return existing.name, found, False
    sid = snapshot_id_for(content, retrieval_utc)
    d = primary / source_id / sid
    d.mkdir(parents=True, exist_ok=True)
    target = d / filename
    target.write_bytes(content)
    return sid, target, True


def load_manifest() -> dict[str, SourceManifestEntry]:
    p = paths.MANIFESTS / "manifest.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text())
    return {e["source_id"]: SourceManifestEntry(**e) for e in data["entries"]}


def save_manifest(entries: dict[str, SourceManifestEntry], generated_utc: str) -> None:
    paths.MANIFESTS.mkdir(parents=True, exist_ok=True)
    body = {
        "generated_utc": generated_utc,
        "entries": [entries[k].model_dump(mode="json") for k in sorted(entries)],
    }
    (paths.MANIFESTS / "manifest.json").write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n")


def append_history(entry: SourceManifestEntry) -> None:
    paths.MANIFESTS.mkdir(parents=True, exist_ok=True)
    with (paths.MANIFESTS / "manifest_history.jsonl").open("a") as f:
        f.write(json.dumps(entry.model_dump(mode="json"), ensure_ascii=False) + "\n")
