"""Licence status reflects what was checked; snapshot file selection is deterministic; local-only files may be absent."""
import json

import pytest

from labourlens import paths
from labourlens.data import fetch, raw_store, validate
from labourlens.models import SourceManifestEntry, sha256_hex


def _prev(status):
    return SourceManifestEntry(source_id="x", source_type="dataset_csv", title="t", publisher="p", canonical_url="https://example.org",
                               release_stage="dataset_snapshot", rights_status=status)


def test_dataset_rights_default_to_assumed_and_local_only():
    assert fetch.dataset_rights({"source_id": "x"}) == ("assumed_open_unverified", "local_only")
    assert fetch.dataset_rights({"source_id": "x"}, _prev("unresolved")) == ("assumed_open_unverified", "local_only")


def test_dataset_rights_verified_only_with_a_recorded_check_or_prior_verification():
    assert fetch.dataset_rights({"licence_verified_on": "2026-11-01"}) == ("verified_open_licence", "commit_raw")
    assert fetch.dataset_rights({}, _prev("verified_open_licence")) == ("verified_open_licence", "commit_raw")
    assert fetch.dataset_rights({}, _prev("assumed_open_unverified")) == ("assumed_open_unverified", "local_only")


@pytest.mark.parametrize("meta_name", ["a.metadata.json", "z.metadata.json"])
def test_store_snapshot_reuse_returns_the_csv_not_the_metadata_file(tmp_path, monkeypatch, meta_name):
    monkeypatch.setattr(paths, "SNAPSHOTS", tmp_path / "snap")
    monkeypatch.setattr(paths, "RAW", tmp_path / "raw")
    content = b"a,b\n1,2\n"
    sid, first, new = raw_store.store_snapshot("ds", content, "d_1.csv", "2026-10-31T00:00:00+00:00", committed=True)
    assert new
    # the metadata file sorts before or after the CSV depending on its name; the CSV must win either way
    (first.parent / meta_name).write_bytes(b"{}")
    sid2, again, new2 = raw_store.store_snapshot("ds", content, "d_1.csv", "2026-11-05T00:00:00+00:00", committed=True)
    assert (sid2, new2) == (sid, False)
    assert again.name == "d_1.csv"


def test_store_snapshot_reuses_a_snapshot_found_in_the_other_store(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "SNAPSHOTS", tmp_path / "snap")
    monkeypatch.setattr(paths, "RAW", tmp_path / "raw")
    content = b"a,b\n1,2\n"
    sid, path, _ = raw_store.store_snapshot("ds", content, "d.csv", "2026-10-31T00:00:00+00:00", committed=True)
    sid2, path2, new2 = raw_store.store_snapshot("ds", content, "d.csv", "2026-11-05T00:00:00+00:00", committed=False)
    assert (sid2, path2, new2) == (sid, path, False)


def _manifest(tmp_path, monkeypatch, entries):
    mdir = tmp_path / "manifests"
    mdir.mkdir()
    (mdir / "manifest.json").write_text("{}")
    (mdir / "manifest_history.jsonl").write_text("")
    monkeypatch.setattr(paths, "ROOT", tmp_path)
    monkeypatch.setattr(paths, "MANIFESTS", mdir)
    monkeypatch.setattr(raw_store, "load_manifest", lambda: entries)
    monkeypatch.setattr(validate.catalog, "datasets", lambda: [{"source_id": s} for s in entries])
    monkeypatch.setattr(validate.catalog, "documents", lambda: [])


def _entry(sid, raw_path, data, policy):
    return SourceManifestEntry(source_id=sid, source_type="dataset_csv", title="t", publisher="p", canonical_url="https://example.org",
                               release_stage="dataset_snapshot", rights_status="assumed_open_unverified" if policy != "commit_raw" else "verified_open_licence",
                               redistribution_policy=policy, retrieval_utc="2026-10-31T00:00:00+00:00", snapshot_id="s", sha256=sha256_hex(data),
                               byte_count=len(data), mime_type="text/csv", raw_path=raw_path, retrieval_status="ok")


def test_manifest_check_reports_absent_local_only_files_without_failing(tmp_path, monkeypatch):
    entries = {"lo": _entry("lo", "data/raw/lo/s/f.csv", b"abc", "local_only")}
    _manifest(tmp_path, monkeypatch, entries)
    checks = {c["name"]: c for c in validate.check_manifest()}
    c = checks["manifest.raw_files_match_sha256"]
    assert c["status"] == "pass" and "local-only, not present" in c["detail"] and "lo" in c["detail"]


def test_manifest_check_still_fails_for_a_missing_committed_file_or_wrong_hash(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "bad.csv").write_bytes(b"changed")
    entries = {"gone": _entry("gone", "data/gone.csv", b"abc", "commit_raw"), "bad": _entry("bad", "data/bad.csv", b"abc", "commit_raw")}
    _manifest(tmp_path, monkeypatch, entries)
    c = {c["name"]: c for c in validate.check_manifest()}["manifest.raw_files_match_sha256"]
    assert c["status"] == "fail" and "file missing" in c["detail"] and "hash/size mismatch" in c["detail"]


def test_committed_manifest_marks_the_three_v3_datasets_unverified_and_local_only():
    m = json.loads((paths.MANIFESTS / "manifest.json").read_text())["entries"]
    by = {e["source_id"]: e for e in m}
    for sid in ("unit_labour_cost_index_quarterly", "value_added_per_worker_quarterly", "avg_weekly_paid_hours_quarterly"):
        assert by[sid]["rights_status"] == "assumed_open_unverified" and by[sid]["redistribution_policy"] == "local_only"
