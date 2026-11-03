"""Fetch every catalogued source, store immutable snapshots, and update the manifest.

A failure on one source is recorded (retrieval_status=failed, failure_reason set) and the run
continues; nothing is skipped silently and no failure is represented as absent data.
"""

from __future__ import annotations

import json
import sys
from typing import Iterable

from labourlens import paths
from labourlens.data import acquire, catalog, raw_store
from labourlens.models import SourceManifestEntry, sha256_hex

ODL_URL = "https://developers.data.gov.sg/open-data-licence"
ODL_NOTE = (
    "Singapore Open Data Licence v1.0 text read 2026-10-30 at the URL above. Attribution notice with "
    "licence link is required. The data.gov.sg metadata API exposes no per-dataset licence field, so the "
    "dataset-level licence label was not independently read from the (script-rendered) dataset page."
)


def dataset_rights_note(entry: dict) -> str:
    """ODL_NOTE plus an optional per-dataset caveat (`rights_note_extra`), e.g. 'to verify on dataset page' for assumed licences."""
    extra = (entry.get("rights_note_extra") or "").strip()
    return f"{ODL_NOTE} {extra}" if extra else ODL_NOTE


def dataset_rights(entry: dict, previous: SourceManifestEntry | None = None) -> tuple[str, str]:
    """(rights_status, redistribution_policy) for a dataset, from what was actually checked.

    `fetch` never reads the script-rendered dataset page, so it cannot verify a licence itself. A dataset is
    `verified_open_licence` only if a human recorded `licence_verified_on` (a date) in its spec, or its existing manifest
    entry is already verified (carried forward, never silently downgraded or upgraded). Everything else is
    `assumed_open_unverified` and kept local-only (not committed) until verified.
    """
    if entry.get("licence_verified_on") or (previous is not None and previous.rights_status == "verified_open_licence"):
        return "verified_open_licence", "commit_raw"
    return "assumed_open_unverified", "local_only"


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def fetch_datasets(fetcher: acquire.Fetcher, only: set[str] | None = None) -> list[SourceManifestEntry]:
    out: list[SourceManifestEntry] = []
    manifest = raw_store.load_manifest()
    for d in catalog.datasets():
        sid = d["source_id"]
        if only and sid not in only:
            continue
        retrieval = acquire.utc_now_iso()
        rights_status, redistribution = dataset_rights(d, manifest.get(sid))
        base = dict(
            source_id=sid,
            source_type="dataset_csv",
            title=d["title"],
            publisher=str(d["publisher"]),
            canonical_url=d["canonical_url"],
            access_method="api",
            release_stage="dataset_snapshot",
            licence_id="Singapore-Open-Data-Licence-1.0",
            licence_url=ODL_URL,
            rights_status=rights_status,
            rights_note=dataset_rights_note(d),
            redistribution_policy=redistribution,
            mime_type="text/csv",
        )
        try:
            _log(f"[fetch] {sid}: metadata")
            meta = acquire.fetch_dataset_metadata(fetcher, d["dataset_id"])
            meta_json = json.loads(meta.content)["data"]
            _log(f"[fetch] {sid}: csv (throttled)")
            csv = acquire.fetch_dataset_csv(fetcher, d["dataset_id"])
            if not csv.content.strip():
                raise acquire.AcquisitionError("empty CSV body")
            if b"\x00" in csv.content[:4096]:
                raise acquire.AcquisitionError("CSV body looks binary")
            snap, path, new = raw_store.store_snapshot(
                sid, csv.content, f"{d['dataset_id']}.csv", retrieval, committed=redistribution == "commit_raw"
            )
            meta_bytes = json.dumps(meta_json, indent=2, sort_keys=True, ensure_ascii=False).encode()
            if new:
                (path.parent / f"{d['dataset_id']}.metadata.json").write_bytes(meta_bytes)
            entry = SourceManifestEntry(
                **base,
                access_url_redacted=csv.final_url_redacted,
                retrieval_utc=retrieval,
                reporting_period_start=meta_json.get("coverageStart", "")[:10] or None,
                reporting_period_end=meta_json.get("coverageEnd", "")[:10] or None,
                publication_date=(meta_json.get("lastUpdatedAt") or "")[:10] or None,
                snapshot_id=snap,
                sha256=sha256_hex(csv.content),
                byte_count=len(csv.content),
                raw_path=paths.rel(path),
                retrieval_status="ok",
                notes=f"publication_date is the dataset lastUpdatedAt from metadata API. dataset_id={d['dataset_id']}. "
                f"managedBy={meta_json.get('managedBy')}. newly_written={new}.",
            )
            if new:
                raw_store.append_history(entry)
        except (acquire.AcquisitionError, KeyError, ValueError) as e:
            _log(f"[fetch] {sid}: FAILED {e}")
            entry = SourceManifestEntry(
                **base,
                retrieval_utc=retrieval,
                retrieval_status="failed",
                failure_reason=str(e),
                snapshot_id=manifest[sid].snapshot_id if sid in manifest else None,
            )
        out.append(entry)
        manifest[sid] = entry
        raw_store.save_manifest(manifest, acquire.utc_now_iso())
    return out


def spec_notes(entry: dict) -> str:
    """Extra manifest notes from a document spec: where the publication date is inferred rather than stated by the publisher (the
    manifest field `publication_date` is otherwise 'as stated'), and any source-specific remark."""
    out = ""
    if entry.get("publication_date_basis"):
        out += f"; publication_date_basis={entry['publication_date_basis']}"
    if entry.get("source_notes"):
        out += f"; {entry['source_notes']}"
    return out


def fetch_documents(fetcher: acquire.Fetcher, only: set[str] | None = None) -> list[SourceManifestEntry]:
    out: list[SourceManifestEntry] = []
    manifest = raw_store.load_manifest()
    for d in catalog.documents():
        sid = d["source_id"]
        if only and sid not in only:
            continue
        retrieval = acquire.utc_now_iso()
        rights = d.get("rights_status", "unresolved")
        base = dict(
            source_id=sid,
            source_type=d["source_type"],
            title=d["title"],
            publisher=d["publisher"],
            canonical_url=d["canonical_url"],
            access_method="direct_http",
            publication_date=d.get("publication_date"),
            reporting_period_start=d.get("period_start"),
            reporting_period_end=d.get("period_end"),
            release_stage=d["release_stage"],
            rights_status=rights,
            rights_note=d.get("rights_note", ""),
            redistribution_policy="local_only",
        )
        try:
            _log(f"[fetch] {sid}")
            r = acquire.fetch_document(fetcher, d["download_url"])
            ext = "pdf" if d["source_type"] == "report_pdf" else "html"
            if ext == "pdf" and not r.content.startswith(b"%PDF-"):
                raise acquire.AcquisitionError("body is not a PDF (missing %PDF- signature)")
            if ext == "html" and b"<html" not in r.content[:4096].lower():
                raise acquire.AcquisitionError("body is not HTML")
            snap, path, new = raw_store.store_snapshot(
                sid, r.content, f"{sid}.{ext}", retrieval, committed=False
            )
            entry = SourceManifestEntry(
                **base,
                access_url_redacted=r.final_url_redacted,
                retrieval_utc=retrieval,
                snapshot_id=snap,
                sha256=sha256_hex(r.content),
                byte_count=len(r.content),
                mime_type=(r.content_type or "").split(";")[0] or None,
                raw_path=paths.rel(path),
                retrieval_status="ok",
                notes=f"newly_written={new}" + spec_notes(d),
            )
            if new:
                raw_store.append_history(entry)
        except acquire.AcquisitionError as e:
            _log(f"[fetch] {sid}: FAILED {e}")
            entry = SourceManifestEntry(
                **base,
                retrieval_utc=retrieval,
                retrieval_status="failed",
                failure_reason=str(e),
                snapshot_id=manifest[sid].snapshot_id if sid in manifest else None,
            )
        out.append(entry)
        manifest[sid] = entry
        raw_store.save_manifest(manifest, acquire.utc_now_iso())
    return out


def run(kind: str = "all", only: Iterable[str] | None = None) -> None:
    only_set = set(only) if only else None
    fetcher = acquire.Fetcher()
    try:
        if kind in ("all", "documents"):
            fetch_documents(fetcher, only_set)
        if kind in ("all", "datasets"):
            fetch_datasets(fetcher, only_set)
    finally:
        fetcher.close()
